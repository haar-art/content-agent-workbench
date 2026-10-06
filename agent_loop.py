"""B3：Function Calling 循环 —— 模型自己决定调哪个工具。"""

import json
import os
import time

from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

from read_candidates import read_candidates
from tools import TOOLS

load_dotenv()

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)
MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")

# 函数表：name -> 真函数。模型报名字，这里负责找
TOOL_FUNCS = {"read_candidates": read_candidates}

# 护栏：最多跑几步
MAX_STEPS = 3
# 运行档案：一行一次运行（JSONL 追加，不覆盖历史）
RUNS_PATH = Path(__file__).parent / "runs.jsonl"


SYSTEM_PROMPT = (
    "你是内容工作台助手，负责帮我准备短视频选题。"
    "你只能从我的选题库里查找选题，不许自己编造。"
    "拿到工具返回的结果后，直接基于结果作答，不重复调用同一工具。"
    "输出格式：只输出 JSON，不要任何解释文字或 markdown 符号，形如："
    '{"topics": [{"id": "选题id", "tier": "tier1", "title": "标题"}]}'
)


messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "帮我看看选题池里现在有哪些选题可以拍。"},
]
start = time.perf_counter()
fetched = None   # 工具一共给了多少条（外部事实）
listed = None    # 模型最终列了多少条
topics = None    # 模型最终列出的选题（内容）


for step in range(MAX_STEPS):
    print(f"--- 第 {step + 1} 步 ---")

    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS,
    )
    msg = resp.choices[0].message
    print("finish_reason:", resp.choices[0].finish_reason)

    if not msg.tool_calls:
        print("=== 最终回答 ===")
        print(msg.content)
        data = json.loads(msg.content)
        topics = data["topics"]
        listed = len(topics)
        print("工具给出:", fetched)
        print("模型列出:", listed)
        if listed != fetched:
            print(f"⚠️ 漏项 —— 工具给了 {fetched} 条，模型只列了 {listed} 条")
        break

    messages.append(msg)

    for tc in msg.tool_calls:
        name = tc.function.name
        args = json.loads(tc.function.arguments)
        print(f"  要调 {name}，参数 {args}")

        result = TOOL_FUNCS[name](**args)
        fetched = len(result)
        print(f"  拿到 {fetched} 条")


        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(result, ensure_ascii=False),
        })
else:
    print("⚠️ 撞到最大步数上限，强制停止 —— 模型没能收尾")

print("历史最终条数：", len(messages))
duration_ms = round((time.perf_counter() - start) * 1000)
print("本次耗时:", duration_ms, "毫秒")
# 攒出这次运行的「一行档案」
record = {
    "ts": datetime.now().isoformat(timespec="seconds"),
    "steps": step + 1,
    "fetched": fetched,
    "listed": listed,
    "topics": topics,
    "passed": listed == fetched,
    "duration_ms": duration_ms,
}
# 落盘：追加到 runs.jsonl，一行一次运行
with open(RUNS_PATH, "a", encoding="utf-8") as f:
    f.write(json.dumps(record, ensure_ascii=False) + "\n")

print("已写入运行档案:", RUNS_PATH.name)
print(record)


