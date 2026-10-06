"""阶段 E：质量评测（B 路线）—— 规则型检查选题硬伤。"""

from read_candidates import read_candidates

MAX_TITLE = 20   # 判据 1 阈值 —— v0 占位，待用真实播放数据校准（别凭感觉调）

# 判据 2 词表：技术黑话（操作 / 协议 / 概念名）—— 产品名和通用词不算门槛
TERMS = ["Git push", "GitHub", "Function Calling", "API", "RAG", "ACP"]

items = read_candidates()
print("一共", len(items), "条")
print()

bad_len = 0
bad_term = 0
n = 0
for it in items:
    n += 1
    title = it["title"]
    n_char = len(title)

    mark = ""
    if n_char > MAX_TITLE:
        mark = mark + " [!]超长"
        bad_len += 1

    has_term = False
    for w in TERMS:
        if w in title:
            mark = mark + " [" + w + "]"
            has_term = True
    if has_term:
        bad_term += 1

    print(n, "|", n_char, "字 |", it["tier"], "|", title, mark)

print()
print("标题超长：", bad_len, "条")
print("含门槛术语：", bad_term, "条")
print("（共", len(items), "条；一条可能两个都踩）")
