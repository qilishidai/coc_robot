import difflib
import random
import re

from 任务流程.基础任务框架 import 基础任务, 任务上下文
from 任务流程.战宠升级.图像算法 import 是否包含指定颜色_HSV
from 工具包.工具函数 import 打印运行耗时


class 无法定位目标兵种或法术错误(Exception):
    """当无法在界面中找到目标兵种或法术时抛出"""

    def __init__(self, 错误信息: str):
        super().__init__(错误信息)
        self.错误信息 = 错误信息

    def __str__(self):
        return f"发生了：{self.错误信息}"


class 打开要升级的兵种或法术任务(基础任务):
    """在研究面板中定位并点击要升级的兵种或法术"""

    # ==================== 界面坐标常量 ====================
    OCR识别区域 = (103, 88, 308, 408)
    全屏区域 = (0, 0, 800, 600)
    关闭按钮坐标 = (243, 13)
    滑动起点 = (306, 108)  # 286 + 20, 88 + 20

    # ==================== 检测参数常量 ====================
    资源不足颜色 = (250, 135, 124)  # 红色调偏粉
    颜色检测阈值 = {'色差H': 10, '色差S': 10, '色差V': 10, '最少像素数': 150}
    名称相似度阈值 = 0.75
    最大连续未变化次数 = 3
    最大滑动次数 = 30

    # ==================== 点击区域偏移量 ====================
    点击区域Y偏移 = 10
    点击区域宽度 = 189  # 199 - 10

    def __init__(self, 上下文: '任务上下文', 欲升级的兵种或法术: str):
        super().__init__(上下文)
        self.欲升级的兵种或法术 = 欲升级的兵种或法术
        self.上次名称集合 = None
        self.连续相同ocr次数 = 0

    def 执行(self) -> bool:
        """执行打开兵种或法术的主流程"""
        try:
            ocr结果 = self.执行OCR识别(self.OCR识别区域)
            print(ocr结果)
            if "升级中" in ocr结果.__str__() or "级中" in ocr结果.__str__():
                self.上下文.置脚本状态("升级：有兵种或法术升级中")
                self.关闭研究面板()
                return False

            if not self.当前界面是否存在目标兵种或法术():
                self.滑动到目标位置()
            return self.尝试点击目标兵种或法术()
        except 无法定位目标兵种或法术错误 as e:
            self.上下文.置脚本状态(str(e))
            self.关闭研究面板()
            return False
        # except Exception:
        #     return False

    def 尝试点击目标兵种或法术(self) -> bool:
        """在当前界面查找并点击目标兵种或法术"""
        识别结果 = self.执行OCR识别(self.全屏区域)

        for 框, 文本, *_ in 识别结果:
            if self.欲升级的兵种或法术 not in 文本:
                continue

            点击区域 = self._计算点击区域(框)

            if self._检测资源不足(点击区域):
                self.上下文.置脚本状态(f"升级：{self.欲升级的兵种或法术} 资源不足")
                self.关闭研究面板()
                return False

            self._执行点击(点击区域)
            return True

        self.上下文.置脚本状态(f"未定位到 {self.欲升级的兵种或法术}")
        return False

    def _计算点击区域(self, 框) -> tuple:
        """根据OCR框计算点击区域坐标"""
        x1 = 框[0][0]
        y1 = 框[0][1] - self.点击区域Y偏移
        x2 = x1 + self.点击区域宽度
        y2 = 框[0][1] + 17
        return (x1, y1, x2, y2)

    def _检测资源不足(self, 区域: tuple) -> bool:
        """检测指定区域是否显示资源不足（红色）"""
        x1, y1, x2, y2 = 区域
        区域图像 = self.上下文.op.获取屏幕图像cv(x1, y1, x2, y2)
        return 是否包含指定颜色_HSV(
            区域图像, self.资源不足颜色,
            **self.颜色检测阈值
        )

    def _执行点击(self, 区域: tuple):
        """点击区域中心"""
        x1, y1, x2, y2 = 区域
        中心x = int((x1 + x2) / 2)
        中心y = int((y1 + y2) / 2)
        self.上下文.置脚本状态(f"准备选中 {self.欲升级的兵种或法术}")
        self.上下文.点击(中心x, 中心y, 是否精确点击=True)

    def 关闭研究面板(self):
        """关闭当前研究面板"""
        self.上下文.点击(*self.关闭按钮坐标, 是否精确点击=True)

    @打印运行耗时
    def 当前界面是否存在目标兵种或法术(self) -> bool:
        """检测当前界面是否存在目标兵种或法术"""
        ocr结果 = self.执行OCR识别(self.OCR识别区域)
        当前名称集合 = self._提取稳定名称文本(ocr结果)

        if not 当前名称集合:
            self._重置连续检测状态()
            return False

        self._更新连续检测状态(当前名称集合)
        self._检查是否超过最大未变化次数()

        return self._模糊匹配目标名称(当前名称集合)

    def _重置连续检测状态(self):
        """重置连续检测的状态"""
        self.连续相同ocr次数 = 0
        self.上次名称集合 = None

    def _更新连续检测状态(self, 当前名称集合: list):
        """更新连续检测状态"""
        if self.上次名称集合 == 当前名称集合:
            self.连续相同ocr次数 += 1
        else:
            self.连续相同ocr次数 = 0
        self.上次名称集合 = 当前名称集合

    def _检查是否超过最大未变化次数(self):
        """检查是否连续多次界面未变化，超过则抛出异常"""
        if self.连续相同ocr次数 >= self.最大连续未变化次数:
            self.上下文.置脚本状态(f"连续{self.最大连续未变化次数}次界面结构未变化")
            raise 无法定位目标兵种或法术错误(
                f"升级：滑动列表已连续{self.最大连续未变化次数}次界面未变化，"
                f"未找到 {self.欲升级的兵种或法术}，可能未解锁"
            )

    def _模糊匹配目标名称(self, 名称集合: list) -> bool:
        """模糊匹配目标兵种/法术名称"""
        目标名称 = self.欲升级的兵种或法术.replace(" ", "")
        for 名称 in 名称集合:
            相似度 = difflib.SequenceMatcher(None, 目标名称, 名称).ratio()
            if 相似度 >= self.名称相似度阈值:
                return True
        return False

    def _提取稳定名称文本(self, ocr结果: list) -> list:
        """从OCR结果中提取稳定的中文名称，过滤价格和噪声"""
        稳定文本列表 = []

        for 项 in ocr结果:
            if not isinstance(项, (list, tuple)) or len(项) < 2:
                continue

            文本 = 项[1]
            if not isinstance(文本, str):
                continue

            文本 = 文本.replace(" ", "")

            # 过滤纯数字（价格区）
            if re.fullmatch(r"[0-9.\-:]+", 文本):
                continue

            # 过滤OCR噪声（过短文本）
            if len(文本) < 2:
                continue

            稳定文本列表.append(文本)

        return sorted(稳定文本列表)

    def 滑动到目标位置(self):
        """通过滑动列表找到目标兵种或法术"""
        for _ in range(self.最大滑动次数):
            self._向上滑动一下()
            if self.当前界面是否存在目标兵种或法术():
                return

        self.上下文.鼠标.左键抬起()
        raise 无法定位目标兵种或法术错误(
            f"升级：滑动{self.最大滑动次数}次后仍未找到 {self.欲升级的兵种或法术}，可能未解锁"
        )

    def _向上滑动一下(self):
        """执行一次向上滑动操作"""
        start_x, start_y = self.滑动起点
        self.上下文.鼠标.移动到(start_x, start_y)
        self.上下文.鼠标.左键按下()

        for _ in range(10):
            self.上下文.鼠标.移动相对位置(0, -random.randint(7, 12))
            self.上下文.脚本延时(5)

        self.上下文.鼠标.左键抬起()
        self.上下文.脚本延时(random.randint(300, 600))
