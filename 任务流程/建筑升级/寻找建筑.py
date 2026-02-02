import random
import time
import cv2
import numpy as np

from 任务流程.基础任务框架 import 任务上下文, 基础任务
from 任务流程.夜世界.夜世界打鱼.夜世界基础任务类 import 夜世界基础任务


class 资源不足错误(Exception):
    """资源不足异常"""

    def __init__(self, 错误信息):
        super().__init__(错误信息)
        self.错误信息 = 错误信息

    def __str__(self):
        return f"发生了：{self.错误信息}"


class 寻找建筑(夜世界基础任务):
    """自动检测并升级城墙"""

    默认颜色阈值 = {'色差H': 10, '色差S': 10, '色差V': 10, '最少像素数': 150}

    def __init__(self, 上下文: '任务上下文', 建筑名称: str | list = "城墙"):
        super().__init__(上下文)
        # 支持单个建筑名称或多个建筑名称
        if isinstance(建筑名称, str):
            self.建筑列表 = [建筑名称]
        elif isinstance(建筑名称, list):
            self.建筑列表 = 建筑名称
        else:
            raise TypeError("建筑名称必须是字符串或字符串列表")
        self.开始时间 = None
        self.当前建筑: str | None = None  # 新增实例变量，用于保存找到的建筑，然后升级建筑任务读取这个变量，用于根据不同的建筑类型执行升级操作
    # ---------------------- 主入口 ----------------------
    def 执行(self) -> bool:
        """任务执行入口"""
        try:
            return self.找建筑循环()
        except 资源不足错误 as e:
            self.上下文.置脚本状态(str(e))
            return False
        except Exception as e:
            self.异常处理(e)
            return False

    # ---------------------- 主流程循环 ----------------------
    def 找建筑循环(self) -> bool:
        """寻找并尝试升级建筑的主循环"""
        self.上下文.置脚本状态(f"开始寻找建筑: {', '.join(self.建筑列表)}")
        self.打开建筑页面()
        self.开始时间 = time.time()
        随机半径 = random.randint(0, 5)

        while True:
            self.上下文.脚本延时(1500)
            ocr结果 = self.执行OCR识别((219, 57, 595, 398))

            建筑列表 = []

            for 项 in ocr结果:
                文本 = 项[1]
                # 排除数字，只保留含有中文字符的，或者你也可以自己定义建筑关键词列表
                if any('\u4e00' <= c <= '\u9fff' for c in 文本):
                    建筑列表.append(文本)

            self.上下文.置脚本状态(f"前可见建筑: {', '.join(建筑列表[:])}")

            # 根据 OCR 结果，如果包含要查找的建筑,那么尝试选中建筑
            if ocr结果 and self.尝试选中指定建筑(ocr结果):
                self.上下文.脚本延时(1500)
                return True

            if "升级中" in str(ocr结果):
                self.上下文.置脚本状态("到顶了")
                break

            if time.time() - self.开始时间 > 120:
                raise RuntimeError(f"找建筑超时: {', '.join(self.建筑列表)}")

            self.滑动屏幕(随机半径)
            self.上下文.置脚本状态(f"滑动屏幕，继续查找")

        self.关闭建筑页面()
        self.上下文.置脚本状态(f"未找到可升级的建筑: {', '.join(self.建筑列表)}")
        return False

    # ---------------------- 界面操作 ----------------------
    def 打开建筑页面(self):
        """点击进入建筑界面并模拟滑动"""
        x = 353 if self.上下文.设置.是否刷主世界 else 450
        self.上下文.点击(x, 13, 延时=1000)
        self.滑动到建筑栏底部()

    def 关闭建筑页面(self):
        """关闭建筑界面"""
        self.上下文.点击(353, 13, 延时=1000)

    def 滑动到建筑栏底部(self):
        """模拟进入建筑界面的滑动动作"""
        self.上下文.鼠标.移动到(399, 116)
        self.上下文.鼠标.左键按下()
        for _ in range(150):
            self.上下文.鼠标.移动相对位置(0, random.randint(-10, -5))
            self.上下文.脚本延时(5)
        self.上下文.鼠标.左键抬起()

    def 滑动屏幕(self, 随机半径: int):
        """模拟屏幕滑动寻找建筑"""
        x = 399 if self.上下文.设置.是否刷主世界 else 450
        start_x = x + 随机半径
        start_y = 116 + 随机半径

        self.上下文.鼠标.移动到(start_x, start_y)
        self.上下文.鼠标.左键按下()
        for _ in range(10):
            self.上下文.鼠标.移动相对位置(0, random.randint(7, 12))
            self.上下文.脚本延时(5)
        self.上下文.鼠标.左键抬起()
        self.上下文.脚本延时(random.randint(1000, 1500))

    # ---------------------- OCR处理 ----------------------
    def 尝试选中指定建筑(self, ocr结果) -> bool:
        """判断ocr结果中是否有指定建筑，有则选中，没有则直接返回"""
        """判断 OCR 结果中是否有指定建筑列表里的建筑"""
        for 识别项 in ocr结果:
            文本内容 = 识别项[1]
            # 只要 OCR 文本匹配建筑列表中的任意一个就选中
            if not any(建筑 in 文本内容 for 建筑 in self.建筑列表):
                continue

            try:
                x1, y1, x2, y2 = self.解析坐标(识别项[0])
            except Exception as e:
                self.上下文.置脚本状态(f"坐标解析失败: {str(e)}")
                continue

            if not self.检查升级条件(x1, y1, x2, y2):
                self.上下文.置脚本状态(f"{str(文本内容)}，不够资源升级，继续寻找")
                continue

            self.上下文.置脚本状态(f"找到目标建筑: {str(文本内容)}, 尝试选中升级")
            self.当前建筑=文本内容
            return self.选中建筑(x1, y1, x2, y2)

        return False

    def 解析坐标(self, 坐标列表):
        """解析OCR坐标"""
        所有x = [点[0] for 点 in 坐标列表]
        所有y = [点[1] for 点 in 坐标列表]
        左上x = int(min(所有x)) + 219
        左上y = int(min(所有y)) + 57
        右下x = 595
        右下y = int(max(所有y)) + 57
        return 左上x, 左上y, 右下x, 右下y

    # ---------------------- 升级检查与点击 ----------------------
    def 检查升级条件(self, x1, y1, x2, y2) -> bool:
        """检查资源是否足够"""
        区域图像 = self.上下文.op.获取屏幕图像cv(x1, y1, x2, y2)
        if self.是否包含指定颜色_HSV(区域图像, (250, 135, 124), **self.默认颜色阈值):
            return False
        else:
            return True

    def 选中建筑(self, x1, y1, x2, y2) -> bool:
        """执行升级操作"""
        中心x = (x1 + x2) // 2 + random.randint(-5, 5)
        中心y = (y1 + y2) // 2 + random.randint(-5, 5)
        self.上下文.点击(中心x, 中心y, 延时=1500)
        return True

    # ---------------------- 工具函数 ----------------------
    @staticmethod
    def 是否包含指定颜色_HSV(图像: np.ndarray, 目标RGB: tuple,
                             色差H=10, 色差S=100, 色差V=100,
                             最少像素数=1000, 是否可视化=False) -> bool:
        """判断图像中是否包含指定颜色块"""
        hsv图像 = cv2.cvtColor(图像, cv2.COLOR_BGR2HSV)
        目标色_BGR = np.uint8([[list(reversed(目标RGB))]])
        目标色_HSV = cv2.cvtColor(目标色_BGR, cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = map(int, 目标色_HSV)

        下限 = np.array([max(0, h - 色差H), max(0, s - 色差S), max(0, v - 色差V)])
        上限 = np.array([min(179, h + 色差H), min(255, s + 色差S), min(255, v + 色差V)])
        掩码 = cv2.inRange(hsv图像, 下限, 上限)
        匹配像素数 = cv2.countNonZero(掩码)

        if 是否可视化:
            cv2.imshow("原图", 图像)
            cv2.imshow("匹配掩码", 掩码)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return 匹配像素数 >= 最少像素数
