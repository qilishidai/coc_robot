from 任务流程.基础任务框架 import 基础任务
from 任务流程.新版升级面板 import 新版升级面板


class 打开研究面板任务(基础任务):
    """检查研究状态并打开新版升级面板的研究列表"""

    # 2026新版UI：研究计数移到主村庄右下角
    研究计数OCR区域 = 新版升级面板.研究计数OCR区域

    def __init__(self, 上下文):
        super().__init__(上下文)
        # 新版统一升级面板驱动
        self.面板 = 新版升级面板(上下文)

    def 执行(self) -> bool:
        try:
            if self._检查研究是否空闲():
                self.上下文.置脚本状态("正在打开研究面板")
                self.面板.打开列表(入口坐标=self.面板.研究入口坐标)
                return True
            return False
        except Exception as e:
            self.上下文.置脚本状态(f"打开研究面板错误：{e}")
            return False

    def _检查研究是否空闲(self) -> bool:
        """检查研究是否有空闲位置"""
        识别结果 = self.执行OCR识别(self.研究计数OCR区域)

        if not 识别结果:
            raise ValueError("OCR识别结果为空")

        原始文本 = 识别结果[0][1]
        清理文本 = (
            原始文本.replace('O', '0')
            .replace('o', '0')
            .replace(' ', '')
        )

        # OCR 常把斜杠误识别为7（如 1/1 识别为 171），做一次恢复
        if "/" not in 清理文本 and len(清理文本) == 3 and 清理文本.isdigit():
            清理文本 = 清理文本[0] + "/" + 清理文本[2]

        空闲位置, 可同时研究总数 = map(int, 清理文本.split("/"))

        # 无空闲位置
        if 空闲位置 == 0:
            self.上下文.置脚本状态(f"实验室有东西在升级：({空闲位置}/{可同时研究总数})")
            return False

        # 哥布林活动特殊情况
        if 可同时研究总数 == 2 and 空闲位置 == 1:
            self.上下文.置脚本状态("当前为哥布林活动，显示1位置但实际不可用")
            return False

        # 正常可用
        if 0 <= 空闲位置 <= 可同时研究总数 <= 2:
            self.上下文.置脚本状态(f"实验室可用：{空闲位置}/{可同时研究总数}")
            return True

        # 异常情况
        self.上下文.置脚本状态(f"实验室状态异常：OCR结果为 {识别结果}")
        return False
