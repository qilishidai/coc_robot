from 任务流程.基础任务框架 import 基础任务


class 打开研究面板任务(基础任务):
    """检查实验室状态并打开研究面板"""

    # ==================== 界面坐标常量 ====================
    实验室状态区域 = (268, 9, 332, 48)
    研究面板点击坐标 = (243, 13)

    def 执行(self) -> bool:
        try:
            if self._检查实验室是否空闲():
                self.上下文.置脚本状态("正在打开研究面板")
                self.上下文.点击(*self.研究面板点击坐标, 是否精确点击=True)
                return True
            return False
        except Exception as e:
            self.上下文.置脚本状态(f"打开研究面板错误：{e}")
            return False

    def _检查实验室是否空闲(self) -> bool:
        """检查实验室是否有空闲位置"""
        识别结果 = self.执行OCR识别(self.实验室状态区域)

        if not 识别结果:
            raise ValueError("OCR识别结果为空")

        原始文本 = 识别结果[0][1]
        清理文本 = (
            原始文本.replace('O', '0')
            .replace('o', '0')
            .replace(' ', '')
        )

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