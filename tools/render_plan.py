#!/usr/bin/env python3
"""Render the settled six-school course plan (data/final_plan.json) into
docs/timeline.md (GitHub-flavored Markdown) and docs/timeline.html (standalone page).

Usage: python3 tools/render_plan.py [--data data/final_plan.json] [--out docs]
"""
import argparse, html, json, os, re, datetime
from collections import OrderedDict, defaultdict

# Fixed categorical order (validated adjacent-pair palette; light / dark steps).
SCHOOL_ORDER = ["ASU ULC", "UMPI YourPace", "UCLA Extension", "BYU IS", "Harvard Extension", "SNHU"]
SCHOOL_COLORS = {
    "ASU ULC":           ("#2a78d6", "#3987e5"),
    "UMPI YourPace":     ("#eb6834", "#d95926"),
    "UCLA Extension":    ("#1baf7a", "#199e70"),
    "BYU IS":            ("#eda100", "#c98500"),
    "Harvard Extension": ("#e87ba4", "#d55181"),
    "SNHU":              ("#008300", "#008300"),
}
SCHOOL_ZH = {
    "ASU ULC": "亚利桑那州立大学 ULC（校内学分）",
    "UMPI YourPace": "缅因大学普雷斯克岛分校 YourPace（能力本位）",
    "UCLA Extension": "加州大学洛杉矶分校推广部",
    "BYU IS": "杨百翰大学独立学习",
    "Harvard Extension": "哈佛大学推广学院",
    "SNHU": "南新罕布什尔大学在线",
}
ALIASES = [
    (r"asu|universal learner|ulc", "ASU ULC"),
    (r"umpi|presque|yourpace", "UMPI YourPace"),
    (r"ucla", "UCLA Extension"),
    (r"byu|brigham", "BYU IS"),
    (r"harvard|hes", "Harvard Extension"),
    (r"snhu|southern new hampshire", "SNHU"),
]

def canon(school):
    s = (school or "").lower()
    for pat, name in ALIASES:
        if re.search(pat, s):
            return name
    return school or "?"

def fmt_cr(x):
    try:
        x = float(x)
    except Exception:
        return str(x)
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x))}"
    return f"{x:.3f}".rstrip("0").rstrip(".") if abs(x*1000 - round(x*1000)) < 1e-6 else f"{x:.3f}"

def fmt_usd(x):
    try:
        return f"${float(x):,.0f}"
    except Exception:
        return str(x)

def esc(s):
    return html.escape(str(s if s is not None else ""))

def md_table_to_html(md):
    """Convert a GitHub pipe table (possibly with surrounding prose) into HTML."""
    if not md:
        return ""
    out, rows, in_tbl = [], [], False
    def flush():
        nonlocal rows
        if not rows:
            return
        head, body = rows[0], rows[1:]
        h = "<table class=\"matrix\"><thead><tr>" + "".join(f"<th>{esc(c)}</th>" for c in head) + "</tr></thead><tbody>"
        for r in body:
            r = r + [""] * (len(head) - len(r))
            h += "<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r[:len(head)]) + "</tr>"
        out.append(h + "</tbody></table>")
        rows = []
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            rows.append(cells)
        else:
            flush()
            if s:
                out.append(f"<p>{esc(s)}</p>")
    flush()
    return "\n".join(out)

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def group_terms(entries):
    terms = OrderedDict()
    for e in entries:
        key = e.get("term_label", "?")
        if key not in terms:
            terms[key] = {"label": key, "start": e.get("start", ""), "end": e.get("end", ""), "rows": []}
        terms[key]["rows"].append(e)
    return terms

