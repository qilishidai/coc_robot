import queue
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from 主入口 import 机器人监控中心
from 工具包.版本管理 import 获取本地版本号, 异步更新远程最新版本, 检查更新
from 工具包.公告管理 import 异步刷新公告与统计
from 数据库.任务数据库 import 机器人设置, 任务数据库
from sv_ttk import set_theme

from 界面.自动启动界面 import 自动启动界面
from 界面.用户协议 import 显示用户协议窗口, 显示协议查看窗口
from 界面.样式配置 import 配置现代化样式
from 界面.日志面板 import 日志面板
from 界面.机器人管理面板 import 机器人管理面板
from 界面.配置管理面板 import 配置管理面板
from 界面.公告面板 import 公告面板


def 显示更新提示窗口(父窗口, 本地版本, 远程版本, 更新内容):
    """显示更新提示窗口，包含更新内容"""
    更新窗口 = tk.Toplevel(父窗口)
    更新窗口.title("发现新版本")
    更新窗口.transient(父窗口)
    更新窗口.grab_set()

    # 窗口尺寸和居中
    宽度, 高度 = 500, 400
    屏幕宽 = 更新窗口.winfo_screenwidth()
    屏幕高 = 更新窗口.winfo_screenheight()
    x = (屏幕宽 - 宽度) // 2
    y = (屏幕高 - 高度) // 2
    更新窗口.geometry(f"{宽度}x{高度}+{x}+{y}")
    更新窗口.resizable(False, False)

    # 标题
    标题框架 = ttk.Frame(更新窗口)
    标题框架.pack(fill=tk.X, padx=20, pady=(20, 10))

    ttk.Label(
        标题框架,
        text="🎉 发现新版本",
        font=("Microsoft YaHei UI", 14, "bold")
    ).pack(anchor=tk.W)

    ttk.Label(
        标题框架,
        text=f"当前版本: {本地版本}  →  最新版本: {远程版本}",
        font=("Microsoft YaHei UI", 10)
    ).pack(anchor=tk.W, pady=(5, 0))

    # 分隔线
    ttk.Separator(更新窗口, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=10)

    # 更新内容标签
    ttk.Label(
        更新窗口,
        text="更新内容:",
        font=("Microsoft YaHei UI", 10, "bold")
    ).pack(anchor=tk.W, padx=20)

    # 更新内容文本框
    内容框架 = ttk.Frame(更新窗口)
    内容框架.pack(fill=tk.BOTH, expand=True, padx=20, pady=(5, 10))

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

    # 插入更新内容
    显示内容 = 更新内容 if 更新内容.strip() else "暂无更新说明"
    文本框.insert(tk.END, 显示内容)
    文本框.configure(state=tk.DISABLED)

    # 按钮区域
    按钮框架 = ttk.Frame(更新窗口)
    按钮框架.pack(fill=tk.X, padx=20, pady=(0, 20))

    def 打开下载页面():
        import webbrowser
        webbrowser.open("https://github.com/qilishidai/coc_robot/releases/latest")

    ttk.Button(
        按钮框架,
        text="前往下载",
        command=打开下载页面,
        width=12
    ).pack(side=tk.LEFT)

    ttk.Button(
        按钮框架,
        text="稍后再说",
        command=更新窗口.destroy,
        width=12
    ).pack(side=tk.RIGHT)


