from 任务流程.基础任务框架 import 任务上下文, 基础任务
from 任务流程.夜世界.夜世界打鱼.夜世界基础任务类 import 夜世界基础任务
from 任务流程.新版升级面板 import 新版升级面板

class 升级按钮定位失败错误(Exception):
    """当英雄不可升级时抛出的异常"""
    def __init__(self):
        super().__init__(f"升级按钮定位失败")
        # self.英雄名称 = 英雄名称

    # def __str__(self):
    #     return f"英雄[{self.英雄名称}]不可升级"

class 升级普通建筑任务(基础任务):
    """自动检测并升级指定建筑

    2026新版UI流程：寻找建筑任务点击列表条目后会弹出升级详情对话框，
    对话框右下角直接是带费用的确认按钮，点击确认即开始升级。
    """

    def __init__(self, 上下文: '任务上下文',要升级的建筑):
        super().__init__(上下文)
        # 新版统一升级面板驱动
        self.面板 = 新版升级面板(上下文)
        self.要升级的建筑= 要升级的建筑

    def 执行(self) -> bool:
        """检查升级详情对话框并点击确认"""
        try:

            self.上下文.置脚本状态(f"正在尝试升级[{self.要升级的建筑}] ")

            # OCR 识别详情对话框右下角的确认按钮区域
            ocr结果 = self.面板.执行OCR识别(self.面板.确认按钮区域)

            if "确认" not in ocr结果.__str__():
                # 抛出不可升级异常
                raise 升级按钮定位失败错误()

            self.上下文.置脚本状态(f"定位到升级确认按钮")

            # 资源不足时确认按钮费用显示为红色
            if self.面板.检测资源不足(self.面板.确认按钮区域):
                self.上下文.置脚本状态(f"[{self.要升级的建筑}] 资源不足，放弃本次升级")
                self.关闭升级界面()
                return False

            # 点击确认开始升级
            self.上下文.点击(*self.面板.确认按钮点击坐标)
            self.上下文.脚本延时(1500)

            self.关闭升级界面()
            return True

        except 升级按钮定位失败错误 as e:
            # 统一处理不可升级情况：关闭页面 + 状态记录
            self.上下文.置脚本状态(str(e))
            self.关闭升级界面()
            return False

        except Exception as e:
            # 其他异常统一处理
            self.异常处理(e)
            return False

    def 关闭升级界面(self):
        """关闭升级详情对话框和升级面板"""
        self.面板.关闭详情对话框()
        self.面板.关闭面板()




from typing import Sequence, List, Optional, Tuple


def 提取建议升级建筑名称(
        ocr结果: Sequence[Tuple[list, str, float]],
        最低置信度: float = 0.8,
        排除城墙: bool = True
) -> Optional[List[str]]:
    """
    从 OCR 识别结果中，提取“建议升级”与“其他升级”之间的建筑名称列表。

    处理流程：
    1. 按文本框的 y 坐标自上而下排序
    2. 定位“建议升级”起始位置与“其他升级”结束位置
    3. 过滤低置信度、非建筑文本
    4. 可选排除“城墙”

    :param ocr结果: OCR 识别结果序列，格式为 (坐标框, 文本, 置信度)
    :param 最低置信度: 建筑文本可接受的最低置信度阈值
    :param 排除城墙: 是否排除城墙
    :return: 建筑名称列表，若未找到有效建筑则返回 None
    """

    if not ocr结果:
        return None

    # 1. 按文本框顶部 y 坐标排序
    排序后结果 = sorted(
        ocr结果,
        key=lambda 项: min(点[1] for 点 in 项[0])
    )

    # 2. 定位“建议升级”和“其他升级”的索引
    起始索引, 结束索引 = _定位升级区间(排序后结果)
    if 起始索引 is None or 结束索引 is None:
        return None

    # 3. 提取建筑名称
    建筑名称列表: List[str] = []

    for _, 原始文本, 置信度 in 排序后结果[起始索引 + 1:结束索引]:
        文本 = 原始文本.strip()

        if 置信度 < 最低置信度:
            continue

        if not 看起来像建筑(文本):
            continue

        if 排除城墙 and "城墙" in 文本:
            continue

        建筑名称列表.append(文本)

    return 建筑名称列表 or None


