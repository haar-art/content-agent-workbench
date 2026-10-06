"""
内容 Agent 工作台 · 阶段 A · v2（上下文工程版）

v1 的病根：5 个 step 各自造 messages，零共享容器 —— Step1 定的口吻，Step3 没地方去找。
v2 的治法：全程共用一个 ContextSession，历史滚动累积，每一轮都把完整历史发给模型。


★ 动手前先读这段分工说明 ★

  已写好（我写的，你负责读懂）：
    - call()          底层改造：收 ctx，透传整个 messages
    - step1_persona() 完整示范：add_user -> call -> add_assistant 三步走
    - main()          顶层串联：创建容器 + 全程传递

  留给你写（4 个函数体里都有 TODO）：
    - step2_research()
    - step3_script()
    - step4_image_prompts()
    - step5_assemble()

  注意：文件现在跑不起来，会抛 NotImplementedError。这是故意的 ——
  填完 4 个 step 才能跑通，跑通的那一刻才算你真读懂了这套机制。


依赖：pip install openai python-dotenv（跟 v1 同一套环境）
前置：同目录必须有 context_builder.py（容器已经在里面写好了，直接 import 复用，不要重写）
"""

import os
import json
from datetime import datetime
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

from context_builder import ContextSession

load_dotenv()
client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
BASE_DIR = Path(__file__).parent

# 账号人设（常量，所有步骤共享，不占 LLM 调用）
PERSONA = "面向零基础观众的「学 AI / 亲手做东西」的博主，人设是翻车但真实的陪练，不说教、有态度、信息密度高。"

# 写稿约束（从 7 维 rubric 里挑影响写稿的几条，先喂这些）
RUBRIC = """1. 开头 3 秒必须有钩子（反常识 / 抛冲突 / 直接甩结论），别寒暄。
2. 全程口语化，零基础能听懂；英文术语必须白话改写（例：RAG → 「让 AI 记得你之前聊过啥」）。
3. 禁用『最/第一/绝对/唯一』等极限词（平台会限流）
4. 零基础观众必须逐字听懂；禁止英文术语和黑话，命令类英文只保留在『屏幕展示』里，不写进口播。"""


# ==================== 底层：整个 v2 里唯一碰网络的地方 ====================

