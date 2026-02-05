"""
任务配置UI自动生成器

根据任务元数据自动生成Tkinter配置界面
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Type
from 任务流程.任务元数据 import 任务元数据, 任务参数定义, UI控件类型
from 数据库.任务数据库 import 任务数据库


class 任务配置界面生成器:
    """自动生成任务配置界面"""

    def __init__(self, 父容器: tk.Widget, 数据库: 任务数据库, 机器人标志: str):
        self.父容器 = 父容器
        self.数据库 = 数据库
        self.机器人标志 = 机器人标志
        self.控件字典: Dict[str, Dict[str, Any]] = {}  # {任务类名: {参数名: 控件对象}}

    def 生成任务配置界面(self, 任务类: Type, 行号: int) -> int:
        """
        为指定任务类生成配置UI

        参数:
            任务类: 任务类对象
            行号: 起始行号
        返回:
            下一个可用行号
        """
        元数据: 任务元数据 = 任务类.元数据
        if not 元数据:
            return 行号

        任务类名 = 元数据.任务名称
        self.控件字典[任务类名] = {}

        # 任务标题
        标题框架 = ttk.LabelFrame(self.父容器, text=元数据.显示名称, padding=10)
        标题框架.grid(row=行号, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        行号 += 1

        # 任务描述
        if 元数据.描述:
            描述标签 = ttk.Label(标题框架, text=元数据.描述, foreground="gray")
            描述标签.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        # 前置任务提示
        if 元数据.前置任务:
            前置提示 = ttk.Label(
                标题框架,
                text=f"依赖：{', '.join(元数据.前置任务)}",
                foreground="blue",
                font=("", 8)
            )
            前置提示.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

        # 生成参数控件
        当前行 = 2
        for 参数定义 in 元数据.参数列表:
            控件 = self._创建参数控件(标题框架, 参数定义, 当前行, 任务类名)
            self.控件字典[任务类名][参数定义.参数名] = 控件
            当前行 += 1

        return 行号

    def _创建参数控件(self, 父容器: tk.Widget, 参数定义: 任务参数定义, 行号: int, 任务类名: str) -> Any:
        """创建单个参数的控件"""

        # 参数标签
        标签 = ttk.Label(父容器, text=f"{参数定义.参数名}:")
        标签.grid(row=行号, column=0, sticky="w", padx=(0, 10), pady=2)

        # 根据类型和UI控件类型创建控件
        控件类型 = 参数定义.UI控件

        # 自动选择控件类型
        if 控件类型 == UI控件类型.自动:
            if 参数定义.参数类型 == bool:
                控件类型 = UI控件类型.复选框
            elif 参数定义.候选项:
                控件类型 = UI控件类型.下拉框
            elif 参数定义.参数类型 in (int, float):
                控件类型 = UI控件类型.输入框
            else:
                控件类型 = UI控件类型.输入框

        # 创建对应控件
        if 控件类型 == UI控件类型.复选框:
            控件 = self._创建复选框(父容器, 参数定义, 行号)
        elif 控件类型 == UI控件类型.下拉框:
            控件 = self._创建下拉框(父容器, 参数定义, 行号)
        elif 控件类型 == UI控件类型.滑块:
            控件 = self._创建滑块(父容器, 参数定义, 行号)
        else:  # 默认输入框
            控件 = self._创建输入框(父容器, 参数定义, 行号)

        # 加载当前值
        self._加载参数值(控件, 参数定义, 任务类名, 控件类型)

        # 描述提示
        if 参数定义.描述:
            提示 = ttk.Label(父容器, text=f"({参数定义.描述})", foreground="gray", font=("", 8))
            提示.grid(row=行号, column=2, sticky="w", padx=(5, 0))

        return 控件

    def _创建复选框(self, 父容器: tk.Widget, 参数定义: 任务参数定义, 行号: int):
        """创建复选框"""
        变量 = tk.BooleanVar(value=参数定义.默认值 or False)
        复选框 = ttk.Checkbutton(父容器, variable=变量)
        复选框.grid(row=行号, column=1, sticky="w")
        复选框.变量 = 变量
        return 复选框

    def _创建输入框(self, 父容器: tk.Widget, 参数定义: 任务参数定义, 行号: int):
        """创建输入框"""
        变量 = tk.StringVar(value=str(参数定义.默认值 or ""))
        输入框 = ttk.Entry(父容器, textvariable=变量, width=30)
        输入框.grid(row=行号, column=1, sticky="w")
        输入框.变量 = 变量
        输入框.参数类型 = 参数定义.参数类型
        return 输入框

    def _创建下拉框(self, 父容器: tk.Widget, 参数定义: 任务参数定义, 行号: int):
        """创建下拉框"""
        变量 = tk.StringVar(value=str(参数定义.默认值 or ""))
        下拉框 = ttk.Combobox(
            父容器,
            textvariable=变量,
            values=[str(x) for x in 参数定义.候选项],
            state="readonly",
            width=28
        )
        下拉框.grid(row=行号, column=1, sticky="w")
        下拉框.变量 = 变量
        return 下拉框

    def _创建滑块(self, 父容器: tk.Widget, 参数定义: 任务参数定义, 行号: int):
        """创建滑块"""
        框架 = ttk.Frame(父容器)
        框架.grid(row=行号, column=1, sticky="w")

        变量 = tk.IntVar(value=参数定义.默认值 or 0)
        滑块 = ttk.Scale(
            框架,
            from_=参数定义.最小值 or 0,
            to=参数定义.最大值 or 100,
            variable=变量,
            orient="horizontal",
            length=200
        )
        滑块.pack(side="left", padx=(0, 10))

        # 显示当前值
        值标签 = ttk.Label(框架, textvariable=变量, width=10)
        值标签.pack(side="left")

        框架.变量 = 变量
        return 框架

    def _加载参数值(self, 控件: Any, 参数定义: 任务参数定义, 任务类名: str, 控件类型: UI控件类型):
        """从数据库加载参数值"""
        参数字典 = self.数据库.获取任务参数(self.机器人标志, 任务类名)

        if 参数定义.参数名 in 参数字典:
            值 = 参数字典[参数定义.参数名]
            if hasattr(控件, '变量'):
                if 控件类型 == UI控件类型.复选框:
                    控件.变量.set(bool(值))
                else:
                    控件.变量.set(值)

    def 保存所有参数(self):
        """保存所有任务的参数到数据库"""
        for 任务类名, 控件字典 in self.控件字典.items():
            参数字典 = {}
            for 参数名, 控件 in 控件字典.items():
                if hasattr(控件, '变量'):
                    值 = 控件.变量.get()

                    # 类型转换
                    if hasattr(控件, '参数类型'):
                        参数类型 = 控件.参数类型
                        if 参数类型 == int:
                            值 = int(值) if 值 else 0
                        elif 参数类型 == float:
                            值 = float(值) if 值 else 0.0
                        elif 参数类型 == bool:
                            值 = bool(值)

                    参数字典[参数名] = 值

            self.数据库.保存任务参数(self.机器人标志, 任务类名, 参数字典)

    def 生成批量配置界面(self, 任务类列表: List[Type]) -> tk.Widget:
        """
        生成包含多个任务的配置界面

        返回:
            包含所有任务配置的滚动框架
        """
        # 创建滚动容器
        画布 = tk.Canvas(self.父容器)
        滚动条 = ttk.Scrollbar(self.父容器, orient="vertical", command=画布.yview)
        滚动框架 = ttk.Frame(画布)

        滚动框架.bind(
            "<Configure>",
            lambda e: 画布.configure(scrollregion=画布.bbox("all"))
        )

        画布.create_window((0, 0), window=滚动框架, anchor="nw")
        画布.configure(yscrollcommand=滚动条.set)

        # 生成所有任务的配置界面
        当前行 = 0
        for 任务类 in 任务类列表:
            if hasattr(任务类, '元数据') and 任务类.元数据:
                临时生成器 = 任务配置界面生成器(滚动框架, self.数据库, self.机器人标志)
                当前行 = 临时生成器.生成任务配置界面(任务类, 当前行)
                # 合并控件字典
                self.控件字典.update(临时生成器.控件字典)

        # 保存按钮
        保存按钮 = ttk.Button(滚动框架, text="保存所有配置", command=self.保存所有参数)
        保存按钮.grid(row=当前行, column=0, columnspan=2, pady=20)

        画布.pack(side="left", fill="both", expand=True)
        滚动条.pack(side="right", fill="y")

        return 画布


# ===== 测试代码 =====
if __name__ == "__main__":
    from 任务流程.示例_使用元数据的任务 import 升级城墙任务_手动
    from 数据库.任务数据库 import 任务数据库

    # 创建测试窗口
    根窗口 = tk.Tk()
    根窗口.title("任务配置测试")
    根窗口.geometry("800x600")

    数据库 = 任务数据库()
    机器人标志 = "测试机器人"

    # 创建生成器
    生成器 = 任务配置界面生成器(根窗口, 数据库, 机器人标志)

    # 生成配置界面
    生成器.生成批量配置界面([升级城墙任务_手动])

    根窗口.mainloop()