from typing import List, Optional, Sequence, Tuple


def 提取建议升级建筑(
    ocr结果: Sequence[Tuple[list, str, float]],
    最低置信度: float = 0.8,
    排除城墙: bool = True
) -> Optional[List[Tuple[list, str, float]]]:
    """
    从 OCR 识别结果中，提取“建议升级”与“其他升级”之间的建筑条目。

    处理流程：
    1. 按文本框的 y 坐标进行自上而下排序
    2. 定位“建议升级”起始位置与“其他升级”结束位置
    3. 过滤低置信度、非建筑文本
    4. 可选排除“城墙”

    :param ocr结果: OCR 识别结果序列，格式为 (坐标框, 文本, 置信度)
    :param 最低置信度: 建筑文本可接受的最低置信度阈值
    :param 排除城墙: 是否在结果中排除“城墙”
    :return: 建筑条目列表，若未找到有效区间则返回 None
    """

    if not ocr结果:
        return None

    # 1. 按文本框顶部 y 坐标排序（从上到下）
    排序后结果 = sorted(
        ocr结果,
        key=lambda 项: min(点[1] for 点 in 项[0])
    )

    # 2. 定位区间边界
    起始索引, 结束索引 = _定位升级区间(排序后结果)
    if 起始索引 is None or 结束索引 is None:
        return None

    # 3. 提取并过滤建筑文本
    建筑列表: List[Tuple[list, str, float]] = []

    for 坐标框, 原始文本, 置信度 in 排序后结果[起始索引 + 1: 结束索引]:
        文本 = 原始文本.strip()

        if 置信度 < 最低置信度:
            continue

        if not 看起来像建筑(文本):
            continue

        if 排除城墙 and "城墙" in 文本:
            continue

        建筑列表.append((坐标框, 文本, 置信度))

    return 建筑列表 or None

from typing import Optional, Sequence, Tuple


def _定位升级区间(
    ocr结果: Sequence[Tuple[list, str, float]]
) -> Tuple[Optional[int], Optional[int]]:
    """
    在 OCR 结果中定位“建议升级”与“其他升级”文本所在的索引区间。

    :param ocr结果: 已按 y 坐标排序的 OCR 结果
    :return: (起始索引, 结束索引)，若未找到则为 (None, None)
    """

    起始索引: Optional[int] = None
    结束索引: Optional[int] = None

    for 索引, (_, 文本, _) in enumerate(ocr结果):
        if "建议升级" in 文本:
            起始索引 = 索引
        elif "其他升级" in 文本 and 起始索引 is not None:
            结束索引 = 索引
            break

    return 起始索引, 结束索引

import re


def 看起来像建筑(文本: str) -> bool:
    """
    判断一段文本是否“语义上可能是建筑名称”。

    过滤规则包括：
    - 长度过短
    - 纯数字 / 金额 / 时间
    - OCR 常见噪声词

    :param 文本: OCR 识别出的文本
    :return: 是否可能是建筑名称
    """

    文本 = 文本.strip()

    # 1. 长度过短（如单字噪声）
    if len(文本) < 2:
        return False

    # 2. 纯数字（价格、数量），包括空格、逗号、点
    if re.fullmatch(r"[\d\s.,]+", 文本):
        return False

    # 3. 时间描述（如 8天18小时 / 11天 / 3小时 / 45分钟）
    if re.fullmatch(r"[\d天小时分钟秒\s]+", 文本):
        return False

    # 4. 金额或数值格式（如 7.000 / 1,500）
    if re.fullmatch(r"[\d.,]+", 文本):
        return False

    # 5. OCR 已知噪声
    噪声词集合 = {"DRDDY", "批究"}
    if 文本 in 噪声词集合:
        return False

    return True
