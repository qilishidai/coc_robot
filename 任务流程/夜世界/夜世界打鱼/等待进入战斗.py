import time
from 任务流程.基础任务框架 import 任务上下文
from 任务流程.夜世界.夜世界打鱼.夜世界基础任务类 import 夜世界基础任务


class 等待进入战斗(夜世界基础任务):
    """注释字符"""
    def __init__(self,上下文: 任务上下文):
        super().__init__(上下文)


    def 执行(self) -> bool:
        """执行进入夜世界的主逻辑"""
        try:
            超时时间 = 30  # 秒
            开始时间 = time.time()

            while time.time() - 开始时间 < 超时时间:

                if self.是否出现换兵种箭头():
                    self.上下文.置脚本状态("已进入战斗")
                    return True
                self.上下文.脚本延时(50)

            raise RuntimeError(f"操作超时：一直卡白云或者某处,导致一直没能进入战斗！已经等待了{超时时间}")
        except RuntimeError as e:
            self.异常处理(e)
            return False

    def 是否出现换兵种箭头(self):
        """验证是否已开始战斗"""
        是否匹配, (x, y) = self.是否出现图片("更换兵种箭头[1].bmp|更换兵种箭头[2].bmp")
        if 是否匹配:
            self.上下文.点击(x-18, y-28)#选中对应兵种
            return True
        else:
            return False
