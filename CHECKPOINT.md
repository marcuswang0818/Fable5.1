# 存档点 / Checkpoint — 2026-09-14 07:30 UTC

按用户指示：**已存档并停止**，等用户确认智能体额度重置且充足后再继续。

## 进度

| 阶段 | 子代理 | 状态 | 文件 |
|---|---|---|---|
| 侦察 Scout | 学位规则 / 校历与价格 / 各校强项（3 个） | ✅ | `data/checkpoint/scout.json` |
| 第一轮 Round 1 | SNHU 12 · HES 12 · ASU ULC 42 · UMPI 42 · UCLA 21.334 · BYU 21（6 个） | ✅ | `data/checkpoint/round1_plans.json` |
| 第二轮 #1 | 学位要求审查（14 条发现） | ✅ | `data/checkpoint/round2_reviews.json` |
| 第二轮 #2 | 去重（10 条发现） | ✅ | `data/checkpoint/round2_reviews.json` |
| 第二轮 #3 | 前置课程时间线 + 合并两位审查员的冲突 → **49 行统一课表**（ISO 日期、每门费用、负荷已算） | ✅ | `data/checkpoint/review3.json` |
| 代码核验 | 课程代码 / 校历 / 价格核验（71 次检索，76 项） | ✅ | `data/checkpoint/codecheck.json` |
| 结算 Settle | 合并为最终【时间线-选课名-计学分-总消费】 | ⏸ 启动约 2 分钟后按指示停止（未产出） | — |
| 校验 Verify | 脚本确定性核算 + 学位要求 / 排期 / 价格三镜头 + 修复循环 | ⏹ 未开始 | — |
| 交付 | `data/final_plan.json` → `docs/timeline.md` + `docs/timeline.html` → Artifact 发布 | ⏹ 未开始（工具已就绪、已冒烟测试） | — |

数字（结算前，第二轮 #3 的统一课表）：150.334 学分 · 49 门 · 2026 列表价 $36,104 · 上层学分约 50（稳妥 39）· 2026-08-20 → 2028-07-02（22.4 个月）。
该课表通过了 `tools/normalize_plan.py` 的全部确定性检查（六校学分精确、UMPI 恰三个 session 12/15/15、BYU 每门 ≤15 周、每个开课日负荷 ≤15.3）。

## 代码核验的要点（结算时必须套用，第二轮 #3 尚未套用）

- **UMPI YourPace**：BUS 100 / ECO 208 / MAT 180 / POS 201 不存在；ECO 207 是宏微观合并课；正确代码 BUS 107（商业与经济导论）、BUS 352（商法 I）、BUS 353（商业伦理）、BUS 341（组织行为）、BUS 325（人力资源）、BUS 315（运营与供应链，非 MIS）、BUS 244（MIS，低层）、BUS 343（项目风险与成本，需先修“项目管理导论”）、BUS 359（IT 项目管理）、BUS 489（战略 capstone）；HTY 161/162、PHI 151/152、ENV 110、SOC 100 已确认。
- **UCLA Extension**：不开 MATH XL 32B / 33B / 61 / 115A（数学梯只到 32A/33A）；已确认 4 学分 XL 课：COM SCI XL 31（$1,100）、XL 32（$1,095）、MATH XL 31B、32A、33A（$1,100）、PSYCH XL 10（$950）、ECON XL 1/2、PHYSICS XL 10；XL 33A 与 SNHU MAT-350 同属 ASU MAT 342/343 只计一次。
- **Harvard Extension**：ENVR E-101 已变为研究生 proseminar，须换（首选 ENVR E-102 可再生能源项目设计）；“PHYS E-123”实为 ENSC E-123 实验电子学；CSCI E-45b、GOVT E-1820、PHYS E-1bx 存在。
- **BYU IS**：ENGL 316 现为 WRTG 316；POLI 170 / GEOL 101 / HIST 201/202 / GEOG 120 / PHSCS 105/106 / STAT 121 已确认；PHIL 213、CS 142 不在 IS。
- **ASU**：MAT 342/343 互斥已确认；ASU 101 对转学分 >23 的学生不要求（无需抵课）；TEL 111 为 3 学分；session-based ULC 确有 8 周 A/B 与 16 周 C。

## 恢复方法

**A. 同一会话/容器仍在**（工作流缓存可用）：
```
Workflow({ scriptPath: "/root/.claude/projects/-home-user-Fable5-1/b8e237a9-e57c-586f-b836-a11399d9348a/workflows/scripts/six-school-plan-continue-wf_5e1bd500-f3c.js", resumeFromRunId: "wf_5e1bd500-f3c" })
```
第二轮 #3 与代码核验从缓存命中，直接进入结算。

**B. 新会话/新容器**（以仓库为准）：
```
Workflow({ scriptPath: "/home/user/Fable5.1/tools/workflow_continue_v2.js", args: { round2FromDisk: true } })
```
脚本跳过第二轮子代理，让结算子代理直接读取 `data/checkpoint/review3.json` 与 `codecheck.json`（以及 `digest_*.md`），随后：脚本确定性核算 → 三镜头校验 → 修复循环（最多 4 轮）。预计 1 个结算子代理 20–40 分钟 + 每轮 3 个校验子代理。

**C. 之后**：
```bash
# 把工作流返回的 final 写入 data/final_plan.json（若返回被截断，从 journal.jsonl 取最后一个 settle 结果，再跑：）
python3 tools/normalize_plan.py --in data/final_plan.json --out data/final_plan.json
python3 tools/render_plan.py --data data/final_plan.json --out docs
```
然后用 Artifact 工具发布 `docs/timeline.html`（favicon 建议 📅；发布前先看一眼渲染结果，重点看甘特图），提交并推送。

## 工具

- `tools/workflow_continue_v2.js` — 续跑工作流（含 round2FromDisk 模式；已修复“HES 8 月底开学被误判为暑期”的检查）。
- `tools/normalize_plan.py` — 与工作流脚本等价的确定性核算：按开课日期归入 8 周块、序号、累计列、每块峰值负荷（学分×8/周数）、六校合计、规则检查。
- `tools/render_plan.py` — 渲染 Markdown 与 HTML（甘特图、每块峰值负荷图（上限 15）、堆叠学分图、累计消费图、分块课表、抵课、要求矩阵、Topic Area 映射、80/20、风险、报名前核对清单）。
- `data/checkpoint/digest_1_scouts.md / digest_2_plans.md / digest_3_reviews.md` — 供子代理阅读的存档摘要。

## 已知问题 / 注意

- 第二轮 #3 的统一课表里仍含代码核验判定“不开/不存在”的课（UCLA XL 32B/33B/61、UMPI 多个 BUS 代码、HES ENVR E-101/PHYS E-123），结算子代理必须按 `codecheck.json` 的更正替换。
- 本环境对学校网站的直接抓取被出口代理阻断；所有代码、价格、日期来自搜索摘要，交付文档按 confirmed / likely / assumed 标注置信度并给出备选。
- 本会话 WebSearch 已用约 92 次（三个新子代理），若在本会话续跑，校验镜头仍可检索。
