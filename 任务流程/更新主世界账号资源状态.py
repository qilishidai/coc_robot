from 任务流程.基础任务框架 import 任务上下文, 基础任务
from 模块.检测.OCR识别器 import 安全OCR引擎
from 模块.检测.YOLO检测器 import 线程安全YOLO检测器
from 模块.检测.模板匹配器 import 模板匹配引擎
import random


class 更新家乡资源状态任务(基础任务):
    """自动检测并升级城墙"""

    def 执行(self) -> bool:
        上下文 = self.上下文
        上下文.脚本延时(random.randint(500, 1000))#等待资源界面数字固定再执行识别
        资源字典=self.识别当前资源(上下文)
        上下文.置脚本状态("主世界资源识别结果："+str(资源字典))
        上下文.数据库.更新状态(上下文.机器人标志,"家乡资源",资源字典)
        return True

    def 识别当前资源(self, 上下文) -> dict:
        """修复后的资源识别方法"""
        try:
            全屏图像 = 上下文.op.获取屏幕图像cv(612,11,794,145)

            # 单次OCR识别（结果按顺序对应各区域）
            result, _ = self.ocr引擎(全屏图像)
            金币文本 = str(result[0][1]) if len(result) > 0 else "0"
            圣水文本 = str(result[1][1]) if len(result) > 1 else "0"
            黑油文本 = str(result[2][1]) if len(result) > 2 else "0"

            return {
                "金币": self.文本转数值(金币文本),
                "圣水": self.文本转数值(圣水文本),
                "黑油": self.文本转数值(黑油文本),
                "总资源": self.文本转数值(金币文本) + self.文本转数值(圣水文本)
            }
        except Exception as e:
            上下文.置脚本状态(f"资源识别失败: {str(e)}")
            return {"金币": 0, "圣水": 0, "黑油": 0, "总资源": 0}



    def 文本转数值(self, 文本: str) -> int:
        """增强型文本转换"""
        try:
            # 处理常见OCR错误字符
            清理文本 = 文本.replace('O', '0').replace('o', '0').replace(' ', '')
            return int(''.join(filter(str.isdigit, 清理文本)))
        except:
            return 0  # 确保始终返回数值
