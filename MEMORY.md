# MEMORY.md — 长期记忆

> 本文件是 4 层上下文的「**长期记忆层**」。
> 与前两份的关键区别：`AGENTS.md` / `USER.md` 是**人写、Agent 读**；本文件是 **Agent 自动写**。
> 规则：**只追加，不覆盖**（append-only）。
> 数据源：`cheat-on-content` 的预测 / 复盘记录。本文件存**结论与 pattern**，不存原始数据。

---

## 一、内容台账

每做一条内容追加一行。7 维各 0-5 分，composite 0-10。

| 日期 | 选题 | 平台 | ER | HP | QL | NA | AB | SR | SAT | composite | 实际播放 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| *(示例)* 2026-09-01 | AI 一条命令误删开发者 700GB | 抖音 | | | | | | | | | | 已发 |

> ⚠️ 上行为格式示例，请用真实数据替换。数据以 `cheat-on-content` 的预测文件为准。

---

## 二、rubric 校准状态

| 项 | 值 |
|---|---|
| 当前 rubric 版本 | **v0**（等权，cold-start 占位） |
| composite 公式 | `(ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0` |
| 校准样本数 | N = ___ / 5 |

**7 维含义**（速查）：

| 代码 | 全称 | 一句话 |
|---|---|---|
| ER | Emotional Resonance | 前 30 秒能否让人产生具体可命名的情感 |
| HP | Hook Potential | 前 3 秒能不能逼人看下去 |
| QL | Quotable Lines | 有几句能被截图独立传播 |
| NA | Narrativity | 有没有可辨识的弧线（vs 平铺直叙）|
| AB | Audience Breadth | 议题潜在受众有多广 |
| SR | Social Resonance | 是否触及当下的社会模式 |
| SAT | Satire Depth | 反讽层数（真诚路线给 3 即可）|

**校准阶段决定「能相信什么」**：

| 样本数 | 能相信什么 |
|---|---|
| N = 0-2 | 啥都别信 |
| N = 3-5 | 只信方向，不信 composite 数字 |
| N ≥ 5 | 可以信 bucket 排序 |
| N ≥ 10 | 中枢可信 ±30% |

---

## 三、创作教训（Agent 自动追加，时间倒序）

> 每条格式：`YYYY-MM-DD · 一句教训 · 依据`

*(暂无)*

---

## 四、待复用素材

> 跑出来但当时没用上的角度 / 钩子 / 标题，留着下次用。

*(暂无)*

---

## 五、Agent 自检清单

每次任务结束时自查：

- [ ] 是否产出完整 5 字段 JSON（`title` / `hook` / `script` / `image_prompts` / `hashtags`）
- [ ] 五件产出是否风格一致（无漂移）
- [ ] `script` 是否 ≤ 200 字
- [ ] 是否有新条目要追加到本文件

---

## 版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1 | 2026-09-14 | 初版。结构对齐 cheat-on-content 的 7 维 rubric + cold-start 阶段说明 |
