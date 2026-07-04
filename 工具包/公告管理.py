import json
import os
import threading
import time
import urllib.parse
import urllib.request

仓库名 = "qilishidai/coc_robot"
分支名 = "main"
公告缓存文件 = "公告缓存.json"
统计缓存文件 = "统计缓存.json"
公告远程文件名 = "公告.json"
统计远程文件名 = "统计数据.json"
开发者标记文件 = "开发者标记.txt"
支持的格式版本 = 1

# 多源 fallback：raw 数据最新但大陆经常不可达；jsdelivr 有约 12 小时 CDN 缓存
数据源模板列表 = [
    "https://raw.githubusercontent.com/{仓库}/{分支}/{路径}",
    "https://cdn.jsdelivr.net/gh/{仓库}@{分支}/{路径}",
    "https://fastly.jsdelivr.net/gh/{仓库}@{分支}/{路径}",
]


def _从多源获取(远程文件名):
    """依次尝试各数据源下载并解析 JSON，全部失败返回 None"""
    路径 = urllib.parse.quote(远程文件名)
    for 模板 in 数据源模板列表:
        url = 模板.format(仓库=仓库名, 分支=分支名, 路径=路径)
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8"))
                print(f"[公告] 请求失败 {url}，状态码：{resp.status}")
        except Exception as e:
            print(f"[公告] 源不可用 {url}：{e}")
    return None


def _原子写缓存(缓存文件, 数据):
    """先写临时文件再替换，避免 UI 主线程轮询时读到半截 JSON"""
    临时文件 = 缓存文件 + ".tmp"
    with open(临时文件, "w", encoding="utf-8") as f:
        json.dump(数据, f, ensure_ascii=False, indent=2)
    os.replace(临时文件, 缓存文件)


def _读取缓存(缓存文件):
    if os.path.exists(缓存文件):
        try:
            with open(缓存文件, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def 读取公告缓存():
    return _读取缓存(公告缓存文件)


def 是否开发者模式():
    """项目根目录存在 开发者标记.txt 时启用开发者功能（该文件不入库）"""
    return os.path.exists(开发者标记文件)


def 读取统计缓存():
    return _读取缓存(统计缓存文件)


def 获取缓存最后更新时间():
    """返回两个缓存文件 mtime 的最大值，供 UI 轮询比对是否有新数据"""
    最大mtime = 0.0
    for 文件 in (公告缓存文件, 统计缓存文件):
        if os.path.exists(文件):
            最大mtime = max(最大mtime, os.path.getmtime(文件))
    return 最大mtime


def 取最新公告(公告数据):
    """从公告数据中取 id 最大的一条；格式不符时返回 None"""
    if not isinstance(公告数据, dict):
        return None
    if 公告数据.get("格式版本") != 支持的格式版本:
        return None
    公告列表 = 公告数据.get("公告列表")
    if not isinstance(公告列表, list) or not 公告列表:
        return None
    有效公告 = [项 for 项 in 公告列表 if isinstance(项, dict) and "标题" in 项]
    if not 有效公告:
        return None
    return max(有效公告, key=lambda 项: 项.get("id", 0))


def 异步刷新公告与统计():
    """后台线程拉取公告和统计数据并写入本地缓存，失败时保留旧缓存"""
    def 后台任务():
        公告 = _从多源获取(公告远程文件名)
        if 公告 is not None:
            _原子写缓存(公告缓存文件, 公告)
            print("[公告] 公告数据已更新")
        if 是否开发者模式():
            统计 = _从多源获取(统计远程文件名)
            if 统计 is not None:
                _原子写缓存(统计缓存文件, 统计)
                print("[公告] 统计数据已更新")

    线程 = threading.Thread(target=后台任务, daemon=True)
    线程.start()


if __name__ == "__main__":
    print("缓存的公告:", 读取公告缓存())
    print("缓存的统计:", 读取统计缓存())

    异步刷新公告与统计()

    for i in range(8):
        print(f"主程序运行中...{i + 1}")
        time.sleep(1)

    公告 = 读取公告缓存()
    print("刷新后的公告:", 公告)
    print("最新一条:", 取最新公告(公告))
    print("刷新后的统计:", 读取统计缓存())
