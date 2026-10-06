"""
context_builder.py —— 4 层上下文组装器（阶段 A · 第 1 件代码）

它只干一件事：把散落的上下文文件读进来，拼成 OpenAI 的 messages 列表。

为什么需要它：
    v1 的 call() 每次都现造一个单元素 messages，五步之间没有任何共享容器。
    Step1 定下的口吻，Step3 根本没地方去找 —— 这就是「漂移」的根。

4 层对应关系：
    第 1 层 任务上下文   add_user() / add_assistant() 往里加（当次用完即丢）
    第 2 层 系统层       AGENTS.md                    —— 人设 + 风格 + 边界
    第 3 层 用户 + 长期  USER.md + MEMORY.md          —— 跨 session 残留
    第 4 层 工具数据     tool 消息（阶段 B 才用，本文件暂不涉及）

用法：
    ctx = ContextSession(Path(__file__).parent)
    ctx.add_user("主题：xxx\\n任务：给出钩子策略和口吻")
    reply = call_llm(ctx.messages)      # 一次调用
    ctx.add_assistant(reply)            # 把模型回话也记进容器
    ctx.add_user("任务：给 3 个候选切入点")
"""

from pathlib import Path


def load_file(path: Path, required: bool = False) -> str:
    """读一个上下文文件。

    required=True  —— 必需文件：缺失或为空都抛异常（这是 bug 信号）
    required=False —— 可选文件：缺失返回空串（首次运行时 MEMORY.md 本来就是空的）
    """
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需上下文文件缺失：{path}")
        return ""

    text = path.read_text(encoding="utf-8").strip()
    if required and not text:
        raise ValueError(f"必需上下文文件是空的：{path}")
    return text



def build_system_message(workdir: Path) -> str:
    """把 3 份上下文文件拼成一条 system 消息的内容。

    顺序有讲究：先规则（AGENTS）、再身份（USER）、最后记忆（MEMORY）。
    模型读 prompt 是从上往下的，越靠前越像「宪法」。
    """
    agents = load_file(workdir / "AGENTS.md", required=True)
    user = load_file(workdir / "USER.md", required=True)
    memory = load_file(workdir / "MEMORY.md")

    parts = [
    "# 系统规则\n" + agents,   # required，必有值，不需要 if
    "# 用户档案\n" + user,     # 同上
    ]
    if memory:
        parts.append("# 长期记忆\n" + memory)
    return "\n\n".join(parts)


class ContextSession:
    """一次任务的上下文会话。

    核心就是一个 self.messages 列表 —— 5 个步骤全程共用这一个容器，
    每步往里加 2 条（模型的输出 + 下一步的任务）。
    """

    def __init__(self, workdir: str, temperature: float = 0.8):
        self.workdir = Path(workdir)
        self.temperature = temperature

        # 第 2 + 3 层：system 消息，整个任务只加一次，每步复用
        self.messages = [
            {"role": "system", "content": build_system_message(self.workdir)}
        ]

    def add_user(self, content: str) -> None:
        """第 1 层：加一条「我要求模型做什么」。"""
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        """第 1 层：把模型这次的回话记进容器，成为下一步的「前文」。"""
        self.messages.append({"role": "assistant", "content": content})

    def stats(self) -> dict:
        """看一眼分层情况 —— 这就是阶段 E「可观测性」的雏形。"""
        counts = {"system": 0, "user": 0, "assistant": 0}
        for m in self.messages:
            counts[m["role"]] = counts.get(m["role"], 0) + 1
        return {
            "总条数": len(self.messages),
            "system": counts["system"],
            "user": counts["user"],
            "assistant": counts["assistant"],
            "system 字符数": len(self.messages[0]["content"]),
        }


if __name__ == "__main__":
    # 模拟一次 3 步的任务流程（不调 LLM，手写假的模型回话）
    ctx = ContextSession(Path(__file__).parent)

    ctx.add_user("主题：一条命令误删了开发者 700GB 数据\n任务：给出钩子策略 + 口吻，2-3 句。")
    ctx.add_assistant("[假回话] 反讽 + 黑色幽默，开头直接甩结论，别铺垫。")

    ctx.add_user("任务：给 3 个候选切入点，选 1 个最优。")
    ctx.add_assistant("[假回话] 最优切入点：AI 替你背锅之前，先删了你的文件。")

    print("=== messages 结构 ===")
    for i, m in enumerate(ctx.messages):
        head = m["content"].split("\n")[0][:46]
        print(f"[{i}] {m['role']:9s} | {head}")

    print("\n=== 分层统计 ===")
    for k, v in ctx.stats().items():
        print(f"{k}: {v}")
