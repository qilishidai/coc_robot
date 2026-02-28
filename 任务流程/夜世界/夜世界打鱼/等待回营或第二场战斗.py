import time
from 任务流程.基础任务框架 import 任务上下文
from 任务流程.夜世界.夜世界打鱼 import 下兵
from 任务流程.夜世界.夜世界打鱼.夜世界基础任务类 import 夜世界基础任务


class 等待回营或第二次战斗(夜世界基础任务):
    """注释字符"""
    def __init__(self,上下文: 任务上下文):
        super().__init__(上下文)



    def 执行(self) -> bool:
        """执行进入夜世界的主逻辑"""
        try:
            超时时间 = 60*3  # 秒
            开始时间 = time.time()

            while time.time() - 开始时间 < 超时时间:

                if self.是否出现换兵种箭头():

                    if hasattr(self.上下文, '英雄技能标志'):
                        self.上下文.英雄技能标志.set()

                    self.上下文.置脚本状态("第二次战斗")
                    self.上下文.置脚本状态("开始下兵逻辑",3*60)
                    下兵(self.上下文).执行()

                self.上下文.脚本延时(50)

                if self.尝试点击回营按钮():
                    return True

            raise RuntimeError(f"操作超时：一直卡白云或者某处,导致一直没能进入战斗！已经等待了{超时时间}")
        except RuntimeError as e:
            self.异常处理(e)
            return False
        finally:
            if hasattr(self.上下文, '英雄技能标志'):
                self.上下文.英雄技能标志.set()
                try: delattr(self.上下文, '英雄技能标志')
                except: pass

    def 是否出现换兵种箭头(self):
        """验证是否已开始战斗"""
        是否匹配, (x, y)=self.是否出现图片("更换兵种箭头[1].bmp|更换兵种箭头[2].bmp|更换兵种箭头[3].bmp|更换兵种箭头[4].bmp|更换兵种箭头[5].bmp",(163,495,800,600))
        if 是否匹配:
            self.上下文.点击(x-18, y-28)#选中对应兵种
            return True
        else:
            return False


    def 尝试点击回营按钮(self):
        """验证是否已开始战斗"""
        是否匹配, (x, y) = self.是否出现图片("夜世界_回营.bmp|夜世界_回营[1].bmp")
        if 是否匹配:
            self.上下文.点击(x, y)
            return True
        else:
            return False
