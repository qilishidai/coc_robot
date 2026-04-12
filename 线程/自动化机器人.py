from abc import ABC
from enum import Enum
import queue
import random

import threading
import time
from typing import Callable

from 任务流程.世界跳转.到主世界任务 import 到主世界任务
from 任务流程.世界跳转.到夜世界任务 import 到夜世界任务
from 任务流程.主世界打鱼 import 主世界打鱼任务
from 任务流程.升级城墙 import 城墙升级任务
from 任务流程.启动模拟器 import 启动模拟器任务
from 任务流程.基础任务框架 import 任务上下文
from 任务流程.夜世界.夜世界打鱼 import 夜世界打鱼任务
from 任务流程.夜世界.收集圣水车 import 收集圣水车任务
from 任务流程.夜世界.更新夜世界账号资源状态 import 更新夜世界资源状态任务
from 任务流程.天鹰火炮成就 import 刷天鹰火炮任务
from 任务流程.建筑升级 import 建筑升级任务
from 任务流程.收集资源 import 收集资源任务

from 任务流程.建筑升级.寻找建筑 import 寻找建筑
from 任务流程.建筑升级.更新工人状态 import 更新工人状态任务
from 任务流程.战宠升级 import 战宠升级任务
from 任务流程.兵种或法术升级 import 兵种或法术升级任务

# from 任务流程.夜世界.更新夜世界账号资源状态 import 更新夜世界资源状态任务
from 任务流程.更新主世界账号资源状态 import 更新家乡资源状态任务
from 任务流程.检查图像 import 检查图像任务
from 任务流程.检测游戏登录状态 import 检测游戏登录状态任务
from 工具包.工具函数 import 是否家乡资源打满, 是否夜世界资源打满
from 数据库.任务数据库 import 任务数据库, 机器人设置, 运行时状态
from 核心.op import op类

from 核心.键盘操作 import 键盘控制器
from 核心.鼠标操作 import 鼠标控制器
from 模块.雷电模拟器操作类 import 雷电模拟器操作类
from 核心.核心异常们 import 图像获取失败
    
            
class Task(ABC):
    """任务流程的具体任务"""
    def start(self):
        raise NotImplementedError()

    def step(self):
        raise NotImplementedError()
    
class 刷天鹰火炮任务(Task):
    """刷天鹰火炮的任务"""
    def start(self, 上下文):
        上下文.置脚本状态("开始执行刷天鹰火炮成就")

    def step(self, 上下文):
        到主世界任务(上下文).执行()  
        刷天鹰火炮任务(上下文).执行()

class 刷主世界任务(Task):
    def start(self, 上下文: 任务上下文):
        上下文.置脚本状态("开始执行主世界打鱼任务,当打满资源时退出")
        self.主世界进攻次数 = 0
    
    def step(self, 上下文: 任务上下文, 当前状态: 运行时状态):                
        到主世界任务(上下文).执行()
        if self.主世界进攻次数 % 5 == 0:
            收集资源任务(上下文).执行()
        
        建筑升级任务(上下文).执行()
        # 更新家乡资源状态任务(上下文).执行()
        城墙升级任务(上下文).执行()

        战宠升级任务(上下文).执行()
        兵种或法术升级任务(上下文).执行()
        更新家乡资源状态任务(上下文).执行()
        
        if "家乡资源" in 当前状态.状态数据 and 是否家乡资源打满(当前状态.状态数据["家乡资源"]):
            上下文.置脚本状态(
                "触发家乡资源已打满条件：金币和圣水末尾含3或5个零；低本黑油为0也视为打满，解锁后黑油同样需满足末尾零条件。"
            )
            上下文.置脚本状态("资源已打满,结束循环家乡打鱼")
            return

        上下文.脚本延时(random.randint(500, 3000))
        主世界打鱼任务(上下文).执行()

        self.主世界进攻次数 += 1
        
class 刷夜世界任务(Task):
    
    def start(self, 上下文: 任务上下文):
        上下文.置脚本状态("开始执行夜世界打鱼任务,当打满资源时退出")
        self.夜世界成功进攻次数 = 0
    
    def step(self, 上下文: 任务上下文, 当前状态: 运行时状态):
        城墙升级任务(上下文).执行()
        上下文.脚本延时(2000)  # 等待资源显示完全
        更新夜世界资源状态任务(上下文).执行()
        if 是否夜世界资源打满(当前状态.状态数据["夜世界资源"]):
            上下文.置脚本状态(
                "触发夜世界资源已打满条件：当夜世界的金币和圣水数量末尾有3个或5个零时，视为打满。"
            )
            上下文.置脚本状态("资源已打满,结束循环夜世界打鱼")

            return
        if self.夜世界成功进攻次数 % 5 == 0:
            上下文.置脚本状态(
                f"夜世界打鱼次数到了{self.夜世界成功进攻次数},收集圣水车"
            )
            收集圣水车任务(上下文).执行()
            收集资源任务(上下文).执行()

        夜世界打鱼任务(上下文).执行()
        上下文.脚本延时(random.randint(500, 3000))
        self.夜世界成功进攻次数 += 1

