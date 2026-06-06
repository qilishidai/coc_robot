"""
企业微信群机器人通知模块

提供发送文本和图片消息到企业微信群的功能。
"""
import base64
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import cv2
import numpy as np
import requests


class 企业微信通知器:
    """企业微信群机器人通知器

    通过 webhook 发送文本和图片消息到企业微信群。
    使用线程池异步发送，避免阻塞主线程。
    """

    def __init__(self, webhook_url: str):
        """初始化通知器

        参数:
            webhook_url: 企业微信群机器人的 Webhook URL
        """
        self.webhook_url = webhook_url
        self.线程池 = ThreadPoolExecutor(max_workers=2, thread_name_prefix="企业微信通知")
        self.上次发送时间 = 0
        self.最小发送间隔 = 1.0  # 秒，防止频率过高

    def 发送文本(self, 内容: str) -> bool:
        """发送文本消息（同步）

        参数:
            内容: 消息文本内容

        返回:
            是否发送成功
        """
        try:
            # 频率限制
            当前时间 = time.time()
            if 当前时间 - self.上次发送时间 < self.最小发送间隔:
                time.sleep(self.最小发送间隔 - (当前时间 - self.上次发送时间))

            payload = {
                "msgtype": "text",
                "text": {
                    "content": 内容
                }
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )

            self.上次发送时间 = time.time()

            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    return True
                else:
                    print(f"企业微信 API 返回错误: {result}")
                    return False
            else:
                print(f"企业微信通知发送失败，HTTP 状态码: {response.status_code}")
                return False

        except Exception as e:
            print(f"发送企业微信文本消息异常: {e}")
            return False

    def 发送图片(self, 图片数据: np.ndarray) -> bool:
        """发送图片消息（同步）

        参数:
            图片数据: OpenCV 格式的图像（BGR numpy 数组）

        返回:
            是否发送成功
        """
        try:
            # 频率限制
            当前时间 = time.time()
            if 当前时间 - self.上次发送时间 < self.最小发送间隔:
                time.sleep(self.最小发送间隔 - (当前时间 - self.上次发送时间))

            # 转换为 base64 和 md5
            base64_str, md5_str = self._图片转base64(图片数据)

            payload = {
                "msgtype": "image",
                "image": {
                    "base64": base64_str,
                    "md5": md5_str
                }
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30  # 图片上传可能较慢
            )

            self.上次发送时间 = time.time()

            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    return True
                else:
                    print(f"企业微信图片 API 返回错误: {result}")
                    return False
            else:
                print(f"企业微信图片发送失败，HTTP 状态码: {response.status_code}")
                return False

        except Exception as e:
            print(f"发送企业微信图片消息异常: {e}")
            return False

    def _图片转base64(self, cv图像: np.ndarray) -> tuple[str, str]:
        """将 OpenCV 图像转换为 base64 和 md5

        参数:
            cv图像: OpenCV 格式的图像（BGR numpy 数组）

        返回:
            (base64字符串, md5字符串)
        """
        # 压缩为 JPEG（质量 80）
        _, buffer = cv2.imencode('.jpg', cv图像, [cv2.IMWRITE_JPEG_QUALITY, 80])
        图片字节 = buffer.tobytes()

        # 生成 base64 和 md5
        base64_str = base64.b64encode(图片字节).decode('utf-8')
        md5_str = hashlib.md5(图片字节).hexdigest()

        return base64_str, md5_str

    def 发送状态消息(self, 机器人标志: str, 状态文本: str, 截图: Optional[np.ndarray] = None):
        """异步发送状态消息（先发文本，再发截图）

        通过线程池异步执行，不阻塞主线程。

        参数:
            机器人标志: 机器人唯一标识
            状态文本: 状态描述文本
            截图: 可选的屏幕截图（OpenCV 格式）
        """
        self.线程池.submit(self._同步发送状态消息, 机器人标志, 状态文本, 截图)

    def _同步发送状态消息(self, 机器人标志: str, 状态文本: str, 截图: Optional[np.ndarray]):
        """同步发送状态消息（内部方法）

        参数:
            机器人标志: 机器人唯一标识
            状态文本: 状态描述文本
            截图: 可选的屏幕截图
        """
        try:
            # 先发送文本
            完整文本 = f"[{机器人标志}]\n{状态文本}"
            文本成功 = self.发送文本(完整文本)

            if not 文本成功:
                print(f"机器人 {机器人标志} 文本消息发送失败")

            # 再发送截图（如果提供）
            if 截图 is not None:
                图片成功 = self.发送图片(截图)
                if not 图片成功:
                    print(f"机器人 {机器人标志} 截图发送失败")

        except Exception as e:
            print(f"发送状态消息异常 (机器人: {机器人标志}): {e}")

    def 关闭(self):
        """关闭线程池，等待所有任务完成"""
        self.线程池.shutdown(wait=True)
