"""
配置管理面板模块 - 自动根据机器人设置数据类的 metadata 生成UI
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Any, Dict, List, get_args, get_origin
from dataclasses import fields
from 工具包.工具函数 import 工具提示
from 数据库.任务数据库 import 机器人设置


class 可编辑列表控件(ttk.Frame):
    """支持添加、删除、多选的列表编辑控件"""

    def __init__(self, 父容器, 默认选项: List[str], 初始值: List[str] = None, 滚轮回调=None):
        super().__init__(父容器)
        self.默认选项 = 默认选项.copy()
        self.当前项目 = (初始值.copy() if 初始值 else [])
        self.滚轮回调 = 滚轮回调

        self._创建界面()
        self._更新列表显示()

        # 绑定滚轮事件到所有子控件
        if self.滚轮回调:
            self._递归绑定滚轮(self)

    def _递归绑定滚轮(self, 控件):
        """递归绑定所有子控件的鼠标滚轮事件"""
        if self.滚轮回调:
            控件.bind("<MouseWheel>", self.滚轮回调)
        for 子控件 in 控件.winfo_children():
            self._递归绑定滚轮(子控件)

    def _创建界面(self):
        # 左侧：可用选项列表
        左侧框架 = ttk.Frame(self)
        左侧框架.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        ttk.Label(左侧框架, text="可选项:").pack(anchor=tk.W)

        滚动条1 = ttk.Scrollbar(左侧框架, orient=tk.VERTICAL)
        self.可选列表 = tk.Listbox(左侧框架, selectmode=tk.MULTIPLE, height=5,
                                 yscrollcommand=滚动条1.set)
        滚动条1.config(command=self.可选列表.yview)
        self.可选列表.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        滚动条1.pack(side=tk.RIGHT, fill=tk.Y)

        # 中间：操作按钮
        中间框架 = ttk.Frame(self)
        中间框架.pack(side=tk.LEFT, padx=5)

        ttk.Button(中间框架, text="→ 添加", width=8, command=self._添加选项).pack(pady=2)
        ttk.Button(中间框架, text="← 移除", width=8, command=self._移除选项).pack(pady=2)
        ttk.Button(中间框架, text="自定义", width=8, command=self._添加自定义项).pack(pady=10)

        # 右侧：已选项目列表
        右侧框架 = ttk.Frame(self)
        右侧框架.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        ttk.Label(右侧框架, text="已选项:").pack(anchor=tk.W)

        滚动条2 = ttk.Scrollbar(右侧框架, orient=tk.VERTICAL)
        self.已选列表 = tk.Listbox(右侧框架, selectmode=tk.MULTIPLE, height=5,
                                 yscrollcommand=滚动条2.set)
        滚动条2.config(command=self.已选列表.yview)
        self.已选列表.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        滚动条2.pack(side=tk.RIGHT, fill=tk.Y)

    def _更新列表显示(self):
        # 更新可选列表
        self.可选列表.delete(0, tk.END)
        for 项 in self.默认选项:
            if 项 not in self.当前项目:
                self.可选列表.insert(tk.END, 项)

        # 更新已选列表
        self.已选列表.delete(0, tk.END)
        for 项 in self.当前项目:
            self.已选列表.insert(tk.END, 项)

    def _添加选项(self):
        选中索引 = self.可选列表.curselection()
        if not 选中索引:
            return

        for idx in 选中索引:
            项 = self.可选列表.get(idx)
            if 项 not in self.当前项目:
                self.当前项目.append(项)

        self._更新列表显示()

    def _移除选项(self):
        选中索引 = self.已选列表.curselection()
        if not 选中索引:
            return

        待移除 = [self.已选列表.get(idx) for idx in 选中索引]
        for 项 in 待移除:
            self.当前项目.remove(项)

        self._更新列表显示()

    def _添加自定义项(self):
        对话框 = tk.Toplevel(self)
        对话框.title("添加自定义项")

        # 设置对话框宽高
        宽度 = 300
        高度 = 180  # 调高一点

        # 获取屏幕尺寸
        屏幕宽 = 对话框.winfo_screenwidth()
        屏幕高 = 对话框.winfo_screenheight()

        # 计算居中坐标
        x坐标 = int((屏幕宽 - 宽度) / 2)
        y坐标 = int((屏幕高 - 高度) / 2)

        对话框.geometry(f"{宽度}x{高度}+{x坐标}+{y坐标}")

        对话框.transient(self.winfo_toplevel())
        对话框.grab_set()

        ttk.Label(对话框, text="输入自定义项名称:").pack(pady=10)
        输入框 = ttk.Entry(对话框, width=30)
        输入框.pack(pady=5)
        输入框.focus()

        def 确认添加():
            自定义项 = 输入框.get().strip()
            if not 自定义项:
                messagebox.showwarning("提示", "名称不能为空")
                return

            if 自定义项 in self.当前项目:
                messagebox.showinfo("提示", "该项已存在")
                return

            self.当前项目.append(自定义项)
            if 自定义项 not in self.默认选项:
                self.默认选项.append(自定义项)
            self._更新列表显示()
            对话框.destroy()

        按钮框架 = ttk.Frame(对话框)
        按钮框架.pack(pady=10)
        ttk.Button(按钮框架, text="确定", command=确认添加).pack(side=tk.LEFT, padx=5)
        ttk.Button(按钮框架, text="取消", command=对话框.destroy).pack(side=tk.LEFT, padx=5)

        输入框.bind("<Return>", lambda e: 确认添加())

    def get(self) -> List[str]:
        """获取当前选中的项目列表"""
        return self.当前项目.copy()

    def set(self, 值: List[str]):
        """设置选中的项目列表"""
        self.当前项目 = 值.copy() if 值 else []
        self._更新列表显示()


class 配置管理面板(ttk.Frame):
    """自动根据机器人设置数据类的 metadata 生成UI的配置管理面板"""

    def __init__(self, 父容器, 监控中心, 数据库, 操作日志回调: Callable[[str], None], 列表刷新回调: Callable[[], None]):
        super().__init__(父容器)
        self.监控中心 = 监控中心
        self.数据库 = 数据库
        self.操作日志回调 = 操作日志回调
        self.列表刷新回调 = 列表刷新回调

        self.当前机器人ID: Optional[str] = None
        self.配置控件映射: Dict[str, Any] = {}

        self._创建界面()

    def _创建界面(self):
        """自动创建配置表单"""
        # 创建主容器
        主容器 = ttk.Frame(self)
        主容器.pack(fill=tk.BOTH, expand=True)

        # 机器人标识（特殊处理，不在dataclass中）
        标识框架 = ttk.Frame(主容器)
        标识框架.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(标识框架, text="机器人标识:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.机器人标识输入框 = ttk.Entry(标识框架)
        self.机器人标识输入框.insert(0, "robot_")
        self.机器人标识输入框.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(标识框架, text="*", foreground="red").grid(row=0, column=2, sticky=tk.W)
        工具提示(self.机器人标识输入框, "用于区分不同机器人的唯一名称")
        标识框架.columnconfigure(1, weight=1)

        # 分隔线
        ttk.Separator(主容器, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # 配置表单区域（带滚动）
        配置画布容器 = ttk.Frame(主容器)
        配置画布容器.pack(fill=tk.BOTH, expand=True, padx=10)

        画布 = tk.Canvas(配置画布容器, highlightthickness=0)
        滚动条 = ttk.Scrollbar(配置画布容器, orient=tk.VERTICAL, command=画布.yview)
        配置表单框架 = ttk.Frame(画布)

        配置表单框架.bind(
            "<Configure>",
            lambda e: 画布.configure(scrollregion=画布.bbox("all"))
        )

        画布.create_window((0, 0), window=配置表单框架, anchor="nw")
        画布.configure(yscrollcommand=滚动条.set)

        画布.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        滚动条.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定鼠标滚轮 - 改进版
        def _鼠标滚轮(event):
            画布.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _递归绑定滚轮(控件):
            """递归绑定所有子控件的鼠标滚轮事件"""
            控件.bind("<MouseWheel>", _鼠标滚轮)
            for 子控件 in 控件.winfo_children():
                _递归绑定滚轮(子控件)

        # 绑定画布和所有子控件
        画布.bind("<MouseWheel>", _鼠标滚轮)
        配置画布容器.bind("<MouseWheel>", _鼠标滚轮)

        # 保存画布引用，用于后续绑定新创建的控件
        self._画布 = 画布
        self._鼠标滚轮回调 = _鼠标滚轮
        self._配置表单框架 = 配置表单框架

        # 自动生成字段
        self._生成配置字段(配置表单框架)

        # 为所有生成的控件绑定滚轮事件
        _递归绑定滚轮(配置表单框架)

        # 按钮区域
        按钮框架 = ttk.Frame(主容器)
        按钮框架.pack(pady=10, fill=tk.X, padx=10)

        # 状态标签
        self.配置状态标签 = ttk.Label(按钮框架, text="就绪", foreground="#666")
        self.配置状态标签.pack(side=tk.LEFT, padx=20)

        # 操作按钮
        操作按钮容器 = ttk.Frame(按钮框架)
        操作按钮容器.pack(side=tk.RIGHT)

        self.主操作按钮 = ttk.Button(
            操作按钮容器,
            text="创建新机器人",
            command=self._处理主操作
        )
        self.主操作按钮.pack(side=tk.LEFT, padx=2)

        self.次要操作按钮 = ttk.Button(
            操作按钮容器,
            text="清空表单",
            command=self._重置表单操作
        )
        self.次要操作按钮.pack(side=tk.LEFT, padx=2)

        self._更新按钮状态()

    def _生成配置字段(self, 父容器):
        """自动根据机器人设置数据类的 metadata 生成字段"""
        行号 = 0

        for 字段 in fields(机器人设置):
            字段名 = 字段.name
            字段类型 = 字段.type
            元数据 = 字段.metadata

            # 跳过隐藏字段
            if 元数据.get("UI类型") == "hidden":
                continue

            # 获取显示配置
            显示名称 = 元数据.get("显示名称", 字段名)
            描述 = 元数据.get("描述", "")
            UI类型 = 元数据.get("UI类型", "entry")

            # 获取默认值
            if 字段.default is not None and 字段.default != 字段.default_factory:
                默认值 = 字段.default
            elif 字段.default_factory:
                默认值 = 字段.default_factory()
            else:
                默认值 = None

            # 创建标签
            ttk.Label(父容器, text=f"{显示名称}:").grid(
                row=行号, column=0, padx=5, pady=5, sticky=tk.E
            )

            # 创建控件
            控件 = self._创建控件(父容器, UI类型, 字段类型, 默认值, 元数据)
            控件.grid(row=行号, column=1, padx=5, pady=5, sticky=tk.EW)

            # 添加提示
            if 描述:
                工具提示(控件, 描述)

            # 保存控件引用
            self.配置控件映射[字段名] = {
                "控件": 控件,
                "类型": 字段类型,
                "UI类型": UI类型,
                "元数据": 元数据
            }

            行号 += 1

        父容器.columnconfigure(1, weight=1)

    def _创建控件(self, 父容器, UI类型: str, 字段类型, 默认值, 元数据: dict):
        """根据UI类型创建具体控件"""
        if UI类型 == "entry":
            控件 = ttk.Entry(父容器)
            if 默认值 is not None:
                控件.insert(0, str(默认值))
            return 控件

        elif UI类型 == "spinbox":
            最小值 = 元数据.get("最小值", 0)
            最大值 = 元数据.get("最大值", 100)
            步进 = 元数据.get("步进", 1)
            控件 = ttk.Spinbox(父容器, from_=最小值, to=最大值, increment=步进)
            if 默认值 is not None:
                控件.set(默认值)
            return 控件

        elif UI类型 == "combo":
            选项 = 元数据.get("选项", [])
            控件 = ttk.Combobox(父容器, values=选项, state="readonly")
            # 使用 is not None 检查，允许空字符串作为有效默认值
            if 默认值 is not None and 默认值 in 选项:
                控件.set(默认值)
            elif 选项:
                控件.current(0)
            return 控件

        elif UI类型 == "bool":
            控件 = ttk.Combobox(父容器, values=["开启", "关闭"], state="readonly")
            控件.set("开启" if 默认值 else "关闭")
            return 控件

        elif UI类型 == "editable_list":
            默认选项 = 元数据.get("默认选项", [])
            初始值 = 默认值 if isinstance(默认值, list) else []
            # 传入滚轮回调函数
            滚轮回调 = getattr(self, '_鼠标滚轮回调', None)
            控件 = 可编辑列表控件(父容器, 默认选项, 初始值, 滚轮回调)
            return 控件

        else:
            # 默认使用Entry
            控件 = ttk.Entry(父容器)
            if 默认值 is not None:
                控件.insert(0, str(默认值))
            return 控件

    def _获取控件值(self, 字段名: str, 控件信息: dict) -> Any:
        """从控件获取值并转换为正确的类型"""
        控件 = 控件信息["控件"]
        字段类型 = 控件信息["类型"]
        UI类型 = 控件信息["UI类型"]

        # 获取原始值
        if UI类型 == "bool":
            原始值 = 控件.get() == "开启"
        elif UI类型 == "editable_list":
            原始值 = 控件.get()
        elif isinstance(控件, ttk.Combobox):
            原始值 = 控件.get()
        else:
            原始值 = 控件.get()

        # 类型转换
        if 字段类型 == int:
            return int(原始值) if 原始值 else 0
        elif 字段类型 == float:
            return float(原始值) if 原始值 else 0.0
        elif 字段类型 == bool:
            return 原始值
        elif get_origin(字段类型) == list:
            return 原始值 if isinstance(原始值, list) else []
        else:
            return 原始值

    def _设置控件值(self, 字段名: str, 控件信息: dict, 值: Any):
        """设置控件的值"""
        控件 = 控件信息["控件"]
        UI类型 = 控件信息["UI类型"]

        if UI类型 == "bool":
            控件.set("开启" if 值 else "关闭")
        elif UI类型 == "editable_list":
            控件.set(值 if isinstance(值, list) else [])
        elif UI类型 == "combo":
            # combo类型需要显式处理，使用 is not None 允许空字符串值
            控件.set(值 if 值 is not None else "")
        elif isinstance(控件, ttk.Spinbox):
            # Spinbox是Entry的子类，必须在Entry之前检查
            控件.delete(0, tk.END)
            控件.insert(0, str(值) if 值 is not None else "0")
        elif isinstance(控件, ttk.Entry):
            控件.delete(0, tk.END)
            控件.insert(0, str(值) if 值 is not None else "")
        elif isinstance(控件, ttk.Combobox):
            控件.set(值 if 值 is not None else "")

    def 载入配置(self, 机器人ID: Optional[str]):
        """加载指定机器人配置到表单"""
        self.当前机器人ID = 机器人ID
        if 机器人ID is None:
            self.新建机器人()
        else:
            self._载入已有配置()
        self._更新按钮状态()

    def _载入已有配置(self):
        """从数据库加载配置并填充表单"""
        if not self.当前机器人ID:
            return

        配置 = self.数据库.获取机器人设置(self.当前机器人ID)
        if not 配置:
            return

        # 设置机器人标识
        self.机器人标识输入框.delete(0, tk.END)
        self.机器人标识输入框.insert(0, self.当前机器人ID)

        # 设置所有配置字段
        for 字段 in fields(机器人设置):
            字段名 = 字段.name
            if 字段名 in self.配置控件映射:
                值 = getattr(配置, 字段名, None)
                self._设置控件值(字段名, self.配置控件映射[字段名], 值)

    def 清空表单(self):
        """重置为新建模式"""
        self.当前机器人ID = None
        self.新建机器人()
        self._更新按钮状态()

    def 新建机器人(self):
        """清空表单并设置默认值"""
        # 设置机器人标识默认值
        self.机器人标识输入框.delete(0, tk.END)
        self.机器人标识输入框.insert(0, "robot_")

        # 设置所有字段为默认值
        默认配置 = 机器人设置()
        for 字段 in fields(机器人设置):
            字段名 = 字段.name
            if 字段名 in self.配置控件映射:
                默认值 = getattr(默认配置, 字段名)
                self._设置控件值(字段名, self.配置控件映射[字段名], 默认值)

    def _更新按钮状态(self):
        """更新按钮文本和状态标签"""
        if self.当前机器人ID is None:
            self.主操作按钮.configure(text="创建新机器人")
            self.次要操作按钮.configure(text="清空表单", state=tk.NORMAL)
            self.配置状态标签.configure(text="正在创建新配置", foreground="#666")
        else:
            self.主操作按钮.configure(text="保存修改")
            self.次要操作按钮.configure(text="放弃修改", state=tk.NORMAL)
            self.配置状态标签.configure(text=f"正在编辑：{self.当前机器人ID}", foreground="#666")

    def _处理主操作(self):
        """处理创建/保存按钮"""
        if self.当前机器人ID:
            self.应用更改()
        else:
            self._执行新建操作()

    def _重置表单操作(self):
        """处理清空/放弃按钮"""
        if self.当前机器人ID:
            self._载入已有配置()
            self.配置状态标签.configure(text="已恢复原始配置", foreground="green")
        else:
            self.新建机器人()
            self.配置状态标签.configure(text="表单已重置", foreground="blue")
        self._更新按钮状态()

    def _执行新建操作(self):
        """执行实际的创建逻辑"""
        try:
            self.应用更改()
            self._更新按钮状态()
            self.配置状态标签.configure(text="创建成功！", foreground="darkgreen")
        except Exception as e:
            self.配置状态标签.configure(text=f"创建失败：{str(e)}", foreground="red")
        finally:
            self.after(2000, self._更新按钮状态)

    def 应用更改(self):
        """收集表单数据并保存"""
        # 获取机器人标识
        机器人标识 = self.机器人标识输入框.get().strip()
        if not 机器人标识:
            messagebox.showerror("错误", "机器人标识不能为空！")
            return

        # 收集所有配置字段
        配置字典 = {}
        try:
            for 字段名, 控件信息 in self.配置控件映射.items():
                配置字典[字段名] = self._获取控件值(字段名, 控件信息)

            # 创建配置对象
            新配置 = 机器人设置(**配置字典)

        except ValueError as e:
            messagebox.showerror("配置错误", f"数值格式错误: {str(e)}")
            return
        except Exception as e:
            messagebox.showerror("配置错误", f"配置错误: {str(e)}")
            return

        # 判断是新建还是更新
        if self.当前机器人ID is None:
            self._创建新机器人(机器人标识, 新配置)
        else:
            self._更新机器人配置(机器人标识, 新配置)
        self._更新按钮状态()

    def _创建新机器人(self, 标识: str, 配置: 机器人设置):
        """创建新机器人"""
        if 标识 in self.监控中心.机器人池:
            messagebox.showerror("错误", "该标识已存在！")
            return

        try:
            self.监控中心.创建机器人(机器人标志=标识, 初始设置=配置)
            self.数据库.保存机器人设置(标识, 配置)
            self.列表刷新回调()
            self.操作日志回调(f"已创建并保存新配置：{标识}")
        except Exception as e:
            messagebox.showerror("创建失败", str(e))

    def _更新机器人配置(self, 新标识: str, 新配置: 机器人设置):
        """更新机器人配置"""
        原标识 = self.当前机器人ID
        if 新标识 != 原标识 and 新标识 in self.监控中心.机器人池:
            messagebox.showerror("错误", "目标标识已存在！")
            return

        try:
            # 先停止原有机器人
            if robot := self.监控中心.机器人池.get(原标识):
                robot.停止()

            # 更新配置并保存
            if 原标识 is not None:
                self.数据库.保存机器人设置(原标识, 新配置)
            self.当前机器人ID = 新标识
            self.列表刷新回调()
            self.操作日志回调(f"已更新配置：{原标识} → {新标识}")
        except Exception as e:
            messagebox.showerror("更新失败", str(e))
