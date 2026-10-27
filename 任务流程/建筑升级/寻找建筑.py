import random
import time
import cv2
import numpy as np

from 任务流程.基础任务框架 import 任务上下文, 基础任务
from 任务流程.夜世界.夜世界打鱼.夜世界基础任务类 import 夜世界基础任务
from 任务流程.新版升级面板 import 新版升级面板
from 任务流程.建筑升级.升级普通建筑 import 提取建议升级建筑, 提取建议升级建筑名称


class 资源不足错误(Exception):
    """资源不足异常"""

    def __init__(self, 错误信息):
        super().__init__(错误信息)
        self.错误信息 = 错误信息

    def __str__(self):
        return f"发生了：{self.错误信息}"

from enum import Enum

class 建筑查找模式(Enum):
    指定建筑 = "指定建筑"
    建议升级中的第一个可用建筑 = "建议升级"

class 寻找建筑(夜世界基础任务):
    """在统一升级面板中寻找指定建筑

    2026新版UI：面板打开时列表停留在顶部，从上往下逐屏查找；
    连续多次滑动后界面内容不变则判定已到列表底部，报告找不到指定建筑。
    """

    默认颜色阈值 = {'色差H': 10, '色差S': 10, '色差V': 10, '最少像素数': 150}

    # 到底判定：连续滑动后列表内容无变化(每次滑动约一屏，2次相同即认定到底)
    最大连续未变化次数 = 2

    def __init__(self, 上下文: '任务上下文', 建筑名称: str | list | None  = None,查找模式: 建筑查找模式 = 建筑查找模式.指定建筑):
        super().__init__(上下文)
        self.查找模式 = 查找模式
        self.开始时间 = None
        self.当前建筑: str | None = None  # 新增实例变量，用于保存找到的建筑，然后升级建筑任务读取这个变量，用于根据不同的建筑类型执行升级操作
        # 新版统一升级面板驱动
        self.面板 = 新版升级面板(上下文)
        # 到底判定状态
        self.上次名称集合 = None
        self.连续相同ocr次数 = 0


        if 查找模式 == 建筑查找模式.指定建筑:
            # 支持单个建筑名称或多个建筑名称
            if isinstance(建筑名称, str):
                self.建筑列表 = [建筑名称]
            elif isinstance(建筑名称, list):
                self.建筑列表 = 建筑名称
            else:
                raise TypeError("建筑名称必须是字符串或字符串列表")

        elif 查找模式 == 建筑查找模式.建议升级中的第一个可用建筑:
            if 建筑名称 is not None:
                raise ValueError("建议升级模式下，不允许传入建筑名称")

            self.建筑列表 = []  # 由 OCR 决定

        else:
            raise ValueError(f"未知的查找模式: {查找模式}")


    # ---------------------- 主入口 ----------------------
    def 执行(self) -> bool:
        """任务执行入口"""
        try:

            if self.查找模式 == 建筑查找模式.指定建筑:
                return self.找建筑循环()
            elif self.查找模式 == 建筑查找模式.建议升级中的第一个可用建筑:
                self.上下文.置脚本状态(f"开始寻找建议升级中的建筑")

                self.打开建筑页面()
                ocr结果 = self.执行OCR识别(self.面板.面板OCR区域)

                self.建筑列表 = 提取建议升级建筑名称(ocr结果)
                if self.建筑列表 is None:
                    self.上下文.置脚本状态(f"警告，无法确定建议升级列表中的建筑,ocr结果为"+ocr结果.__str__())
                    self.关闭建筑页面()
                    return False

                self.上下文.置脚本状态(f"建议升级{', '.join(self.建筑列表)}")

                是否选中 = self.尝试选中指定建筑(提取建议升级建筑(ocr结果))
                if not 是否选中:
                    # 未选中任何建筑，关闭面板避免影响后续任务
                    self.关闭建筑页面()
                return 是否选中

        except 资源不足错误 as e:
            self.上下文.置脚本状态(str(e))
            return False
        except Exception as e:
            self.异常处理(e)
            return False






    # ---------------------- 主流程循环 ----------------------
    def 找建筑循环(self) -> bool:
        """从列表顶部开始从上往下寻找指定建筑

        性能优化：每屏只做一次OCR，滑动后下一轮OCR同时用于找建筑和到底判定；
        每次滑动约一屏距离(保留重叠)，整列表只需几轮即可扫完。
        找到返回 True，滑动到列表底部仍未找到则关闭面板并返回 False
        """
        self.上下文.置脚本状态(f"开始寻找建筑: {', '.join(self.建筑列表)}")
        self.打开建筑页面()
        self.开始时间 = time.time()
        self.上次名称集合 = None
        self.连续相同ocr次数 = 0

        while True:
            self.上下文.脚本延时(300)
            ocr结果 = self.执行OCR识别(self.面板.面板OCR区域)

            建筑列表 = self.提取可见中文名称(ocr结果)
            self.上下文.置脚本状态(f"当前可见建筑: {', '.join(建筑列表)}")

            # 根据 OCR 结果，如果包含要查找的建筑,那么尝试选中建筑
            if ocr结果 and self.尝试选中指定建筑(ocr结果):
                self.上下文.脚本延时(1500)
                return True

            # 滑动后内容与上一屏完全相同，说明列表已不再滚动(到底)
            if self.列表已到底(ocr结果):
                break

            if time.time() - self.开始时间 > 120:
                self.关闭建筑页面()
                raise RuntimeError(f"找建筑超时: {', '.join(self.建筑列表)}")

            self.面板.向上滑动一下()

        self.关闭建筑页面()
        self.上下文.置脚本状态(f"已滑动到列表底部，找不到指定的建筑: {', '.join(self.建筑列表)}")
        return False

    # ---------------------- 界面操作 ----------------------
    def 打开建筑页面(self):
        """点击建造按钮打开新版升级面板并切换到建筑列表，列表停留在顶部"""
        self.面板.打开列表(入口坐标=self.面板.建筑入口坐标)

    def 关闭建筑页面(self):
        """点击面板右上角X关闭建筑界面"""
        self.面板.关闭面板()

    # ---------------------- 到底判定 ----------------------
    def 列表已到底(self, ocr结果) -> bool:
        """检测连续多次滑动后界面内容未变化，判断列表是否已到底"""
        当前名称集合 = self.提取名称集合(ocr结果)

        if not 当前名称集合:
            self.连续相同ocr次数 = 0
            self.上次名称集合 = None
            return False

        if self.上次名称集合 == 当前名称集合:
            self.连续相同ocr次数 += 1
        else:
            self.连续相同ocr次数 = 0
        self.上次名称集合 = 当前名称集合

        return self.连续相同ocr次数 >= self.最大连续未变化次数

    def 提取名称集合(self, ocr结果) -> list:
        """从OCR结果中提取稳定的中文名称，过滤数字和噪声"""
        名称集合 = []
        for 项 in ocr结果:
            if not isinstance(项, (list, tuple)) or len(项) < 2:
                continue
            文本 = 项[1]
            if not isinstance(文本, str):
                continue
            文本 = 文本.replace(" ", "")
            if any('\u4e00' <= c <= '\u9fff' for c in 文本):
                名称集合.append(文本)
        return sorted(名称集合)

    def 提取可见中文名称(self, ocr结果) -> list:
        """提取当前可见的中文名称文本，用于日志展示"""
        建筑列表 = []
        for 项 in ocr结果:
            文本 = 项[1]
            # 排除数字，只保留含有中文字符的
            if any('\u4e00' <= c <= '\u9fff' for c in 文本):
                建筑列表.append(文本)
        return 建筑列表

    # ---------------------- OCR处理 ----------------------
    # 列表顶部固定显示"正在升级"队列，其中的建筑名称与可升级建筑相同，
    # 但点击不会弹出升级对话框，必须排除。正在升级的建筑始终位于
    # "建议升级/其他升级"锚点上方，以锚点y坐标为界过滤。
    升级区锚点文本 = ("建议升级", "其他升级")

    def 获取升级区锚点y(self, ocr结果):
        """获取'建议升级/其他升级'锚点的最小y坐标(OCR局部坐标)

        返回 None 表示锚点不在当前可见区域(已滑过列表顶部)
        """
        锚点y列表 = []
        for 识别项 in ocr结果:
            if not isinstance(识别项, (list, tuple)) or len(识别项) < 2:
                continue
            文本 = str(识别项[1]).replace(" ", "")
            if any(锚点 in 文本 for 锚点 in self.升级区锚点文本):
                锚点y列表.append(min(点[1] for 点 in 识别项[0]))
        return min(锚点y列表) if 锚点y列表 else None

    def 尝试选中指定建筑(self, ocr结果) -> bool:
        """判断ocr结果中是否有指定建筑，有则选中，没有则直接返回

        只允许选中锚点下方的行，防止误点顶部正在升级的建筑导致卡死；
        锚点不可见说明已滑过列表顶部，此时不做限制
        """
        锚点y = self.获取升级区锚点y(ocr结果)

        for 识别项 in ocr结果:
            文本内容 = 识别项[1]
            # 只要 OCR 文本匹配建筑列表中的任意一个就选中
            if not any(建筑 in 文本内容 for 建筑 in self.建筑列表):
                continue

            # 正在升级的建筑显示在锚点上方，直接跳过
            行顶部y = min(点[1] for 点 in 识别项[0])
            if 锚点y is not None and 行顶部y <= 锚点y:
                self.上下文.置脚本状态(f"跳过正在升级中的建筑: {文本内容}")
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
        """解析OCR坐标，换算为面板行的全屏区域"""
        return self.面板.解析行坐标(坐标列表)

    # ---------------------- 升级检查与点击 ----------------------
    def 检查升级条件(self, x1, y1, x2, y2) -> bool:
        """检查资源是否足够"""
        # 新版面板右边缘为800，检查整行区域内的资源不足红色文字
        区域图像 = self.上下文.op.获取屏幕图像cv(x1, y1, 800, y2)
        if self.面板.检测资源不足((x1, y1, 800, y2)):
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
