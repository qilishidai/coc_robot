from datetime import datetime, timedelta

from 任务流程.基础任务框架 import 基础任务, 任务上下文
from 任务流程.兵种或法术升级.打开研究面板 import 打开研究面板任务
from 任务流程.兵种或法术升级.打开要升级的兵种或法术 import 打开要升级的兵种或法术任务
from 任务流程.兵种或法术升级.完成兵种或法术升级 import 完成兵种或法术升级任务


class 兵种或法术升级任务(基础任务):
    """自动升级指定的兵种或法术"""

    def __init__(self, 上下文: '任务上下文'):
        super().__init__(上下文)

    def 执行(self) -> bool:
        欲升级目标 = self.上下文.设置.欲升级的兵种或法术

        if not 欲升级目标:
            self.上下文.置脚本状态("研究升级：未配置要升级的兵种或法术，跳过")
            return False

        # 检查冷却时间
        if not self._检查冷却时间():
            return False

        self.上下文.置脚本状态(f"研究升级：开始升级 {欲升级目标}")

        # 步骤1：打开研究面板
        if not 打开研究面板任务(self.上下文).执行():
            self._记录失败状态("实验室不可用或已有升级中")
            return False

        # 步骤2：定位并点击目标兵种或法术
        if not 打开要升级的兵种或法术任务(self.上下文, 欲升级目标).执行():
            self._记录失败状态(f"无法打开 {欲升级目标} 升级界面")
            return False

        # 步骤3：完成升级操作
        if not 完成兵种或法术升级任务(self.上下文).执行():
            self._记录失败状态("升级操作未完成")
            return False

        # 成功后清除失败记录
        self.数据库.更新状态(self.机器人标志, "研究升级失败记录", None)
        self.上下文.置脚本状态(f"研究升级：{欲升级目标} 升级完成")
        return True

    def _检查冷却时间(self) -> bool:
        """检查是否处于冷却期"""
        完整状态 = self.数据库.获取最新完整状态(self.机器人标志).状态数据
        上次记录 = 完整状态.get("研究升级失败记录")

        if not 上次记录:
            return True

        记录时间 = datetime.fromtimestamp(上次记录.get("时间", 0))
        冷却时间 = timedelta(hours=self.上下文.设置.研究升级检查间隔)

        if datetime.now() - 记录时间 < 冷却时间:
            剩余分钟 = int((冷却时间 - (datetime.now() - 记录时间)).total_seconds() / 60)
            self.上下文.置脚本状态(f"研究升级：冷却中，{剩余分钟}分钟后再试")
            return False

        return True

    def _记录失败状态(self, 原因: str):
        """记录失败状态到数据库，用于冷却判断"""
        状态记录 = {
            "时间": datetime.now().timestamp(),
            "原因": 原因
        }
        self.数据库.更新状态(self.机器人标志, "研究升级失败记录", 状态记录)
        self.上下文.置脚本状态(f"研究升级：{原因}")
