"""工具说明书：告诉模型「有哪些工具、什么时候用」。

只放 schema（纯数据），不要 import 任何东西。
真干活的函数住在 read_candidates.py —— 不要复制进来。

为什么不能复制：复制 = 两份真身，改了一份另一份不变，早晚分叉。
B3 的循环文件里会建一张函数表把两边绑起来（靠 name 对应）：

    TOOL_FUNCS = {"read_candidates": read_candidates}
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_candidates",
            "description": "读取候选选题池 candidates.md，当需要知道有哪些选题的时候，列出所有候选选题，排除 tier3。返回一个 list，每条记录是一个 dict。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]
