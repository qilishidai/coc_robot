import random
import time

import cv2
import numpy as np

from 任务流程.基础任务框架 import 任务上下文, 基础任务
from 任务流程.更新主世界账号资源状态 import 更新家乡资源状态任务
from 模块.检测.OCR识别器 import 安全OCR引擎
from 模块.检测.YOLO检测器 import 线程安全YOLO检测器
from 模块.检测.模板匹配器 import 模板匹配引擎
from 数据库.任务数据库 import 任务数据库, 机器人设置


class 资源不足错误(Exception):
    def __init__(self, 错误信息):
        super().__init__(错误信息)
        self.错误信息 = 错误信息

    def __str__(self):
        return f"发生了：{self.错误信息}"

class 城墙升级任务(基础任务):
    """自动检测并升级城墙"""

    @property
    def 设置(self) -> 机器人设置:
        配置 = self.数据库.获取机器人设置(self.机器人标志)
        return 配置

    def 执行(self) -> bool:
        try:
            上下文 = self.上下文
            # 初始化配置
            if not self.检查功能开启(上下文):
                return True

            while self.已够资源升级():
                if not self.刷一次墙():
                    上下文.置脚本状态("本次刷墙失败,终止循环刷墙")
                    break

            return True
        except 资源不足错误 as e:
            self.上下文.置脚本状态(e.__str__())
            return False
        except Exception as e:

            self.异常处理(e)
            return False

    def 刷一次墙(self):
        上下文=self.上下文

        上下文.置脚本状态("开始刷一块墙")
        # 初始化操作
        self.进入城墙界面(上下文)
        随机半径 = random.randint(0, 5)
        开始找墙时间=time.time()

        # 主循环
        while True:
            上下文.脚本延时(1500)

            # OCR识别处理
            ocr结果 = self.执行OCR识别(上下文)

            print(ocr结果)
            if not ocr结果:
                continue

            # 处理OCR结果
            if self.处理OCR结果(上下文, ocr结果):
                上下文.脚本延时(1500)
                return True  # 成功升级

            # if "其他升级" in ocr结果.__str__() or "升级中" in ocr结果.__str__():
                # 上下文.置脚本状态("其他升级")
                # break

            if time.time()-开始找墙时间>60*2:
                raise RuntimeError("找墙超时,超过了120秒")


            # 滑动屏幕
            self.滑动屏幕(上下文, 随机半径)
            上下文.置脚本状态("往上滑动继续找墙")

        上下文.点击(353, 13, 延时=1000)#关闭建筑栏
        # 超时处理
        上下文.置脚本状态("未找到可升级城墙")
        return False


    def 检查功能开启(self, 上下文) -> bool:
        """检查是否开启刷墙功能"""

        是否开启 = 上下文.数据库.获取机器人设置(上下文.机器人标志).开启刷墙
        if not 是否开启:
            上下文.置脚本状态("刷墙功能已关闭")
            return False
        else:
            return True


    def 已够资源升级(self)-> bool:
        上下文=self.上下文
        更新家乡资源状态任务(上下文).执行()
        当前金币 = 上下文.数据库.获取最新完整状态(上下文.机器人标志).状态数据["家乡资源"]["金币"]
        当前圣水 = 上下文.数据库.获取最新完整状态(上下文.机器人标志).状态数据["家乡资源"]["圣水"]
        刷墙起始金币= 上下文.数据库.获取机器人设置(上下文.机器人标志).刷墙起始金币
        刷墙起始圣水= 上下文.数据库.获取机器人设置(上下文.机器人标志).刷墙起始圣水

        if 当前金币>刷墙起始金币:
            上下文.置脚本状态("金币满足用户设定的条件,开始刷墙")
            return True
        elif 当前圣水>刷墙起始圣水:
            上下文.置脚本状态("圣水满足用户设定的条件,开始刷墙")
            return True
        else:
            上下文.置脚本状态(f"未到达刷墙要求,设定的条件为金币超过{刷墙起始圣水},或圣水超过{刷墙起始圣水}")
            return False

    def 进入城墙界面(self, 上下文):
        """点击进入城墙界面"""
        x = 353 if self.设置.是否刷主世界 else 450
        上下文.脚本延时(1000)
        上下文.点击(x, 13, 延时=1000)
        上下文.鼠标.移动到(399,116)
        上下文.鼠标.左键按下()
        for _ in range(150):
            上下文.鼠标.移动相对位置(0,random.randint(-10,-5))
            上下文.脚本延时(5)
        上下文.鼠标.左键抬起()



    def 执行OCR识别(self, 上下文) -> list:
        """执行屏幕OCR识别"""

        try:
            # 截取识别区域
            #屏幕图像 = 上下文.op.获取屏幕图像cv(266, 68, 559, 389)
            屏幕图像 = 上下文.op.获取屏幕图像cv(219,57,595,398)
            # cv2.imshow("a",屏幕图像)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
            # 使用OCR引擎识别
            ocr结果, _ = self.ocr引擎(屏幕图像)
            return ocr结果
        except Exception as e:
            上下文.置脚本状态(f"OCR识别失败: {str(e)}")
            return []

    def 处理OCR结果(self, 上下文, ocr结果) -> bool:
        """解析OCR结果并处理,并尝试升级城墙,返回false则升级失败"""
        for 识别项 in ocr结果:
            文本内容 = 识别项[1]
            if "城墙" not in 文本内容:
                continue

            # 获取坐标信息
            try:
                # 位置数组 = [int(x) for x in 识别项[0]]
                # 左上x = 位置数组[0] + 266
                # 左上y = 位置数组[1] + 68
                # 右下x = 559
                # 右下y = 位置数组[3] + 68

                # 提取坐标点
                坐标点列表 = 识别项[0]  # 是一个列表，里面是 4 个 [x, y]
                print(识别项)
                # 分别提取出所有 x 和所有 y
                所有x = [点[0] for 点 in 坐标点列表]
                所有y = [点[1] for 点 in 坐标点列表]

                # 求出左上角和右下角的 x 和 y（做近似包围框处理）
                # 左上x = int(min(所有x)) + 266
                # 左上y = int(min(所有y)) + 68
                # # 右下x = int(max(所有x)) + 266
                # 右下x = 559
                # 右下y = int(max(所有y)) + 68
                #
                左上x = int(min(所有x)) + 219
                左上y = int(min(所有y)) + 57
                # 右下x = int(max(所有x)) + 266
                右下x = 595
                右下y = int(max(所有y)) + 57
            except Exception as e:
                上下文.置脚本状态(f"坐标解析失败: {str(e)}")
                continue



            # 检查升级能力
            if not self.检查升级条件(上下文, 左上x, 左上y, 右下x, 右下y):
                return False

            # 执行升级操作
            return self.执行升级(上下文, 左上x, 左上y, 右下x, 右下y)

        return False

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

    def 检查升级条件(self, 上下文, x1, y1, x2, y2) -> bool:
        """检查资源是否足够"""
        try:
            # 颜色块检测（模拟FindColorBlock）
            区域图像 = 上下文.op.获取屏幕图像cv(x1, y1, x2, y2)

            是否有红色调偏粉色块=self.是否包含指定颜色_HSV(
                区域图像, (250, 135, 124),
                色差H=10, 色差S=10, 色差V=10,
                最少像素数=150
            )
            if 是否有红色调偏粉色块:  # 根据实际情况调整阈值
                上下文.置脚本状态("资源不足无法升级")
                上下文.点击(353, 13)  # 返回
                raise 资源不足错误("资源不足,退出刷墙功能")
                #return False
            return True
        except 资源不足错误 as e:
            raise#捕获后再次抛出
        except Exception as e:
            上下文.置脚本状态(f"资源检查失败: {str(e)}")
            return False

    def 执行升级(self, 上下文, x1, y1, x2, y2) -> bool:
        """执行升级操作"""
        try:
            # 计算点击中心
            中心x = (x1 + x2) // 2 + random.randint(-5, 5)
            中心y = (y1 + y2) // 2 + random.randint(-5, 5)
            上下文.点击(中心x, 中心y, 延时=1500)

            # # 选择升级资源
            # 当前金币 = 上下文.数据库.获取最新资源(上下文.机器人标志).get("金币", 0)
            # 当前圣水 = 上下文.数据库.获取最新资源(上下文.机器人标志).get("圣水", 0)


            当前金币=上下文.数据库.获取最新完整状态(上下文.机器人标志).状态数据["家乡资源"]["金币"]
            当前圣水=上下文.数据库.获取最新完整状态(上下文.机器人标志).状态数据["家乡资源"]["圣水"]
            区域图像=上下文.op.获取屏幕图像cv(276,440,626,468)
            #区域图像=上下文.op.获取屏幕图像cv(133,428,677,491)

            金币图片 = "升级建筑的金币小图标.bmp|升级建筑的金币小图标1.bmp" if self.设置.是否刷主世界 else "升级建筑的金币小图标夜.bmp|升级建筑的金币小图标1夜.bmp"
            圣水图片 = "升级建筑的圣水小图标.bmp|升级建筑的圣水小图标1.bmp" if self.设置.是否刷主世界 else "升级建筑的圣水小图标夜.bmp|升级建筑的圣水小图标1夜.bmp"
            有金币图标,(金币x,金币y),金币调试图=self.模板识别.执行匹配(区域图像,金币图片,0.9)
            有圣水图标, (圣水x, 圣水y), _ = self.模板识别.执行匹配(区域图像, 圣水图片,0.9)
            金币x=276+金币x-27
            金币y=440+金币y+30

            圣水x=276+圣水x-27
            圣水y=440+圣水y+30


            # 屏幕图像=上下文.op.获取屏幕图像cv(0,0,800,600)
            # cv2.rectangle(屏幕图像, (圣水x, 圣水y), (圣水x+10, 圣水y+10), (0, 255, 0), 2)
            # cv2.imshow("a",屏幕图像)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()




            if 当前圣水 > 当前金币 and 有圣水图标:
                上下文.置脚本状态("使用圣水升级")
                上下文.点击(圣水x, 圣水y, 延时=1000)
            elif 有金币图标:
                上下文.置脚本状态("使用金币升级")
                上下文.点击(金币x, 金币y, 延时=1000)
            else:
                raise RuntimeError("无法定位升级按钮")
            # 上下文.脚本延时(2000)
            上下文.置脚本状态("点击升级")
            # 确认升级
            if self.设置.是否刷主世界:
                上下文.点击(573, 495, 延时=500)
            else:
                上下文.点击(400, 520, 延时=500)
            上下文.置脚本状态("城墙升级成功")
            return True
        except Exception as e:
            上下文.置脚本状态(f"升级操作失败: {str(e)}")
            return False

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
