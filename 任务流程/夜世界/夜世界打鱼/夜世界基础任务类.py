from typing import Tuple

from 任务流程.基础任务框架 import 任务上下文
from abc import ABC, abstractmethod

from 模块.检测.YOLO检测器 import 线程安全YOLO检测器
from 模块.检测.模板匹配器 import 模板匹配引擎
from 模块.检测.OCR识别器 import 安全OCR引擎
import cv2


class 夜世界基础任务(ABC):
    """游戏任务基类"""

    def __init__(self, 上下文: '任务上下文'):
        self.上下文 = 上下文
        self.模板识别 = 模板匹配引擎()
        self.ocr引擎 = 安全OCR引擎()
        self.检测器 = 线程安全YOLO检测器()
        self.数据库 = 上下文.数据库
        self.机器人标志 = 上下文.机器人标志

    @abstractmethod
    def 执行(self) -> bool:
        """
        返回True继续下一个任务，返回False终止流程
        """
        pass

    def 是否出现图片(self, 模板路径: str, 区域: Tuple[int, int, int, int] = (0, 0, 800, 600),相似度阈值=0.9) -> Tuple[
            bool, Tuple[int, int]]:
        """
        当前机器人操作的模拟器是否出现指定图片，并返回坐标。

        参数:
            模板路径: 模板图路径（可为多个路径用 | 分隔）
            区域: 指定识别区域，格式为 (x1, y1, x2, y2)

        返回:
            是否匹配, (x, y) 坐标
        """
        x1, y1, x2, y2 = 区域
        屏幕图像 = self.上下文.op.获取屏幕图像cv(x1, y1, x2, y2)
        是否匹配, (x, y), _ = self.模板识别.执行匹配(屏幕图像, 模板路径, 相似度阈值)

        # 注意坐标需要加上区域偏移量
        if 是否匹配:
            return True, (x + x1, y + y1)
        else:
            return False, (x + x1, y + y1)

    def 执行OCR识别(self, 区域: Tuple[int, int, int, int] = (0, 0, 800, 600)) -> list:
        """执行屏幕OCR识别"""

        try:
            # 截取识别区域
            x1, y1, x2, y2 = 区域
            屏幕图像 = self.上下文.op.获取屏幕图像cv(x1, y1, x2, y2)
            # 使用OCR引擎识别
            ocr结果, _ = self.ocr引擎(屏幕图像)
            #self.上下文.置脚本状态(f"ocr结果: {ocr结果}")
            return ocr结果 if ocr结果 is not None else []
        except Exception as e:
            self.上下文.置脚本状态(f"OCR识别失败: {str(e)}")
            return []

    def 异常处理(self, 异常: Exception, 是否重启游戏=True, 是否重启机器人=True):
        """统一异常处理 - 委托给上下文处理"""
        self.上下文.处理异常(self.__class__.__name__, 异常, 是否重启游戏, 是否重启机器人)
