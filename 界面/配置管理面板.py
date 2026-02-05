"""
配置管理面板模块 - 机器人配置表单和CRUD操作
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional
from 工具包.工具函数 import 工具提示
from 数据库.任务数据库 import 机器人设置


class 配置管理面板(ttk.Frame):
    """配置管理面板"""

    def __init__(self, 父容器, 监控中心, 数据库, 操作日志回调: Callable[[str], None], 列表刷新回调: Callable[[], None]):
        """
        初始化配置管理面板
        :param 父容器: 父容器控件
        :param 监控中心: 机器人监控中心实例
        :param 数据库: 任务数据库实例
        :param 操作日志回调: 记录操作日志的回调函数
        :param 列表刷新回调: 刷新机器人列表的回调函数
        """
        super().__init__(父容器)
        self.监控中心 = 监控中心
        self.数据库 = 数据库
        self.操作日志回调 = 操作日志回调
        self.列表刷新回调 = 列表刷新回调

        self.当前机器人ID: Optional[str] = None
        self.配置输入项 = {}

        self._创建界面()

    def _创建界面(self):
        """创建配置表单和按钮"""
        配置表单 = ttk.Frame(self)
        配置表单.pack(pady=10, padx=10, fill=tk.X)

        英雄列表 = ["野蛮人之王", "弓箭女皇", "亡灵王子", "飞盾战神", "大守护者"]
        配置项定义 = [
            ('机器人标识', 'entry', 'robot_', '用于区分不同机器人的唯一名称'),
            ('模拟器索引', 'spinbox', (0, 99, 1), '对应雷电多开器中的模拟器ID，0表示第一个模拟器,如果不明白请设置为0'),
            ('服务器', 'combo', ['国际服', '国服'], '选择游戏服务器版本,目前只支持国际服'),
            ('最小资源', 'entry', '200000', '搜索村庄对方必须高过的资源总量,超过该值才会触发进攻'),
            ('进攻资源边缘靠近比例下限', 'entry', '0.6', '在被识别到的资源建筑中，它们靠近地图边缘的比例达到此值时，才认为"资源建筑够靠边"，满足进攻条件。范围是0到1，高本建议设为0.6，低本可设为0.0。可以理解为当这个值比较大时辅助只打外围采集器'),
            ('是否开启刷墙', 'combo', ['开启', '关闭'], '是否使用金币或圣水刷墙'),
            ('刷墙起始金币', 'entry', '200000', '金币高于此数值触发刷墙任务'),
            ('刷墙起始圣水', 'entry', '200000', '圣水高于此数值触发刷墙任务,但是请注意,如果是低本,请将此值设置得足够大,以免触发圣水刷墙,但是目前还不能够圣水刷墙造成错误'),
            ('辅助运行模式', 'combo', ['只打主世界', '只打夜世界','先打满主世界再打夜世界'], '打鱼模式,字面意思,打满后辅助会停止运行.'),
            ('是否刷天鹰火炮', 'combo', ['关闭', '开启'], '开启后会自动搜索天鹰火炮并使用雷电法术攻击，用于刷成就'),
            ('欲升级的英雄', 'listbox', 英雄列表, '选择想要升级的英雄，可多选或选择默认')
        ]

        for 行, (标签, 类型, 默认值, 提示文本) in enumerate(配置项定义):
            ttk.Label(配置表单, text=f"{标签}：").grid(row=行, column=0, padx=5, pady=5, sticky=tk.E)

            if 类型 == 'entry':
                控件 = ttk.Entry(配置表单)
                控件.insert(0, 默认值)
            elif 类型 == 'combo':
                控件 = ttk.Combobox(配置表单, values=默认值, font=("微软雅黑", 10))
                控件.current(0)
            elif 类型 == 'spinbox':
                控件 = ttk.Spinbox(配置表单, from_=默认值[0], to=默认值[1], increment=默认值[2])
            elif 类型 == 'listbox':
                # 创建容器框架
                容器框架 = ttk.Frame(配置表单)
                # 创建滚动条
                滚动条 = ttk.Scrollbar(容器框架, orient=tk.VERTICAL)
                # 创建Listbox并关联滚动条
                实际listbox = tk.Listbox(容器框架, selectmode=tk.MULTIPLE, height=5, yscrollcommand=滚动条.set)
                滚动条.config(command=实际listbox.yview)
                # 填充数据
                for 英雄 in 默认值:
                    实际listbox.insert(tk.END, 英雄)
                # 布局
                实际listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                滚动条.pack(side=tk.RIGHT, fill=tk.Y)
                # 将容器框架作为控件返回（需要特殊处理）
                容器框架._listbox = 实际listbox  # 保存引用以便后续访问
                控件 = 容器框架  # 将容器框架赋值给控件变量

            控件.grid(row=行, column=1, padx=5, pady=5, sticky=tk.EW)
            # 添加工具提示
            工具提示(控件, 提示文本)

            self.配置输入项[标签] = 控件
            ttk.Label(配置表单, text="*" if 标签 == "机器人标识" else "").grid(row=行, column=2, sticky=tk.W)

        # 按钮框架
        按钮框架 = ttk.Frame(self)
        按钮框架.pack(pady=10, fill=tk.X)

        # 状态显示标签
        self.配置状态标签 = ttk.Label(按钮框架, text="就绪", foreground="#666")
        self.配置状态标签.pack(side=tk.LEFT, padx=50)

        # 按钮容器（右对齐）
        操作按钮容器 = ttk.Frame(按钮框架)
        操作按钮容器.pack(side=tk.LEFT)

        # 动态按钮组
        self.主操作按钮 = ttk.Button(
            操作按钮容器,
            text="新建机器人",
            command=self._处理主操作
        )
        self.主操作按钮.pack(side=tk.LEFT, padx=2)

        self.次要操作按钮 = ttk.Button(
            操作按钮容器,
            text="重置表单",
            command=self._重置表单操作
        )
        self.次要操作按钮.pack(side=tk.LEFT, padx=2)

        # 初始状态
        self._更新按钮状态()

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

        if 配置 := self.数据库.获取机器人设置(self.当前机器人ID):
            self.配置输入项["机器人标识"].delete(0, tk.END)
            self.配置输入项["机器人标识"].insert(0, self.当前机器人ID)

            self.配置输入项["模拟器索引"].delete(0, tk.END)
            self.配置输入项["模拟器索引"].insert(0, str(配置.雷电模拟器索引))

            self.配置输入项["服务器"].set(配置.服务器)

            self.配置输入项["最小资源"].delete(0, tk.END)
            self.配置输入项["最小资源"].insert(0, str(配置.欲进攻的最小资源))

            self.配置输入项["进攻资源边缘靠近比例下限"].delete(0, tk.END)
            self.配置输入项["进攻资源边缘靠近比例下限"].insert(0, str(配置.欲进攻资源建筑靠近地图边缘最小比例))

            self.配置输入项["是否开启刷墙"].set("开启" if 配置.开启刷墙 else "关闭")

            self.配置输入项["刷墙起始金币"].delete(0, tk.END)
            self.配置输入项["刷墙起始金币"].insert(0, str(配置.刷墙起始金币))

            self.配置输入项["刷墙起始圣水"].delete(0, tk.END)
            self.配置输入项["刷墙起始圣水"].insert(0, str(配置.刷墙起始圣水))

            模式 = "先打满主世界再打夜世界"
            if 配置.是否刷主世界 and 配置.是否刷夜世界:
                模式 = "先打满主世界再打夜世界"
            elif 配置.是否刷主世界:
                模式 = "只打主世界"
            elif 配置.是否刷夜世界:
                模式 = "只打夜世界"
            self.配置输入项["辅助运行模式"].set(模式)

            # 加载天鹰火炮配置
            self.配置输入项["是否刷天鹰火炮"].set("开启" if getattr(配置, '是否刷天鹰火炮', False) else "关闭")

            # 加载欲升级的英雄
            欲升级英雄控件容器 = self.配置输入项["欲升级的英雄"]
            # 获取实际的listbox控件
            欲升级英雄控件 = 欲升级英雄控件容器._listbox if hasattr(欲升级英雄控件容器, '_listbox') else 欲升级英雄控件容器
            # 先取消所有选中
            欲升级英雄控件.selection_clear(0, tk.END)

            # 根据配置选择对应的英雄
            for idx, 英雄 in enumerate(欲升级英雄控件.get(0, tk.END)):
                if 英雄 in 配置.欲升级的英雄:
                    欲升级英雄控件.selection_set(idx)

    def 清空表单(self):
        """重置为新建模式"""
        self.当前机器人ID = None
        self.新建机器人()
        self._更新按钮状态()

    def 新建机器人(self):
        """清空表单并设置默认值"""
        for 标签, 控件 in self.配置输入项.items():
            if 标签 == "机器人标识":
                控件.delete(0, tk.END)
                控件.insert(0, "robot_")
            elif 标签 == "模拟器索引":
                控件.delete(0, tk.END)
                控件.insert(0, "0")
            elif 标签 == "服务器":
                控件.current(0)
            elif 标签 == "最小资源":
                控件.delete(0, tk.END)
                控件.insert(0, "200000")

    def _更新按钮状态(self):
        """更新按钮文本和状态标签"""
        if self.当前机器人ID is None:  # 新建模式
            self.主操作按钮.configure(text="创建新机器人")
            self.次要操作按钮.configure(text="清空表单", state=tk.NORMAL)
            self.配置状态标签.configure(text="正在创建新配置", foreground="#666")
        else:  # 编辑模式
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
            self._载入已有配置()  # 放弃修改
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
        配置数据 = {}
        for k, v in self.配置输入项.items():
            # 检查是否是包含listbox的容器框架
            if hasattr(v, '_listbox'):
                实际控件 = v._listbox
                # 获取所有选中项的值
                选中索引 = 实际控件.curselection()
                选中值 = [实际控件.get(i) for i in 选中索引]
                配置数据[k] = 选中值
            elif isinstance(v, tk.Listbox):
                # 获取所有选中项的值
                选中索引 = v.curselection()
                选中值 = [v.get(i) for i in 选中索引]
                配置数据[k] = 选中值
            else:
                配置数据[k] = v.get()

        if not 配置数据["机器人标识"].strip():
            messagebox.showerror("错误", "机器人标识不能为空！")
            return

        try:
            新配置 = 机器人设置(
                雷电模拟器索引=int(配置数据["模拟器索引"]),
                服务器=配置数据["服务器"],
                欲进攻的最小资源=int(配置数据["最小资源"]),
                开启刷墙=True if 配置数据["是否开启刷墙"] == "开启" else False,
                刷墙起始金币=int(配置数据["刷墙起始金币"]),
                刷墙起始圣水=int(配置数据["刷墙起始圣水"]),
                欲进攻资源建筑靠近地图边缘最小比例=float(配置数据["进攻资源边缘靠近比例下限"]),
                是否刷夜世界=True if 配置数据["辅助运行模式"] == "只打夜世界" or 配置数据["辅助运行模式"] == "先打满主世界再打夜世界" else False,
                是否刷主世界=True if 配置数据["辅助运行模式"] == "只打主世界" or 配置数据["辅助运行模式"] == "先打满主世界再打夜世界" else False,
                是否刷天鹰火炮=True if 配置数据.get("是否刷天鹰火炮") == "开启" else False,
                欲升级的英雄=配置数据.get("欲升级的英雄", []),
            )
        except ValueError as e:
            messagebox.showerror("配置错误", f"数值格式错误: {str(e)}")
            return

        # 判断是新建还是更新
        if self.当前机器人ID is None:
            self._创建新机器人(配置数据["机器人标识"], 新配置)
        else:
            self._更新机器人配置(配置数据["机器人标识"], 新配置)
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
