import queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
from 主入口 import 机器人监控中心
from 工具包.工具函数 import 打印运行耗时, 工具提示
from 工具包.版本管理 import 获取本地版本号, 异步更新远程最新版本, 是否需要更新
from 数据库.任务数据库 import 机器人设置, 任务数据库
from 线程.自动化机器人 import 自动化机器人
from sv_ttk import set_theme


from 界面.自动启动界面 import 自动启动界面


class 增强型机器人控制界面:
    def __init__(self, master, 监控中心):

        self.master = master
        self.监控中心 = 监控中心
        self.日志队列 = 监控中心.日志队列
        self.master.title("机器人监控控制中心 " + 获取本地版本号())
        self._设置窗口尺寸(1200, 700)

        self.当前机器人ID = None
        self.上一次机器人ID = None
        self.数据库 = 任务数据库()
        self.配置缓存 = {}  # 缓存未保存的修改

        self._创建主框架()
        self._创建左侧控制面板()
        self._创建右侧配置面板()
        self.更新日志显示()
        self._定时刷新机器人列表()
        self._定时刷新日志()
        set_theme("light")
        self._配置现代化样式()
        self._加载保存的配置()  # 启动时自动加载
        self.master.protocol("WM_DELETE_WINDOW", self._窗口关闭处理)
        self._更新按钮状态()

        self.日志缓存时间戳 = {}  # 记录每个机器人的最新日志时间戳
        self.日志缓存内容 = {}  # 可选：记录日志内容缓存（如有必要保留所有日志）

    def _配置现代化样式(self):
        """配置现代化控件样式"""
        style = ttk.Style()

        # 配置圆角按钮
        style.configure("TButton", padding=6, relief="flat",
                        font=("Segoe UI", 10))
        style.map("TButton",
                  relief=[("active", "sunken"), ("!active", "flat")],
                  background=[("active", "#e5e5e5"), ("!active", "white")]
                  )

        # 状态按钮颜色
        style.configure("success.TButton", foreground="white", background="#2ea44f")
        style.map("success.TButton",
                  background=[("active", "#22863a"), ("!active", "#2ea44f")])
        style.configure("danger.TButton", foreground="white", background="#cb2431")
        style.map("danger.TButton",
                  background=[("active", "#9f1c23"), ("!active", "#cb2431")])
        style.configure("primary.TButton", foreground="white", background="#0366d6")
        style.map("primary.TButton",
                  background=[("active", "#0256b5"), ("!active", "#0366d6")])

        # 列表样式
        style.configure("TListbox", font=("Segoe UI", 10), relief="flat")

        # 标签框样式
        style.configure("TLabelframe", font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))

        # 输入控件
        style.configure("TEntry", padding=5, relief="flat")

    def _定时刷新日志(self):
        try:
            日志消息 = self.日志队列.get_nowait()

            当前机器人 = self.获取当前机器人()
            机器人ID = 日志消息.get("机器人ID")
            # print(f"收到日志更新消息发送人为{机器人ID},当前选中的机器人为{当前机器人.机器人标志}")

            if 当前机器人 and 机器人ID == 当前机器人.机器人标志:
                # 记录最近收到的级别，供着色使用
                self._最近日志级别 = 日志消息.get("级别", "正常")
                self._最近日志文本 = 日志消息.get("内容", "")
                self.更新日志显示()
        except queue.Empty:
            pass
        finally:
            # 无论是否异常，都安排下一次调用
            self.master.after(200, self._定时刷新日志)

    def _定时刷新机器人列表(self):
        self.更新机器人列表()
        self.master.after(500, self._定时刷新机器人列表)

    #@打印运行耗时
    def 更新日志显示(self):
        当前机器人 = self.获取当前机器人()

        if 当前机器人 is None:
            模拟日志 = [
                f"[{time.strftime('%H:%M:%S')}] 系统状态正常",
                f"[{time.strftime('%H:%M:%S')}] 欢迎使用脚本，具体使用步骤如下:",
                f"[{time.strftime('%H:%M:%S')}] 1.在模拟器中安装部落冲突并登录你的账号，确保进入主世界。",
                f"[{time.strftime('%H:%M:%S')}] 2.模拟器分辨率设置宽800，高600，dpi160",
                f"[{time.strftime('%H:%M:%S')}] 3.部落冲突中设置配兵,目前支持所有普通兵种,超级兵种支持超级野蛮人以及超级哥布林",
                f"[{time.strftime('%H:%M:%S')}] 4.打开游戏后",
                f"[{time.strftime('%H:%M:%S')}] 5.先在左边选中需要启动的账号,点击'启动'按钮运行脚本",
                f"[{time.strftime('%H:%M:%S')}] 6.或者在右边配置页面新建机器人再启动"
            ]
        else:
            机器人标志 = 当前机器人.机器人标志
            # 获取上次记录时间戳
            上次时间 = self.日志缓存时间戳.get(机器人标志, 0)
            日志列表 = 当前机器人.数据库.查询日志历史(机器人标志, 起始时间=上次时间+ 0.00001)

            if 日志列表:
                # 更新缓存时间戳为最新日志时间
                最新时间 = max(项.记录时间 for 项 in 日志列表)
                self.日志缓存时间戳[机器人标志] = 最新时间

            # 将缓存日志追加起来（如果你希望显示所有日志）
            self.日志缓存内容.setdefault(机器人标志, []).extend(日志列表)

            全部日志 = self.日志缓存内容[机器人标志]
            全部日志.sort(key=lambda 日志: 日志.记录时间)

            模拟日志 = [
                # f"[{time.strftime('%H:%M:%S', time.localtime(项.记录时间))}] {项.机器人标志} {项.日志内容}"
                f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(项.记录时间))}  {项.日志内容}"
                for 项 in 全部日志
            ]

        # 🌟 记录滚动条位置
        当前视图 = self.日志文本框.yview()

        self.日志文本框.configure(state='normal')
        self.日志文本框.delete(1.0, tk.END)

        # 配置文本颜色 tag
        self.日志文本框.tag_configure('正常', foreground="#1f2937")
        self.日志文本框.tag_configure('警告', foreground="#b45309")
        self.日志文本框.tag_configure('错误', foreground="#b91c1c")

        # 将日志按“前缀”粗略推断级别（兼容从DB回放的历史日志）
        def 推断级别(文本: str) -> str:
            if 文本.strip().startswith("[错误]"):
                return "错误"
            if 文本.strip().startswith("[警告]"):
                return "警告"
            return "正常"

        for log in 模拟日志[-500:]:
            级别 = 推断级别(log)
            self.日志文本框.insert(tk.END, log + '\n', 级别)

        # 最近一条实时日志（如果有）以结构化级别覆盖显示尾部颜色
        if hasattr(self, "_最近日志文本"):
            级别 = getattr(self, "_最近日志级别", "正常")
            # 替换末尾一行的 tag（简单做法：重新写入末行）
            self.日志文本框.insert(tk.END, '', '正常')

        self.日志文本框.configure(state='disabled')

        # 🌟 判断用户是否在底部
        if 当前视图[1] > 0.95:
            self.日志文本框.see(tk.END)
        else:
            self.日志文本框.yview_moveto(当前视图[0])

    def 获取当前机器人(self) -> 自动化机器人 | None:
        if self.当前机器人ID:
            return self.监控中心.机器人池.get(self.当前机器人ID)
        return None

    def _加载保存的配置(self):
        """从数据库加载已保存的配置"""

        所有配置 = self.数据库.查询所有机器人设置()

        for 机器人标志, 设置 in 所有配置.items():
            try:
                self.监控中心.创建机器人(
                    机器人标志=机器人标志,
                    初始设置=设置  # 这里设置已经是一个 机器人设置 实例
                )

            except Exception as e:
                messagebox.showerror("配置加载错误", f"加载{机器人标志}失败: {str(e)}")

    def _设置窗口尺寸(self, 宽度, 高度):
        屏幕宽度 = self.master.winfo_screenwidth()
        屏幕高度 = self.master.winfo_screenheight()
        self.master.geometry(f"{宽度}x{高度}+{(屏幕宽度 - 宽度) // 2}+{(屏幕高度 - 高度) // 2}")

    def _创建主框架(self):
        self.主框架 = ttk.Frame(self.master)
        self.主框架.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _创建左侧控制面板(self):
        左侧容器 = ttk.LabelFrame(self.主框架, text="机器人管理")
        左侧容器.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # 机器人列表管理
        self.机器人列表框 = ttk.Treeview(左侧容器, columns=('status'), show='tree headings', height=8)
        self.机器人列表框.column('#0', width=250, anchor=tk.W)
        self.机器人列表框.heading('#0', text='机器人标识', anchor=tk.W)
        self.机器人列表框.column('status', width=80, anchor=tk.CENTER)
        self.机器人列表框.heading('status', text='状态', anchor=tk.CENTER)
        self.机器人列表框.pack(pady=5, fill=tk.BOTH, expand=True)
        self.机器人列表框.bind('<<TreeviewSelect>>', self.更新当前选择)
        self.机器人列表框.bind("<Button-1>", self.处理列表点击)

        # 列表操作按钮
        列表操作面板 = ttk.Frame(左侧容器)
        列表操作面板.pack(pady=5, fill=tk.X)
        ttk.Button(列表操作面板, text="刷新列表", command=self.更新机器人列表).pack(side=tk.LEFT, padx=2)
        ttk.Button(列表操作面板, text="删除选中", command=self.删除选中机器人).pack(side=tk.LEFT, padx=2)

        # 状态显示
        self.当前状态面板 = ttk.LabelFrame(左侧容器, text="当前状态")
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
        # 控制按钮框架 = ttk.Frame(左侧容器)

        控制按钮框架 = ttk.LabelFrame(左侧容器, text="控制当前选中")
        控制按钮框架.pack(fill=tk.X, pady=5)

        ttk.Button(控制按钮框架, text="启动", command=self.启动机器人).pack(side=tk.LEFT, padx=5)
        ttk.Button(控制按钮框架, text="暂停", command=self.暂停机器人).pack(side=tk.LEFT, padx=5)
        ttk.Button(控制按钮框架, text="继续", command=self.继续机器人).pack(side=tk.LEFT, padx=5)
        ttk.Button(控制按钮框架, text="停止", command=self.停止机器人).pack(side=tk.LEFT, padx=5)





    def 启动机器人(self):
        机器人 = self.获取当前机器人()
        if 机器人:
            try:
                机器人.启动()
                self.记录操作日志(f"{机器人.机器人标志} 已启动")
            except Exception as e:
                messagebox.showerror("启动失败", str(e))

    def 暂停机器人(self):
        机器人 = self.获取当前机器人()
        if 机器人:
            try:
                机器人.暂停()
                self.记录操作日志(f"{机器人.机器人标志} 已暂停")
            except Exception as e:
                messagebox.showerror("暂停失败", str(e))

    def 继续机器人(self):
        机器人 = self.获取当前机器人()
        if 机器人:
            try:
                机器人.继续()
                self.记录操作日志(f"{机器人.机器人标志} 已继续运行")
            except Exception as e:
                messagebox.showerror("继续失败", str(e))

    def 停止机器人(self):
        机器人 = self.获取当前机器人()
        if 机器人:
            try:
                机器人.停止()
                self.记录操作日志(f"{机器人.机器人标志} 已停止")
            except Exception as e:
                messagebox.showerror("停止失败", str(e))

    def 选项卡切换回调(self, event):
        notebook = event.widget  # 当前Notebook控件
        当前索引 = notebook.index(notebook.select())  # 获取当前选中索引
        当前标签 = notebook.tab(当前索引, "text")  # 获取当前选项卡标签

        if 当前标签 == "配置管理":
            self.载入选中配置()


    def _创建右侧配置面板(self):
        右侧容器 = ttk.Notebook(self.主框架)
        右侧容器.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        右侧容器.bind("<<NotebookTabChanged>>", self.选项卡切换回调)
        # 日志选项卡
        日志框架 = ttk.Frame(右侧容器)
        self.日志文本框 = scrolledtext.ScrolledText(日志框架, wrap=tk.WORD, font=('Consolas', 11))
        self.日志文本框.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        右侧容器.add(日志框架, text="运行日志")

        # 配置编辑选项卡
        配置框架 = ttk.Frame(右侧容器)
        配置表单 = ttk.Frame(配置框架)
        配置表单.pack(pady=10, padx=10, fill=tk.X)

        英雄列表 = ["野蛮人之王", "弓箭女皇", "亡灵王子", "飞盾战神", "大守护者"]
        配置项定义 = [
            ('机器人标识', 'entry', 'robot_', '用于区分不同机器人的唯一名称'),
            ('模拟器索引', 'spinbox', (0, 99, 1), '对应雷电多开器中的模拟器ID，0表示第一个模拟器,如果不明白请设置为0'),
            ('服务器', 'combo', ['国际服', '国服'], '选择游戏服务器版本,目前只支持国际服'),
            ('最小资源', 'entry', '200000', '搜索村庄对方必须高过的资源总量,超过该值才会触发进攻'),
            ('进攻资源边缘靠近比例下限', 'entry', '0.6', '在被识别到的资源建筑中，它们靠近地图边缘的比例达到此值时，才认为“资源建筑够靠边”，满足进攻条件。范围是0到1，高本建议设为0.6，低本可设为0.0。可以理解为当这个值比较大时辅助只打外围采集器'),
            ('是否开启刷墙', 'combo', ['开启', '关闭'], '是否使用金币或圣水刷墙'),
            ('刷墙起始金币', 'entry', '200000', '金币高于此数值触发刷墙任务'),
            ('刷墙起始圣水', 'entry', '200000', '圣水高于此数值触发刷墙任务,但是请注意,如果是低本,请将此值设置得足够大,以免触发圣水刷墙,但是目前还不能够圣水刷墙造成错误'),
            ('辅助运行模式', 'combo', ['只打主世界', '只打夜世界','先打满主世界再打夜世界'], '打鱼模式,字面意思,打满后辅助会停止运行.'),
            # 新增：欲升级的英雄
            ('欲升级的英雄', 'listbox', 英雄列表, '选择想要升级的英雄，可多选或选择默认')
        ]

        self.配置输入项 = {}
        for 行, (标签, 类型, 默认值, 提示文本) in enumerate(配置项定义):
            ttk.Label(配置表单, text=f"{标签}：").grid(row=行, column=0, padx=5, pady=5, sticky=tk.E)

            if 类型 == 'entry':
                控件 = ttk.Entry(配置表单)
                控件.insert(0, 默认值)
            elif 类型 == 'combo':
                控件 = ttk.Combobox(配置表单, values=默认值,font=("微软雅黑", 10))
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

        按钮框架 = ttk.Frame(配置框架)
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
        右侧容器.add(配置框架, text="配置管理")

        # 自动启动选项卡
        自动启动框架 = 自动启动界面(右侧容器, self.监控中心)
        右侧容器.add(自动启动框架, text="自动启动")

        # 调度器=任务调度器界面(配置框架)
        # 右侧容器.add(调度器, text="运行日志")

    def _更新按钮状态(self):
        """根据当前模式更新按钮状态"""
        # 机器人选择变化时
        # 新建 / 保存操作完成后
        # 表单重置时
        # 界面初始化
        # 这四个都有调用刷新
        if self.当前机器人ID is None:  # 新建模式
            self.主操作按钮.configure(text="创建新机器人")
            self.次要操作按钮.configure(text="清空表单", state=tk.NORMAL)
            self.配置状态标签.configure(text="正在创建新配置")
        else:  # 编辑模式
            self.主操作按钮.configure(text="保存修改")
            self.次要操作按钮.configure(text="放弃修改", state=tk.NORMAL)
            self.配置状态标签.configure(text=f"正在编辑：{self.当前机器人ID}")

    def _处理主操作(self):
        """智能处理保存/创建操作"""
        if self.当前机器人ID:
            self.应用更改()
        else:
            self._执行新建操作()

    def _重置表单操作(self):
        """根据模式执行不同重置操作"""
        if self.当前机器人ID:
            self.载入选中配置()  # 放弃修改
            self.配置状态标签.configure(text="已恢复原始配置", foreground="green")
        else:
            self.新建机器人()
            self.配置状态标签.configure(text="表单已重置", foreground="blue")
        self._更新按钮状态()
        #self.master.after(2000, lambda: self.配置状态标签.configure(text=""))

    def _执行新建操作(self):
        # 执行实际的创建逻辑
        try:
            self.应用更改()
            self._更新按钮状态()
            self.配置状态标签.configure(text="创建成功！", foreground="darkgreen")
        except Exception as e:
            self.配置状态标签.configure(text=f"创建失败：{str(e)}", foreground="red")
        finally:
            self.master.after(2000, self._更新按钮状态)

    def 新建机器人(self):
        """清空表单准备新建"""
        self.当前机器人ID = None
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

    def 应用更改(self):
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
                是否刷主世界=True if 配置数据["辅助运行模式"] == "只打主世界" or 配置数据[
                    "辅助运行模式"] == "先打满主世界再打夜世界" else False,
                欲升级的英雄=配置数据.get("欲升级的英雄", []),  # 新加的字段

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

    def _创建新机器人(self, 标识, 配置):
        if 标识 in self.监控中心.机器人池:
            messagebox.showerror("错误", "该标识已存在！")
            return

        try:
            self.监控中心.创建机器人(机器人标志=标识, 初始设置=配置)
            self.数据库.保存机器人设置(标识, 配置)
            self.更新机器人列表()
            self.记录操作日志(f"已创建并保存新配置：{标识}")
        except Exception as e:
            messagebox.showerror("创建失败", str(e))

    def 记录操作日志(self, 内容):
        self.日志文本框.configure(state='normal')
        self.日志文本框.insert(tk.END, f"[操作] {内容}\n")
        self.日志文本框.configure(state='disabled')
        self.日志文本框.see(tk.END)

    def _更新机器人配置(self, 新标识, 新配置):
        原标识 = self.当前机器人ID
        if 新标识 != 原标识 and 新标识 in self.监控中心.机器人池:
            messagebox.showerror("错误", "目标标识已存在！")
            return

        try:
            # 先停止原有机器人
            if robot := self.监控中心.机器人池.get(原标识):
                robot.停止()

            # 更新配置并保存
            # self.监控中心.更新机器人配置(原标识, 新标识, 新配置)
            if 原标识 is not None:
                self.数据库.保存机器人设置(原标识, 新配置)
            self.当前机器人ID = 新标识
            self.更新机器人列表()
            self.记录操作日志(f"已更新配置：{原标识} → {新标识}")
        except Exception as e:
            messagebox.showerror("更新失败", str(e))

    def 撤销更改(self):
        """恢复当前选择的配置"""
        if self.当前机器人ID:
            self.载入选中配置()

    def 删除选中机器人(self):
        if not self.当前机器人ID:
            return

        if not messagebox.askyesno("确认删除", f"确定要永久删除 {self.当前机器人ID} 的配置吗？"):
            return

        try:
            # 判断机器人是否在机器人池中
            if self.当前机器人ID in self.监控中心.机器人池:
                try:
                    # 停止机器人并移除
                    机器人实例 = self.监控中心.机器人池[self.当前机器人ID]
                    机器人实例.停止()
                    del self.监控中心.机器人池[self.当前机器人ID]
                    self.记录操作日志(f"{self.当前机器人ID}：机器人已停止并从池中移除")
                except Exception as e:
                    messagebox.showwarning("停止失败", f"停止机器人时发生错误：{e}")

            # 删除数据库配置
            self.数据库.删除机器人设置(self.当前机器人ID)
            self.记录操作日志(f"{self.当前机器人ID}：配置已删除")

            # 清除当前选择并刷新列表
            self.当前机器人ID = None
            self.更新机器人列表()

        except Exception as e:
            messagebox.showerror("删除失败", f"删除过程中发生异常：{e}")

    # def 更新当前选择(self, event):
    #     选中项 = self.机器人列表框.selection()
    #     # 防止重复触发：记录上一次选中的项，只有变化时才更新
    #     if hasattr(self, '上次选中项') and self.上次选中项 == 选中项:
    #         return  # 和上次一样，不处理
    #
    #     self.上次选中项 = 选中项
    #
    #     if 选中项:
    #         self.当前机器人ID = self.机器人列表框.item(选中项[0], 'text')
    #         self._更新按钮状态()
    #         self.更新日志显示()
    #         选中项 = self.机器人列表框.selection()
    #         if 选中项:
    #             新机器人ID = self.机器人列表框.item(选中项[0], 'text')
    #             if 新机器人ID != self.上一次机器人ID:
    #                 self.当前机器人ID = 新机器人ID
    #                 self.载入选中配置()
    #                 self.更新状态显示()
    #                 self.上一次机器人ID = 新机器人ID

    def 处理列表点击(self, event):
        """处理列表点击事件以实现取消选择"""
        item = self.机器人列表框.identify_row(event.y)
        if not item:  # 点击空白处
            self.机器人列表框.selection_remove(self.机器人列表框.selection())
            self.当前机器人ID = None
            self.更新日志显示()
            self._更新按钮状态()
            self.更新状态显示()
            self._重置表单操作()

    def 更新当前选择(self, event):
        选中项 = self.机器人列表框.selection()
        if not 选中项:
            return

        新机器人ID = self.机器人列表框.item(选中项[0], 'text')

        # 只有当机器人改变时才更新日志
        if 新机器人ID != self.当前机器人ID:
            self.当前机器人ID = 新机器人ID
            self.载入选中配置()
            self.更新状态显示()
            self.更新日志显示()  # 只在切换时刷新日志
            # self.载入选中配置()
            #
            # self.更新状态显示()

    def 载入选中配置(self):
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

            self.配置输入项["是否开启刷墙"].set("开启" if 配置.开启刷墙 == True else "关闭")

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

            # ---------- 新增：加载欲升级的英雄 ----------
            欲升级英雄控件容器 = self.配置输入项["欲升级的英雄"]
            # 获取实际的listbox控件
            欲升级英雄控件 = 欲升级英雄控件容器._listbox if hasattr(欲升级英雄控件容器, '_listbox') else 欲升级英雄控件容器
            # 先取消所有选中
            欲升级英雄控件.selection_clear(0, tk.END)

            # 根据配置选择对应的英雄
            for idx, 英雄 in enumerate(欲升级英雄控件.get(0, tk.END)):

                if 英雄 in 配置.欲升级的英雄:
                    欲升级英雄控件.selection_set(idx)
            #欲升级英雄控件.update()

            self._更新按钮状态()

    def 更新状态显示(self):
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
        当前选择 = self.机器人列表框.selection()
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

        # 恢复选择
        if self.当前机器人ID and self.当前机器人ID in self.监控中心.机器人池:
            for item in self.机器人列表框.get_children():
                if self.机器人列表框.item(item, 'text') == self.当前机器人ID:
                    self.机器人列表框.selection_set(item)
                    break

        # 清除无效选择
        # if self.当前机器人ID and self.当前机器人ID not in self.监控中心.机器人池:
        #     self.当前机器人ID = None

        # 清除所有选择
        self.机器人列表框.selection_remove(self.机器人列表框.selection())

        # 重新设置选择（如果有当前ID）
        if self.当前机器人ID:
            for item in self.机器人列表框.get_children():
                if self.机器人列表框.item(item, 'text') == self.当前机器人ID:
                    self.机器人列表框.selection_set(item)
                    break

    def _窗口关闭处理(self):
        # 遍历所有机器人，停止它们
        for 机器人 in self.监控中心.机器人池.values():
            try:
                机器人.停止()
            except Exception as e:
                print(f"停止机器人 {机器人.机器人标志} 时出错: {e}")

        self.master.destroy()


if __name__ == "__main__":
    print("当前版本号：", 获取本地版本号())
    异步更新远程最新版本()
    日志队列 = queue.Queue()
    监控中心 = 机器人监控中心(日志队列)
    root = tk.Tk()
    界面 = 增强型机器人控制界面(root, 监控中心)
    是否需要更新()
    root.mainloop()
