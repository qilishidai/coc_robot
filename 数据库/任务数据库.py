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
    雷电模拟器索引: int = field(
        default=1,
        metadata={
            "显示名称": "模拟器索引",
            "描述": "对应雷电多开器中的模拟器ID，0表示第一个模拟器",
            "UI类型": "spinbox",
            "最小值": 0,
            "最大值": 99,
            "步进": 1
        }
    )

    服务器: str = field(
        default="国际服",
        metadata={
            "显示名称": "服务器",
            "描述": "选择游戏服务器版本，目前只支持国际服",
            "UI类型": "combo",
            "选项": ["国际服", "调试服务器"]
        }
    )

    部落冲突包名: str | None = field(
        default=None,
        metadata={
            "显示名称": "包名",
            "描述": "游戏包名，自动根据服务器设置",
            "UI类型": "hidden"  # 隐藏字段，不在UI中显示
        }
    )

    欲进攻的最小资源: int = field(
        default=700000,
        metadata={
            "显示名称": "最小资源",
            "描述": "搜索村庄对方必须高过的资源总量，超过该值才会触发进攻",
            "UI类型": "entry"
        }
    )

    欲进攻资源建筑靠近地图边缘最小比例: float = field(
        default=0.5,
        metadata={
            "显示名称": "资源边缘比例",
            "描述": "资源建筑靠近地图边缘的比例下限（0-1），高本建议0.6，低本可设为0",
            "UI类型": "entry"
        }
    )

    开启刷墙: bool = field(
        default=False,
        metadata={
            "显示名称": "是否开启刷墙",
            "描述": "是否使用金币或圣水刷墙",
            "UI类型": "bool"
        }
    )

    刷墙起始金币: int = field(
        default=100000,
        metadata={
            "显示名称": "刷墙起始金币",
            "描述": "金币高于此数值触发刷墙任务",
            "UI类型": "entry"
        }
    )

    刷墙起始圣水: int = field(
        default=100000,
        metadata={
            "显示名称": "刷墙起始圣水",
            "描述": "圣水高于此数值触发刷墙任务，低本建议设置较大值避免误触发",
            "UI类型": "entry"
        }
    )

    是否刷主世界: bool = field(
        default=True,
        metadata={
            "显示名称": "是否刷主世界",
            "描述": "是否启用主世界打鱼模式",
            "UI类型": "bool"
        }
    )

    是否刷夜世界: bool = field(
        default=False,
        metadata={
            "显示名称": "是否刷夜世界",
            "描述": "是否启用夜世界打鱼模式",
            "UI类型": "bool"
        }
    )

    是否刷天鹰火炮: bool = field(
        default=False,
        metadata={
            "显示名称": "是否刷天鹰火炮",
            "描述": "开启后会自动搜索天鹰火炮并使用雷电法术攻击，用于刷成就",
            "UI类型": "bool"
        }
    )
    是否快速刷资源: bool = field(
        default=False,
        metadata={
            "显示名称": "是否快速刷资源（速刷模式）",
            "描述": "开启后下兵和法术后等待4-7秒直接放弃战斗回营，不等待战斗自然结束。，建议使用快速下兵的兵种[瓦基丽武神]。加上下兵的时间，一场战斗大概14秒进攻完毕。谨慎开启，速度太快容易封控！！想要使用推荐12本后开启",
            "UI类型": "bool"
        }
    )

    欲升级的英雄或建筑: List[str] = field(
        default_factory=lambda: ["弓箭女皇", "亡灵王子", "飞盾战神"],
        metadata={
            "显示名称": "欲升级的英雄或建筑",
            "描述": "选择想要升级的英雄或建筑，可多选、添加自定义项",
            "UI类型": "editable_list",
            "默认选项": ["野蛮人之王", "弓箭女皇", "亡灵王子", "飞盾战神", "大守护者"]
        }
    )

    是否升级建议升级的建筑: bool = field(
        default=True,
        metadata={
            "显示名称": "升级建议建筑",
            "描述": "是否自动升级系统建议的建筑",
            "UI类型": "bool"
        }
    )

    建筑升级检查间隔: float = field(
        default=0.0,
        metadata={
            "显示名称": "建筑升级检查间隔(小时)",
            "描述": "检查建筑升级的时间间隔，单位为小时，0表示每次都检查",
            "UI类型": "entry"
        }
    )

    欲升级的战宠: str = field(
        default="",
        metadata={
            "显示名称": "要自动升级的战宠",
            "描述": "选择要自动升级的战宠，空白则不启动自动升级",
            "UI类型": "combo",
            "选项": ["", "莱希","闪枭","大耗","独角","冰牙","地兽","猛蜥","凤凰","灵狐","愤怒水母","阿啾"]
        }
    )

    战宠升级检查间隔: float = field(
        default=0.0,
        metadata={
            "显示名称": "战宠升级检查间隔(小时)",
            "描述": "检查建筑升级的时间间隔，单位为小时，0表示每次都检查",
            "UI类型": "entry"
        }
    )

    欲升级的兵种或法术: str = field(
        default="",
        metadata={
            "显示名称": "要自动升级的兵种或法术",
            "描述": "选择要自动研究升级的兵种或法术，空白则不启动自动升级",
            "UI类型": "combo",
            "选项": [
                "",
                # 圣水兵种
                "野蛮人", "弓箭手", "哥布林", "巨人", "炸弹人", "气球兵",
                "法师", "天使", "飞龙", "皮卡超人", "飞龙宝宝", "掘地矿工",
                "雷电飞龙", "大雪怪", "龙骑士", "雷霆泰坦", "根蔓骑士",
                "巨矛投手", "陨石戈仑",
                # 黑油兵种
                "亡灵", "野猪骑士", "瓦基丽武神", "戈仑石人", "女巫",
                "熔岩猎犬", "巨石投手", "戈仑冰人", "英雄猎手", "守护者学徒",
                "德鲁伊", "烈焰熔炉",
                # 攻城器械
                "攻城战车", "攻城飞艇", "攻城气球", "攻城训练营", "攻城滚木车","攻城烈焰车","攻城钻机","部队发射器",
                # 法术
                "雷电法术", "疗伤法术", "狂暴法术", "弹跳法术", "冰冻法术",
                "镜像法术","隐形法术", "回溯法术", "复苏法术","图腾法术",
                "伤害药水法术", "地震法术", "急速法术", "骷髅法术", "蝙蝠法术",
                "疯狂蔓生法术", "冰障法术"
            ]
        }
    )

    研究升级检查间隔: float = field(
        default=1.0,
        metadata={
            "显示名称": "研究升级检查间隔(小时)",
            "描述": "检查兵种或法术研究升级的时间间隔，单位为小时，0表示每次都检查",
            "UI类型": "entry"
        }
    )

    是否采集进攻界面图像: bool = field(
        default=False,
        metadata={
            "显示名称": "是否采集进攻界面图像",
            "描述": "开启此选项后，每搜索一次村庄都会截图一张保存到磁盘中，保存在项目路径的数据集文件夹中，采集的图片用于训练yolo模型，此选项为高级用户使用",
            "UI类型": "bool"
        }
    )

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
        self._执行数据迁移()

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

    def _执行数据迁移(self):
        """执行数据库字段迁移，确保兼容性

        迁移内容：
        - 欲升级的英雄 -> 欲升级的英雄或建筑
        """
        字段映射 = {
            "欲升级的英雄": "欲升级的英雄或建筑"
        }

        with self._获取连接() as conn:
            结果列表 = conn.execute("SELECT 机器人标志, 设置JSON FROM 机器人设置").fetchall()

            for 机器人标志, 设置JSON in 结果列表:
                配置字典 = json.loads(设置JSON)
                需要更新 = False

                # 检查并迁移旧字段名
                for 旧字段名, 新字段名 in 字段映射.items():
                    if 旧字段名 in 配置字典:
                        # 如果新字段名不存在，则迁移旧值
                        if 新字段名 not in 配置字典:
                            配置字典[新字段名] = 配置字典[旧字段名]
                        # 删除旧字段名
                        del 配置字典[旧字段名]
                        需要更新 = True

                # 如果有修改，保存回数据库
                if 需要更新:
                    conn.execute(
                        "UPDATE 机器人设置 SET 设置JSON = ? WHERE 机器人标志 = ?",
                        (json.dumps(配置字典), 机器人标志)
                    )

            if 结果列表:
                conn.commit()
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