def call(ctx: ContextSession, temperature: float = 0.8) -> str:
    """把容器里的 messages 整个发出去，返回模型回话。

    【和 v1 的关键区别 —— 这一处改动就是「治漂移」的全部机械原理】

      v1：call(prompt) -> 内部现造 messages=[{"role":"user","content":prompt}]
                        每一步只有一条消息，模型看不见之前任何一步。

      v2：call(ctx)    -> 直接透传 ctx.messages，整个历史一起发。
                        模型每一轮都看得到前面所有轮说过的话，
                        Step1 定的口吻跑不掉 —— 漂移的根被切断了。

    顺带解释你上午答的那个矛盾：memories 列表里 system 只有 1 条（构造一次），
    但每次调用都把整个列表传出去，所以 system 实际被发送了 5 次（传输 N 次）。
    """
    resp = client.chat.completions.create(
        model=MODEL,
        messages=ctx.messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content.strip()


# ==================== 中层：5 个 step ====================

def step1_persona(ctx: ContextSession, topic: str) -> str:
    """人设锚定。【完整示范 —— 看懂这三段，剩下 4 个照抄结构】

    注意三件事：
      1. 函数签名里没有「上一步的结果」这种参数 —— 历史全在 ctx 里，不用靠参数传
      2. 先 ctx.add_user(...) 说明这一步要模型干什么，再 call(ctx)
      3. call 完必须 ctx.add_assistant(reply) 把回话记回容器
         —— 这一步漏了，整个机制当场作废（下一步看不到这一步说过什么）

    对比 v1：v1 的这个函数是 return call(prompt)，prompt 一发出去就没了。
    回话没有存回任何地方，所以 Step2 收到的 hook_strategy 是从参数传进去的死字符串，
    而不是「模型的历史输出」。两者在 API 层面长得一样，但语义完全不同：
    后者会随对话累积，前者永远只有孤零零一条。
    """
    ctx.add_user(f"""严禁使用 markdown 符号（*、#、** 等），输出纯文本。
你是{PERSONA}

主题：{topic}

任务：只输出这条内容该用什么「钩子策略 + 口吻」，2-3 句话，不要写正文。""")

    reply = call(ctx)
    ctx.add_assistant(reply)
    return reply

def step2_research(ctx: ContextSession) -> str:
    """选题研究：给 3 个候选切入点，选 1 个最优并说明理由。"""
    ctx.add_user(f"""严禁使用 markdown 符号（*、#、** 等），输出纯文本。
你是{PERSONA}
任务：给出 3 个候选切入点（不同角度），然后选 1 个最优，说明为什么它最抓零基础观众。
输出格式（严格遵守，第一行必须是「最优切入点：」，不要任何前置说明）：
最优切入点：xxx
理由：xxx""")
    reply = call(ctx)
    ctx.add_assistant(reply)
    return reply

def step3_script(ctx: ContextSession) -> dict:
    """文稿生成：产出 title / hook / script / hashtags。"""
    ctx.add_user(f"""严禁使用 markdown 符号（*、#、** 等），输出纯文本。
你是{PERSONA}
写作要求：{RUBRIC}
只输出 JSON：
{{"title":"标题，带钩子，≤20字","hook":"开头3秒口播，1-2句","script":"正文口播稿，≤200字，按句分段，纯口语","hashtags":["#话题1","#话题2","#话题3"]}}""")
    text = call(ctx).strip().strip("`").removeprefix("json").strip()
    ctx.add_assistant(text)
    data = json.loads(text)
    REQUIRED3 = {"title", "hook", "script", "hashtags"}
    missing = REQUIRED3 - data.keys()
    assert not missing, f"step3 缺字段：{missing}"
    return data

def step4_image_prompts(ctx: ContextSession) -> list:
    """配图提示词：产出 2 条竖版提示词。"""
    ctx.add_user(f"""严禁使用 markdown 符号（*、#、** 等），输出纯文本。
你是短视频封面/配图提示词专家。
任务：只输出 JSON 数组，2 个元素，每个是一条可直接喂图像模型的竖版提示词（含构图/色调/光影/文字元素）。""")
    text = call(ctx).strip().strip("`").removeprefix("json").strip()
    ctx.add_assistant(text)
    data = json.loads(text)
    assert isinstance(data, list), f"step4 该返回数组，实际是 {type(data).__name__}"
    assert 1 <= len(data) <= 3, f"step4 该返回 1-3 条，实际 {len(data)} 条"
    return data



def step5_assemble(topic: str, hook_strategy: str, angle: str,
                   script_part: dict, image_prompts: list) -> dict:
    """组装：纯代码，不再调 LLM，把各步结果拼成最终脚本包。
    
    中间产物（hook_strategy / angle）也保留，方便你人工干预或排错。 """
    result = {
            "topic": topic,
            "hook_strategy": hook_strategy,
            "angle": angle,
            "title": script_part["title"],
            "hook": script_part["hook"],
            "script": script_part["script"],
            "image_prompts": image_prompts,
            "hashtags": script_part["hashtags"],
            }

    REQUIRED = {"topic", "hook", "hook_strategy", "angle",
                "title", "script", "image_prompts", "hashtags"}
    missing = REQUIRED - result.keys()
    assert not missing, f"脚本包缺字段：{missing}"
    return result

def save_script(result: dict) -> Path:
    """把最终脚本包落盘成 json，返回文件路径。"""
    # 1. 目录：不存在就建，存在就跳过（exist_ok=True 就是这个意思）
    out_dir = BASE_DIR / "output"
    out_dir.mkdir(exist_ok=True)

    # 2. 文件名：时间戳，跑几次就存几份，不互相覆盖
    filename = datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"

    # 3. 拼完整路径（用 / 拼接，别用字符串 + ）
    out_path = out_dir / filename

    # 4. 写盘：encoding="utf-8" 防中文乱码
    #    ensure_ascii=False 让中文原样存，别转成 \uXXXX
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 5. 返回路径给调用方 —— 不返回，外面就没法知道存哪了
    return out_path

    


# ==================== 顶层：串联 ====================

def main():
    topic = input("输入主题：").strip() or "一条命令误删了开发者 700GB 数据"

    # 唯一的容器，全程带着走
    ctx = ContextSession(BASE_DIR)
    print(f"[初始化] 上下文已装载，system 字符数 {ctx.stats()['system 字符数']}\n")

    print("[Step1] 人设锚定…")
    hook_strategy = step1_persona(ctx, topic)
    print("  ->", hook_strategy)

    print("[Step2] 选题研究…")
    angle_full = step2_research(ctx)
    angle = angle_full.strip().splitlines()[0]
    print("  ->", angle)

    print("[Step3] 文稿生成…")
    script_part = step3_script(ctx)
    print("  ->", script_part["title"])

    print("[Step4] 配图提示词…")
    image_prompts = step4_image_prompts(ctx)
    print("  ->", len(image_prompts), "张")

    print("[Step5] 组装…")
    result = step5_assemble(topic, hook_strategy, angle, script_part, image_prompts)

    print("\n===== 最终脚本包 =====")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    saved = save_script(result)
    print(f"\n已保存到：{saved}")
    

    print("\n===== 上下文用量（阶段 E 可观测性雏形）=====")
    for k, v in ctx.stats().items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