class 自动化机器人:
    """为单个用户提供游戏自动化服务的机器人实例"""

    def __init__(
        self,
        机器人标志: str,
        消息队列: queue.Queue,
        数据库: 任务数据库,
        日志队列: queue.Queue,
    ):
        # 基础属性
        self.机器人标志 = 机器人标志
        self.消息队列 = 消息队列  # 用来给监控中心发送消息
        self.数据库 = 数据库
        self.日志队列 = 日志队列

        self.继续事件 = threading.Event()
        self.停止事件 = threading.Event()
        self.上线 = threading.Event()
        self.停止事件.set()  # 目前未启动线程,处于停止状态
        self.op: op类

    
    def 记录启动时间(self):
        self.数据库.记录启动时间(self.机器人标志, time.time())
    
    def 获取启动时间(self) -> float:
        return self.数据库.获取启动时间(self.机器人标志)
    
    def 启动(self):
        self.数据库.记录日志(self.机器人标志, f"启动标志为{self.机器人标志}的机器人", time.time() + 60)
        self.上线.set()
        if self.停止事件.is_set():
            self.停止事件.clear()
            #线程执行完毕后不可重复 start，因此在检测到停止事件后需新建线程实例，用于重新启动任务流程。，所以创建线程操作放在启动里面
            self.主线程 = threading.Thread(
                target=self._任务流程,
                name=f"任务线程-{self.机器人标志}",
                daemon=True
            )
            self.主线程.start()

        else:
            print("目前线程未停止,无需再次启动")

    def 暂停(self):
        """标记暂停状态"""
        print("已暂停")
        self.继续事件.clear()

    def 继续(self):
        """清除暂停状态"""
        print("已继续")
        self.继续事件.set()

    def 停止(self, 停止原因=""):
        """标记终止状态"""
        self.继续()  # 唤醒可能已经暂停的线程
        self.停止事件.set()
        # 等待线程停止,如果未启动则没有主线程属性,加一层判断
        if hasattr(self, "主线程") and self.主线程.is_alive():
            self.主线程.join()

    @property
    def 设置(self) -> 机器人设置:
        配置 = self.数据库.获取机器人设置(self.机器人标志)
        return 配置

    @property
    def 当前状态(self) -> str:
        if self.停止事件.is_set():
            return "已停止"
        elif not self.继续事件.is_set():
            return "暂停中"
        else:
            return "运行中"

    def 记录日志(self, 日志内容: str, 超时的时间: float = 60, 级别: str = "正常"):
        """记录日志到数据库并通过队列发送到UI
        级别: "正常" | "警告" | "错误"（默认"正常"）。保持原有调用兼容，新增关键字参数 级别。
        """

        # 规范级别取值
        合法级别 = {"正常", "警告", "错误"}
        if 级别 not in 合法级别:
            级别 = "正常"

        # 根据级别为文本添加可解析前缀（仅非“正常”时）
        带级别前缀的内容 = 日志内容
        if 级别 != "正常" and not (
            日志内容.startswith("[警告]") or 日志内容.startswith("[错误]")
        ):
            前缀 = "[警告]" if 级别 == "警告" else "[错误]"
            带级别前缀的内容 = f"{前缀} {日志内容}"

        # 控制台输出
        print(
            f"[机器人消息] {self.机器人标志} {time.strftime('%Y年%m月%d日 %H:%M:%S')}: {带级别前缀的内容}"
        )
        # 写入数据库（保持原表结构，内容中包含级别前缀）
        self.数据库.记录日志(
            self.机器人标志, 带级别前缀的内容, time.time() + 超时的时间
        )

        # 发送到UI日志队列（携带结构化级别，便于实时渲染）
        if self.日志队列:
            self.日志队列.put(
                {
                    "内容": f"[{time.strftime('%H:%M:%S')}] {带级别前缀的内容}",
                    "机器人ID": self.机器人标志,
                    "类型": "运行",
                    "级别": 级别,
                }
            )

    def _任务流程(self):
        """主任务逻辑"""
        self.op = op类()
        if self.op is None:
            print("op创建失败")
        # 不可以在构造函数执行,因为每次启动都可能更新设置
        self.雷电模拟器 = 雷电模拟器操作类(
            self.数据库.获取机器人设置(self.机器人标志).雷电模拟器索引
        )
        
        上下文 = 任务上下文(
            机器人标志=self.机器人标志,
            消息队列=self.消息队列,
            数据库=self.数据库,
            停止事件=self.停止事件,
            继续事件=self.继续事件,
            置脚本状态=self.记录日志,
            op=self.op,
            雷电模拟器=self.雷电模拟器,
            鼠标=鼠标控制器(self.雷电模拟器.取绑定窗口句柄()),
            键盘=键盘控制器(self.雷电模拟器.取绑定窗口句柄()),
        )
        上下文.打开模拟器()
        
        # 上下文.置脚本状态("开始执行",1000)
        上下文.继续事件.set()
        print("本次运行时的设置为" + self.设置.__str__())

        try:
            检测登录 = 检测游戏登录状态任务(
                上下文
            )  # 检测任务需要重复调用，这里先创建，但是不执行

            启动模拟器任务(上下文).执行()

            上下文.op.绑定(self.雷电模拟器.取绑定窗口句柄的下级窗口句柄())
            上下文.鼠标 = 鼠标控制器(self.雷电模拟器.取绑定窗口句柄())
            上下文.键盘 = 键盘控制器(self.雷电模拟器.取绑定窗口句柄())

            检查图像任务(上下文).执行()
            tasks = []
            if self.设置.是否刷天鹰火炮:
                tasks.append(刷天鹰火炮任务())
            if self.设置.是否刷主世界:
                tasks.append(刷主世界任务())
            if self.设置.是否刷夜世界:
                tasks.append(刷夜世界任务())
            
            for task in tasks:
                task.start(上下文)
            
            while True:
                检测登录.执行()
                当前状态 = 上下文.数据库.获取最新完整状态(self.机器人标志)
                for task in tasks:
                    task.step(上下文, 当前状态)
                
                start = self.获取启动时间()
                assert start is not None, "至少手动启动了一次"
                
                if self.设置.默认上线时长 > 0 and time.time() - start > self.设置.默认上线时长 * 3600:
                    启动间隔 = self.设置.启动间隔 * 3600
                    启动间隔 += random.randint(int(-0.1 * 启动间隔), int(0.1 * 启动间隔))
                    
                    if self.设置.启动间隔 <= 0:
                        # 如果设置了非正数的启动间隔，则视为不再自动重启
                        启动间隔 = time.time() + 10 * 365 * 24 * 3600  
                        self.停止("已达到默认上线时长，自动结束运行") 
                    上下文.置脚本状态("已达到默认上线时长，自动结束运行", 启动间隔)
                    self.上线.clear()
                    上下文.关闭模拟器()
                    break

        except 图像获取失败 as e:
            上下文.发送重启请求(f"异常: {str(e)}")
            print(
                "-" * 10
                + f"{self.机器人标志} 线程因为异常而消亡"
                + "-" * 10
                + f"异常: {str(e)}"
            )
        except SystemExit as e:
            print("-" * 10 + f"{self.机器人标志} 线程因为捕获到退出而消亡" + "-" * 10)
            print(f"具体信息:{str(e)}")
        finally:
            上下文.op.安全清理()

    def 剩余超时时间(self):
        """检查是否超时，返回 剩余超时时间"""

        最后日志 = self.数据库.读取最后日志(self.机器人标志)
        # 无历史日志的情况
        if not 最后日志:
            return -1  # 无日志视为第一次启动,不是超时的异常状态

        # 主动停止不视为超时
        if self.停止事件.is_set():
            return -1

        实际间隔 = round(time.time() - 最后日志.记录时间)
        超时阈值 = round(最后日志.下次超时 - 最后日志.记录时间)

        return 超时阈值 - 实际间隔

    def 检查超时(self) -> tuple[bool, str]:
        """检查是否超时，返回 (是否超时, 原因)。未超时返回 (False, '')"""

        最后日志 = self.数据库.读取最后日志(self.机器人标志)
        # 无历史日志的情况
        if not 最后日志:
            return (False, "无历史日志记录")  # 无日志视为第一次启动,不是超时的异常状态

        # 主动停止不视为超时
        if self.停止事件.is_set():

            return (False, f"{self.机器人标志} 线程已主动停止,不是异常状态")

        if time.time() > 最后日志.下次超时:
            实际间隔 = round(time.time() - 最后日志.记录时间)
            超时阈值 = round(最后日志.下次超时 - 最后日志.记录时间)

            原因 = (
                f"数据库最后日志记录已超时（内容：[{最后日志.日志内容}]），"
                f"实际间隔 {实际间隔} 秒超过阈值 {超时阈值} 秒"
            )

            return True, 原因

        return (False, "")
