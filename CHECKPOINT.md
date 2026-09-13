# 存档点 / Checkpoint — 2026-09-13 16:00 UTC

按用户指示：**已存档并停止**，等用户确认智能体额度重置且充足后再继续。

## 已完成（结果已保存在 `data/checkpoint/`）

| 阶段 | 子代理 | 状态 | 文件 |
|---|---|---|---|
| 侦察 Scout | 学位规则 / 校历与价格 / 各校强项（3 个） | ✅ 完成 | `scout.json` |
| 第一轮 Round 1 | SNHU 12 · HES 12 · ASU ULC 42 · UMPI YourPace 42 · UCLA Ext 21.334 · BYU IS 21（6 个） | ✅ 完成，六校学分与费用合计均校验通过 | `round1_plans.json` |
| 第二轮 Round 2 | #1 学位要求审查（14 条发现）· #2 去重（10 条发现） | ✅ 完成 | `round2_reviews.json` |
| 第二轮 Round 2 | #3 前置课程时间线 | ⏸ 运行中被停止（未保存） | — |
| 结算 Settle | 合并为【时间线-选课名-计学分-总消费】 | ⏹ 未开始 | — |
| 校验 Verify | 算术 / 学位要求 / 排期可行性 三镜头 + 修复循环 | ⏹ 未开始 | — |
| 交付 | `docs/timeline.md` + `docs/timeline.html` + Artifact 发布 | ⏹ 未开始（渲染脚本 `tools/render_plan.py` 已就绪） | — |

第一轮六校初稿合计：150.334 学分，约 $36,129（SNHU 4,248 · HES 6,780 · ULC 5,525 · UMPI 5,400 · UCLA 8,800 · BYU 5,376）。
这是**去重与前置排序之前**的数字，结算后会变。

## 恢复方法（下次开始时）

1. 用 Workflow 工具运行 `tools/workflow_continue.js`（`scriptPath`），并把 `data/checkpoint/all.json` 的内容作为 `args` 传入（对象 `{scouts, plans, reviews}`）。
   脚本会自动只补跑缺失的第二轮审查（#3 前置时间线），然后结算、三镜头校验、修复循环。
2. 把返回的 `final` 写入 `data/final_plan.json`，运行：
   ```bash
   python3 tools/render_plan.py --data data/final_plan.json --out docs
   ```
3. 用 Artifact 工具发布 `docs/timeline.html`（favicon 建议 📅），提交并推送。

若容器仍在（同一会话），也可直接 `Workflow({scriptPath: ".../multi-school-course-plan-wf_3e7abfc3-fcc.js", resumeFromRunId: "wf_3e7abfc3-fcc"})`，
已完成的 11 个子代理结果会从缓存命中；但容器回收后该缓存即失效，因此以 `data/checkpoint/` 为准。

## 恢复时需注意的已知问题

- 第二轮审查 #1 报告其会话中 WebSearch 不可用（很可能是额度耗尽的征兆），其结论基于第一轮数据与先验知识；结算前可让校验镜头复核。
- UMPI YourPace 第一轮 14 门中多数课程代码标为 `assumed`（YourPace 目录无法直接抓取）；报名前必须到 UMPI 官网核对。
- UCLA Extension 第 8 门（MATH XL 115A）标为 `assumed`；去重审查 #2 已指出 UCLA 线性代数与 SNHU MAT-350 重叠，结算时需按其建议替换。
- 本环境对学校网站的直接抓取被出口代理阻断，所有课程代码、价格、日期均来自搜索摘要，交付文档中已按 confirmed / likely / assumed 标注置信度。

## 额度说明（本次停止的直接原因之一）

- 第二轮审查 #1 的记录显示：**本会话的 WebSearch 预算已用尽（200/200）**，三个侦察子代理共用了约 227 次检索。
  因此即使容器仍在，本会话内继续跑的子代理也无法再检索；结算与校验阶段本身不依赖检索（只用已保存数据），
  但若希望校验镜头能复核课程代码，应在**新会话**中恢复（新会话有新的检索预算）。
