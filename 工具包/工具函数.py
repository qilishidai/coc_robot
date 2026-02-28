import functools
import time

import cv2
import tkinter as tk

import os
import subprocess

def 打印运行耗时(函数):
    @functools.wraps(函数)
    def 包装器(*参数, **关键字参数):
        开始时间 = time.time()
        结果 = 函数(*参数, **关键字参数)
        结束时间 = time.time()
        耗时 = 结束时间 - 开始时间
        print(f"函数「{函数.__name__}」运行耗时：{耗时:.4f} 秒")
        return 结果
    return 包装器


def 生成贝塞尔轨迹(起点, 控制点1, 控制点2, 终点, 步数=30):
    """生成三阶贝塞尔曲线路径"""
    轨迹 = []
    for i in range(步数 + 1):
        t = i / 步数
        x = (1 - t) ** 3 * 起点[0] + 3 * (1 - t) ** 2 * t * 控制点1[0] + 3 * (1 - t) * t ** 2 * 控制点2[
            0] + t ** 3 * 终点[0]
        y = (1 - t) ** 3 * 起点[1] + 3 * (1 - t) ** 2 * t * 控制点1[1] + 3 * (1 - t) * t ** 2 * 控制点2[
            1] + t ** 3 * 终点[1]
        轨迹.append((int(x), int(y)))
    return 轨迹

def 显示图像(屏幕图像):
    cv2.imshow("test",屏幕图像)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def 是否家乡资源打满(资源字典: dict) -> bool:
    """根据资源字典判断是否资源打满，低本无黑油时也视为打满"""

    def 是打满(数值: int) -> bool:
        return str(数值).endswith("000") or str(数值).endswith("00000")

    金币 = 资源字典.get("金币", 0)
    圣水 = 资源字典.get("圣水", 0)
    黑油 = 资源字典.get("黑油", 0)

    return (
        是打满(金币) and
        是打满(圣水) and
        是打满(黑油)
        #(黑油 == 0 or 是打满(黑油))
    )



def 是否夜世界资源打满(资源字典: dict) -> bool:
    """根据资源字典判断是否资源打满"""

    # 单项资源打满阈值，例如末尾 ≥ 4 个 0（十万级别）
    def 是打满(数值: int) -> bool:
        return str(数值).endswith("000") or str(数值).endswith("00000")

    return (
            是打满(资源字典.get("金币", 0)) and
            是打满(资源字典.get("圣水", 0))
    )

def 单行资源识别(ocr引擎, img):
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        5
    )
    result, _ = ocr引擎(binary,  use_cls=False)
    if result and len(result) > 0:
        清理文本 = result[0][1].replace('O', '0').replace('o', '0').replace(' ', '')
        return int(''.join(filter(str.isdigit, 清理文本)))
    return 0


from tkinter import ttk
import tkinter as tk

class 工具提示:
    def __init__(self, 控件, 文本):
        self.控件 = 控件
        self.文本 = 文本
        self.提示框 = None
        self.定时器 = None
        self.控件.bind("<Enter>", self.进入)
        self.控件.bind("<Leave>", self.离开)

    def 进入(self, 事件):
        self.定时器 = self.控件.after(500, self._显示提示框)

    def _显示提示框(self):
        if self.提示框:
            return
        x = self.控件.winfo_rootx() + 20
        y = self.控件.winfo_rooty() + self.控件.winfo_height() + 10
        self.提示框 = tk.Toplevel(self.控件)
        self.提示框.wm_overrideredirect(True)
        self.提示框.wm_geometry(f"+{x}+{y}")
        标签 = tk.Label(self.提示框, text=self.文本, background="#ffffe0", relief="solid", borderwidth=1, font=("微软雅黑", 12),wraplength=300)
        标签.pack(ipadx=1)

    def 离开(self, 事件):
        if self.定时器:
            self.控件.after_cancel(self.定时器)
            self.定时器 = None
        if self.提示框:
            self.提示框.destroy()
            self.提示框 = None
