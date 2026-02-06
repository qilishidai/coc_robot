# YOLO检测器完整指南

> 本教程详细讲解如何使用YOLO检测器，从数据集收集、标注、训练到部署的完整流程。

## 🎯 适合人群

- ✅ 需要识别游戏中的特定目标（建筑、兵种等）
- ✅ 有一定Python基础
- ✅ 了解机器学习基本概念（可选）

## 📚 目录

1. [YOLO简介](#1️⃣-yolo简介)
2. [环境准备](#2️⃣-环境准备)
3. [数据集收集](#3️⃣-数据集收集)
4. [数据标注](#4️⃣-数据标注)
5. [模型训练](#5️⃣-模型训练)
6. [模型测试](#6️⃣-模型测试)
7. [导出ONNX模型](#7️⃣-导出onnx模型)
8. [在项目中使用](#8️⃣-在项目中使用)
9. [进阶技巧](#9️⃣-进阶技巧)
10. [常见问题](#🐛-常见问题)

---

## 1️⃣ YOLO简介

### 什么是YOLO？

**YOLO**（You Only Look Once）是一种实时目标检测算法，能够：
- 识别图像中的物体
- 标出物体的位置（边界框）
- 给出物体的类别和置信度

### 项目中的两种实现

| 实现 | 位置 | 版本 | 用途 | 状态 |
|------|------|------|------|------|
| **主检测器** | `模块/检测/YOLO检测器/` | YOLOv5 | 通用目标检测（金矿、圣水等） | ✅ 推荐 |
| **天鹰检测器** | `任务流程/天鹰火炮成就/` | YOLOv8 | 单一目标检测（天鹰火炮） | ⚠️ 即将淘汰 |

**重要通知**：
- 天鹰火炮检测器是开源贡献者为单一任务开发的独立实现
- 对于多线程环境会创建多个检测器，资源上有一定消耗
- 即将整合到主检测器中，使用统一的YOLOv5框架
- 新开发的检测任务请使用主检测器

### 主检测器特点

```python
# 模块/检测/YOLO检测器/yolo.py - 线程安全YOLO检测器

from 模块.检测 import 线程安全YOLO检测器

# 自动使用单例模式，多线程安全
检测器 = 线程安全YOLO检测器()

# 检测图像
结果 = 检测器.检测(图像)
# 返回格式：
# [
#     {
#         "类别名称": "金矿",
#         "裁剪坐标": [x1, y1, x2, y2],
#         "置信度": 0.95
#     },
#     ...
# ]
```

**默认类别**：`["金矿", "金库", "圣水采集器", "圣水瓶"]`

---

## 2️⃣ 环境准备

### 安装依赖

```bash
# 1. 安装YOLOv5（用于训练）
pip install ultralytics

# 2. 安装标注工具
pip install labelImg

# 3. 已安装的依赖（项目自带）
# - onnxruntime
# - opencv-python
# - numpy
# - pillow
```

### GPU支持（可选，加速训练）

```bash
# 安装CUDA版本的PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 验证GPU
python -c "import torch; print(torch.cuda.is_available())"
```

---

## 3️⃣ 数据集收集

### 方法1：手动截图（推荐）

**步骤**：

1. **启动游戏并进入目标场景**
   ```python
   # 使用项目的截图功能
   from 核心.op import op类

   op = op类()  # 参考测试脚本的初始化方式

   # 截取当前屏幕
   图像 = op.获取屏幕图像cv(0, 0, 800, 600)

   # 保存
   import cv2
   cv2.imwrite(f"dataset/raw/image_{i}.png", 图像)
   ```

2. **创建数据集目录**
   ```bash
   mkdir -p dataset/images/train
   mkdir -p dataset/images/val
   mkdir -p dataset/labels/train
   mkdir -p dataset/labels/val
   ```

3. **收集多样化的数据**
   - 不同场景（主界面、进攻界面、村庄）
   - 不同时间（白天、夜晚）
   - 不同状态（建筑升级中、完成）
   - 不同角度（如果有）
   - **数量建议**：
     - 最少：每个类别50张
     - 推荐：每个类别200-500张
     - 最佳：每个类别1000+张

### 方法2：自动采集脚本

```python
# 自动采集数据集.py

import cv2
import time
from 核心.op import op类

def 自动采集数据集(总数量=1000, 间隔秒=2):
    """自动截图收集数据集"""
    op = op类(0)

    print(f"将收集 {总数量} 张图像，每 {间隔秒} 秒一张")
    print("请切换到游戏画面...")
    time.sleep(5)

    for i in range(总数量):
        try:
            # 截图
            图像 = op.获取屏幕图像cv(0, 0, 800, 600)

            # 保存
            文件名 = f"dataset/raw/image_{i:05d}.png"
            cv2.imwrite(文件名, 图像)

            print(f"[{i+1}/{总数量}] 已保存: {文件名}")

            # 等待
            time.sleep(间隔秒)

        except KeyboardInterrupt:
            print("\n采集中断")
            break
        except Exception as e:
            print(f"错误: {e}")

    print(f"\n采集完成！共 {i+1} 张图像")

if __name__ == "__main__":
    自动采集数据集(总数量=500, 间隔秒=3)
```

### 数据清洗

**删除无效图像**：
- 模糊的
- 加载中的
- 弹窗遮挡的
- 目标不清晰的

**技巧**：使用Python快速筛选

```python
import cv2
from pathlib import Path

# 显示所有图像，按键删除
for 图像路径 in Path("dataset/raw").glob("*.png"):
    图像 = cv2.imread(str(图像路径))
    cv2.imshow("检查图像（按D删除，按空格继续）", 图像)

    键 = cv2.waitKey(0)
    if 键 == ord('d'):  # 删除
        图像路径.unlink()
        print(f"已删除: {图像路径.name}")

cv2.destroyAllWindows()
```

---

## 4️⃣ 数据标注

### 使用LabelImg标注

**1. 安装并启动**

```bash
pip install labelImg
labelImg
```

**2. 配置LabelImg**

- **Open Dir**：选择 `dataset/images/train`
- **Change Save Dir**：选择 `dataset/labels/train`
- **View → Auto Save mode**：开启自动保存
- 快捷键：
  - `W`：创建框
  - `D`：下一张
  - `A`：上一张
  - `Del`：删除框

**3. 标注步骤**

1. 点击 **Create RectBox**（或按 `W`）
2. 在目标周围拖动鼠标框选
3. 输入类别名称（如 `金矿`）
4. 重复步骤1-3标注所有目标
5. 按 `D` 保存并下一张

**4. 标注规范**

```
✅ 正确标注：
┌─────────┐
│  金矿   │  <- 框紧贴目标边缘
└─────────┘

❌ 错误标注：
┌──────────────┐
│              │  <- 框太大，包含背景
│    金矿      │
└──────────────┘

❌ 错误标注：
┌────┐
│金矿│  <- 框太小，目标被裁剪
└────┘
```

**5. 类别命名规则**

- 使用**中文**（与代码一致）
- 避免空格和特殊字符
- 保持一致性

**示例类别**：
```
金矿
金库
圣水采集器
圣水瓶
天鹰火炮
大本营
城墙
```

### 标注文件格式

LabelImg生成的YOLO格式标注文件（.txt）：

```
# dataset/labels/train/image_00001.txt

0 0.5 0.3 0.15 0.2
1 0.7 0.6 0.12 0.18
# ↑ ↑   ↑   ↑    ↑
# 类别索引 中心x 中心y 宽度 高度（归一化0-1）
```

### 数据集划分

```python
# 划分训练集和验证集.py

import shutil
from pathlib import Path
import random

def 划分数据集(源目录, 训练集比例=0.8):
    """将数据集划分为训练集和验证集"""

    源目录 = Path(源目录)
    图像列表 = list(源目录.glob("*.png")) + list(源目录.glob("*.jpg"))

    # 打乱顺序
    random.shuffle(图像列表)

    # 计算划分点
    训练数量 = int(len(图像列表) * 训练集比例)

    # 创建目标目录
    训练图像目录 = Path("dataset/images/train")
    验证图像目录 = Path("dataset/images/val")
    训练标签目录 = Path("dataset/labels/train")
    验证标签目录 = Path("dataset/labels/val")

    for 目录 in [训练图像目录, 验证图像目录, 训练标签目录, 验证标签目录]:
        目录.mkdir(parents=True, exist_ok=True)

    # 复制文件
    for i, 图像路径 in enumerate(图像列表):
        标签路径 = 图像路径.with_suffix('.txt')

        if not 标签路径.exists():
            print(f"警告: 缺少标签文件 {标签路径}")
            continue

        # 判断是训练集还是验证集
        if i < 训练数量:
            shutil.copy(图像路径, 训练图像目录)
            shutil.copy(标签路径, 训练标签目录)
        else:
            shutil.copy(图像路径, 验证图像目录)
            shutil.copy(标签路径, 验证标签目录)

    print(f"划分完成:")
    print(f"  训练集: {训练数量} 张")
    print(f"  验证集: {len(图像列表) - 训练数量} 张")

if __name__ == "__main__":
    划分数据集("dataset/raw", 训练集比例=0.8)
```

---

## 5️⃣ 模型训练

### 创建数据集配置文件

```yaml
# dataset/coc_dataset.yaml

path: ./dataset  # 数据集根目录
train: images/train  # 训练集图像目录
val: images/val  # 验证集图像目录

# 类别数量
nc: 4

# 类别名称（按索引顺序）
names:
  0: 金矿
  1: 金库
  2: 圣水采集器
  3: 圣水瓶
```

### 训练脚本

```python
# train_yolo.py

from ultralytics import YOLO

def 训练模型(
    数据集配置="dataset/coc_dataset.yaml",
    预训练模型="yolov5n.pt",  # n(nano) < s < m < l < x
    训练轮数=100,
    图像大小=640,
    批次大小=16,
    设备="0"  # "0"=GPU, "cpu"=CPU
):
    """训练YOLO模型"""

    # 加载预训练模型
    模型 = YOLO(预训练模型)

    # 开始训练
    结果 = 模型.train(
        data=数据集配置,
        epochs=训练轮数,
        imgsz=图像大小,
        batch=批次大小,
        device=设备,
        project="runs/train",
        name="coc_detect",

        # 可选参数
        patience=50,  # 早停耐心值
        save=True,  # 保存模型
        cache=True,  # 缓存图像加速训练
        workers=4,  # 数据加载线程数
        pretrained=True,  # 使用预训练权重
        optimizer='SGD',  # 优化器
        verbose=True,  # 显示详细日志

        # 数据增强
        hsv_h=0.015,  # 色调
        hsv_s=0.7,  # 饱和度
        hsv_v=0.4,  # 明度
        degrees=0.0,  # 旋转角度
        translate=0.1,  # 平移
        scale=0.5,  # 缩放
        shear=0.0,  # 剪切
        flipud=0.0,  # 上下翻转
        fliplr=0.5,  # 左右翻转
        mosaic=1.0,  # mosaic增强
    )

    print("\n训练完成！")
    print(f"最佳模型: {结果.save_dir / 'weights' / 'best.pt'}")
    print(f"最后模型: {结果.save_dir / 'weights' / 'last.pt'}")

    return 结果

if __name__ == "__main__":
    # 开始训练
    训练模型(
        数据集配置="dataset/coc_dataset.yaml",
        预训练模型="yolov5n.pt",  # 轻量级模型
        训练轮数=100,
        批次大小=16
    )
```

### 训练参数说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `epochs` | 训练轮数 | 100-300 |
| `imgsz` | 图像大小 | 640（项目固定） |
| `batch` | 批次大小 | 16（GPU 8GB）<br>8（GPU 4GB）<br>-1（自动） |
| `device` | 设备 | "0"（GPU）<br>"cpu"（CPU） |
| `patience` | 早停耐心值 | 50 |
| `optimizer` | 优化器 | SGD（推荐）<br>Adam |

### 模型选择

| 模型 | 大小 | 速度 | 精度 | 推荐场景 |
|------|------|------|------|----------|
| YOLOv5n | 最小 | 最快 | 低 | 实时性要求高 |
| YOLOv5s | 小 | 快 | 中 | **推荐** |
| YOLOv5m | 中 | 中 | 高 | 精度要求高 |
| YOLOv5l | 大 | 慢 | 很高 | 离线分析 |
| YOLOv5x | 最大 | 最慢 | 最高 | 最高精度需求 |

### 监控训练过程

训练中会生成以下文件：

```
runs/train/coc_detect/
├── weights/
│   ├── best.pt        # 最佳模型（验证集最优）
│   └── last.pt        # 最后一轮模型
├── results.png        # 训练曲线图
├── confusion_matrix.png  # 混淆矩阵
├── F1_curve.png       # F1曲线
├── PR_curve.png       # 精确率-召回率曲线
└── train_batch*.jpg   # 训练批次示例

```

**关键指标**：
- **mAP50**：平均精度（IoU=0.5），越高越好
- **mAP50-95**：平均精度（IoU=0.5-0.95），越高越好
- **Precision**：精确率，越高越好
- **Recall**：召回率，越高越好

---

## 6️⃣ 模型测试

### 验证模型性能

```python
from ultralytics import YOLO

# 加载训练好的模型
模型 = YOLO("runs/train/coc_detect/weights/best.pt")

# 在验证集上测试
结果 = 模型.val(
    data="dataset/coc_dataset.yaml",
    imgsz=640,
    batch=16,
    conf=0.25,  # 置信度阈值
    iou=0.45,   # NMS IoU阈值
    device="0"
)

# 打印结果
print(f"mAP50: {结果.box.map50:.4f}")
print(f"mAP50-95: {结果.box.map:.4f}")
```

### 单张图像测试

```python
from ultralytics import YOLO
import cv2

# 加载模型
模型 = YOLO("runs/train/coc_detect/weights/best.pt")

# 推理
结果列表 = 模型.predict(
    source="test_image.png",
    imgsz=640,
    conf=0.25,
    save=True,  # 保存结果图像
    project="runs/predict",
    name="test"
)

# 解析结果
for 结果 in 结果列表:
    boxes = 结果.boxes
    for box in boxes:
        类别 = int(box.cls[0])
        置信度 = float(box.conf[0])
        坐标 = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

        print(f"类别: {模型.names[类别]}")
        print(f"置信度: {置信度:.4f}")
        print(f"坐标: {坐标}")
```

### 批量测试

```python
# 测试整个目录
模型.predict(
    source="dataset/images/val",
    imgsz=640,
    conf=0.25,
    save=True,
    project="runs/predict",
    name="val_results"
)
```

---

## 7️⃣ 导出ONNX模型

### 为什么导出ONNX？

- ✅ 跨平台兼容性
- ✅ 更快的推理速度
- ✅ 不依赖PyTorch
- ✅ 项目使用ONNX Runtime

### 导出脚本

```python
# export_onnx.py

from ultralytics import YOLO

def 导出ONNX(
    模型路径="runs/train/coc_detect/weights/best.pt",
    输出目录="模块/检测/YOLO检测器/模型",
    简化=True
):
    """将PT模型导出为ONNX格式"""

    # 加载模型
    模型 = YOLO(模型路径)

    # 导出ONNX
    onnx路径 = 模型.export(
        format="onnx",
        imgsz=640,
        simplify=简化,  # 简化模型结构
        opset=12,  # ONNX opset版本
        dynamic=False  # 固定输入尺寸
    )

    print(f"\n导出成功！")
    print(f"ONNX模型: {onnx路径}")

    # 可选：复制到项目目录
    import shutil
    from pathlib import Path

    目标路径 = Path(输出目录) / "best.onnx"
    目标路径.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(onnx路径, 目标路径)
    print(f"已复制到: {目标路径}")

    return onnx路径

if __name__ == "__main__":
    导出ONNX(
        模型路径="runs/train/coc_detect/weights/best.pt",
        输出目录="模块/检测/YOLO检测器/模型"
    )
```

### 验证ONNX模型

```python
import onnxruntime as ort
import numpy as np
import cv2

# 加载ONNX模型
会话 = ort.InferenceSession("模块/检测/YOLO检测器/模型/best.onnx")

# 准备输入
图像 = cv2.imread("test.png")
图像 = cv2.resize(图像, (640, 640))
图像 = 图像.transpose(2, 0, 1).astype(np.float32) / 255.0
输入张量 = np.expand_dims(图像, 0)

# 推理
输入名 = 会话.get_inputs()[0].name
输出 = 会话.run(None, {输入名: 输入张量})

print("ONNX模型运行正常！")
print(f"输出形状: {output[0].shape}")
```

---

## 8️⃣ 在项目中使用

### 方法1：使用主检测器（推荐）

**步骤1：放置模型文件**

```bash
# 将导出的ONNX模型复制到指定位置
cp best.onnx 模块/检测/YOLO检测器/模型/best.onnx
```

**步骤2：更新类别列表**

编辑 `模块/检测/YOLO检测器/yolo.py:340`：

```python
# 修改默认类别列表
if 类别列表 is None:
    类别列表 = ["金矿", "金库", "圣水采集器", "圣水瓶"]  # 你的类别
```

**步骤3：在任务中使用**

```python
from 任务流程.基础任务框架 import 基础任务

class 检测建筑任务(基础任务):
    def 执行(self) -> bool:
        try:
            上下文 = self.上下文

            # 1. 截取屏幕
            屏幕图像 = 上下文.op.获取屏幕图像cv(0, 0, 800, 600)

            # 2. YOLO检测（self.检测器已预初始化）
            检测结果 = self.检测器.检测(屏幕图像)

            # 3. 处理结果
            for 目标 in 检测结果:
                类别 = 目标["类别名称"]
                坐标 = 目标["裁剪坐标"]  # [x1, y1, x2, y2]
                置信度 = 目标["置信度"]

                上下文.置脚本状态(f"检测到: {类别}, 置信度: {置信度:.2f}")

                # 计算中心点
                中心x = (坐标[0] + 坐标[2]) // 2
                中心y = (坐标[1] + 坐标[3]) // 2

                # 点击目标
                if 类别 == "金矿" and 置信度 > 0.7:
                    上下文.点击(中心x, 中心y, 500)

            return True

        except Exception as e:
            self.异常处理(e)
            return False
```

### 方法2：自定义检测器（高级）

如果需要使用不同的模型路径或类别列表：

```python
from 模块.检测 import 线程安全YOLO检测器

class 自定义检测任务(基础任务):
    def __init__(self, 上下文):
        super().__init__(上下文)

        # 使用自定义模型
        self.自定义检测器 = 线程安全YOLO检测器(
            模型路径="path/to/custom_model.onnx",
            类别列表=["类别1", "类别2", "类别3"]
        )

    def 执行(self) -> bool:
        # 使用自定义检测器
        结果 = self.自定义检测器.检测(图像)
        # ...
```

### 完整示例：自动收集资源

```python
from 任务流程.基础任务框架 import 基础任务

class 自动收集资源(基础任务):
    """使用YOLO检测并收集资源建筑"""

    def 执行(self) -> bool:
        try:
            上下文 = self.上下文
            上下文.置脚本状态("开始收集资源...")

            # 1. 返回主界面
            self.返回主界面()

            # 2. 检测资源建筑
            资源列表 = self.检测资源建筑()

            if not 资源列表:
                上下文.置脚本状态("未检测到可收集的资源")
                return True

            上下文.置脚本状态(f"检测到 {len(资源列表)} 个资源建筑")

            # 3. 逐个收集
            收集数量 = 0
            for 资源 in 资源列表:
                if self.收集单个资源(资源):
                    收集数量 += 1
                    上下文.脚本延时(500)

            上下文.置脚本状态(f"收集完成，共 {收集数量} 个")
            return True

        except Exception as e:
            self.异常处理(e)
            return False

    def 检测资源建筑(self):
        """检测所有资源建筑"""
        上下文 = self.上下文

        # 截取主界面
        屏幕图像 = 上下文.op.获取屏幕图像cv(0, 0, 800, 600)

        # YOLO检测
        检测结果 = self.检测器.检测(屏幕图像)

        # 过滤资源建筑
        资源类型 = ["金矿", "圣水采集器"]
        资源列表 = []

        for 目标 in 检测结果:
            if 目标["类别名称"] in 资源类型:
                # 过滤低置信度
                if 目标["置信度"] >= 0.6:
                    资源列表.append(目标)

        # 按置信度排序
        资源列表.sort(key=lambda x: x["置信度"], reverse=True)

        return 资源列表

    def 收集单个资源(self, 资源):
        """点击收集单个资源"""
        上下文 = self.上下文

        # 计算中心点
        坐标 = 资源["裁剪坐标"]
        中心x = (坐标[0] + 坐标[2]) // 2
        中心y = (坐标[1] + 坐标[3]) // 2

        # 点击资源建筑
        上下文.点击(中心x, 中心y, 800)

        # 检测收集按钮
        屏幕图像 = 上下文.op.获取屏幕图像cv(0, 0, 800, 600)
        是否匹配, (按钮x, 按钮y), _ = self.模板识别.执行匹配(
            屏幕图像, "收集按钮.bmp", 0.9
        )

        if 是否匹配:
            上下文.点击(按钮x, 按钮y, 500)
            上下文.置脚本状态(f"收集 {资源['类别名称']}")
            return True

        return False

    def 返回主界面(self):
        """返回到主界面"""
        # ... 实现返回逻辑
        pass
```

---

## 9️⃣ 进阶技巧

### 1. 提高检测精度

**数据增强**：

```python
# 在训练时增加数据增强
模型.train(
    # ...
    mosaic=1.0,      # Mosaic增强
    mixup=0.1,       # Mixup增强
    copy_paste=0.1,  # Copy-Paste增强
    hsv_h=0.015,     # 色调变化
    hsv_s=0.7,       # 饱和度变化
    hsv_v=0.4,       # 明度变化
    degrees=0.0,     # 旋转（游戏通常不需要）
    translate=0.1,   # 平移
    scale=0.5,       # 缩放
    fliplr=0.5       # 左右翻转
)
```

**多模型集成**：

```python
from 模块.检测 import 线程安全YOLO检测器

class 集成检测(基础任务):
    def __init__(self, 上下文):
        super().__init__(上下文)

        # 加载多个模型
        self.模型1 = 线程安全YOLO检测器("model1.onnx", 类别)
        self.模型2 = 线程安全YOLO检测器("model2.onnx", 类别)

    def 检测(self, 图像):
        # 两个模型都检测
        结果1 = self.模型1.检测(图像)
        结果2 = self.模型2.检测(图像)

        # 合并结果（投票或平均置信度）
        # ...
```

### 2. 优化推理速度

**使用TensorRT（NVIDIA GPU）**：

```python
# 导出TensorRT引擎
模型.export(format="engine", device=0, half=True)

# TensorRT推理速度更快
```

**降低图像大小**（牺牲精度）：

```python
# 使用更小的输入尺寸
检测结果 = 模型.predict(图像, imgsz=320)  # 默认640
```

**批量推理**：

```python
# 一次推理多张图像
图像列表 = [图1, 图2, 图3]
结果列表 = 模型.predict(图像列表, imgsz=640)
```

### 3. 处理小目标

**过滤策略**：

```python
def 过滤小目标(检测结果, 最小宽度=20, 最小高度=20, 最小面积=400):
    """过滤掉太小的目标"""
    有效结果 = []

    for 目标 in 检测结果:
        坐标 = 目标["裁剪坐标"]
        宽度 = 坐标[2] - 坐标[0]
        高度 = 坐标[3] - 坐标[1]
        面积 = 宽度 * 高度

        if 宽度 >= 最小宽度 and 高度 >= 最小高度 and 面积 >= 最小面积:
            有效结果.append(目标)

    return 有效结果
```

**训练时增加小目标样本**：

- 收集更多小目标的图像
- 使用更高分辨率的训练数据

### 4. 降低误检

**提高置信度阈值**：

```python
# 只保留高置信度的结果
检测结果 = [目标 for 目标 in 检测结果 if 目标["置信度"] >= 0.7]
```

**二次确认**：

```python
def 二次确认检测(self, 目标):
    """使用模板匹配二次确认YOLO检测结果"""
    坐标 = 目标["裁剪坐标"]

    # 截取检测区域
    区域图像 = self.上下文.op.获取屏幕图像cv(
        坐标[0], 坐标[1],
        坐标[2] - 坐标[0],
        坐标[3] - 坐标[1]
    )

    # 模板匹配确认
    是否匹配, _, _ = self.模板识别.执行匹配(区域图像, "确认模板.bmp", 0.8)

    return 是否匹配
```

---

## 🐛 常见问题

### 问题1：训练时显存不足

**错误信息**：
```
CUDA out of memory
```

**解决方案**：
```python
# 1. 减小批次大小
模型.train(batch=8)  # 或4、2

# 2. 使用更小的模型
模型 = YOLO("yolov5n.pt")  # 而不是yolov5s.pt

# 3. 减小图像大小（不推荐，项目固定640）
模型.train(imgsz=416)

# 4. 使用CPU训练（极慢）
模型.train(device="cpu")
```

### 问题2：检测结果不准确

**原因分析**：
- 训练数据不足
- 数据质量差（模糊、遮挡）
- 训练轮数不够
- 类别不平衡

**解决方案**：
```python
# 1. 增加训练数据
# 每个类别至少200张

# 2. 提高数据质量
# 删除模糊、遮挡的图像

# 3. 增加训练轮数
模型.train(epochs=200)

# 4. 平衡各类别样本数量
# 或使用类别权重
```

### 问题3：ONNX导出失败

**错误信息**：
```
ONNX export failed
```

**解决方案**：
```bash
# 更新依赖
pip install --upgrade onnx onnxruntime ultralytics

# 或指定opset版本
模型.export(format="onnx", opset=11)
```

### 问题4：推理速度慢

**解决方案**：

1. **使用GPU推理**
   ```python
   # 确保ONNX Runtime使用GPU
   providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
   会话 = ort.InferenceSession(模型路径, providers=providers)
   ```

2. **减小输入尺寸**（牺牲精度）
   ```python
   # 不推荐，项目固定640
   ```

3. **使用TensorRT**
   ```python
   模型.export(format="engine")
   ```

### 问题5：训练中断后恢复

```python
# 从最后一次保存的权重继续训练
模型 = YOLO("runs/train/coc_detect/weights/last.pt")
模型.train(resume=True)
```

---

## 📚 相关资源

### 官方文档

- [Ultralytics YOLOv5](https://github.com/ultralytics/yolov5)
- [Ultralytics Docs](https://docs.ultralytics.com/)
- [ONNX Runtime](https://onnxruntime.ai/)

### 标注工具

- [LabelImg](https://github.com/heartexlabs/labelImg)
- [Roboflow](https://roboflow.com/) - 在线标注和数据增强
- [CVAT](https://github.com/opencv/cvat) - 专业标注工具

### 相关文档

- [任务开发进阶](./03-任务开发进阶.md) - 使用YOLO的基础教程
- [任务开发API](../核心文档/任务开发API.md) - 完整API参考

---

## 🔗 下一步

- **数据收集**：开始收集你的训练数据
- **模型训练**：训练你的第一个模型
- **部署使用**：在项目中使用训练好的模型

---

**提示**：本教程覆盖了从零到部署的完整流程。如果遇到问题，请在 [Issues](https://github.com/qilishidai/coc_robot/issues) 中反馈！

**最后更新**：2026-02-07
