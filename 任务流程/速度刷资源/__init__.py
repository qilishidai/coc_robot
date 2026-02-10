from 任务流程.速度刷资源.打开进攻页面 import 打开进攻页面任务
from 任务流程.速度刷资源.等待战斗结束并回营 import 等待战斗结束并回营任务
from 任务流程.速度刷资源.进攻 import 进攻任务
from 任务流程.基础任务框架 import 任务上下文
from 任务流程.夜世界.夜世界打鱼.夜世界基础任务类 import 夜世界基础任务
from 任务流程.速度刷资源.搜索敌人 import 搜索目标敌人任务



class 主世界速度刷资源任务(夜世界基础任务):
    """注释字符"""
    def __init__(self, 上下文: 任务上下文):
        super().__init__(上下文)


    def 执行(self) -> bool:
        """执行进入夜世界的主逻辑"""
        self.上下文.置脚本状态("速度刷资源开启")
        try:
            任务列表 = [
                打开进攻页面任务(self.上下文),
                搜索目标敌人任务(self.上下文),
                进攻任务(self.上下文),
                等待战斗结束并回营任务(self.上下文),

            ]

            for 索引, 子任务 in enumerate(任务列表, start=1):
                任务名 = type(子任务).__name__
                if not 子任务.执行(self.上下文):
                    self.上下文.置脚本状态(f"[失败] 子任务 [{任务名}] 执行失败，终止主世界打鱼任务链")
                    return False
            return True

        except RuntimeError as e:
            self.异常处理( e)
            return False

    def 异常处理(self, 异常: Exception):
        super().异常处理( 异常)
        self.上下文.发送重启请求(f"任务[{self.__class__.__name__}] 触发了异常：{异常}")


