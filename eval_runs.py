"""阶段 E：自动评测 —— 读 runs.jsonl，判定每次运行，汇总通过率。"""

import json
from pathlib import Path

RUNS_PATH = Path(__file__).parent / "runs.jsonl"

# ---- 1. 读 ----
lines = RUNS_PATH.read_text(encoding="utf-8").strip().splitlines()

runs = [json.loads(line) for line in lines]


# ---- 2. 判 + 报 ----
ok = 0

for row in runs:
    if row["passed"]:
        ok += 1
    else:
        print("⚠️ 翻车:",row["ts"])

total = len(runs)

if total > 0:
    print("总运行：",total)
    print("通过：",ok)
    print(f"通过率:{round(ok/total * 100)}%")
else:
    print("还没有运行记录 —— 先去跑 agent_loop.py 几次")
