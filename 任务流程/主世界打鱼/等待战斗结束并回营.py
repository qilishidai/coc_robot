import time

from 任务流程.基础任务框架 import 基础任务, 任务上下文
from 模块.检测.OCR识别器 import 安全OCR引擎
from 模块.检测.YOLO检测器 import 线程安全YOLO检测器
from 模块.检测.模板匹配器 import 模板匹配引擎


class 等待战斗结束并回营任务(基础任务):

    def 执行(self) -> bool:
        上下文 = self.上下文
        # 初始点击回营按钮
        上下文.置脚本状态("开始执行回营操作",3*60)
        self.等待回营地按钮出现(上下文)
        上下文.置脚本状态("回营完成")
        return True

    def 等待回营地按钮出现(self, 上下文) -> bool:
        """使用模板匹配检测下一个按钮"""

        按钮区域 = (0, 0, 800, 600)
        模板路径 = "回营1.bmp|回营.bmp｜回营2.bmp|回营3.bmp|领取奖励.bmp|回营_领取奖励.bmp"
        超时时间 = 3*60  # 等待3分钟就超时
        开始时间 = time.time()

        是否已点击回营=False
        while time.time() - 开始时间 < 超时时间:
            # 获取按钮区域图像
            屏幕图像 = 上下文.op.获取屏幕图像cv(*按钮区域)
            # 执行模板匹配
            是否匹配, (x, y), _ = self.模板识别.执行匹配(屏幕图像, 模板路径, 相似度阈值=0.9)
            if 是否匹配:
                是否已点击回营=True
                上下文.点击(x,y)

            if 是否已点击回营==True and 是否匹配==False:
                return True

            # 间隔检测
            上下文.脚本延时(500)

        return False