import random

from 任务流程.基础任务框架 import 任务上下文
from 任务流程.夜世界.夜世界打鱼.夜世界基础任务类 import 夜世界基础任务
from 任务流程.新版升级面板 import 新版升级面板

class 英雄不可升级错误(Exception):
    """当英雄不可升级时抛出的异常"""
    def __init__(self, 英雄名称):
        super().__init__(f"英雄[{英雄名称}]不可升级")
        self.英雄名称 = 英雄名称

    def __str__(self):
        return f"英雄[{self.英雄名称}]不可升级"

class 升级英雄任务(夜世界基础任务):
    """自动检测并升级指定英雄

    2026新版UI：英雄已整合进统一升级面板的列表中，寻找建筑任务点击英雄条目后
    弹出升级详情对话框，对话框右下角直接是带费用的确认按钮，点击确认即开始升级。
    """

    def __init__(self, 上下文: '任务上下文', 要升级的英雄: str):
        super().__init__(上下文)
        self.要升级的英雄 = 要升级的英雄

        # 新版统一升级面板驱动
        self.面板 = 新版升级面板(上下文)

    def 执行(self) -> bool:
        """检查英雄升级详情对话框并点击确认"""

        try:
            # OCR 识别详情对话框右下角的确认按钮区域
            ocr结果 = self.面板.执行OCR识别(self.面板.确认按钮区域)

            if "确认" in ocr结果.__str__():
                self.上下文.置脚本状态(f"{self.要升级的英雄} 可升级")

                # 资源不足时确认按钮费用显示为红色
                if self.面板.检测资源不足(self.面板.确认按钮区域):
                    self.上下文.置脚本状态(f"[{self.要升级的英雄}] 资源不足，放弃本次升级")
                    self.关闭英雄升级页面()
                    return False

                # 点击确认开始升级
                self.上下文.点击(*self.面板.确认按钮点击坐标)
                self.上下文.脚本延时(1500)

                self.关闭英雄升级页面()
                return True
            else:
                # 抛出不可升级异常
                raise 英雄不可升级错误(self.要升级的英雄)

        except 英雄不可升级错误 as e:
            # 统一处理不可升级情况：关闭页面 + 状态记录
            self.关闭英雄升级页面()
            self.上下文.置脚本状态(str(e))
            return False

        except Exception as e:
            # 其他异常统一处理
            self.异常处理(e)
            return False

    def 关闭英雄升级页面(self):
        """关闭英雄升级详情对话框和升级面板"""
        self.面板.关闭详情对话框()
        self.面板.关闭面板()
