"""
GitHub Actions 定时任务脚本：拉取仓库 Traffic 数据并累积合并到 统计数据.json

Traffic API 只保留最近 14 天数据，因此需要每日运行本脚本把数据持久化。
合并策略：每日明细 以日期为 key 覆盖写入（同一天取 API 最新值，天然幂等），
累计 字段每次由 每日明细 全量重算，绝不增量累加。

环境变量：
  TRAFFIC_TOKEN  访问 Traffic API 的 token（需要仓库 push 权限）
  REPO           仓库全名，如 qilishidai/coc_robot
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

统计文件 = "统计数据.json"


def api_get(路径):
    url = f"https://api.github.com{路径}"
    请求 = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {os.environ['TRAFFIC_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(请求, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def 读取现有统计():
    if os.path.exists(统计文件):
        with open(统计文件, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"格式版本": 1, "更新时间": "", "累计": {}, "每日明细": {}}


def 合并每日数据(每日明细, 数组, 次数字段, 独立字段):
    """把 Traffic API 返回的按天数组按日期覆盖合并进 每日明细"""
    for 项 in 数组:
        日期 = 项["timestamp"][:10]
        当日 = 每日明细.setdefault(日期, {})
        当日[次数字段] = 项["count"]
        当日[独立字段] = 项["uniques"]


def main():
    仓库 = os.environ["REPO"]

    try:
        克隆数据 = api_get(f"/repos/{仓库}/traffic/clones")
        访问数据 = api_get(f"/repos/{仓库}/traffic/views")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("=" * 60)
            print("错误：当前 token 无权访问 Traffic API（需要仓库 push 权限）。")
            print("GITHUB_TOKEN 通常没有此权限，请创建 PAT 并存入仓库 secrets：")
            print("  1. GitHub → Settings → Developer settings →")
            print("     Personal access tokens → classic，勾选 repo 作用域")
            print("     （或 fine-grained token：仅本仓库，Administration: Read-only）")
            print("  2. 仓库 Settings → Secrets and variables → Actions →")
            print("     New repository secret，名称填 TRAFFIC_TOKEN")
            print("=" * 60)
            sys.exit(1)
        raise

    仓库信息 = api_get(f"/repos/{仓库}")
    发布列表 = api_get(f"/repos/{仓库}/releases?per_page=100")

    统计 = 读取现有统计()
    每日明细 = 统计.setdefault("每日明细", {})
    合并每日数据(每日明细, 克隆数据.get("clones", []), "克隆次数", "独立克隆")
    合并每日数据(每日明细, 访问数据.get("views", []), "访问次数", "独立访客")

    统计["格式版本"] = 1
    统计["更新时间"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    统计["累计"] = {
        "克隆次数": sum(d.get("克隆次数", 0) for d in 每日明细.values()),
        "独立克隆按日累计": sum(d.get("独立克隆", 0) for d in 每日明细.values()),
        "访问次数": sum(d.get("访问次数", 0) for d in 每日明细.values()),
        "独立访客按日累计": sum(d.get("独立访客", 0) for d in 每日明细.values()),
        "star数": 仓库信息.get("stargazers_count", 0),
        "release总下载量": sum(
            资产.get("download_count", 0)
            for 发布 in 发布列表
            for 资产 in 发布.get("assets", [])
        ),
    }
    统计["每日明细"] = dict(sorted(每日明细.items()))

    with open(统计文件, "w", encoding="utf-8") as f:
        json.dump(统计, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"统计已更新：{json.dumps(统计['累计'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
