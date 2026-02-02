from 任务流程.基础任务框架 import 任务上下文, 基础任务
from 工具包.工具函数 import 显示图像
from 模块.检测.OCR识别器 import 安全OCR引擎
from 模块.检测.YOLO检测器 import 线程安全YOLO检测器
from 模块.检测.模板匹配器 import 模板匹配引擎

class 更新夜世界资源状态任务(基础任务):
    """识别夜世界资源，并更新数据库"""

    def 执行(self) -> bool:
        上下文 = self.上下文
        资源字典 = self.识别当前资源(上下文)
        上下文.置脚本状态("夜世界资源识别结果："+str(资源字典))
        上下文.数据库.更新状态(上下文.机器人标志, "夜世界资源", 资源字典)
        return True

    def 识别当前资源(self, 上下文) -> dict:
        """识别夜世界的金币和圣水资源"""
        try:

            图像 = 上下文.op.获取屏幕图像cv(593,3,793,105)
            #显示图像(图像)
            result, _ = self.ocr引擎(图像)
            #print(result)
            金币文本 = str(result[0][1]) if len(result) > 0 else "0"
            圣水文本 = str(result[1][1]) if len(result) > 1 else "0"

            金币 = self.文本转数值(金币文本)
            圣水 = self.文本转数值(圣水文本)

            return {
                "金币": 金币,
                "圣水": 圣水,
                "总资源": 金币 + 圣水
            }
        except Exception as e:
            上下文.置脚本状态(f"夜资源识别失败: {str(e)}")
            return {"金币": 0, "圣水": 0, "总资源": 0}

    def 文本转数值(self, 文本: str) -> int:
        """文字转换为数值，去除 OCR 错误"""
        try:
            清理文本 = 文本.replace('O', '0').replace('o', '0').replace(' ', '')
            return int(''.join(filter(str.isdigit, 清理文本)))
        except:
            return 0
