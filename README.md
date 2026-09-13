# 六校排课 · ASU Online BA in General Studies（爆学分臻享版）

Multi-school course plan for a credit-maxed (150.334 semester credits) ASU Online
Bachelor of Arts in General Studies, themed **Technology & Government** /
**Socio-Technical Systems: Energy & Environment (Power Electronics)**, drawn from six
platforms:

| Platform | Credits | Shape |
|---|---:|---|
| SNHU Online | 12 | 4 × 3-credit, 8-week terms |
| Harvard Extension School | 12 | 3 × 4-credit |
| ASU Universal Learner Courses (session-based) | 42 | 14 × 3-credit, native ASU credit |
| UMPI YourPace | 42 | exactly three 8-week sessions |
| UCLA Extension | 21.334 | 8 × 4 quarter units = 32 qu × 2/3 |
| BYU Independent Study | 21 | 7 × 3-credit, each finished within one semester window |

## Deliverables

- `docs/timeline.md` — 时间线 · 选课名 · 计学分 · 总消费 (GitHub-readable)
- `docs/timeline.html` — the same plan as a standalone page (also published as a Claude artifact)
- `data/final_plan.json` — the settled plan (source of truth for the renderers)
- `data/scout.json`, `data/round1_plans.json`, `data/round2_reviews.json` — intermediate agent output

## Method

1. **Scout** — three agents: ASU General Studies BA rules & transfer policy; 2026–2029 calendars and prices; per-school subject strengths.
2. **Round 1** — six school-specific planners (one per platform) each fill exactly their credit quota, tagging every course with the ASU requirement it serves and an 80/20 strength-vs-savings tag.
3. **Round 2** — three reviewers: degree-requirements audit, duplicate removal, prerequisite timeline.
4. **Settlement** — one synthesizer merges all fixes into a single chronological plan from 2026 Fall A.
5. **Verify** — three adversarial lenses (arithmetic, requirements, schedule feasibility) with a fix loop.

Regenerate the documents after editing the JSON:

```bash
python3 tools/render_plan.py --data data/final_plan.json --out docs
```

Caveat: the agents could only use web-search snippets (direct page fetches are blocked in
the build environment), so every course code, price and date must be re-checked on the
school's own site before enrolling. Rows tagged `assumed` are the least certain.