# ----------------------------------------------------------------------------
# Markdown
# ----------------------------------------------------------------------------
def render_md(plan, meta):
    t = plan["totals"]
    entries = sorted(plan["entries"], key=lambda e: e.get("seq", 0))
    terms = group_terms(entries)
    L = []
    L.append("# 六校 150.334 学分 · ASU Online BA in General Studies · 结算版时间线\n")
    L.append(f"> 生成日期 {meta['date']} · 主题：Technology & Government / Socio-Technical Systems: Energy & Environment（Power Electronics）· 起点 2026 秋 A（ULC 已在读）\n")
    L.append("")
    L.append("| 总学分 | 上层（300+）学分 | 总消费 | 起止 | 时长 | 均价 |")
    L.append("|---:|---:|---:|:--|:--|---:|")
    months = t.get("months", "")
    per_cr = float(t["cost_usd"]) / float(t["credits"]) if float(t.get("credits", 0)) else 0
    L.append(f"| **{fmt_cr(t['credits'])}** | {fmt_cr(t.get('upper_division_credits', ''))} | **{fmt_usd(t['cost_usd'])}** | {t.get('first_term','')} → {t.get('last_term','')} | {months} 个月 | {fmt_usd(per_cr)}/学分 |")
    L.append("")
    L.append("## 六校分摊（学校 · 门数 · 学分 · 消费 · 每学分）\n")
    L.append("| 学校 | 门数 | 学分 | 消费 | 每学分 |")
    L.append("|:--|---:|---:|---:|---:|")
    for s in plan.get("per_school_totals", []):
        pc = s.get("per_credit_usd") or (float(s["cost_usd"]) / float(s["credits"]) if float(s.get("credits", 0)) else 0)
        L.append(f"| {canon(s['school'])} | {s.get('courses','')} | {fmt_cr(s['credits'])} | {fmt_usd(s['cost_usd'])} | {fmt_usd(pc)} |")
    L.append("")
    L.append("## 时间线 · 选课名 · 计学分 · 总消费\n")
    L.append("| # | 时间线 | 学校 | 代码 | 选课名 | 计学分 | 层级 | 满足要求 | 前置由 | 费用 | 累计学分 | 累计消费 |")
    L.append("|---:|:--|:--|:--|:--|---:|:--|:--|:--|---:|---:|---:|")
    for term in terms.values():
        blk_cr = sum(float(r.get("credits_counted", 0)) for r in term["rows"])
        blk_cost = sum(float(r.get("cost_usd", 0)) for r in term["rows"])
        L.append(f"| | **{term['label']}** {term['start']} → {term['end']} | | | *本块 {fmt_cr(blk_cr)} 学分 · {fmt_usd(blk_cost)}* | | | | | | | |")
        for r in term["rows"]:
            title = r.get("title", "")
            if r.get("title_zh"):
                title += f"<br>{r['title_zh']}"
            L.append("| {seq} | {term} | {school} | `{code}` | {title} | {cr} | {lvl} | {req} | {pre} | {cost} | {ccr} | {ccost} |".format(
                seq=r.get("seq", ""), term=f"{r.get('start','')}→{r.get('end','')}", school=canon(r.get("school")),
                code=r.get("code", ""), title=title, cr=fmt_cr(r.get("credits_counted", 0)), lvl=r.get("level", ""),
                req=r.get("requirement_bucket", ""), pre=r.get("prereqs_satisfied_by", "") or "—",
                cost=fmt_usd(r.get("cost_usd", 0)), ccr=fmt_cr(r.get("cumulative_credits", 0)), ccost=fmt_usd(r.get("cumulative_cost_usd", 0))))
    L.append("")
    L.append("## 每个学期块的负荷\n")
    L.append("| 时间块 | 起止 | 门数 | 学分 | 消费 | 学校 |")
    L.append("|:--|:--|---:|---:|---:|:--|")
    for b in plan.get("per_term_load", []):
        L.append(f"| {b.get('term_label','')} | {b.get('start','')} → {b.get('end','')} | {b.get('courses','')} | {fmt_cr(b.get('credits',0))} | {fmt_usd(b.get('cost_usd',0))} | {b.get('schools','')} |")
    L.append("")
    L.append("## ASU 101 / IDS 321 / IDS 402 抵课方案\n")
    for s in plan.get("substitutions", []):
        L.append(f"- **{s['asu_course']}** ← {s['substitute']} — {s['justification']}")
    L.append("")
    L.append("## 学位要求对照矩阵（ASU BA in General Studies, General Studies Gold）\n")
    L.append(plan.get("requirement_matrix", ""))
    L.append("")
    L.append("## 假设\n")
    for a in plan.get("assumptions", []):
        L.append(f"- {a}")
    L.append("")
    L.append("## 风险与注意\n")
    for r in plan.get("risks", []):
        L.append(f"- {r}")
    if plan.get("verifier_minor_notes"):
        L.append("")
        L.append("### 校验员次要备注\n")
        for n in plan["verifier_minor_notes"]:
            L.append(f"- {n}")
    if plan.get("unresolved_blocking"):
        L.append("")
        L.append("### ⚠ 未解决的阻断问题\n")
        for n in plan["unresolved_blocking"]:
            L.append(f"- {n}")
    L.append("")
    L.append("## 学位概述\n")
    L.append(plan.get("degree_summary", ""))
    L.append("")
    if plan.get("sources"):
        L.append("## 来源\n")
        for s in plan["sources"]:
            L.append(f"- {s}")
    L.append("")
    L.append("---")
    L.append(f"方法：侦察（学位规则 / 校历与价格 / 各校强项）→ 第一轮六个学校子代理 → 第二轮三个审查子代理（学位要求 / 去重 / 前置时间线）→ 结算 → 三个对抗校验镜头（算术 / 学位要求 / 排期可行性）{plan.get('verify_rounds','')} 轮。本环境无法直接抓取学校网页（仅搜索摘要），所有课程代码、价格、日期均需在报名前到官网复核。")
    return "\n".join(L)

