import random
import time
from dataclasses import dataclass

from 任务流程.基础任务框架 import 基础任务, 任务上下文
from 工具包.工具函数 import 生成贝塞尔轨迹
from 模块.检测.模板匹配器 import 模板匹配引擎

@dataclass
class 滑动配置:
    起点: tuple[int, int]
    终点: tuple[int, int]

class 进入世界任务基类(基础任务):
    def __init__(self, 上下文: 任务上下文, 判断图标路径: str, 船模板路径: str, 状态文本: str,滑动参数: 滑动配置):
        super().__init__(上下文)
        self.判断图标路径 = 判断图标路径
        self.船模板路径 = 船模板路径
        self.状态文本 = 状态文本
        self.滑动配置 = 滑动参数

    def 执行(self) -> bool:
        try:
            上下文 = self.上下文
            if self.是否在目标世界():
                上下文.置脚本状态(f"已经在{self.状态文本}")
                return True
            else:
                上下文.置脚本状态(f"开始尝试进入{self.状态文本}")

            按钮区域 = (0, 0, 800, 600)
            超时时间 = 30
            开始时间 = time.time()

            while time.time() - 开始时间 < 超时时间:
                屏幕图像 = 上下文.op.获取屏幕图像cv(*按钮区域)
                是否匹配, (x, y), _ = self.模板识别.执行匹配(屏幕图像, self.船模板路径, 相似度阈值=0.9)

                if 是否匹配:
                    上下文.点击(x, y)
                    上下文.脚本延时(500)

                if self.是否在目标世界():
                    上下文.置脚本状态(f"成功进入{self.状态文本}")
                    return True

                self.滑动屏幕(上下文, self.滑动配置.起点, self.滑动配置.终点)
                上下文.脚本延时(1000)

                if time.time() - 开始时间 > 3:
                    上下文.置脚本状态("切换世界超过三秒,尝试拉远视距")
                    for _ in range(20):
                        上下文.键盘.按字符按压("f5")
                        上下文.脚本延时(50)

            raise RuntimeError(f"操作超时：未找到{self.状态文本}入口")
        except Exception as e:
            self.异常处理(e)
            return False


    def 是否在目标世界(self) -> bool:
        屏幕图像 = self.上下文.op.获取屏幕图像cv(0, 0, 800, 600)
        是否匹配, _, _ = self.模板识别.执行匹配(屏幕图像, self.判断图标路径, 相似度阈值=0.9)
        return 是否匹配

    def 滑动屏幕(self, 上下文, 起点坐标, 终点坐标):
        """使用贝塞尔曲线模拟人类滑动操作"""
        起点x, 起点y = 起点坐标
        终点x, 终点y = 终点坐标

        # 随机偏移增强人类行为模拟
        起点x += random.randint(-5, 5)
        起点y += random.randint(-5, 5)
        终点x += random.randint(-5, 5)
        终点y += random.randint(-5, 5)

        # 控制点随机生成在起点和终点附近
        控制点1 = (
            起点x + (终点x - 起点x) * 0.3 + random.randint(-30, 30),
            起点y + (终点y - 起点y) * 0.3 + random.randint(-30, 30),
        )
        控制点2 = (
            起点x + (终点x - 起点x) * 0.6 + random.randint(-30, 30),
            起点y + (终点y - 起点y) * 0.6 + random.randint(-30, 30),
        )

        路径点 = 生成贝塞尔轨迹((起点x, 起点y), 控制点1, 控制点2, (终点x, 终点y), 步数=random.randint(25, 40))

        上下文.鼠标.移动到(路径点[0][0], 路径点[0][1])
        上下文.鼠标.左键按下()

        for 当前点 in 路径点[1:]:
            上下文.鼠标.移动到(当前点[0], 当前点[1])
            上下文.脚本延时(random.randint(5, 15))  # 模拟人类微小不规律移动

        上下文.鼠标.左键抬起()
        上下文.脚本延时(random.randint(500, 1000))

