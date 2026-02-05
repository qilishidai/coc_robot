import threading
import time
from pathlib import Path

import cv2
import numpy as np
from io import BytesIO
import onnxruntime
from PIL import Image

np.set_printoptions(precision=4)


def 调整边界框尺寸(边界框数组, 当前尺寸, 原始形状):
    """将边界框从缩放后的尺寸调整回原始图像尺寸"""
    原始高度, 原始宽度 = 原始形状
    # 计算之前添加的填充量
    横向填充 = max(原始高度 - 原始宽度, 0) * (当前尺寸 / max(原始形状))
    纵向填充 = max(原始宽度 - 原始高度, 0) * (当前尺寸 / max(原始形状))

    # 去除填充后的实际图像尺寸
    无填充高度 = 当前尺寸 - 纵向填充
    无填充宽度 = 当前尺寸 - 横向填充

    # 将边界框坐标转换到原始图像坐标系
    边界框数组[:, 0] = ((边界框数组[:, 0] - 横向填充 // 2) / 无填充宽度) * 原始宽度  # x1
    边界框数组[:, 1] = ((边界框数组[:, 1] - 纵向填充 // 2) / 无填充高度) * 原始高度  # y1
    边界框数组[:, 2] = ((边界框数组[:, 2] - 横向填充 // 2) / 无填充宽度) * 原始宽度  # x2
    边界框数组[:, 3] = ((边界框数组[:, 3] - 纵向填充 // 2) / 无填充高度) * 原始高度  # y2
    return 边界框数组


def 生成检测结果(图像列表, 检测结果列表, 模型尺寸, 类别列表):
    """将检测结果转换为易读格式"""
    结果列表 = []
    # 确保输入是列表形式
    if not isinstance(图像列表, list):
        图像列表 = [图像列表]

    for 图像索引, (当前图像, 检测结果) in enumerate(zip(图像列表, 检测结果列表)):
        if 检测结果 is not None:
            # 将边界框调整回原始尺寸
            调整后结果 = 调整边界框尺寸(检测结果, 模型尺寸, 当前图像.shape[:2])
            for x1, y1, x2, y2, 置信度, 类别索引 in 调整后结果:
                结果列表.append({
                    "裁剪坐标": [int(x1), int(y1), int(x2), int(y2)],
                    "类别名称": 类别列表[int(类别索引)],
                    "置信度": float(置信度)
                })
        else:
            print("未检测到目标")
    return 结果列表


def 中心转角点(中心坐标数组):
    """将[中心x, 中心y, 宽, 高]转换为[左上x, 左上y, 右下x, 右下y]"""
    角点数组 = np.copy(中心坐标数组)
    角点数组[:, 0] = 中心坐标数组[:, 0] - 中心坐标数组[:, 2] / 2  # 左上x
    角点数组[:, 1] = 中心坐标数组[:, 1] - 中心坐标数组[:, 3] / 2  # 左上y
    角点数组[:, 2] = 中心坐标数组[:, 0] + 中心坐标数组[:, 2] / 2  # 右下x
    角点数组[:, 3] = 中心坐标数组[:, 1] + 中心坐标数组[:, 3] / 2  # 右下y
    return 角点数组


def 非极大抑制(检测框列表, 得分列表, 阈值):
    """非极大值抑制算法实现"""
    x1 = 检测框列表[:, 0]  # 左上x坐标
    y1 = 检测框列表[:, 1]  # 左上y坐标
    x2 = 检测框列表[:, 2]  # 右下x坐标
    y2 = 检测框列表[:, 3]  # 右下y坐标
    各框面积 = (x2 - x1 + 1) * (y2 - y1 + 1)

    # 按得分降序排列的索引
    得分排序索引 = 得分列表.argsort()[::-1]
    保留索引 = []

    while 得分排序索引.size > 0:
        # 取当前最高分索引
        当前最高分索引 = 得分排序索引[0]
        保留索引.append(当前最高分索引)

        if 得分排序索引.size == 1:
            break

        # 计算交叠区域
        其他框索引 = 得分排序索引[1:]
        xx1 = np.maximum(x1[当前最高分索引], x1[其他框索引])
        yy1 = np.maximum(y1[当前最高分索引], y1[其他框索引])
        xx2 = np.minimum(x2[当前最高分索引], x2[其他框索引])
        yy2 = np.minimum(y2[当前最高分索引], y2[其他框索引])

        # 计算交叠面积和IOU
        交叠宽 = np.maximum(0.0, xx2 - xx1 + 1)
        交叠高 = np.maximum(0.0, yy2 - yy1 + 1)
        交叠面积 = 交叠宽 * 交叠高
        IOU = 交叠面积 / (各框面积[当前最高分索引] + 各框面积[其他框索引] - 交叠面积)

        # 保留IOU低于阈值的框
        保留掩码 = np.where(IOU <= 阈值)[0]
        得分排序索引 = 得分排序索引[保留掩码 + 1]  # +1 因为其他框索引从1开始

    return np.array(保留索引)


def 非极大抑制处理(预测结果, 置信度阈值=0.25, IOU阈值=0.45, 指定类别=None, 跨类合并=False, 多标签=False):
    """执行非极大值抑制处理"""
    类别数量 = 预测结果.shape[2] - 5
    候选掩码 = 预测结果[..., 4] > 置信度阈值  # 初步筛选

    # 初始化参数
    最大检测数 = 300
    最大处理框数 = 30000
    超时限制 = 10.0  # 秒

    输出结果 = [np.zeros((0, 6))] * 预测结果.shape[0]
    开始时间 = time.time()

    for 图像索引, 单图预测 in enumerate(预测结果):
        单图预测 = 单图预测[候选掩码[图像索引]]  # 应用置信度筛选

        if not 单图预测.shape[0]:
            continue

        # 计算最终置信度 (物体置信度 * 类别置信度)
        类别置信度 = 单图预测[:, 5:] * 单图预测[:, 4:5]

        # 转换边界框格式
        边界框 = 中心转角点(单图预测[:, :4])

        if 多标签:
            # 多标签处理（保留多个类别）
            行索引, 列索引 = np.where(类别置信度 > 置信度阈值)
            单图预测 = np.concatenate(
                (边界框[行索引], 类别置信度[行索引, 列索引][:, None], 列索引[:, None]), axis=1)
        else:
            # 单标签处理（取最高分类别）
            最高置信度 = 类别置信度.max(axis=1, keepdims=True)
            最高类别 = 类别置信度.argmax(axis=1)
            单图预测 = np.concatenate((边界框, 最高置信度, 最高类别[:, None]), axis=1)
            单图预测 = 单图预测[最高置信度.reshape(-1) > 置信度阈值]

        # 筛选指定类别
        if 指定类别 is not None:
            保留掩码 = np.isin(单图预测[:, 5], 指定类别)
            单图预测 = 单图预测[保留掩码]

        # 边界框数量检查
        框数量 = 单图预测.shape[0]
        if not 框数量:
            continue
        elif 框数量 > 最大处理框数:
            单图预测 = 单图预测[单图预测[:, 4].argsort()[::-1][:最大处理框数]]

        # 执行NMS
        类别偏移 = 单图预测[:, 5:6] * (0 if 跨类合并 else 4096)  # 按类别偏移
        处理框 = 单图预测[:, :4] + 类别偏移  # 添加偏移防止跨类合并
        保留索引 = 非极大抑制(处理框, 单图预测[:, 4], IOU阈值)

        if 保留索引.shape[0] > 最大检测数:
            保留索引 = 保留索引[:最大检测数]

        输出结果[图像索引] = 单图预测[保留索引]

        if time.time() - 开始时间 > 超时限制:
            print(f"警告：NMS处理超时（{超时限制}秒）")
            break

    return 输出结果


class ONNX推理模型:
    """ONNX模型基础推理类"""

    def __init__(self, 模型路径):
        self.推理会话 = onnxruntime.InferenceSession(模型路径)
        self.输入名称 = self.获取输入名称()
        self.输出名称 = self.获取输出名称()

    def 获取输入名称(self):
        return [输入节点.name for 输入节点 in self.推理会话.get_inputs()]

    def 获取输出名称(self):
        return [输出节点.name for 输出节点 in self.推理会话.get_outputs()]

    def 构造输入字典(self, 输入数据):
        return {名称: 输入数据 for 名称 in self.输入名称}

    def 预处理图像(self, 输入源, 目标尺寸, 灰度模式=False):
        """将输入图像转换为模型需要的张量格式"""
        if isinstance(输入源, np.ndarray):
            图像对象 = Image.fromarray(输入源)
        elif isinstance(输入源, bytes):
            图像对象 = Image.open(BytesIO(输入源))
        else:
            图像对象 = Image.open(输入源)

        图像对象 = 图像对象.convert('RGB')
        if 灰度模式:
            图像对象 = 图像对象.convert('L')

        # 调整尺寸并转换格式
        图像对象 = 图像对象.resize(目标尺寸, Image.Resampling.LANCZOS)
        图像数组 = np.array(图像对象)

        if 灰度模式:
            图像数组 = np.expand_dims(图像数组, 0)  # (1, H, W)
        else:
            图像数组 = 图像数组.transpose(2, 0, 1)  # (C, H, W)

        图像数组 = np.expand_dims(图像数组, 0).astype(np.float32) / 255.0
        return 图像数组

#此类已淘汰,推荐使用线程安全yolo检测器
class YOLO检测器(ONNX推理模型):
    """YOLO目标检测器"""

    def __init__(self, 模型路径="yolov5n.onnx", 类别列表=None):
        super().__init__(模型路径)
        # 模型参数配置
        if 类别列表 is None:
            类别列表 = [
                '人', '自行车', '汽车', '摩托车', '飞机', '公交车', '火车', '卡车', '船', '交通灯',
                '消防栓', '停车标志', '停车计时器', '长椅', '鸟', '猫', '狗', '马', '羊', '牛',
                '大象', '熊', '斑马', '长颈鹿', '背包', '雨伞', '手提包', '领带', '行李箱', '飞盘',
                '滑雪板', '雪橇', '运动球', '风筝', '棒球棒', '棒球手套', '滑板', '冲浪板',
                '网球拍', '瓶子', '红酒杯', '杯子', '叉子', '刀', '勺子', '碗', '香蕉', '苹果',
                '三明治', '橙子', '西兰花', '胡萝卜', '热狗', '披萨', '甜甜圈', '蛋糕', '椅子', '沙发',
                '盆栽', '床', '餐桌', '马桶', '电视', '笔记本', '鼠标', '遥控器', '键盘', '手机',
                '微波炉', '烤箱', '烤面包机', '水槽', '冰箱', '书', '时钟', '花瓶', '剪刀', '泰迪熊',
                '吹风机', '牙刷'
            ]
        self.模型尺寸 = 640  # 训练使用的输入尺寸
        self.类别列表 = 类别列表
        self.类别数量 = len(self.类别列表)  # 修正类别数量为80

    def 预处理图像(self, 输入源):
        """YOLO专用预处理（保持长宽比的填充缩放）"""

        def 保持比例缩放(图像对象, 目标尺寸):
            原宽, 原高 = 图像对象.size
            目标宽, 目标高 = 目标尺寸

            # 计算缩放比例
            缩放比例 = min(目标宽 / 原宽, 目标高 / 原高)
            新宽 = int(原宽 * 缩放比例)
            新高 = int(原高 * 缩放比例)

            # 缩放并放置在灰色背景中央
            缩放图 = 图像对象.resize((新宽, 新高), Image.Resampling.BICUBIC)
            新图像 = Image.new('RGB', 目标尺寸, (114, 114, 114))
            新图像.paste(缩放图, ((目标宽 - 新宽) // 2, (目标高 - 新高) // 2))
            return 新图像

        if isinstance(输入源, np.ndarray):
            图像对象 = Image.fromarray(输入源)
        elif isinstance(输入源, bytes):
            图像对象 = Image.open(BytesIO(输入源))
        else:
            图像对象 = Image.open(输入源)

        处理后的图像 = 保持比例缩放(图像对象, (self.模型尺寸, self.模型尺寸))
        图像数组 = np.array(处理后的图像)

        # 转换为CHW格式并归一化
        图像张量 = 图像数组.transpose(2, 0, 1).astype(np.float32) / 255.0
        return np.expand_dims(图像张量, axis=0)  # 添加batch维度

    def 检测(self, 输入源):
        """执行目标检测"""
        # 预处理图像
        输入张量 = self.预处理图像(输入源)

        # 运行推理
        输入字典 = self.构造输入字典(输入张量)
        原始输出 = self.推理会话.run(self.输出名称, 输入字典)[0]

        # 后处理
        检测结果 = 非极大抑制处理(原始输出)

        # 转换为易读格式
        if isinstance(输入源, (str, bytes)):
            原始图像 = Image.open(输入源 if isinstance(输入源, str) else BytesIO(输入源))
        else:
            原始图像 = 输入源

        最终结果 = 生成检测结果(
            图像列表=np.array(原始图像),
            检测结果列表=检测结果,
            模型尺寸=self.模型尺寸,
            类别列表=self.类别列表
        )
        return 最终结果


class 线程安全YOLO检测器(ONNX推理模型):
    """YOLO目标检测器（线程安全的单例模式）"""

    _实例字典 = {}  # 存储不同模型路径对应的实例
    _类锁 = threading.Lock()  # 类级别的锁

    def __new__(cls, 模型路径=None, 类别列表=None):
        with cls._类锁:
            if 模型路径 not in cls._实例字典:
                # 先创建空实例，锁在__init__中初始化
                cls._实例字典[模型路径] = super().__new__(cls)
            return cls._实例字典[模型路径]

    def __init__(self, 模型路径=None, 类别列表=None):
        # 使用类锁保护实例锁的创建
        with type(self)._类锁:
            if not hasattr(self, '_实例锁'):
                self._实例锁 = threading.Lock()

        # 使用实例锁保护后续初始化
        with self._实例锁:
            if hasattr(self, '_已初始化'):
                return

            if 模型路径 is None:
                # 构建模型默认路径（自动跨平台兼容）
                模型路径 = (
                        Path(__file__).parent  # 当前文件所在目录
                        / "模型"  # 模型子目录
                        / "best.onnx"  # 模型文件名
                ).resolve()  # 转换为绝对路径

                # 验证模型文件是否存在
                if not 模型路径.exists():
                    raise FileNotFoundError(
                        f"未找到默认模型文件，请确认以下路径存在: {模型路径}\n"
                        f"或通过参数显式指定模型路径"
                    )

                # 转换为字符串（部分老库需要字符串路径）
                模型路径 = str(模型路径)

            super().__init__(模型路径)
            # 模型参数配置
            if 类别列表 is None:
                类别列表 =  ["金矿", "金库", "圣水采集器", "圣水瓶"]
            self.模型尺寸 = 640
            self.类别列表 = 类别列表
            self.类别数量 = len(类别列表)
            self._已初始化 = True

    def 预处理图像(self, 输入源):
        """YOLO专用预处理（保持长宽比的填充缩放）"""

        def 保持比例缩放(图像对象, 目标尺寸):
            原宽, 原高 = 图像对象.size
            目标宽, 目标高 = 目标尺寸

            # 计算缩放比例
            缩放比例 = min(目标宽 / 原宽, 目标高 / 原高)
            新宽 = int(原宽 * 缩放比例)
            新高 = int(原高 * 缩放比例)

            # 缩放并放置在灰色背景中央
            缩放图 = 图像对象.resize((新宽, 新高), Image.Resampling.BICUBIC)
            新图像 = Image.new('RGB', 目标尺寸, (114, 114, 114))
            新图像.paste(缩放图, ((目标宽 - 新宽) // 2, (目标高 - 新高) // 2))
            return 新图像

        if isinstance(输入源, np.ndarray):
            # 如果是 OpenCV 图像（BGR），先转换为 RGB
            if 输入源.shape[-1] == 3:  # 彩色图像
                输入源 = cv2.cvtColor(输入源, cv2.COLOR_BGR2RGB)
            图像对象 = Image.fromarray(输入源)

        elif isinstance(输入源, bytes):
            图像对象 = Image.open(BytesIO(输入源))
        else:
            图像对象 = Image.open(输入源)

        处理后的图像 = 保持比例缩放(图像对象, (self.模型尺寸, self.模型尺寸))
        图像数组 = np.array(处理后的图像)

        # 转换为CHW格式并归一化
        图像张量 = 图像数组.transpose(2, 0, 1).astype(np.float32) / 255.0
        return np.expand_dims(图像张量, axis=0)  # 添加batch维度

    def 检测(self, 输入源):
        with self._实例锁:
            # 预处理图像
            输入张量 = self.预处理图像(输入源)

            # 运行推理
            输入字典 = self.构造输入字典(输入张量)
            原始输出 = self.推理会话.run(self.输出名称, 输入字典)[0]

            # 后处理
            检测结果 = 非极大抑制处理(原始输出)

            # 转换为易读格式
            if isinstance(输入源, (str, bytes)):
                原始图像 = Image.open(输入源 if isinstance(输入源, str) else BytesIO(输入源))
            else:
                原始图像 = 输入源

            最终结果 = 生成检测结果(
                图像列表=np.array(原始图像),
                检测结果列表=检测结果,
                模型尺寸=self.模型尺寸,
                类别列表=self.类别列表
            )
            return 最终结果


# 使用方法示例
if __name__ == "__main__":
    # 初始化检测器
    检测器 = 线程安全YOLO检测器(模型路径="模型/best.onnx")

    # 输入支持多种格式：文件路径、字节流、numpy数组、PIL图像
    # 示例1：文件路径
    结果1 = 检测器.检测(r"D:\yolo\coc\images\50965031.bmp")

    # 示例2：字节流
    with open(r"D:\yolo\coc\images\50965031.bmp", "rb") as f:
        图片字节 = f.read()
    结果2 = 检测器.检测(图片字节)

    # 示例3：numpy数组
    numpy图像 = np.array(Image.open(r"D:\yolo\coc\images\50965031.bmp"))
    结果3 = 检测器.检测(numpy图像)

    # 打印结果
    print("检测结果：")
    for 目标 in 结果1:
        print(f"类别：{目标['类别名称']}, 坐标：{目标['裁剪坐标']}, 置信度：{目标['置信度']:.4f}")