class 增强型机器人控制界面:
    def __init__(self, master, 监控中心):
        """初始化主控界面"""
        self.master = master
        self.监控中心 = 监控中心
        self.日志队列 = 监控中心.日志队列
        self.数据库 = 任务数据库()

        # 配置样式
        set_theme("light")
        配置现代化样式()

        # 设置窗口
        master.title("机器人监控控制中心 " + 获取本地版本号())
        master.protocol("WM_DELETE_WINDOW", self._窗口关闭处理)
        self._设置窗口尺寸(1200, 700)

        # 创建菜单
        self._创建菜单栏()

        # 创建子面板
        self._创建面板()

        # 加载保存的配置
        self._加载保存的配置()

    def _创建面板(self):
        """实例化并组装各子面板"""
        主框架 = ttk.Frame(self.master)
        主框架.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部：公告横幅（无数据时高度为0，不可见）
        self.公告横幅 = 公告面板(主框架)
        self.公告横幅.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        # 左侧：机器人管理面板
        self.机器人管理 = 机器人管理面板(
            父容器=主框架,
            监控中心=self.监控中心,
            选择变化回调=self._处理机器人选择变化
        )
        self.机器人管理.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # 右侧：Notebook
        右侧选项卡 = ttk.Notebook(主框架)
        右侧选项卡.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        右侧选项卡.bind("<<NotebookTabChanged>>", self._选项卡切换回调)

        # Tab 1: 日志面板
        self.日志面板 = 日志面板(
            父容器=右侧选项卡,
            日志队列=self.日志队列,
            获取当前机器人回调=lambda: self.机器人管理.获取当前机器人()
        )
        右侧选项卡.add(self.日志面板, text="运行日志")

        # Tab 2: 配置管理面板
        self.配置面板 = 配置管理面板(
            父容器=右侧选项卡,
            监控中心=self.监控中心,
            数据库=self.数据库,
            操作日志回调=lambda 内容: self.日志面板.记录操作日志(内容),
            列表刷新回调=lambda: self.机器人管理.更新机器人列表()
        )
        右侧选项卡.add(self.配置面板, text="配置管理")

        # Tab 3: 自动启动
        自动启动 = 自动启动界面(右侧选项卡, self.监控中心)
        右侧选项卡.add(自动启动, text="自动启动")

        # 配置网格权重
        主框架.rowconfigure(0, weight=1)
        主框架.columnconfigure(0, weight=1)
        主框架.columnconfigure(1, weight=3)

    # 中介者：协调面板间通信
    def _处理机器人选择变化(self, 机器人ID, 删除=None):
        """
        机器人选择变化时的回调
        :param 机器人ID: 新选中的机器人ID（或None）
        :param 删除: 如果提供，表示删除了指定ID的机器人
        """
        if 删除:
            # 删除数据库配置
            try:
                self.数据库.删除机器人设置(删除)
                self.日志面板.记录操作日志(f"{删除}：配置已删除")
            except Exception as e:
                messagebox.showerror("删除失败", f"删除数据库配置时发生异常：{e}")
            # 清空配置面板
            self.配置面板.清空表单()
        else:
            # 正常选择变化
            self.配置面板.载入配置(机器人ID)
            self.日志面板.通知机器人切换()
            self.机器人管理.更新状态显示()

    def _选项卡切换回调(self, event):
        """切换到配置管理时刷新配置"""
        notebook = event.widget
        当前索引 = notebook.index(notebook.select())
        当前标签 = notebook.tab(当前索引, "text")

        if 当前标签 == "配置管理":
            当前ID = self.机器人管理.当前机器人ID
            self.配置面板.载入配置(当前ID)

    # 保留的工具方法
    def _设置窗口尺寸(self, 宽度, 高度):
        """居中显示窗口"""
        屏幕宽度 = self.master.winfo_screenwidth()
        屏幕高度 = self.master.winfo_screenheight()
        x = (屏幕宽度 - 宽度) // 2
        y = (屏幕高度 - 高度) // 2
        self.master.geometry(f"{宽度}x{高度}+{x}+{y}")

    def _加载保存的配置(self):
        """启动时加载所有机器人配置"""
        所有配置 = self.数据库.查询所有机器人设置()
        for 机器人标志, 设置 in 所有配置.items():
            try:
                self.监控中心.创建机器人(
                    机器人标志=机器人标志,
                    初始设置=设置
                )
            except Exception as e:
                messagebox.showerror("配置加载错误", f"加载{机器人标志}失败: {str(e)}")

    # 菜单栏
    def _创建菜单栏(self):
        """创建菜单栏，命令委托给子模块"""
        菜单栏 = tk.Menu(self.master)
        self.master.config(menu=菜单栏)

        设置菜单 = tk.Menu(菜单栏, tearoff=0)
        菜单栏.add_cascade(label="设置", menu=设置菜单)
        设置菜单.add_command(label="撤销协议同意", command=self._撤销协议同意)
        设置菜单.add_separator()
        设置菜单.add_command(
            label="查看用户协议",
            command=lambda: 显示协议查看窗口(self.master)
        )

        帮助菜单 = tk.Menu(菜单栏, tearoff=0)
        菜单栏.add_cascade(label="帮助", menu=帮助菜单)
        帮助菜单.add_command(label="关于", command=self._显示关于)

    def _撤销协议同意(self):
        """撤销协议同意，保留在主控类（需要访问数据库和窗口关闭）"""
        确认 = messagebox.askyesno(
            "撤销协议同意",
            "撤销协议同意后，程序将立即退出。\n下次启动时需要重新阅读并同意用户协议。\n\n确定要撤销吗？"
        )
        if 确认:
            self.数据库.撤销协议同意()
            messagebox.showinfo("已撤销", "协议同意已撤销，程序即将退出。")
            self._窗口关闭处理()

    def _显示关于(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于",
            f"版本: {获取本地版本号()}\n\n"
            "这是一个技术学习演示项目，仅供研究和学习使用。\n\n"
            "⚠️ 警告：请勿用于真实游戏环境。\n"
            "使用本软件操作真实账号可能导致账号被封禁，\n"
            "并可能违反相关法律法规。\n\n"
            "GitHub: https://github.com/qilishidai/coc_robot"
        )

    def _窗口关闭处理(self):
        """关闭窗口时停止所有机器人"""
        for 机器人 in self.监控中心.机器人池.values():
            try:
                机器人.停止()
            except:
                pass
        self.master.destroy()


if __name__ == "__main__":
    # 检查协议状态
    数据库 = 任务数据库()
    if not 数据库.检查协议是否已同意():
        if not 显示用户协议窗口():
            sys.exit(0)
        数据库.保存协议同意记录()

    # 启动正常流程
    获取本地版本号()
    异步更新远程最新版本()
    异步刷新公告与统计()
    日志队列 = queue.Queue()
    监控中心 = 机器人监控中心(日志队列)
    root = tk.Tk()
    界面 = 增强型机器人控制界面(root, 监控中心)

    # 检查更新并显示更新内容
    需要更新, 本地版本, 远程版本, 更新内容, _ = 检查更新()
    if 需要更新:
        root.after(500, lambda: 显示更新提示窗口(root, 本地版本, 远程版本, 更新内容))

    root.mainloop()
