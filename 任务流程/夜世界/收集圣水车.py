from dataclasses import dataclass
from 任务流程.基础任务框架 import 任务上下文
from 任务流程.夜世界.夜世界打鱼.夜世界基础任务类 import 夜世界基础任务


@dataclass
class 滑动配置:
    起点: tuple[int, int]
    终点: tuple[int, int]


class 收集圣水车任务(夜世界基础任务):
    MAX_连续失败次数 = 5  # 定义最大允许失败次数常量
    收集圣水连续出错次数 = 0  # 初始化计数器

    def __init__(self, 上下文: '任务上下文'):
        super().__init__(上下文)
        # self

    def 执行(self) -> bool:
        try:
            找不到夜世界船的次数 = 0

            while True:

                是否匹配, (x, y) = self.是否出现图片(
                    "夜世界的船1.bmp|夜世界的船2.bmp|夜世界的船3.bmp|"
                    "夜世界的船4.bmp|夜世界的船6.bmp|夜世界的船7.bmp"
                )

                if 是否匹配:
                    if self.是否在危险区域内(x, y):
                        self.上下文.置脚本状态("圣水车位于危险区域，跳过收集")
                        self._处理失败()
                        return False

                    self.上下文.置脚本状态("定位到了夜世界的船，计算偏移，尝试点击圣水车，开始收集")
                    self.上下文.点击(x - 118, y + 46)
                    # 成功打开了，并收集圣水
                    if self.尝试收集圣水():
                        return True


                    self.上下文.置脚本状态("未成功打开圣水车界面，用户可能更换了默认背景，尝试备用方案。建议使用默认背景",级别="警告")
                    self.上下文.点击(x - 169, y - 64)
                    if self.尝试收集圣水():
                        return True



                    self.上下文.置脚本状态("未成功打开圣水车界面，收集失败, 拉远视距尝试")
                    self.上下文.键盘.按字符按压("f5")
                    self.上下文.脚本延时(200)
                    self._处理失败()
                    # self.上下文.键盘.按字符按压("esc")
                    return False

                else:
                    找不到夜世界船的次数 += 1
                    self.上下文.置脚本状态(f"定位圣水车位置中... ({找不到夜世界船的次数},最大重试5次)")
                    self.上下文.滑动屏幕((595, 182), (135, 250))  # 滑动屏幕寻找


                    if 找不到夜世界船的次数 > 5:
                        raise RuntimeError("无法定位圣水车位置")
        except RuntimeError as e:
            self.异常处理(e)
            return False

    def 尝试收集圣水(self):
        if self.是否包含文本(self.执行OCR识别((328, 92, 489, 131)), "圣水车"):
            self.上下文.点击(605, 471)  # 收集圣水
            self.上下文.脚本延时(1000)
            self.上下文.点击(699, 103)  # 关闭界面
            self.收集圣水连续出错次数 = 0
            return True
        return False

    @staticmethod
    def 是否在危险区域内(x, y) -> bool:
        """检查坐标是否在宝石购买按钮区域"""
        return 744 <= x <= 794 and 225 <= y <= 274

    def _处理失败(self):
        """处理收集失败的情况"""
        self.收集圣水连续出错次数 += 1
        self.上下文.置脚本状态(f"收集失败次数: {self.收集圣水连续出错次数}/{self.MAX_连续失败次数}")
        # 检查是否超过最大失败次数
        if self.收集圣水连续出错次数 >= self.MAX_连续失败次数:
            raise RuntimeError(f"收集圣水连续失败超过{self.MAX_连续失败次数}次")

    def 是否包含文本(self, result: list, target: str) -> bool:
        for item in result:
            if len(item) > 1 and target in str(item[1]):
                return True
        return False