# ----------------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------------
def svg_stacked_load(terms_load, entries):
    """Per-term credit load stacked by school. Returns SVG string + legend order."""
    # Build per-term per-school credits from entries (authoritative)
    order = []
    per = OrderedDict()
    for e in sorted(entries, key=lambda e: e.get("seq", 0)):
        k = e.get("term_label", "?")
        if k not in per:
            per[k] = defaultdict(float); order.append(k)
        per[k][canon(e.get("school"))] += float(e.get("credits_counted", 0))
    n = len(order)
    if n == 0:
        return ""
    W, H = max(640, 56 * n + 80), 300
    padL, padR, padT, padB = 44, 12, 18, 70
    maxv = max(sum(v.values()) for v in per.values()) or 1
    top = int((maxv // 3 + 1) * 3)
    plotH = H - padT - padB
    plotW = W - padL - padR
    bw = plotW / n
    bar = min(34, bw * 0.62)
    def y(v): return padT + plotH - (v / top) * plotH
    s = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="每个学期块的学分负荷，按学校堆叠">']
    # grid
    for g in range(0, top + 1, 3):
        yy = y(g)
        s.append(f'<line x1="{padL}" x2="{W-padR}" y1="{yy:.1f}" y2="{yy:.1f}" class="grid"/>')
        s.append(f'<text x="{padL-6}" y="{yy+4:.1f}" class="tick" text-anchor="end">{g}</text>')
    s.append(f'<line x1="{padL}" x2="{W-padR}" y1="{y(0):.1f}" y2="{y(0):.1f}" class="axis"/>')
    for i, k in enumerate(order):
        x0 = padL + i * bw + (bw - bar) / 2
        acc = 0.0
        segs = []
        for sc in SCHOOL_ORDER:
            v = per[k].get(sc, 0)
            if v <= 0: continue
            y1, y0 = y(acc), y(acc + v)
            h = max(0, y1 - y0 - 2)
            segs.append(f'<rect x="{x0:.1f}" y="{y0+1:.1f}" width="{bar:.1f}" height="{h:.1f}" rx="2" fill="var(--c-{slug(sc)})"><title>{esc(k)} · {esc(sc)} · {fmt_cr(v)} 学分</title></rect>')
            acc += v
        s.extend(segs)
        s.append(f'<text x="{x0+bar/2:.1f}" y="{y(acc)-5:.1f}" class="val" text-anchor="middle">{fmt_cr(acc)}</text>')
        lab = re.sub(r"\s*\(.*?\)\s*", " ", k).strip()
        s.append(f'<text x="{x0+bar/2:.1f}" y="{H-padB+16}" class="tick" text-anchor="end" transform="rotate(-38 {x0+bar/2:.1f} {H-padB+16})">{esc(lab)}</text>')
    s.append("</svg>")
    return "\n".join(s)

def svg_cumulative(entries, key, label, fmt):
    pts = []
    for e in sorted(entries, key=lambda e: e.get("seq", 0)):
        pts.append((e.get("term_label", "?"), float(e.get(key, 0))))
    if not pts:
        return ""
    # collapse to per-term last value
    per = OrderedDict()
    for k, v in pts:
        per[k] = v
    ks = list(per.keys()); vs = list(per.values())
    n = len(ks)
    W, H = max(640, 56 * n + 80), 300
    padL, padR, padT, padB = 62, 14, 18, 70
    maxv = max(vs) or 1
    plotH, plotW = H - padT - padB, W - padL - padR
    def x(i): return padL + (i + 0.5) * plotW / n
    def y(v): return padT + plotH - (v / maxv) * plotH
    s = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">']
    steps = 4
    for g in range(steps + 1):
        v = maxv * g / steps
        s.append(f'<line x1="{padL}" x2="{W-padR}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/>')
        s.append(f'<text x="{padL-6}" y="{y(v)+4:.1f}" class="tick" text-anchor="end">{fmt(v)}</text>')
    path = " ".join(("M" if i == 0 else "L") + f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vs))
    area = path + f" L{x(n-1):.1f},{y(0):.1f} L{x(0):.1f},{y(0):.1f} Z"
    s.append(f'<path d="{area}" class="area"/>')
    s.append(f'<path d="{path}" class="line"/>')
    for i, v in enumerate(vs):
        s.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="4" class="dot"><title>{esc(ks[i])} · {fmt(v)}</title></circle>')
        lab = re.sub(r"\s*\(.*?\)\s*", " ", ks[i]).strip()
        s.append(f'<text x="{x(i):.1f}" y="{H-padB+16}" class="tick" text-anchor="end" transform="rotate(-38 {x(i):.1f} {H-padB+16})">{esc(lab)}</text>')
    s.append(f'<text x="{x(n-1)+2:.1f}" y="{y(vs[-1])-10:.1f}" class="val" text-anchor="end">{fmt(vs[-1])}</text>')
    s.append("</svg>")
    return "\n".join(s)

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def render_html(plan, meta):
    t = plan["totals"]
    entries = sorted(plan["entries"], key=lambda e: e.get("seq", 0))
    terms = group_terms(entries)
    per_cr = float(t["cost_usd"]) / float(t["credits"]) if float(t.get("credits", 0)) else 0
    school_css = "\n".join(f"  --c-{slug(k)}: {v[0]};" for k, v in SCHOOL_COLORS.items())
    school_css_dark = "\n".join(f"    --c-{slug(k)}: {v[1]};" for k, v in SCHOOL_COLORS.items())

    # school cards
    cards = []
    by_school = {canon(s["school"]): s for s in plan.get("per_school_totals", [])}
    for sc in SCHOOL_ORDER:
        s = by_school.get(sc, {})
        cr = float(s.get("credits", 0)); cost = float(s.get("cost_usd", 0))
        pc = s.get("per_credit_usd") or (cost / cr if cr else 0)
        cards.append(f'''<li class="school"><span class="chip" style="background:var(--c-{slug(sc)})"></span>
      <div><div class="s-name">{esc(sc)}</div><div class="s-zh">{esc(SCHOOL_ZH.get(sc, ""))}</div></div>
      <dl><div><dt>门</dt><dd>{esc(s.get("courses", "–"))}</dd></div><div><dt>学分</dt><dd>{fmt_cr(cr)}</dd></div><div><dt>消费</dt><dd>{fmt_usd(cost)}</dd></div><div><dt>每学分</dt><dd>{fmt_usd(pc)}</dd></div></dl></li>''')

    # timeline rows
    rows = []
    for ti, term in enumerate(terms.values(), 1):
        blk_cr = sum(float(r.get("credits_counted", 0)) for r in term["rows"])
        blk_cost = sum(float(r.get("cost_usd", 0)) for r in term["rows"])
        last = term["rows"][-1]
        rows.append(f'''<tr class="term"><th colspan="12"><span class="t-label">{esc(term["label"])}</span><span class="t-dates">{esc(term["start"])} → {esc(term["end"])}</span><span class="t-sum">本块 {fmt_cr(blk_cr)} 学分 · {fmt_usd(blk_cost)}</span><span class="t-cum">累计 {fmt_cr(last.get("cumulative_credits", 0))} 学分 · {fmt_usd(last.get("cumulative_cost_usd", 0))}</span></th></tr>''')
        for r in term["rows"]:
            sc = canon(r.get("school"))
            conf = (r.get("confidence") or "").lower()
            conf_cls = "conf-" + ("c" if conf.startswith("conf") else "l" if conf.startswith("lik") else "a" if conf else "n")
            rows.append(f'''<tr class="{conf_cls}">
  <td class="num">{esc(r.get("seq", ""))}</td>
  <td class="school-cell"><span class="chip" style="background:var(--c-{slug(sc)})"></span>{esc(sc)}</td>
  <td class="code">{esc(r.get("code", ""))}</td>
  <td class="title"><span class="en">{esc(r.get("title", ""))}</span>{('<span class="zh">' + esc(r.get("title_zh")) + '</span>') if r.get("title_zh") else ''}{('<span class="note">' + esc(r.get("note")) + '</span>') if r.get("note") else ''}</td>
  <td class="num">{fmt_cr(r.get("credits_counted", 0))}</td>
  <td class="lvl"><span class="pill {esc(r.get("level", ""))}">{esc({"upper": "上层", "lower": "下层"}.get(r.get("level", ""), r.get("level", "")))}</span></td>
  <td class="req">{esc(r.get("requirement_bucket", ""))}{('<span class="theme">' + esc(r.get("cluster_or_theme")) + '</span>') if r.get("cluster_or_theme") else ''}</td>
  <td class="pre">{esc(r.get("prereqs_satisfied_by") or "—")}</td>
  <td class="num">{fmt_usd(r.get("cost_usd", 0))}</td>
  <td class="num cum">{fmt_cr(r.get("cumulative_credits", 0))}</td>
  <td class="num cum">{fmt_usd(r.get("cumulative_cost_usd", 0))}</td>
  <td class="conf">{esc(r.get("confidence", ""))}</td>
</tr>''')

    subs = "".join(f'<li><b>{esc(s["asu_course"])}</b> <span class="arrow">←</span> {esc(s["substitute"])}<p>{esc(s["justification"])}</p></li>' for s in plan.get("substitutions", []))
    assumptions = "".join(f"<li>{esc(a)}</li>" for a in plan.get("assumptions", []))
    risks = "".join(f"<li>{esc(a)}</li>" for a in plan.get("risks", []))
    minor = "".join(f"<li>{esc(a)}</li>" for a in plan.get("verifier_minor_notes", []) or [])
    unresolved = "".join(f"<li>{esc(a)}</li>" for a in plan.get("unresolved_blocking", []) or [])
    sources = "".join(f"<li>{esc(a)}</li>" for a in plan.get("sources", []) or [])
    legend = "".join(f'<span class="lg"><span class="chip" style="background:var(--c-{slug(sc)})"></span>{esc(sc)}</span>' for sc in SCHOOL_ORDER)
    load_rows = "".join(f'<tr><td>{esc(b.get("term_label",""))}</td><td>{esc(b.get("start",""))} → {esc(b.get("end",""))}</td><td class="num">{esc(b.get("courses",""))}</td><td class="num">{fmt_cr(b.get("credits",0))}</td><td class="num">{fmt_usd(b.get("cost_usd",0))}</td><td>{esc(b.get("schools",""))}</td></tr>' for b in plan.get("per_term_load", []))

    page = f'''<title>六校排课结算版</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=JetBrains+Mono:wght@400;600&family=Noto+Sans+SC:wght@400;500;700&display=swap">
<style>
:root {{
  color-scheme: light;
  --bg: #f4f6f8; --surface: #ffffff; --surface-2: #eef1f5;
  --ink: #151a21; --ink-2: #4b5563; --muted: #8a919b; --hair: #dfe3e9; --hair-2: #c9cfd8;
  --accent: #2b3a67; --accent-soft: #e6eaf6; --accent-ink: #1f2b4d;
  --good: #0ca30c; --warn: #fab219; --crit: #d03b3b;
{school_css}
  --font-display: "Archivo", "Noto Sans SC", system-ui, sans-serif;
  --font-body: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme: dark;
    --bg: #0f1114; --surface: #171a1f; --surface-2: #1f232a;
    --ink: #f1f3f6; --ink-2: #b6bdc7; --muted: #8a919b; --hair: #2a2f37; --hair-2: #3a4049;
    --accent: #9fb0e8; --accent-soft: #232a42; --accent-ink: #c7d2f5;
{school_css_dark}
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --bg: #0f1114; --surface: #171a1f; --surface-2: #1f232a;
  --ink: #f1f3f6; --ink-2: #b6bdc7; --muted: #8a919b; --hair: #2a2f37; --hair-2: #3a4049;
  --accent: #9fb0e8; --accent-soft: #232a42; --accent-ink: #c7d2f5;
{school_css_dark}
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: var(--font-body); font-size: 14px; line-height: 1.55; padding-inline: clamp(16px, 4vw, 48px); padding-block: 28px 64px; }}
.wrap {{ max-width: 1280px; margin: 0 auto; display: grid; gap: 28px; }}
header.hero {{ display: grid; gap: 10px; }}
.eyebrow {{ font-family: var(--font-display); font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--accent); font-weight: 600; }}
h1 {{ font-family: var(--font-display); font-size: clamp(24px, 3.4vw, 38px); line-height: 1.15; margin: 0; text-wrap: balance; font-weight: 700; letter-spacing: -.01em; }}
h1 .en {{ display: block; font-size: .55em; font-weight: 500; color: var(--ink-2); margin-top: 6px; letter-spacing: 0; }}
.sub {{ color: var(--ink-2); max-width: 70ch; margin: 0; }}
h2 {{ font-family: var(--font-display); font-size: 18px; margin: 0 0 12px; font-weight: 600; letter-spacing: .01em; display: flex; align-items: baseline; gap: 10px; }}
h2 small {{ font-family: var(--font-body); font-weight: 400; color: var(--muted); font-size: 12px; }}
section {{ display: grid; gap: 4px; }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }}
.kpi {{ background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; padding: 14px 16px; display: grid; gap: 2px; }}
.kpi dt {{ font-size: 12px; color: var(--muted); letter-spacing: .06em; }}
.kpi dd {{ margin: 0; font-family: var(--font-display); font-size: 28px; font-weight: 600; line-height: 1.1; }}
.kpi dd small {{ font-size: 13px; font-weight: 500; color: var(--ink-2); margin-left: 4px; font-family: var(--font-body); }}
.kpi.primary {{ border-color: var(--accent); background: var(--accent-soft); }}
.kpi.primary dd {{ color: var(--accent-ink); }}
ul.schools {{ list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px; }}
.school {{ display: grid; grid-template-columns: 10px 1fr auto; gap: 12px; align-items: center; background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; padding: 12px 14px; }}
.school .chip {{ width: 10px; height: 38px; border-radius: 3px; display: block; }}
.s-name {{ font-family: var(--font-display); font-weight: 600; }}
.s-zh {{ color: var(--muted); font-size: 12px; }}
.school dl {{ margin: 0; display: grid; grid-auto-flow: column; gap: 14px; }}
.school dl div {{ display: grid; text-align: right; }}
.school dt {{ font-size: 11px; color: var(--muted); }}
.school dd {{ margin: 0; font-family: var(--font-mono); font-variant-numeric: tabular-nums; font-size: 13px; }}
.charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }}
figure {{ margin: 0; background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; padding: 14px 14px 10px; display: grid; gap: 6px; }}
figcaption {{ font-family: var(--font-display); font-weight: 600; font-size: 13px; color: var(--ink-2); display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 12px; font-size: 12px; color: var(--ink-2); font-weight: 400; }}
.lg {{ display: inline-flex; align-items: center; gap: 6px; }}
.lg .chip {{ width: 10px; height: 10px; border-radius: 2px; display: inline-block; }}
svg.chart {{ width: 100%; height: auto; display: block; font-family: var(--font-mono); }}
svg .grid {{ stroke: var(--hair); stroke-width: 1; }}
svg .axis {{ stroke: var(--hair-2); stroke-width: 1; }}
svg .tick {{ fill: var(--muted); font-size: 10.5px; }}
svg .val {{ fill: var(--ink-2); font-size: 11px; font-weight: 600; }}
svg .line {{ fill: none; stroke: var(--accent); stroke-width: 2; stroke-linejoin: round; }}
svg .area {{ fill: var(--accent); opacity: .10; }}
svg .dot {{ fill: var(--accent); stroke: var(--surface); stroke-width: 2; }}
svg rect:hover, svg .dot:hover {{ opacity: .8; }}
.tablewrap {{ overflow-x: auto; background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; }}
table {{ border-collapse: collapse; width: 100%; min-width: 1120px; font-size: 13px; }}
thead th {{ position: sticky; top: 0; background: var(--surface-2); color: var(--ink-2); font-weight: 600; text-align: left; padding: 10px 10px; border-bottom: 1px solid var(--hair-2); font-size: 12px; letter-spacing: .04em; white-space: nowrap; z-index: 1; }}
thead th.num {{ text-align: right; }}
td {{ padding: 9px 10px; border-bottom: 1px solid var(--hair); vertical-align: top; }}
td.num {{ text-align: right; font-family: var(--font-mono); font-variant-numeric: tabular-nums; white-space: nowrap; }}
td.cum {{ color: var(--ink-2); }}
td.code {{ font-family: var(--font-mono); font-weight: 600; white-space: nowrap; }}
td.school-cell {{ white-space: nowrap; }}
td .chip {{ display: inline-block; width: 8px; height: 14px; border-radius: 2px; vertical-align: -2px; margin-right: 7px; }}
td.title .en {{ display: block; font-weight: 500; }}
td.title .zh {{ display: block; color: var(--ink-2); font-size: 12px; }}
td.title .note {{ display: block; color: var(--muted); font-size: 11.5px; margin-top: 2px; }}
td.req {{ max-width: 220px; }}
td.req .theme {{ display: block; color: var(--muted); font-size: 11.5px; }}
td.pre {{ color: var(--ink-2); font-size: 12px; max-width: 200px; }}
td.conf {{ color: var(--muted); font-size: 11px; white-space: nowrap; }}
tr.conf-a td.conf {{ color: var(--crit); }}
.pill {{ display: inline-block; font-size: 11px; padding: 1px 7px; border-radius: 999px; border: 1px solid var(--hair-2); color: var(--ink-2); white-space: nowrap; }}
.pill.upper {{ background: var(--accent-soft); color: var(--accent-ink); border-color: transparent; }}
tr.term th {{ background: var(--surface-2); text-align: left; padding: 10px 10px; border-top: 2px solid var(--hair-2); border-bottom: 1px solid var(--hair); font-weight: 500; }}
tr.term th span {{ margin-right: 18px; }}
.t-label {{ font-family: var(--font-display); font-weight: 700; color: var(--accent-ink); font-size: 14px; }}
.t-dates {{ color: var(--ink-2); font-family: var(--font-mono); font-size: 12px; }}
.t-sum, .t-cum {{ color: var(--ink-2); font-size: 12px; }}
.t-cum {{ color: var(--muted); }}
table.matrix, table.load {{ min-width: 0; }}
table.matrix th, table.load th {{ position: static; }}
.two {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }}
.panel {{ background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; padding: 14px 16px; }}
.panel ul, .panel ol {{ margin: 0; padding-left: 18px; display: grid; gap: 6px; }}
.panel li p {{ margin: 2px 0 0; color: var(--ink-2); font-size: 12.5px; }}
.arrow {{ color: var(--muted); margin: 0 4px; }}
.warn {{ border-color: var(--crit); }}
footer {{ color: var(--muted); font-size: 12px; max-width: 90ch; border-top: 1px solid var(--hair); padding-top: 14px; }}
:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
@media (max-width: 640px) {{ .school {{ grid-template-columns: 10px 1fr; }} .school dl {{ grid-column: 2; grid-auto-flow: row; grid-template-columns: repeat(4, 1fr); }} .school dl div {{ text-align: left; }} }}
@media (prefers-reduced-motion: no-preference) {{ svg rect, svg .dot {{ transition: opacity .15s; }} }}
</style>
<div class="wrap">
<header class="hero">
  <div class="eyebrow">排课 · 结算版 · 爆学分臻享版 · {esc(meta["date"])}</div>
  <h1>六校 150.334 学分时间线<span class="en">ASU Online BA in General Studies · Technology &amp; Government / Socio-Technical Systems: Energy &amp; Environment (Power Electronics)</span></h1>
  <p class="sub">从 2026 秋 A（ULC 已在读）起，SNHU 12 · Harvard Extension 12 · ASU ULC 42 · UMPI YourPace 42（三个 8 周 session）· UCLA Extension 21.334（32 quarter units）· BYU IS 21（每门一学期内完成）。80% 取各校强项，20% 外校省钱；忽略 ASU 30 学分驻校要求；ASU 101 / IDS 321 / IDS 402 以六校课程抵替。</p>
</header>

<section>
  <dl class="kpis">
    <div class="kpi primary"><dt>总学分 · 计入</dt><dd>{fmt_cr(t["credits"])}</dd></div>
    <div class="kpi primary"><dt>总消费 · USD</dt><dd>{fmt_usd(t["cost_usd"])}</dd></div>
    <div class="kpi"><dt>上层（300+）学分</dt><dd>{fmt_cr(t.get("upper_division_credits", ""))}<small>/ 需 ≥45</small></dd></div>
    <div class="kpi"><dt>起 → 止</dt><dd style="font-size:17px">{esc(t.get("first_term",""))}<br>{esc(t.get("last_term",""))}</dd></div>
    <div class="kpi"><dt>时长</dt><dd>{esc(t.get("months",""))}<small>个月</small></dd></div>
    <div class="kpi"><dt>每学分均价</dt><dd>{fmt_usd(per_cr)}</dd></div>
  </dl>
</section>

<section>
  <h2>六校分摊 <small>门数 · 学分 · 消费 · 每学分</small></h2>
  <ul class="schools">{"".join(cards)}</ul>
</section>

<section>
  <h2>负荷与累计 <small>每个学期块的学分（按学校堆叠）· 累计消费</small></h2>
  <div class="charts">
    <figure><figcaption>每块学分负荷 <span class="legend">{legend}</span></figcaption>{svg_stacked_load(plan.get("per_term_load", []), entries)}</figure>
    <figure><figcaption>累计消费（USD）</figcaption>{svg_cumulative(entries, "cumulative_cost_usd", "累计消费", fmt_usd)}</figure>
  </div>
</section>

<section>
  <h2>时间线 · 选课名 · 计学分 · 总消费 <small>按学期块分组；累计列为逐行滚动合计</small></h2>
  <div class="tablewrap">
  <table>
    <thead><tr><th class="num">#</th><th>学校</th><th>代码</th><th>选课名</th><th class="num">计学分</th><th>层级</th><th>满足要求</th><th>前置由</th><th class="num">费用</th><th class="num">累计学分</th><th class="num">累计消费</th><th>置信</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
  </div>
</section>

<section>
  <h2>每个学期块的负荷 <small>门数 · 学分 · 消费</small></h2>
  <div class="tablewrap"><table class="load"><thead><tr><th>时间块</th><th>起止</th><th class="num">门数</th><th class="num">学分</th><th class="num">消费</th><th>学校</th></tr></thead><tbody>{load_rows}</tbody></table></div>
</section>

<section class="two">
  <div class="panel"><h2>ASU 101 / IDS 321 / IDS 402 抵课</h2><ul>{subs}</ul></div>
  <div class="panel"><h2>假设</h2><ul>{assumptions}</ul></div>
</section>

<section>
  <h2>学位要求对照 <small>ASU BA in General Studies · General Studies Gold · 四个 cluster</small></h2>
  <div class="tablewrap" style="padding:8px 12px">{md_table_to_html(plan.get("requirement_matrix", ""))}</div>
  <p class="sub" style="margin-top:8px">{esc(plan.get("degree_summary", ""))}</p>
</section>

<section class="two">
  <div class="panel"><h2>风险与注意</h2><ul>{risks}</ul></div>
  <div class="panel{' warn' if unresolved else ''}"><h2>校验备注 <small>{esc(plan.get("verify_rounds",""))} 轮对抗校验</small></h2>{('<b>未解决的阻断问题</b><ul>' + unresolved + '</ul>') if unresolved else ''}<ul>{minor or "<li>无</li>"}</ul></div>
</section>

<section class="panel"><h2>来源</h2><ul>{sources or "<li>见 data/*.json</li>"}</ul></section>

<footer>方法：侦察（学位规则 / 校历与价格 / 各校强项）→ 第一轮六个学校子代理 → 第二轮三个审查子代理（学位要求 / 去重 / 前置时间线）→ 结算 → 三个对抗校验镜头（算术 / 学位要求 / 排期可行性）。本环境无法直接抓取学校网页（仅搜索摘要），所有课程代码、价格、日期均需在报名前到官网复核；标为 assumed 的行以红色置信标出。</footer>
</div>
'''
    return page

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/final_plan.json")
    ap.add_argument("--out", default="docs")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args()
    plan = load(a.data)
    meta = {"date": a.date}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "timeline.md"), "w", encoding="utf-8") as f:
        f.write(render_md(plan, meta))
    with open(os.path.join(a.out, "timeline.html"), "w", encoding="utf-8") as f:
        f.write(render_html(plan, meta))
    print("wrote", os.path.join(a.out, "timeline.md"), os.path.join(a.out, "timeline.html"))

if __name__ == "__main__":
    main()
