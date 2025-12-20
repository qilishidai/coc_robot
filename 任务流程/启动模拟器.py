import time

from 任务流程.基础任务框架 import 基础任务, 任务上下文

class 模拟器等待超时错误(Exception):
    pass


class 启动模拟器任务(基础任务):
    """启动模拟器并打开游戏"""
    @staticmethod
    def 获取窗口DPI(hwnd):
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.GetDpiForWindow.restype = ctypes.c_uint
        user32.GetDpiForWindow.argtypes = [wintypes.HWND]

        dpi = user32.GetDpiForWindow(hwnd)
        return dpi

    def 执行(self, 上下文: '任务上下文') -> bool:
        try:
            模拟器索引 = 上下文.数据库.获取机器人设置(上下文.机器人标志).雷电模拟器索引
            包名 = 上下文.数据库.获取机器人设置(上下文.机器人标志).部落冲突包名

            模拟器 = 上下文.雷电模拟器

            if 模拟器.是否已启动():
                上下文.置脚本状态("模拟器已启动，直接打开游戏,等待游戏启动")
                模拟器.打开应用(包名)
                #上下文.脚本延时(1000)#等待游戏启动
            else:
                上下文.置脚本状态("模拟器未启动，正在启动模拟器")
                模拟器.启动模拟器并打开应用(包名)

                # 等待模拟器启动
                开始时间 = time.time()
                最大等待时间 = 60*3  # 秒，可自行调整

                while not 模拟器.是否已启动():
                    if time.time() - 开始时间 > 最大等待时间:
                        raise 模拟器等待超时错误("等待模拟器启动超时")
                    上下文.置脚本状态("等待模拟器启动中…")
                    上下文.脚本延时(500)


                上下文.置脚本状态("模拟器启动完毕")

                # 等待进入安卓系统
                开始时间 = time.time()
                最大等待时间 = 60*3  # 秒，可自行调整

                while not 模拟器.是否进入安卓():
                    if time.time() - 开始时间 > 最大等待时间:
                        raise 模拟器等待超时错误("等待进入安卓系统超时")
                    上下文.置脚本状态("等待进入安卓系统中…")
                    上下文.脚本延时(500)

                #上下文.雷电模拟器.等待安卓系统完全启动()
                上下文.置脚本状态("等待安卓系统完全启动")


                # 上下文.雷电模拟器.等待安卓系统完全启动()
                上下文.脚本延时(3*1000)
                上下文.置脚本状态("等待完毕,执行后续操作")

            # 检查窗口 DPI 是否为 100%
            窗口句柄 = 模拟器.取绑定窗口句柄()

            当前DPI = self.获取窗口DPI(窗口句柄)

            if 当前DPI != 96:
                缩放百分比 = round(当前DPI / 96 * 100)
                上下文.置脚本状态(f"模拟器窗口缩放约为 {缩放百分比}%，不是100%")

                # 自动设置 DPI_UNAWARE
                上下文.置脚本状态("正在设置模拟器 DPI_UNAWARE 模式…")
                模拟器.设置模拟器DPI兼容性()  # <- 调用类方法

                模拟器.关闭雷电模拟器()

                # 提示重启或直接抛异常让外层处理
                raise RuntimeError(f"模拟器窗口缩放不是100%，已设置 DPI_UNAWARE，模拟器将自动重启生效")
            return True

        except Exception as e:
            self.异常处理(上下文, e)
            上下文.发送重启请求(str(e))
            return False

    def 异常处理(self, 上下文: '任务上下文', 异常: Exception):
        上下文.置脚本状态(f"任务[{self.__class__.__name__}] 异常：{异常}")

