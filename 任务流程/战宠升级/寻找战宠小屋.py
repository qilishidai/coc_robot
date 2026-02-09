from pathlib import Path
from 任务流程.基础任务框架 import 基础任务, 任务上下文
from 模块.检测.YOLO检测器 import 线程安全YOLO检测器


class 寻找战宠小屋任务(基础任务):
    """
    任务：寻找战宠小屋并点击打开
    """

    def __init__(self, 上下文: '任务上下文', 点击延时: int = 500):
        super().__init__(上下文)
        self.点击延时 = 点击延时

        # 模型路径
        模型目录 = Path(__file__).parent / "模型"
        onnx路径 = 模型目录 / "战宠小屋检测模块.onnx"

        # 初始化检测器
        self.战宠小屋检测器 = 线程安全YOLO检测器(onnx路径, ["战宠小屋"])

    def 执行(self) -> bool:
        """
        执行任务：寻找战宠小屋并点击打开
        返回:
            bool: 成功返回 True，失败返回 False
        """
        try:

            屏幕图像 = self.上下文.op.获取屏幕图像cv(0, 0, 800, 600)

            # YOLO 检测
            检测结果 = self.战宠小屋检测器.检测(屏幕图像)
            if not 检测结果 or not isinstance(检测结果, list):
                self.上下文.置脚本状态("战宠小屋未检测到或检测结果异常")
                return False

            # 根据置信度选择最佳框
            框 = max(检测结果, key=lambda d: d.get('置信度', 0))
            if '裁剪坐标' not in 框:
                self.上下文.置脚本状态("检测结果缺少裁剪坐标")
                return False

            # 点击战宠小屋
            x1, y1, x2, y2 = 框['裁剪坐标']
            中心x = (x1 + x2) // 2
            中心y = (y1 + y2) // 2
            self.上下文.置脚本状态(f"找到战宠小屋，位置：({中心x}, {中心y})")
            self.上下文.点击(中心x, 中心y, 延时=500)

        except Exception as e:
            self.上下文.置脚本状态(f"战宠小屋检测异常: {e}")
            return False



        # 点击打开战宠小屋按钮
        try:
            是否匹配, (x, y) = self.是否出现图片("打开战宠小屋按钮.bmp")
            if 是否匹配:
                self.上下文.点击(x, y)
                self.上下文.置脚本状态("打开战宠小屋成功")
                return True
            else:
                self.上下文.置脚本状态("未定位到打开战宠小屋按钮")
                return False
        except Exception as e:
            self.上下文.置脚本状态(f"打开按钮检测异常: {e}")
            return False
