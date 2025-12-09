from datetime import datetime, timedelta
from 任务流程.夜世界.夜世界打鱼.夜世界基础任务类 import 夜世界基础任务
from 任务流程.建筑升级.升级英雄 import 升级英雄任务
from 任务流程.建筑升级.寻找建筑 import 寻找建筑
from 任务流程.建筑升级.更新工人状态 import 更新工人状态任务


class 建筑升级任务(夜世界基础任务):
    """循环执行建筑升级，直到没有空闲工人为止；失败记录并一天内不重试"""

    def __init__(self, 上下文):
        super().__init__(上下文)
        self.空闲工人: bool = False
        self.当前建筑: str | None = None

    def 执行(self) -> bool:
        try:
            if self.上下文.设置.欲升级的英雄==[]:
                self.上下文.置脚本状态("建筑升级任务,要升级的建筑列表为空,跳过升级建筑任务")
                return False

            # 先检查上次失败时间
            完整状态 = self.数据库.获取最新完整状态(self.机器人标志).状态数据
            上次失败 = 完整状态.get("建筑升级失败记录")
            if 上次失败:
                失败时间 = datetime.fromtimestamp(上次失败.get("时间", 0))
                if datetime.now() - 失败时间 < timedelta(hours=1):
                    self.上下文.置脚本状态("建筑升级任务小时内已失败过，不再重试,等过一小时后重试")
                    return False


            self.上下文.置脚本状态("开始执行循环建筑升级任务")

            while True:
                # 1. 更新工人状态
                工人任务 = 更新工人状态任务(self.上下文)
                成功 = 工人任务.执行()
                if not 成功:
                    self.记录失败("更新工人状态任务失败")
                    return False

                self.空闲工人 = 工人任务.是否有空闲工人()
                if not self.空闲工人:
                    self.上下文.置脚本状态("无空闲工人，建筑升级结束")
                    return True

                # 2. 寻找可升级建筑
                寻找任务 = 寻找建筑(self.上下文, self.上下文.设置.欲升级的英雄)
                成功 = 寻找任务.执行()
                if not 成功:
                    self.记录失败("寻找建筑任务执行失败")
                    return False

                self.当前建筑 = 寻找任务.当前建筑
                if not self.当前建筑:
                    self.上下文.置脚本状态("未找到可升级建筑")
                    return True

                # 3. 升级找到的建筑
                升级任务 = 升级英雄任务(self.上下文, self.当前建筑)
                成功 = 升级任务.执行()
                if not 成功:
                    self.记录失败(f"升级建筑 {self.当前建筑} 失败")
                    return False

                self.上下文.置脚本状态(f"已完成建筑升级: {self.当前建筑}")

        except Exception as e:
            self.异常处理(e)
            self.记录失败(f"任务异常: {str(e)}")
            return False

    def 记录失败(self, 原因: str):
        """将失败状态记录到数据库"""
        失败记录 = {
            "时间": datetime.now().timestamp(),
            "原因": 原因
        }
        self.数据库.更新状态(self.机器人标志, "建筑升级失败记录", 失败记录)
        self.上下文.置脚本状态(f"建筑升级失败记录已写入数据库: {原因}")
