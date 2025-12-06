import subprocess
import threading
import time
import winreg
import win32gui


class 雷电模拟器操作类:
    """
    雷电模拟器类，用于控制和管理雷电模拟器实例。

    属性:
    雷电模拟器安装目录 (str): 雷电模拟器的安装目录。
    雷电模拟器索引 (int): 要控制的模拟器实例索引。
    """
    #这三个类变量,所有实例获取的都是一样的.存在于类定义中，所有实例共享
    _命令行锁=threading.RLock()
    _实例字典 = {}
    _初始化锁 = threading.Lock()

    def __new__(cls, 模拟器索引=0):
        with cls._初始化锁:
            if 模拟器索引 not in cls._实例字典:
                cls._实例字典[模拟器索引] = super().__new__(cls)
            return cls._实例字典[模拟器索引]

    def __init__(self, 模拟器索引=0):
        """
        初始化雷电模拟器实例。

        参数:
        模拟器索引 (int): 要控制的模拟器实例索引。默认值为0。
        """

        if hasattr(self, '_已初始化'):
            return

        key = winreg.HKEY_CURRENT_USER
        sub_key = r"Software\leidian\LDPlayer9"
        value_name = "InstallDir"

        # 获取注册表值得到雷电模拟器安装目录
        self.雷电模拟器安装目录 = self.get_registry_value(key, sub_key, value_name)
        self.雷电模拟器索引 = 模拟器索引

        self.模拟器exe路径 = self.雷电模拟器安装目录 + "dnplayer.exe"

        self.已初始化=True


    def 设置模拟器DPI兼容性(self, 模式="DPIUNAWARE"):
        """
            设置模拟器为 DPI_UNAWARE 模式后：
            1. 模拟器内部仍按 100% DPI 渲染，解决非100%系统缩放导致的截图偏差。
            2. 系统只是放大显示窗口，视觉上像是100%缩放。
            3. OpenGL 获取到的仍是模拟器内部的原始未缩放图像，因此截图准确。
        模式:
            "DPIUNAWARE"               → 系统放大（变大但模糊）
            "HIGHDPIAWARE"             → 高 DPI 自适应（清晰）
            "DPIUNAWARE GDISCALED"     → GDI 强制放大（更大）
        """
        键值 = "~ " + 模式

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers",
                0,
                winreg.KEY_SET_VALUE
            )

            winreg.SetValueEx(key, self.模拟器exe路径, 0, winreg.REG_SZ, 键值)
            winreg.CloseKey(key)

            print(f"✔ DPI 设置成功：{模式}")
        except Exception as e:
            print("❌ DPI 设置失败：", e)

    # -----------------------
    # 新增：取消 DPI 兼容性
    # -----------------------
    def 取消模拟器DPI兼容性(self):
        """删除注册表对应项，使模拟器恢复默认 DPI 行为"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers",
                0,
                winreg.KEY_SET_VALUE
            )

            winreg.DeleteValue(key, self.模拟器exe路径)
            winreg.CloseKey(key)
            print("✔ 已取消 DPI 兼容性设置（恢复默认）")

        except FileNotFoundError:
            print("（提示）当前无 DPI 设置，无需取消")
        except Exception as e:
            print("❌ 取消 DPI 设置失败：", e)


    @staticmethod
    def get_registry_value(key, sub_key, value_name):
        """
        从注册表中获取指定的值。

        参数:
        key (winreg.HKEY_*): 注册表项根。
        sub_key (str): 注册表子项路径。
        value_name (str): 注册表值的名称。

        返回值:
        str: 注册表值的内容，如果注册表路径不存在或发生错误，返回None。
        """
        try:
            reg_key = winreg.OpenKey(key, sub_key)
            value, value_type = winreg.QueryValueEx(reg_key, value_name)
            winreg.CloseKey(reg_key)
            return value
        except FileNotFoundError:
            raise RuntimeError("指定的注册表路径不存在,雷电模拟器未正确安装")
        except Exception as e:
            raise RuntimeError(f"注册表访问失败: {str(e)}")



    @staticmethod
    def 将雷电模拟器命令行返回信息解析为字典(text):
        """
        将雷电模拟器命令行返回的文本解析为字典。

        参数:
        text (str): 包含文本内容的字符串，每行代表一个条目，条目之间使用换行符分隔。
                    每个条目应包含逗号分隔的值，分别为索引、标题、顶层窗口句柄、绑定窗口句柄、
                    是否进入Android、进程PID、VBox进程PID、宽度、高度、DPI。

        返回值:
        dict: 包含解析后内容的字典。字典的键为索引，值为包含条目内容的字典。
              条目字典包含以下键值对：
                  - "标题"：标题字符串
                  - "顶层窗口句柄"：顶层窗口句柄整数
                  - "绑定窗口句柄"：绑定窗口句柄整数
                  - "是否进入Android"：是否进入Android布尔值
                  - "进程PID"：进程PID整数
                  - "VBox进程PID"：VBox进程PID整数
                  - "宽度"：宽度整数
                  - "高度"：高度整数
                  - "DPI"：DPI整数
        """

        result = {}
        lines = text.strip().split('\n')
        for line in lines:
            parts = line.split(',')
            index = int(parts[0])
            title = parts[1]
            top_window_handle = int(parts[2])
            bound_window_handle = int(parts[3])
            enter_android = bool(int(parts[4]))
            process_pid = int(parts[5])
            vbox_process_pid = int(parts[6])
            width = int(parts[7])
            height = int(parts[8])
            dpi = int(parts[9])

            result[index] = {
                "标题": title,
                "顶层窗口句柄": top_window_handle,
                "绑定窗口句柄": bound_window_handle,
                "是否进入Android": enter_android,
                "进程PID": process_pid,
                "VBox进程PID": vbox_process_pid,
                "宽度": width,
                "高度": height,
                "DPI": dpi
            }

        return result

    def 重启模拟器(self):
        with self._命令行锁:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            模拟器状态 = subprocess.run(
                [self.雷电模拟器安装目录 + "ldconsole.exe", "action","--index",str(self.雷电模拟器索引),"--key","call.reboot","--value","nulll"],
                encoding='gbk',
                stdout=subprocess.PIPE,
                startupinfo=startupinfo
            )
            return 模拟器状态.stdout

    def 修改分辨率(self, 宽度=800, 高度=600, dpi=160):
        """
        修改当前模拟器实例的分辨率设置。
        注意：该修改在模拟器未重启前不会生效。

        参数:
        宽度 (int): 分辨率宽度。
        高度 (int): 分辨率高度。
        dpi (int): 模拟器DPI。
        """
        with self._命令行锁:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            分辨率参数 = f"{宽度},{高度},{dpi}"
            subprocess.run(
                [self.雷电模拟器安装目录 + "ldconsole.exe", "modify", "--index", str(self.雷电模拟器索引),
                 "--resolution", 分辨率参数],
                shell=False,
                startupinfo=startupinfo
            )

    def 取模拟器所有状态(self):
        """
        获取所有模拟器实例的状态。

        返回值:
        dict: 当前模拟器实例的状态信息字典，包含以下键值对：
              - "标题"：标题字符串
              - "顶层窗口句柄"：顶层窗口句柄整数
              - "绑定窗口句柄"：绑定窗口句柄整数
              - "是否进入Android"：是否进入Android布尔值
              - "进程PID"：进程PID整数
              - "VBox进程PID"：VBox进程PID整数
              - "宽度"：宽度整数
              - "高度"：高度整数
              - "DPI"：DPI整数
        """
        with self._命令行锁:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            模拟器状态 = subprocess.run(
                [self.雷电模拟器安装目录 + "ldconsole.exe", "list2"],
                encoding='gbk',
                stdout=subprocess.PIPE,
                startupinfo=startupinfo
            )
            雷电模拟器运行信息 = self.将雷电模拟器命令行返回信息解析为字典(模拟器状态.stdout)
            return 雷电模拟器运行信息[self.雷电模拟器索引]
    def 是否进入安卓(self):
        return self.取模拟器所有状态()["是否进入Android"]

    def 是否已启动(self):
        """
        检查当前模拟器实例是否启动。

        返回值:
        bool: 如果模拟器进程PID不为-1，则返回True，否则返回False。
        """
        return True if self.取模拟器所有状态()["进程PID"] != -1 else False

    def 取模拟器名称(self):
        """
        获取当前模拟器实例的的标题名称。

        返回值:
        str: 当前模拟器实例的的标题名称。
        """
        return self.取模拟器所有状态()["标题"]

    def 取顶层窗口句柄(self):
        """
        获取当前模拟器实例的顶层窗口句柄。

        返回值:
        int: 顶层窗口句柄。
        """
        return self.取模拟器所有状态()["顶层窗口句柄"]

    def 取绑定窗口句柄(self):
        """
        获取当前模拟器实例的绑定窗口句柄。

        返回值:
        int: 绑定窗口句柄。
        """
        return self.取模拟器所有状态()["绑定窗口句柄"]

    def 取绑定窗口句柄的下级窗口句柄(self):
        父窗口句柄 = self.取模拟器所有状态()["绑定窗口句柄"]
        子窗口列表 = []

        def 枚举子窗口回调(hwnd, param):
            子窗口列表.append(hwnd)
            return True

        win32gui.EnumChildWindows(父窗口句柄, 枚举子窗口回调, None)

        if 子窗口列表:
            # print(子窗口列表[0])
            return int(子窗口列表[0])
        else:
            return None

    def 启动模拟器并打开应用(self, 包名):
        """
        启动当前模拟器实例并打开指定的应用。

        参数:
        包名 (str): 要打开的应用的包名。
        """
        with self._命令行锁:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(
                [self.雷电模拟器安装目录 + "ldconsole.exe", "launchex", "--index", str(self.雷电模拟器索引), "--packagename", 包名],
                shell=False,
                startupinfo=startupinfo
            )

    def 等待安卓系统完全启动(self):
        """
        阻塞等待模拟器中 Android 系统完全启动完成。

        本方法使用雷电模拟器提供的 ldconsole 工具执行 ADB 命令，轮询读取 Android 属性 `sys.boot_completed`。
        当该属性返回值为 '1' 时表示系统启动完成。为了确保系统完全加载桌面，额外等待 5 秒。

        注意：
            - 该方法会阻塞线程直到模拟器启动完成，建议配合线程或设置调用超时。
            - 调用时需确保模拟器已启动。

        异常：
            - 若 ldconsole.exe 路径错误或未正确启动模拟器，可能引发 subprocess 错误。

        示例：
            模拟器 = 雷电模拟器操作类(0)
            模拟器.启动模拟器()
            模拟器.等待安卓系统完全启动()
        """
        adb命令 = [
            self.雷电模拟器安装目录 + "ldconsole.exe",
            "adb",
            "--index", str(self.雷电模拟器索引),
            "--command", "shell getprop sys.boot_completed"
        ]

        while True:
            with self._命令行锁:
                结果 = subprocess.run(adb命令, stdout=subprocess.PIPE, encoding='gbk')
            if 结果.stdout.strip() == '1':
                print("adb返回安装系统已经启动")
                break
            time.sleep(1)

        # 等完全加载好桌面，比如再等5秒
        time.sleep(10)

    def 关闭雷电模拟器(self):
        with self._命令行锁:
            关闭命令 = [self.雷电模拟器安装目录 + "ldconsole.exe", "quit", "--index", str(self.雷电模拟器索引)]
            subprocess.run(关闭命令, encoding='gbk')

    def 打开应用(self, 包名):
        with self._命令行锁:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.run(
                [self.雷电模拟器安装目录 + "ldconsole.exe", "runapp", "--index", str(self.雷电模拟器索引), "--packagename", 包名],
                shell=False,
                startupinfo=startupinfo
            )

    def 关闭模拟器中的应用(self, 包名):
        """
        关闭当前模拟器实例中的指定应用。

        参数:
        包名 (str): 要关闭的应用的包名。
        """
        with self._命令行锁:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.run(
                [self.雷电模拟器安装目录 + "ldconsole.exe", "killapp", "--index", str(self.雷电模拟器索引), "--packagename", 包名],
                shell=False,
                startupinfo=startupinfo
            )
            time.sleep(1)

if __name__ == '__main__':
    # 不同索引返回不同实例
    模拟器1 = 雷电模拟器操作类(0)
    模拟器1.重启模拟器()