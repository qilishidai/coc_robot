import difflib
import random
import re
from datetime import datetime, timedelta

from 任务流程.基础任务框架 import 基础任务, 任务上下文
from 任务流程.战宠升级.完成宠物升级 import 完成宠物升级任务
from 任务流程.新版升级面板 import 新版升级面板


class 战宠升级任务(基础任务):
    """自动升级指定的战宠

    2026新版UI：战宠升级列表已整合进统一升级面板（底栏战宠入口），
    不再需要通过YOLO寻找地图上的战宠小屋。
    流程：打开面板战宠列表 -> 模糊匹配目标战宠 -> 点击条目 -> 确认升级。
    """

    # ==================== 检测参数常量 ====================
    名称相似度阈值 = 0.6
    最大滑动次数 = 20
    最大连续未变化次数 = 3
    # 升级队列条中出现这些时间单位说明有战宠正在升级
    队列时间关键词 = ("天", "小时", "分钟")

    def __init__(self, 上下文: '任务上下文'):
        super().__init__(上下文)
        # 新版统一升级面板驱动
        self.面板 = 新版升级面板(上下文)
        self.上次名称集合 = None
        self.连续相同ocr次数 = 0

    def 执行(self) -> bool:
        欲升级战宠 = self.上下文.设置.欲升级的战宠

        if not 欲升级战宠:
            self.上下文.置脚本状态("战宠升级：未配置要升级的战宠，跳过")
            return False

        # 检查冷却时间
        完整状态 = self.数据库.获取最新完整状态(self.机器人标志).状态数据
        上次记录 = 完整状态.get("战宠升级失败记录")
        if 上次记录:
            记录时间 = datetime.fromtimestamp(上次记录.get("时间", 0))
            冷却时间 = timedelta(hours=self.上下文.设置.战宠升级检查间隔)
            if datetime.now() - 记录时间 < 冷却时间:
                剩余分钟 = int((冷却时间 - (datetime.now() - 记录时间)).total_seconds() / 60)
                self.上下文.置脚本状态(f"战宠升级：冷却中，{剩余分钟}分钟后再试")
                return False

        self.上下文.置脚本状态(f"战宠升级：开始升级 {欲升级战宠}")

        # 打开新版升级面板的战宠列表
        self.面板.打开列表(入口坐标=self.面板.战宠入口坐标)

        try:
            # 先检查升级队列：战宠正在升级时队列条显示剩余时间，此时不能再发起升级
            队列内容 = self.获取升级队列内容()
            if 队列内容:
                self.上下文.置脚本状态(f"战宠升级：战宠正在升级中({队列内容})，跳过本次升级")
                self.记录状态(f"战宠正在升级中({队列内容})")
                self.面板.关闭面板()
                return False

            if not self.寻找并点击目标战宠(欲升级战宠):
                self.记录状态("未能定位目标战宠")
                self.面板.关闭面板()
                return False

            self.上下文.脚本延时(1500)

            if not 完成宠物升级任务(self.上下文).执行():
                self.记录状态("升级操作未完成")
                return False

            # 成功后清除失败记录
            self.数据库.更新状态(self.机器人标志, "战宠升级失败记录", None)
            self.上下文.置脚本状态(f"战宠升级：{欲升级战宠} 升级完成")
            return True

        except Exception as e:
            self.记录状态(f"任务异常: {str(e)}")
            self.面板.关闭面板()
            return False

    # ---------------------- 升级队列检查 ----------------------
    def 获取升级队列内容(self) -> str | None:
        """检查战宠列表顶部的升级队列条

        有战宠正在升级时队列条显示 战宠名+剩余时间(如 贪婪渡鸦 4天18小时)，
        空闲时显示"未指派"。返回队列文本(含时间关键词)表示忙碌，空闲返回 None
        """
        ocr结果 = self.面板.执行OCR识别(self.面板.战宠队列条OCR区域)

        队列文本 = "".join(
            项[1] for 项 in ocr结果
            if isinstance(项, (list, tuple)) and len(项) >= 2 and isinstance(项[1], str)
        )

        if any(关键词 in 队列文本 for 关键词 in self.队列时间关键词):
            return 队列文本
        return None

    # ---------------------- 寻找战宠 ----------------------
    def 寻找并点击目标战宠(self, 欲升级战宠: str) -> bool:
        """在战宠列表中滑动查找并点击目标战宠"""
        for _ in range(self.最大滑动次数):
            ocr结果 = self.面板.执行OCR识别(self.面板.面板OCR区域)

            if self.尝试点击目标战宠(ocr结果, 欲升级战宠):
                return True

            if self.列表已到底(ocr结果):
                break

            self.面板.向上滑动一下()

        self.上下文.置脚本状态(f"战宠升级：滑动{self.最大滑动次数}次未找到 {欲升级战宠}，可能已满级或未解锁")
        return False

    def 尝试点击目标战宠(self, ocr结果, 欲升级战宠: str) -> bool:
        """在当前OCR结果中模糊匹配目标战宠并点击"""
        for 识别项 in ocr结果:
            文本内容 = 识别项[1].replace(" ", "")

            # 排除队列条区域的"未指派"文本，避免误点；
            # 队列中有战宠时已在执行入口提前返回，不会走到这里
            if "未指派" in 文本内容:
                continue

            if not self.模糊匹配名称(文本内容, 欲升级战宠):
                continue

            try:
                行区域 = self.面板.解析行坐标(识别项[0])
            except Exception as e:
                self.上下文.置脚本状态(f"坐标解析失败: {str(e)}")
                continue

            self.上下文.置脚本状态(f"战宠升级：找到目标战宠 {文本内容}, 尝试选中")
            self.选中战宠行(行区域)
            return True

        return False

    def 模糊匹配名称(self, 文本内容: str, 欲升级战宠: str) -> bool:
        """模糊匹配战宠名称，过滤纯数字等噪声"""
        if not 文本内容 or len(文本内容) < 2:
            return False

        if re.fullmatch(r"[0-9.\-:]+", 文本内容):
            return False

        相似度 = difflib.SequenceMatcher(None, 欲升级战宠.replace(" ", ""), 文本内容).ratio()
        return 相似度 >= self.名称相似度阈值

    def 选中战宠行(self, 行区域: tuple):
        """点击战宠条目打开升级详情对话框"""
        x1, y1, x2, y2 = 行区域
        中心x = (x1 + x2) // 2 + random.randint(-5, 5)
        中心y = (y1 + y2) // 2 + random.randint(-5, 5)
        self.上下文.点击(中心x, 中心y, 延时=1500)

    def 列表已到底(self, ocr结果) -> bool:
        """检测连续多次界面未变化，判断列表是否已到底"""
        当前名称集合 = self.提取名称集合(ocr结果)

        if not 当前名称集合:
            self.连续相同ocr次数 = 0
            self.上次名称集合 = None
            return False

        if self.上次名称集合 == 当前名称集合:
            self.连续相同ocr次数 += 1
        else:
            self.连续相同ocr次数 = 0
        self.上次名称集合 = 当前名称集合

        return self.连续相同ocr次数 >= self.最大连续未变化次数

    def 提取名称集合(self, ocr结果) -> list:
        """从OCR结果中提取稳定的中文名称，过滤价格和噪声"""
        稳定文本列表 = []

        for 项 in ocr结果:
            if not isinstance(项, (list, tuple)) or len(项) < 2:
                continue

            文本 = 项[1]
            if not isinstance(文本, str):
                continue

            文本 = 文本.replace(" ", "")

            if re.fullmatch(r"[0-9.\-:]+", 文本):
                continue

            if len(文本) < 2:
                continue

            稳定文本列表.append(文本)

        return sorted(稳定文本列表)

    def 记录状态(self, 原因: str):
        """记录状态到数据库，用于冷却判断"""
        状态记录 = {
            "时间": datetime.now().timestamp(),
            "原因": 原因
        }
        self.数据库.更新状态(self.机器人标志, "战宠升级失败记录", 状态记录)
