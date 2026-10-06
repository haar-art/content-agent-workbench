import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def parse_block(block: str) -> dict:
    """把一块文本，变成一个 dict。"""
    lines = block.splitlines()

    head = lines[0]
    tier_part, _, title = head.partition("] ")
    tier = tier_part.removeprefix("[")

    item = {"tier": tier, "title": title.strip()}

    for l in lines[1:]:
        if l.startswith("- **"):
            k, _, v = l.partition("**: ")
            item[k.removeprefix("- **")] = v.strip()

    return item


def read_candidates() -> list:
    """读 candidates.md，返回一个 list，一条记录一个 dict。"""
    raw = os.getenv("CANDIDATES_PATH")
    if not raw:
        raise ValueError("CANDIDATES_PATH 没配置，去看 .env")

    p = Path(raw)
    if not p.exists():
        raise FileNotFoundError(f"选题池文件不存在：{p}")

    text = p.read_text(encoding="utf-8")
    parts = text.split("\n### ")
    blocks = parts[1:]
    items = [parse_block(b) for b in blocks]
    return [x for x in items if x["tier"] != "tier3"]


if __name__ == "__main__":
    items = read_candidates()
    print("解析出多少条：", len(items))
    print()
    for it in items[:3]:
        print(it["tier"], "|", it["title"])
        print("   id =", it.get("id"))
    print()
    print("第 1 条的字段名：", list(items[0].keys()))
