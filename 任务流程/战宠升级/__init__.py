from 任务流程.基础任务框架 import 基础任务, 任务上下文
from datetime import datetime, timedelta

from 任务流程.战宠升级.寻找战宠小屋 import 寻找战宠小屋任务


class 战宠升级任务(基础任务):

    def __init__(self, 上下文: '任务上下文'):
        super().__init__(上下文)

    def 执行(self) -> bool:

        # if self.上下文.设置.欲升级的战宠=="不自动升级":
        #     self.上下文.置脚本状态("战宠升级任务,已关闭,跳过升级战宠任务")
        #     return False

        完整状态 = self.数据库.获取最新完整状态(self.机器人标志).状态数据
        上次失败 = 完整状态.get("战宠升级失败记录")
        if 上次失败:
            失败时间 = datetime.fromtimestamp(上次失败.get("时间", 0))
            if datetime.now() - 失败时间 < timedelta(hours=self.上下文.设置.战宠升级检查间隔):
                self.上下文.置脚本状态(
                    F"战宠升级任务：上次失败距离现在不到 {self.上下文.设置.战宠升级检查间隔} 小时，暂不重试，等间隔过去后将再次尝试")
                return False

            self.上下文.置脚本状态("开始执行，战宠升级任务")

        寻找战宠小屋任务(self.上下文).执行()

