# ==== 数据库管理 ====
import json
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class 任务日志:
    机器人标志: str
    日志内容: str
    记录时间: float
    下次超时: float

@dataclass
class 机器人设置:
    雷电模拟器索引:int=1
    服务器:str="国际服"
    部落冲突包名: str | None = None
    欲进攻的最小资源:int=700000
    欲进攻资源建筑靠近地图边缘最小比例:float=0.5
    开启刷墙:bool=False
    刷墙起始金币:int=100000
    刷墙起始圣水: int = 100000
    是否刷主世界:bool=True
    是否刷夜世界:bool=False
    是否刷天鹰火炮:bool=False  # 天鹰火炮成就刷取，默认关闭
    欲升级的英雄: List[str]=field(default_factory=lambda: [ "弓箭女皇", "亡灵王子", "飞盾战神"])

    def __post_init__(self):
        self.部落冲突包名 = ("com.supercell.clashofclans"
                        if self.服务器 == "国际服" else
                             "com.atrasis.original.emulator")
                        # "com.tencent.tmgp.supercell.clashofclans")

@dataclass
class 运行时状态:
    机器人标志: str
    记录时间: float
    状态数据: Dict[str, Any]  # 使用中文键存储状态


class 任务数据库:
    """集成化数据库管理"""

    def __init__(self, 文件路径=os.path.join(os.path.dirname(__file__), '任务系统.db')):
        self.文件路径 = 文件路径
        self._初始化表结构()

    def _获取连接(self):
        """获取线程安全连接"""
        conn = sqlite3.connect(
            self.文件路径,
            check_same_thread=False,
            timeout=15
        )
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _初始化表结构(self):
        """初始化所有数据库表"""
        with self._获取连接() as conn:
            # 状态记录表（支持任意状态类型）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS 运行时状态 (
                    记录ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    机器人标志 TEXT NOT NULL,
                    记录时间 REAL NOT NULL,
                    状态类型 TEXT NOT NULL,  -- 如：resources/builder/upgrade_queue
                    状态值 TEXT NOT NULL    -- JSON格式存储
                )""")


            # 任务日志表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS 任务日志 (
                    记录ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    机器人标志 TEXT NOT NULL,
                    日志内容 TEXT,
                    记录时间 REAL NOT NULL,
                    下次超时 REAL NOT NULL
                )""")

            # 机器人设置表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS 机器人设置 (
                    机器人标志 TEXT PRIMARY KEY,
                    设置JSON TEXT
                )""")

            # 系统配置表（用于存储协议同意状态等全局配置）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS 系统配置 (
                    配置键 TEXT PRIMARY KEY,
                    配置值 TEXT,
                    更新时间 REAL
                )""")

            # 任务参数表（存储任务的配置参数）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS 任务参数 (
                    机器人标志 TEXT NOT NULL,
                    任务类名 TEXT NOT NULL,
                    参数名 TEXT NOT NULL,
                    参数值 TEXT NOT NULL,  -- JSON格式
                    更新时间 REAL,
                    PRIMARY KEY (机器人标志, 任务类名, 参数名)
                )""")

            # 任务状态表（存储任务运行时的状态）
            conn.execute("""
                CREATE TABLE IF NOT EXISTS 任务状态 (
                    机器人标志 TEXT NOT NULL,
                    任务类名 TEXT NOT NULL,
                    状态键 TEXT NOT NULL,
                    状态值 TEXT NOT NULL,  -- JSON格式
                    更新时间 REAL,
                    PRIMARY KEY (机器人标志, 任务类名, 状态键)
                )""")


    # ==== 日志操作 ====
    def 记录日志(self, 机器人标志: str, 日志内容: str, 下次超时: float):
        """原子化日志记录
        下次超时:为下次超时的时间戳
        """
        with self._获取连接() as conn:
            游标 = conn.execute(
                "INSERT INTO 任务日志 (机器人标志, 日志内容, 记录时间, 下次超时) VALUES (?, ?, ?, ?)",
                (机器人标志, 日志内容, time.time(), 下次超时)
            )

            conn.commit()

    def 读取最后日志(self, 机器人标志: str) -> 任务日志:
        """获取最后有效日志"""
        with self._获取连接() as conn:
            结果 = conn.execute("""
                SELECT 日志内容, 记录时间, 下次超时 
                FROM 任务日志 
                WHERE 机器人标志 = ?
                ORDER BY 记录ID DESC 
                LIMIT 1
            """, (机器人标志,)).fetchone()
        return 任务日志(机器人标志, *结果) if 结果 else None

    def 查询日志历史(self, 机器人标志: str, 起始时间: float = 0, 截止时间: float = None, 最大条数: int = 100) -> List[任务日志]:
        """查询用户的历史日志（可指定时间范围与返回数量）"""
        if 截止时间 is None:
            截止时间 = time.time()
        with self._获取连接() as conn:
            结果列表 = conn.execute("""
                SELECT 日志内容, 记录时间, 下次超时
                FROM 任务日志
                WHERE 机器人标志 = ? AND 记录时间 BETWEEN ? AND ?
                ORDER BY 记录时间 DESC
                LIMIT ?
            """, (机器人标志, 起始时间, 截止时间, 最大条数)).fetchall()
        return [任务日志(机器人标志, *行) for 行 in 结果列表]

    # ==== 设置管理 ====
    def 保存机器人设置(self, 机器人标志: str, 设置: 机器人设置):
        """保存用户配置"""
        with self._获取连接() as conn:
            conn.execute(
                "INSERT INTO 机器人设置 VALUES (?, ?) ON CONFLICT DO UPDATE SET 设置JSON=excluded.设置JSON",
                (机器人标志, json.dumps(设置.__dict__))
            )
            conn.commit()

    def 获取机器人设置(self, 机器人标志: str) -> 机器人设置:
        """加载用户配置"""
        with self._获取连接() as conn:
            结果 = conn.execute(
                "SELECT 设置JSON FROM 机器人设置 WHERE 机器人标志 = ?",
                (机器人标志,)
            ).fetchone()
        return 机器人设置(**json.loads(结果[0])) if 结果 else 机器人设置()

    def 查询所有机器人设置(self) -> Dict[str, 机器人设置]:
        """获取数据库中所有机器人的设置"""
        所有设置 = {}
        with self._获取连接() as conn:
            结果列表 = conn.execute("SELECT 机器人标志, 设置JSON FROM 机器人设置").fetchall()
            for 机器人标志, 设置JSON in 结果列表:
                所有设置[机器人标志] = 机器人设置(**json.loads(设置JSON))
        return 所有设置

    def 删除机器人设置(self, 机器人标志: str):
        """删除指定机器人的设置"""
        with self._获取连接() as conn:
            conn.execute("DELETE FROM 机器人设置 WHERE 机器人标志 = ?", (机器人标志,))
            conn.commit()

    # ==== 状态操作 ====
    def 更新状态(self, 机器人标志: str, 状态类型: str, 状态数据: Any):
        """原子化状态更新（保留历史记录）"""
        with self._获取连接() as conn:
            conn.execute(
                """INSERT INTO 运行时状态 
                (机器人标志, 记录时间, 状态类型, 状态值)
                VALUES (?, ?, ?, ?)""",
                (机器人标志, time.time(), 状态类型, json.dumps(状态数据))
            )
            conn.commit()

    def 获取所有状态类型(self, 机器人标志: str = None) -> List[str]:
        """从数据库动态获取所有出现过的状态类型"""
        with self._获取连接() as conn:
            if 机器人标志:
                # 获取指定机器人的状态类型
                结果 = conn.execute("""
                    SELECT DISTINCT 状态类型 
                    FROM 运行时状态 
                    WHERE 机器人标志 = ?
                    ORDER BY 状态类型
                """, (机器人标志,)).fetchall()
            else:
                # 获取所有状态类型
                结果 = conn.execute("""
                    SELECT DISTINCT 状态类型 
                    FROM 运行时状态 
                    ORDER BY 状态类型
                """).fetchall()

        return [行[0] for 行 in 结果] if 结果 else []

    def 获取最新完整状态(self, 机器人标志: str) -> 运行时状态:
        """合并所有类型的最新状态"""
        完整状态 = {}
        # 动态获取该机器人有记录的状态类型
        状态类型列表 = self.获取所有状态类型(机器人标志)
        # 状态类型列表 = ['资源', '建筑工人', '升级队列', '部落战']  # 可扩展中文类型

        with self._获取连接() as conn:
            for 类型 in 状态类型列表:
                结果 = conn.execute("""
                    SELECT 状态值 
                    FROM 运行时状态 
                    WHERE 机器人标志 = ? AND 状态类型 = ?
                    ORDER BY 记录ID DESC 
                    LIMIT 1
                """, (机器人标志, 类型)).fetchone()

                if 结果:
                    完整状态[类型] = json.loads(结果[0])

        return 运行时状态(
            机器人标志=机器人标志,
            记录时间=time.time(),
            状态数据=完整状态
        )


    # ==== 系统配置操作 ====
    def 检查协议是否已同意(self) -> bool:
        """检查用户是否已同意协议"""
        with self._获取连接() as conn:
            结果 = conn.execute(
                "SELECT 配置值 FROM 系统配置 WHERE 配置键 = ?",
                ("协议已同意",)
            ).fetchone()
        return 结果 is not None and 结果[0] == "true"

    def 保存协议同意记录(self):
        """保存用户同意协议的记录"""
        with self._获取连接() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO 系统配置 VALUES (?, ?, ?)",
                ("协议已同意", "true", time.time())
            )
            conn.commit()

    def 撤销协议同意(self):
        """撤销用户协议同意记录，下次启动将重新显示协议"""
        with self._获取连接() as conn:
            conn.execute(
                "DELETE FROM 系统配置 WHERE 配置键 = ?",
                ("协议已同意",)
            )
            conn.commit()

    def 获取状态历史(self, 机器人标志: str,
                     状态类型: Optional[str] = None,
                     起始时间: float = 0,
                     截止时间: float = None,
                     最大条数: int = 500) -> List[Dict]:
        """通用历史查询"""
        截止时间 = 截止时间 or time.time()
        查询参数 = [机器人标志, 起始时间, 截止时间, 最大条数]
        类型条件 = ""

        if 状态类型:
            类型条件 = "AND 状态类型 = ?"
            查询参数.insert(3, 状态类型)

        with self._获取连接() as conn:
            records = conn.execute(f"""
                SELECT 记录时间, 状态类型, 状态值
                FROM 运行时状态
                WHERE 机器人标志 = ?
                  AND 记录时间 BETWEEN ? AND ?
                  {类型条件}
                ORDER BY 记录时间 DESC
                LIMIT ?
            """, 查询参数).fetchall()

        return [{
            "时间": row[0],
            "类型": row[1],
            "数据": json.loads(row[2])
        } for row in records]

    # ==== 任务参数操作 ====
    def 保存任务参数(self, 机器人标志: str, 任务类名: str, 参数字典: Dict[str, Any]):
        """保存任务的所有参数"""
        with self._获取连接() as conn:
            for 参数名, 参数值 in 参数字典.items():
                conn.execute("""
                    INSERT OR REPLACE INTO 任务参数
                    (机器人标志, 任务类名, 参数名, 参数值, 更新时间)
                    VALUES (?, ?, ?, ?, ?)
                """, (机器人标志, 任务类名, 参数名, json.dumps(参数值), time.time()))
            conn.commit()

    def 获取任务参数(self, 机器人标志: str, 任务类名: str) -> Dict[str, Any]:
        """获取任务的所有参数"""
        with self._获取连接() as conn:
            结果列表 = conn.execute("""
                SELECT 参数名, 参数值
                FROM 任务参数
                WHERE 机器人标志 = ? AND 任务类名 = ?
            """, (机器人标志, 任务类名)).fetchall()

        return {行[0]: json.loads(行[1]) for 行 in 结果列表} if 结果列表 else {}

    def 删除任务参数(self, 机器人标志: str, 任务类名: str = None):
        """删除任务参数（不指定任务类名则删除该机器人的所有任务参数）"""
        with self._获取连接() as conn:
            if 任务类名:
                conn.execute("DELETE FROM 任务参数 WHERE 机器人标志 = ? AND 任务类名 = ?",
                           (机器人标志, 任务类名))
            else:
                conn.execute("DELETE FROM 任务参数 WHERE 机器人标志 = ?", (机器人标志,))
            conn.commit()

    # ==== 任务状态操作 ====
    def 保存任务状态(self, 机器人标志: str, 任务类名: str, 状态字典: Dict[str, Any]):
        """保存任务的状态数据"""
        with self._获取连接() as conn:
            for 状态键, 状态值 in 状态字典.items():
                conn.execute("""
                    INSERT OR REPLACE INTO 任务状态
                    (机器人标志, 任务类名, 状态键, 状态值, 更新时间)
                    VALUES (?, ?, ?, ?, ?)
                """, (机器人标志, 任务类名, 状态键, json.dumps(状态值), time.time()))
            conn.commit()

    def 获取任务状态(self, 机器人标志: str, 任务类名: str) -> Dict[str, Any]:
        """获取任务的状态数据"""
        with self._获取连接() as conn:
            结果列表 = conn.execute("""
                SELECT 状态键, 状态值
                FROM 任务状态
                WHERE 机器人标志 = ? AND 任务类名 = ?
            """, (机器人标志, 任务类名)).fetchall()

        return {行[0]: json.loads(行[1]) for 行 in 结果列表} if 结果列表 else {}

    def 删除任务状态(self, 机器人标志: str, 任务类名: str = None):
        """删除任务状态（不指定任务类名则删除该机器人的所有任务状态）"""
        with self._获取连接() as conn:
            if 任务类名:
                conn.execute("DELETE FROM 任务状态 WHERE 机器人标志 = ? AND 任务类名 = ?",
                           (机器人标志, 任务类名))
            else:
                conn.execute("DELETE FROM 任务状态 WHERE 机器人标志 = ?", (机器人标志,))
            conn.commit()

    def 获取所有任务参数配置(self, 机器人标志: str) -> Dict[str, Dict[str, Any]]:
        """获取该机器人所有任务的参数配置 {任务类名: {参数名: 参数值}}"""
        with self._获取连接() as conn:
            结果列表 = conn.execute("""
                SELECT 任务类名, 参数名, 参数值
                FROM 任务参数
                WHERE 机器人标志 = ?
            """, (机器人标志,)).fetchall()

        配置字典 = {}
        for 任务类名, 参数名, 参数值 in 结果列表:
            if 任务类名 not in 配置字典:
                配置字典[任务类名] = {}
            配置字典[任务类名][参数名] = json.loads(参数值)

        return 配置字典



if __name__ == "__main__":
    数据库 = 任务数据库()

    # 1. 保存和读取机器人设置
    设置 = 机器人设置(雷电模拟器索引=2, 服务器="国服")
    数据库.保存机器人设置("机器人001", 设置)

    获取的设置 = 数据库.获取机器人设置("机器人001")
    print("获取的设置：", 获取的设置)

    # 2. 记录和查询日志
    数据库.记录日志("机器人001", "任务启动成功", time.time() + 60)

    最后一条日志 = 数据库.读取最后日志("机器人001")
    print("最后一条日志：", 最后一条日志)

    日志列表 = 数据库.查询日志历史("机器人001", 最大条数=5)
    print("历史日志：")
    for 日志 in 日志列表:
        print(f"[{time.ctime(日志.记录时间)}] {日志.日志内容}")

    # 查询一个没有设置记录的机器人
    默认设置 = 数据库.获取机器人设置("机器人002")
    print("默认设置：", 默认设置)

    # 3. 更新和读取状态信息
    数据库.更新状态("机器人001", "资源", {
        "金币": 1500000,
        "圣水": 800000,
        "暗黑重油": 2000
    })

    数据库.更新状态("机器人001", "建筑工人", {
        "空闲工人": 2,
        "工人总数": 5
    })

    数据库.更新状态("机器人001", "升级队列", {
        "当前升级": "箭塔",
        "剩余时间": 3600
    })

    当前状态 = 数据库.获取最新完整状态("模拟器索引0")
    print("当前完整状态：")
    for 类型, 数据 in 当前状态.状态数据.items():
        print(f"- {类型}：{数据}")

    # 查询资源状态的历史记录    当前状态 = 数据库.获取最新完整状态("模拟器索引0")
    #     print("当前完整状态：")
    #     for 类型, 数据 in 当前状态.状态数据.items():
    #         print(f"- {类型}：{数据}")
    print("资源状态历史：")
    for 记录 in 数据库.获取状态历史("机器人001", "资源"):
        print(f"[{time.ctime(记录['时间'])}] {记录['数据']}")

    全部设置 = 数据库.查询所有机器人设置()
    print("全部机器人设置：")
    for 标志, 设置 in 全部设置.items():
        print(f"{标志} -> {设置}")


    print(数据库.获取最新完整状态("模拟器索引0").状态数据["家乡资源"]["金币"])