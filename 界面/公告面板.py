"""
公告面板 - 主窗口顶部公告横幅

数据由 工具包.公告管理 的后台线程写入本地缓存，
本面板只在主线程中读取缓存并通过 after 轮询刷新，保证 tkinter 线程安全。
"""
import tkinter as tk
from tkinter import ttk

from 工具包.公告管理 import (
    读取公告缓存,
    读取统计缓存,
    获取缓存最后更新时间,
    取最新公告,
)

标题截断长度 = 50


class 公告面板(ttk.Frame):
    def __init__(self, 父容器):
        super().__init__(父容器)
        self._已显示mtime = 0.0
        self._轮询剩余次数 = 30  # 30 次 × 2 秒 = 启动后最多轮询 1 分钟

        self._从缓存刷新()
        self.after(2000, self._轮询缓存)

    # ---------- 数据刷新 ----------

    def _轮询缓存(self):
        """主线程定时检查缓存文件是否被后台线程更新"""
        self._轮询剩余次数 -= 1
        最新mtime = 获取缓存最后更新时间()
        if 最新mtime > self._已显示mtime:
            self._从缓存刷新()
        if self._轮询剩余次数 > 0:
            self.after(2000, self._轮询缓存)

    def _从缓存刷新(self):
        """读取缓存并重建横幅内容；无数据时保持空 Frame（高度约为0，不可见）"""
        self._已显示mtime = 获取缓存最后更新时间()

        for 控件 in self.winfo_children():
            控件.destroy()

        公告数据 = 读取公告缓存()
        最新公告 = 取最新公告(公告数据)
        统计数据 = 读取统计缓存()

        if 最新公告 is None and 统计数据 is None:
            return

        内容行 = ttk.Frame(self)
        内容行.pack(fill=tk.X, padx=5, pady=3)

        if 最新公告 is not None:
            标题 = str(最新公告.get("标题", ""))
            if len(标题) > 标题截断长度:
                标题 = 标题[:标题截断长度] + "…"
            样式 = "重要公告.TLabel" if 最新公告.get("重要") else "公告.TLabel"
            公告标签 = ttk.Label(
                内容行,
                text=f"📢 {标题}",
                style=样式,
                cursor="hand2"
            )
            公告标签.pack(side=tk.LEFT)
            公告标签.bind("<Button-1>", lambda e: self._打开公告详情窗口(公告数据))

        统计文本 = self._生成统计文本(统计数据)
        if 统计文本:
            ttk.Label(内容行, text=统计文本, style="公告统计.TLabel").pack(side=tk.RIGHT)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(2, 0))

    @staticmethod
    def _生成统计文本(统计数据):
        if not isinstance(统计数据, dict):
            return ""
        累计 = 统计数据.get("累计")
        if not isinstance(累计, dict):
            return ""
        用户数 = 累计.get("近14天独立克隆")
        拉取数 = 累计.get("克隆次数")
        部分 = []
        if 用户数:
            部分.append(f"👥 近14天用户 {用户数}")
        if 拉取数:
            部分.append(f"累计拉取 {拉取数} 次")
        return " · ".join(部分)

    # ---------- 详情弹窗 ----------

    def _打开公告详情窗口(self, 公告数据):
        """弹窗显示全部历史公告，按 id 降序"""
        公告列表 = []
        if isinstance(公告数据, dict) and isinstance(公告数据.get("公告列表"), list):
            公告列表 = [项 for 项 in 公告数据["公告列表"]
                    if isinstance(项, dict) and "标题" in 项]
        公告列表.sort(key=lambda 项: 项.get("id", 0), reverse=True)

        详情窗口 = tk.Toplevel(self)
        详情窗口.title("公告")
        详情窗口.transient(self.winfo_toplevel())
        详情窗口.grab_set()

        宽度, 高度 = 550, 420
        屏幕宽 = 详情窗口.winfo_screenwidth()
        屏幕高 = 详情窗口.winfo_screenheight()
        x = (屏幕宽 - 宽度) // 2
        y = (屏幕高 - 高度) // 2
        详情窗口.geometry(f"{宽度}x{高度}+{x}+{y}")
        详情窗口.resizable(False, False)

        ttk.Label(
            详情窗口,
            text="📢 公告",
            font=("Microsoft YaHei UI", 14, "bold")
        ).pack(anchor=tk.W, padx=20, pady=(20, 10))

        内容框架 = ttk.Frame(详情窗口)
        内容框架.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        文本框 = tk.Text(
            内容框架,
            wrap=tk.WORD,
            font=("Microsoft YaHei UI", 9),
            relief=tk.FLAT,
            bg="#f5f5f5",
            padx=10,
            pady=10
        )
        滚动条 = ttk.Scrollbar(内容框架, orient=tk.VERTICAL, command=文本框.yview)
        文本框.configure(yscrollcommand=滚动条.set)

        滚动条.pack(side=tk.RIGHT, fill=tk.Y)
        文本框.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        文本框.tag_configure("标题", font=("Microsoft YaHei UI", 10, "bold"))
        文本框.tag_configure("重要标题", font=("Microsoft YaHei UI", 10, "bold"),
                          foreground="#cb2431")

        if not 公告列表:
            文本框.insert(tk.END, "暂无公告")
        for 序号, 公告 in enumerate(公告列表):
            前缀 = "【重要】" if 公告.get("重要") else ""
            标题行 = f"{前缀}{公告.get('标题', '')}  ({公告.get('日期', '')})\n"
            标签 = "重要标题" if 公告.get("重要") else "标题"
            文本框.insert(tk.END, 标题行, 标签)
            文本框.insert(tk.END, f"{公告.get('内容', '')}\n")
            if 序号 < len(公告列表) - 1:
                文本框.insert(tk.END, "\n" + "─" * 40 + "\n\n")
        文本框.configure(state=tk.DISABLED)

        ttk.Button(
            详情窗口,
            text="关闭",
            command=详情窗口.destroy,
            width=12
        ).pack(pady=(0, 20))
