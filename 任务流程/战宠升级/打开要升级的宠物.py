import random

import cv2
import numpy as np

from 任务流程.基础任务框架 import 基础任务, 任务上下文
from 任务流程.战宠升级.图像算法 import 从内部点获取黑框坐标

class 无法定位目标宠物错误(Exception):
    def __init__(self, 错误信息):
        super().__init__(错误信息)
        self.错误信息 = 错误信息

    def __str__(self):
        return f"发生了：{self.错误信息}"


class 打开要升级的宠物任务(基础任务):

    def __init__(self, 上下文: '任务上下文',欲打开的宠物):
        super().__init__(上下文)
        self.欲打开的宠物=欲打开的宠物
        self.宠物模板列表={
            "莱希":"莱希.bmp",
            "闪枭":"闪枭.bmp",
            "大耗":"大耗.bmp",
            "独角":"独角.bmp",
            "冰牙":"冰牙.bmp",
            "地兽":"地兽.bmp",
            "猛蜥":"猛蜥.bmp",
            "凤凰":"凤凰.bmp",
            "灵狐":"灵狐.bmp",
            "愤怒水母":"愤怒水母.bmp",
            "阿啾":"阿啾.bmp"}

    def 执行(self) -> bool:
        if self.是否出现图片("战宠小屋_立即完成升级.bmp"):
            self.上下文.置脚本状态("有宠物正在升级中")
            self.关闭战宠小屋页面()
            return False

        try:

            if not self.当前是否存在目标宠物():
                self.滑动到目标宠物位置()

            self.检测可打开条件()

            _, (x, y) = self.是否出现图片(self.宠物模板列表[self.欲打开的宠物])
            self.上下文.点击(x,y)#打开要升级的宠物界面

        except 无法定位目标宠物错误 as e:
            self.上下文.置脚本状态(e.__str__())
            return False
        except Exception as e:
            self.异常处理(e)
            return False


    def 滑动到目标宠物位置(self):
        print(123)
        随机半径=20
        start_x = 734 + 随机半径
        start_y = 429 + 随机半径
        self.上下文.鼠标.移动到(start_x, start_y)
        self.上下文.鼠标.左键按下()

        for x in range(200):
            self.上下文.鼠标.移动相对位置(-random.randint(5,8),0)
            self.上下文.脚本延时(0)

            if self.当前是否存在目标宠物():
                self.上下文.鼠标.左键抬起()
                self.上下文.脚本延时(random.randint(800, 1000))
                return

        self.上下文.鼠标.左键抬起()
        raise 无法定位目标宠物错误(f"滑动了好久还没找到要升级的宠物{self.欲打开的宠物}")

    def 检测可打开条件(self):

        _, (x, y) = self.是否出现图片(self.宠物模板列表[self.欲打开的宠物])
        屏幕图像 = self.上下文.op.获取屏幕图像cv(0, 0, 800, 600)
        # 获取宠物区域
        (x1,y1),(x2,y2)=从内部点获取黑框坐标(屏幕图像,x,y,调试=False)

        #判断是否最高等级
        ocr结果=self.执行OCR识别((x1,y1,x2,y2))
        if "最高等级" in ocr结果.__str__():
            self.上下文.置脚本状态(f"当前欲升级的宠物{self.欲打开的宠物}已达到最高等级，无法继续打开升级")
            self.关闭战宠小屋页面()
            return False

        #判断是否够资源升级
        区域图像=self.上下文.op.获取屏幕图像cv(x1,y1,x2,y2)
        是否有红色调偏粉色块 = self.是否包含指定颜色_HSV(
            区域图像, (250, 135, 124),
            色差H=10, 色差S=10, 色差V=10,
            最少像素数=150
        )
        if 是否有红色调偏粉色块:  # 根据实际情况调整阈值
            self.上下文.置脚本状态(f"{self.欲打开的宠物},因为资源不足无法升级")
            self.关闭战宠小屋页面()
            return False

        self.上下文.置脚本状态(f"{self.欲打开的宠物},可以打开升级，即将开始升级")
        return True

    def 关闭战宠小屋页面(self):
        """关闭界面"""
        self.上下文.键盘.按字符按压("esc")


    @staticmethod
    def 是否包含指定颜色_HSV(图像: np.ndarray, 目标RGB: tuple,
                             色差H=10, 色差S=100, 色差V=100,
                             最少像素数=1000, 是否可视化=False) -> bool:

        "H (色相),S (饱和度),V (亮度)表示这三者的偏移的容忍程度"

        # 将图像转换为 HSV
        hsv图像 = cv2.cvtColor(图像, cv2.COLOR_BGR2HSV)

        # RGB → HSV（先转 BGR 再转 HSV）
        目标色_BGR = np.uint8([[list(reversed(目标RGB))]])  # RGB -> BGR
        目标色_HSV = cv2.cvtColor(目标色_BGR, cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = map(int, 目标色_HSV)  # ⚠️ 转成 int 防止溢出

        # 定义 HSV 范围上下限
        下限 = np.array([max(0, h - 色差H), max(0, s - 色差S), max(0, v - 色差V)])
        上限 = np.array([min(179, h + 色差H), min(255, s + 色差S), min(255, v + 色差V)])

        # 掩码提取
        掩码 = cv2.inRange(hsv图像, 下限, 上限)
        匹配像素数 = cv2.countNonZero(掩码)

        #print(f"目标HSV: {目标色_HSV}  匹配像素数: {匹配像素数}")

        if 是否可视化:
            cv2.imshow("原图", 图像)
            cv2.imshow("匹配掩码", 掩码)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return 匹配像素数 >= 最少像素数


    def 当前是否存在目标宠物(self):
        是否存在,(x,y)=self.是否出现图片(self.宠物模板列表[self.欲打开的宠物], 区域=(169,312,641,533))

        return 是否存在


    def 滑动屏幕(self, 上下文, 随机半径):
        """模拟滑动操作"""
        x = 399 if self.设置.是否刷主世界 else 450
        start_x = x + 随机半径
        start_y = 116 + 随机半径

        上下文.鼠标.移动到(start_x, start_y)
        上下文.鼠标.左键按下()

        for _ in range(10):
            dy = random.randint(7, 12)
            上下文.鼠标.移动相对位置(0,random.randint(7,12))
            #上下文.鼠标.移动到(start_x, start_y + dy)
            上下文.脚本延时(5)
        上下文.鼠标.左键抬起()

        上下文.脚本延时(random.randint(1000, 1500))
