"""
机器人管理面板模块 - 机器人列表、状态显示和控制功能
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional


class 机器人管理面板(ttk.LabelFrame):
    """机器人管理面板"""

    def __init__(self, 父容器, 监控中心, 选择变化回调: Callable[[Optional[str]], None]):
        """
        初始化机器人管理面板
        :param 父容器: 父容器控件
        :param 监控中心: 机器人监控中心实例
        :param 选择变化回调: 机器人选择变化时的回调函数，参数为机器人ID（或None）
        """
        super().__init__(父容器, text="机器人管理")
        self.监控中心 = 监控中心
        self.选择变化回调 = 选择变化回调
        self.当前机器人ID: Optional[str] = None

        self._创建界面()
        self._定时刷新机器人列表()

    def _创建界面(self):
        """创建管理面板界面"""
        # 机器人列表 Treeview
        self.机器人列表框 = ttk.Treeview(self, columns=('status'), show='tree headings', height=8, style="Robot.Treeview")
        self.机器人列表框.column('#0', width=250, anchor=tk.W)
        self.机器人列表框.heading('#0', text='机器人标识', anchor=tk.W)
        self.机器人列表框.column('status', width=80, anchor=tk.CENTER)
        self.机器人列表框.heading('status', text='状态', anchor=tk.CENTER)
        self.机器人列表框.pack(pady=5, fill=tk.BOTH, expand=True)
        self.机器人列表框.bind('<<TreeviewSelect>>', self._更新当前选择)
        self.机器人列表框.bind("<Button-1>", self._处理列表点击)

        # 列表操作按钮
        列表操作面板 = ttk.Frame(self)
        列表操作面板.pack(pady=5, fill=tk.X)
        ttk.Button(列表操作面板, text="刷新列表", command=self.更新机器人列表).pack(side=tk.LEFT, padx=2)
        ttk.Button(列表操作面板, text="删除选中", command=self._删除选中机器人).pack(side=tk.LEFT, padx=2)

        # 状态显示
        self.当前状态面板 = ttk.LabelFrame(self, text="当前状态")
        self.当前状态面板.pack(fill=tk.X, pady=5)
        self.状态标签组 = {
            '标识': ttk.Label(self.当前状态面板, text="标识：未选择"),
            '状态': ttk.Label(self.当前状态面板, text="状态：-"),
            '服务器': ttk.Label(self.当前状态面板, text="服务器：-"),
            '模拟器': ttk.Label(self.当前状态面板, text="模拟器：-"),
            '资源': ttk.Label(self.当前状态面板, text="最小资源：-"),
        }
        for idx, 标签 in enumerate(self.状态标签组.values()):
            标签.grid(row=idx // 2, column=idx % 2, sticky=tk.W, padx=5, pady=2)

        # 控制按钮
        控制按钮框架 = ttk.LabelFrame(self, text="控制当前选中")
        控制按钮框架.pack(fill=tk.X, pady=5)

        ttk.Button(控制按钮框架, text="启动", command=self._启动机器人).pack(side=tk.LEFT, padx=5)
        ttk.Button(控制按钮框架, text="暂停", command=self._暂停机器人).pack(side=tk.LEFT, padx=5)
        ttk.Button(控制按钮框架, text="继续", command=self._继续机器人).pack(side=tk.LEFT, padx=5)
        ttk.Button(控制按钮框架, text="停止", command=self._停止机器人).pack(side=tk.LEFT, padx=5)

    def _定时刷新机器人列表(self):
        """定时刷新机器人列表"""
        self.更新机器人列表()
        self.after(500, self._定时刷新机器人列表)

    def 获取当前机器人(self):
        """返回当前选中的机器人实例"""
        if self.当前机器人ID:
            return self.监控中心.机器人池.get(self.当前机器人ID)
        return None

    def _处理列表点击(self, event):
        """处理列表点击事件以实现取消选择"""
        item = self.机器人列表框.identify_row(event.y)
        if not item:  # 点击空白处
            self.机器人列表框.selection_remove(self.机器人列表框.selection())
            self.当前机器人ID = None
            self.更新状态显示()
            self.选择变化回调(None)

    def _更新当前选择(self, event):
        """处理列表选择变化"""
        选中项 = self.机器人列表框.selection()
        if not 选中项:
            return

        新机器人ID = self.机器人列表框.item(选中项[0], 'text')

        # 只有当机器人改变时才更新
        if 新机器人ID != self.当前机器人ID:
            self.当前机器人ID = 新机器人ID
            self.更新状态显示()
            self.选择变化回调(新机器人ID)

    def 更新状态显示(self):
        """刷新状态标签显示"""
        if robot := self.获取当前机器人():
            self.状态标签组['标识'].config(text=f"标识：{robot.机器人标志}")
            self.状态标签组['状态'].config(text=f"状态：{robot.当前状态}")
            self.状态标签组['服务器'].config(text=f"服务器：{robot.设置.服务器}")
            self.状态标签组['模拟器'].config(text=f"模拟器：{robot.设置.雷电模拟器索引}")
            self.状态标签组['资源'].config(text=f"最小资源：{robot.设置.欲进攻的最小资源}")
        else:
            self.状态标签组['标识'].config(text=f"标识：未选择")
            self.状态标签组['状态'].config(text=f"状态：-")
            self.状态标签组['服务器'].config(text=f"服务器：-")
            self.状态标签组['模拟器'].config(text=f"模拟器：-")
            self.状态标签组['资源'].config(text=f"最小资源：-")

    def 更新机器人列表(self):
        """刷新列表显示"""
        原列表项 = {self.机器人列表框.item(item, 'text'): item
                    for item in self.机器人列表框.get_children()}

        # 同步监控中心的机器人
        for 标识 in self.监控中心.机器人池.keys():
            if 标识 not in 原列表项:
                self.机器人列表框.insert('', tk.END, text=标识, values=('未运行',))

        # 移除不存在的项
        for 标识, item in 原列表项.items():
            if 标识 not in self.监控中心.机器人池:
                self.机器人列表框.delete(item)

        # 更新状态显示
        for item in self.机器人列表框.get_children():
            标识 = self.机器人列表框.item(item, 'text')
            if robot := self.监控中心.机器人池.get(标识):
                self.机器人列表框.set(item, 'status', robot.当前状态)

        # 清除所有选择
        self.机器人列表框.selection_remove(self.机器人列表框.selection())

        # 重新设置选择（如果有当前ID）
        if self.当前机器人ID:
            for item in self.机器人列表框.get_children():
                if self.机器人列表框.item(item, 'text') == self.当前机器人ID:
                    self.机器人列表框.selection_set(item)
                    break

    def _启动机器人(self):
        """启动当前选中的机器人"""
        机器人 = self.获取当前机器人()
        if 机器人:
            try:
                机器人.启动()
                return f"{机器人.机器人标志} 已启动"
            except Exception as e:
                messagebox.showerror("启动失败", str(e))
        return None

    def _暂停机器人(self):
        """暂停当前选中的机器人"""
        机器人 = self.获取当前机器人()
        if 机器人:
            try:
                机器人.暂停()
                return f"{机器人.机器人标志} 已暂停"
            except Exception as e:
                messagebox.showerror("暂停失败", str(e))
        return None

    def _继续机器人(self):
        """继续当前选中的机器人"""
        机器人 = self.获取当前机器人()
        if 机器人:
            try:
                机器人.继续()
                return f"{机器人.机器人标志} 已继续运行"
            except Exception as e:
                messagebox.showerror("继续失败", str(e))
        return None

    def _停止机器人(self):
        """停止当前选中的机器人"""
        机器人 = self.获取当前机器人()
        if 机器人:
            try:
                机器人.停止()
                return f"{机器人.机器人标志} 已停止"
            except Exception as e:
                messagebox.showerror("停止失败", str(e))
        return None

    def _删除选中机器人(self):
        """删除选中的机器人"""
        if not self.当前机器人ID:
            return

        if not messagebox.askyesno("确认删除", f"确定要永久删除 {self.当前机器人ID} 的配置吗？"):
            return

        删除的ID = self.当前机器人ID
        try:
            # 判断机器人是否在机器人池中
            if self.当前机器人ID in self.监控中心.机器人池:
                try:
                    # 停止机器人并移除
                    机器人实例 = self.监控中心.机器人池[self.当前机器人ID]
                    机器人实例.停止()
                    del self.监控中心.机器人池[self.当前机器人ID]
                except Exception as e:
                    messagebox.showwarning("停止失败", f"停止机器人时发生错误：{e}")

            # 清除当前选择并刷新列表
            self.当前机器人ID = None
            self.更新机器人列表()
            self.更新状态显示()

            # 通知主控类删除配置
            self.选择变化回调(None, 删除=删除的ID)

        except Exception as e:
            messagebox.showerror("删除失败", f"删除过程中发生异常：{e}")
