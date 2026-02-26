"""
自动启动管理器 - 封装Windows计划任务的操作
用户无需关心bat文件和计划任务的细节
"""
import subprocess
import os
from pathlib import Path
from typing import Optional, List, Dict
import json


class 自动启动管理器:
    """管理机器人的自动启动计划任务"""

    def __init__(self, 项目根目录: str = None):
        """
        初始化管理器
        :param 项目根目录: 项目根目录路径，默认为当前文件的上级目录
        """
        if 项目根目录 is None:
            项目根目录 = Path(__file__).parent.parent.absolute()
        self.项目根目录 = Path(项目根目录)
        self.配置文件路径 = self.项目根目录 / "自动启动配置.json"
        self.bat文件目录 = self.项目根目录 / "自动启动脚本"
        self.bat文件目录.mkdir(exist_ok=True)

    def 获取所有自动启动配置(self) -> Dict[str, dict]:
        """
        获取所有机器人的自动启动配置
        :return: {机器人标识: {启用: bool, 时间: str, 任务名称: str}}
        """
        if not self.配置文件路径.exists():
            return {}

        try:
            with open(self.配置文件路径, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return {}

    def 保存自动启动配置(self, 配置数据: Dict[str, dict]):
        """
        保存所有自动启动配置到文件
        :param 配置数据: 配置字典
        """
        try:
            with open(self.配置文件路径, 'w', encoding='utf-8') as f:
                json.dump(配置数据, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            raise

    def 设置机器人自动启动(self, 机器人标识: str, 启动时间: str, 使用虚拟环境: bool = True) -> bool:
        """
        为指定机器人设置自动启动
        :param 机器人标识: 机器人的唯一标识
        :param 启动时间: 启动时间，格式为 "HH:MM"，例如 "09:00"
        :param 使用虚拟环境: 是否使用虚拟环境启动
        :return: 是否设置成功
        """
        try:
            # 1. 生成bat文件
            bat文件路径 = self._生成bat文件(机器人标识, 使用虚拟环境)

            # 2. 创建计划任务
            任务名称 = f"COC_Robot_{机器人标识}"
            self._创建计划任务(任务名称, bat文件路径, 启动时间)

            # 3. 保存配置
            所有配置 = self.获取所有自动启动配置()
            所有配置[机器人标识] = {
                "启用": True,
                "时间": 启动时间,
                "任务名称": 任务名称,
                "bat文件": str(bat文件路径),
                "使用虚拟环境": 使用虚拟环境
            }
            self.保存自动启动配置(所有配置)

            return True
        except Exception as e:
            print(f"设置自动启动失败: {e}")
            return False

    def 取消机器人自动启动(self, 机器人标识: str) -> bool:
        """
        取消指定机器人的自动启动
        :param 机器人标识: 机器人的唯一标识
        :return: 是否取消成功
        """
        try:
            所有配置 = self.获取所有自动启动配置()

            if 机器人标识 not in 所有配置:
                return True  # 本来就没有配置，视为成功

            配置 = 所有配置[机器人标识]
            任务名称 = 配置.get("任务名称")

            # 1. 删除计划任务
            if 任务名称:
                self._删除计划任务(任务名称)

            # 2. 删除bat文件
            bat文件路径 = 配置.get("bat文件")
            if bat文件路径 and Path(bat文件路径).exists():
                Path(bat文件路径).unlink()

            # 3. 更新配置
            del 所有配置[机器人标识]
            self.保存自动启动配置(所有配置)

            return True
        except Exception as e:
            print(f"取消自动启动失败: {e}")
            return False

    def 更新机器人启动时间(self, 机器人标识: str, 新时间: str) -> bool:
        """
        更新机器人的启动时间
        :param 机器人标识: 机器人的唯一标识
        :param 新时间: 新的启动时间，格式为 "HH:MM"
        :return: 是否更新成功
        """
        所有配置 = self.获取所有自动启动配置()

        if 机器人标识 not in 所有配置:
            return False

        配置 = 所有配置[机器人标识]
        使用虚拟环境 = 配置.get("使用虚拟环境", True)

        # 重新设置（会覆盖旧的计划任务）
        return self.设置机器人自动启动(机器人标识, 新时间, 使用虚拟环境)

    def 获取机器人自动启动状态(self, 机器人标识: str) -> Optional[dict]:
        """
        获取指定机器人的自动启动状态
        :param 机器人标识: 机器人的唯一标识
        :return: 配置信息字典，如果未配置则返回None
        """
        所有配置 = self.获取所有自动启动配置()
        return 所有配置.get(机器人标识)

    def 检查计划任务是否存在(self, 任务名称: str) -> bool:
        """
        检查Windows计划任务是否存在
        :param 任务名称: 任务名称
        :return: 是否存在
        """
        try:
            cmd = ["schtasks", "/Query", "/TN", 任务名称]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk')
            return result.returncode == 0
        except Exception:
            return False

    def _生成bat文件(self, 机器人标识: str, 使用虚拟环境: bool) -> Path:
        """
        生成启动bat文件
        :param 机器人标识: 机器人标识
        :param 使用虚拟环境: 是否使用虚拟环境
        :return: bat文件路径
        """
        bat文件名 = f"启动_{机器人标识}.bat"
        bat文件路径 = self.bat文件目录 / bat文件名

        # 构建bat文件内容
        bat内容 = "@echo off\n"
        bat内容 += f"cd /d {self.项目根目录}\n"

        if 使用虚拟环境:
            bat内容 += "call .venv\\Scripts\\activate.bat\n"

        bat内容 += f"python 主入口.py --机器人 标志={机器人标识}\n"

        # 写入文件
        with open(bat文件路径, 'w', encoding='utf-8-sig') as f:
            f.write(bat内容)

        return bat文件路径

    def _创建计划任务(self, 任务名称: str, bat文件路径: Path, 启动时间: str):
        """
        创建Windows计划任务
        :param 任务名称: 任务名称
        :param bat文件路径: bat文件的完整路径
        :param 启动时间: 启动时间，格式为 "HH:MM"
        """
        cmd = [
            "schtasks",
            "/Create",
            "/TN", 任务名称,
            "/TR", str(bat文件路径),
            "/SC", "DAILY",
            "/ST", 启动时间,
            "/F"  # 强制创建，如果已存在则覆盖
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk')

        if result.returncode != 0:
            raise Exception(f"创建计划任务失败: {result.stderr}")

    def _删除计划任务(self, 任务名称: str):
        """
        删除Windows计划任务
        :param 任务名称: 任务名称
        """
        cmd = ["schtasks", "/Delete", "/TN", 任务名称, "/F"]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk')

        if result.returncode != 0:
            # 如果任务不存在，也不算错误
            if "找不到" not in result.stderr and "cannot find" not in result.stderr.lower():
                raise Exception(f"删除计划任务失败: {result.stderr}")

    def 获取所有计划任务列表(self) -> List[str]:
        """
        获取所有COC_Robot相关的计划任务
        :return: 任务名称列表
        """
        try:
            cmd = ["schtasks", "/Query", "/FO", "LIST"]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='gbk')

            if result.returncode != 0:
                return []

            # 解析输出，找到所有COC_Robot开头的任务
            任务列表 = []
            for line in result.stdout.split('\n'):
                if line.startswith("任务名:") or line.startswith("TaskName:"):
                    任务名 = line.split(":", 1)[1].strip()
                    if "COC_Robot_" in 任务名:
                        任务列表.append(任务名)

            return 任务列表
        except Exception as e:
            print(f"获取计划任务列表失败: {e}")
            return []

    def 清理无效配置(self):
        """
        清理配置文件中已经不存在的计划任务
        """
        所有配置 = self.获取所有自动启动配置()
        有效配置 = {}

        for 机器人标识, 配置 in 所有配置.items():
            任务名称 = 配置.get("任务名称")
            if 任务名称 and self.检查计划任务是否存在(任务名称):
                有效配置[机器人标识] = 配置

        if len(有效配置) != len(所有配置):
            self.保存自动启动配置(有效配置)
            print(f"已清理 {len(所有配置) - len(有效配置)} 个无效配置")


if __name__ == "__main__":
    # 测试代码
    管理器 = 自动启动管理器()

    # 测试设置自动启动
    print("测试设置自动启动...")
    成功 = 管理器.设置机器人自动启动("测试机器人1", "09:00")
    print(f"设置结果: {'成功' if 成功 else '失败'}")

    # 测试获取配置
    print("\n测试获取配置...")
    配置 = 管理器.获取机器人自动启动状态("测试机器人1")
    print(f"配置信息: {配置}")

    # 测试获取所有配置
    print("\n测试获取所有配置...")
    所有配置 = 管理器.获取所有自动启动配置()
    print(f"所有配置: {所有配置}")

    # 测试取消自动启动
    print("\n测试取消自动启动...")
    成功 = 管理器.取消机器人自动启动("测试机器人1")
    print(f"取消结果: {'成功' if 成功 else '失败'}")
