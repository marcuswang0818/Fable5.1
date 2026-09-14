#!/usr/bin/env python3
"""Render the settled six-school course plan (data/final_plan.json) into
docs/timeline.md (GitHub-flavored Markdown) and docs/timeline.html (standalone page).

The plan JSON is expected to be normalized first (tools/normalize_plan.py or the
workflow's normalize()): entries carry seq, term_label, block_start/end, ISO
start/end, cumulative columns and load_8wk_at_start; per_term_load carries
peak_load_8wk.

Usage: python3 tools/render_plan.py [--data data/final_plan.json] [--out docs] [--date YYYY-MM-DD]
"""
import argparse, datetime, html, json, os, re
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
SCHOOL_SHORT = {"ASU ULC": "ULC", "UMPI YourPace": "UMPI", "UCLA Extension": "UCLA", "BYU IS": "BYU", "Harvard Extension": "HES", "SNHU": "SNHU"}
ALIASES = [
    (r"snhu|southern new hampshire", "SNHU"),
    (r"harvard|\bhes\b", "Harvard Extension"),
    (r"umpi|presque|yourpace", "UMPI YourPace"),
    (r"ucla", "UCLA Extension"),
    (r"byu|brigham", "BYU IS"),
    (r"asu|universal learner|ulc", "ASU ULC"),
]
TODAY = "2026-09-14"


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
    return f"{x:.3f}".rstrip("0").rstrip(".")


def fmt_usd(x):
    try:
        return f"${float(x):,.0f}"
    except Exception:
        return str(x)


def esc(s):
    return html.escape(str(s if s is not None else ""))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def md_inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def md_to_html(md):
    """Small Markdown subset: pipe tables, bullet lists, headings, paragraphs."""
    if not md:
        return ""
    out, rows, items = [], [], []

    def flush_table():
        nonlocal rows
        if not rows:
            return
        head, body = rows[0], rows[1:]
        h = "<table class=\"matrix\"><thead><tr>" + "".join(f"<th>{md_inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
        for r in body:
            r = r + [""] * (len(head) - len(r))
            h += "<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in r[:len(head)]) + "</tr>"
        out.append(h + "</tbody></table>")
        rows = []

    def flush_list():
        nonlocal items
        if items:
            out.append("<ul>" + "".join(f"<li>{md_inline(i)}</li>" for i in items) + "</ul>")
            items = []

    for line in md.splitlines():
        s = line.strip()
        if s.startswith("|"):
            flush_list()
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            rows.append(cells)
            continue
        flush_table()
        if re.match(r"^[-*•]\s+", s):
            items.append(re.sub(r"^[-*•]\s+", "", s))
        elif re.match(r"^\d+[.)]\s+", s):
            items.append(re.sub(r"^\d+[.)]\s+", "", s))
        else:
            flush_list()
            if s.startswith("#"):
                out.append(f"<h4>{md_inline(s.lstrip('#').strip())}</h4>")
            elif s:
                out.append(f"<p>{md_inline(s)}</p>")
    flush_table(); flush_list()
    return "\n".join(out)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def group_terms(entries):
    terms = OrderedDict()
    for e in entries:
        key = e.get("term_label", "?")
        if key not in terms:
            terms[key] = {"label": key, "start": e.get("block_start") or e.get("start", ""), "end": e.get("block_end") or e.get("end", ""), "rows": []}
        terms[key]["rows"].append(e)
    return terms


def short_label(k):
    return re.sub(r"\s*\(.*?\)\s*", " ", k).strip()


def conf_class(r):
    conf = (r.get("confidence") or "").lower()
    return "conf-" + ("c" if conf.startswith("conf") else "l" if conf.startswith("lik") else "a" if conf else "n")


LEVEL_ZH = {"upper": "上层", "lower": "下层"}
THEME_ZH = {"primary-strength": "强项", "secondary-savings": "省钱"}


# ----------------------------------------------------------------------------
# Markdown
# ----------------------------------------------------------------------------
def render_md(plan, meta):
    t = plan["totals"]
    entries = sorted(plan["entries"], key=lambda e: e.get("seq", 0))
    terms = group_terms(entries)
    L = []
    L.append("# 六校 150.334 学分 · ASU Online BA in General Studies · 结算版时间线\n")
    L.append(f"> 生成日期 {meta['date']} · 主题：Technology & Government / Socio-Technical Systems: Energy & Environment（Power Electronics）· 起点 2026 秋 A（ULC 已在读）· 今天 {TODAY}\n")
    L.append("")
    L.append("| 总学分 | 上层（300+）学分 | 总消费 | 门数 | 起止 | 时长 | 均价 |")
    L.append("|---:|---:|---:|---:|:--|:--|---:|")
    per_cr = t.get("per_credit_usd") or (float(t["cost_usd"]) / float(t["credits"]) if float(t.get("credits", 0)) else 0)
    L.append(f"| **{fmt_cr(t['credits'])}** | {fmt_cr(t.get('upper_division_credits', ''))} | **{fmt_usd(t['cost_usd'])}** | {t.get('courses', len(entries))} | {t.get('first_term','')} → {t.get('last_term','')} | {t.get('months','')} 个月 | {fmt_usd(per_cr)}/学分 |")
    L.append("")
    L.append("## 六校分摊（学校 · 门数 · 学分 · 上层学分 · 消费 · 每学分）\n")
    L.append("| 学校 | 门数 | 学分 | 上层学分 | 消费 | 每学分 |")
    L.append("|:--|---:|---:|---:|---:|---:|")
    for s in plan.get("per_school_totals", []):
        pc = s.get("per_credit_usd") or (float(s["cost_usd"]) / float(s["credits"]) if float(s.get("credits", 0)) else 0)
        L.append(f"| {canon(s['school'])} | {s.get('courses','')} | {fmt_cr(s['credits'])} | {fmt_cr(s.get('upper_division_credits',''))} | {fmt_usd(s['cost_usd'])} | {fmt_usd(pc)} |")
    L.append("")
    L.append("## 时间线 · 选课名 · 计学分 · 总消费\n")
    L.append("按 8 周时间块（ASU A/B session 网格，以开课日期归块）分组；累计列为逐行滚动合计；负荷 = 开课当日所有在读课程的 学分×8/周数 之和（上限 15）。\n")
    L.append("| # | 起止 | 学校 | 代码 | 选课名 | 计学分 | 层级 | 满足要求 | 前置由 | 费用 | 累计学分 | 累计消费 | 负荷 | 置信 |")
    L.append("|---:|:--|:--|:--|:--|---:|:--|:--|:--|---:|---:|---:|---:|:--|")
    loads = {b.get("term_label"): b for b in plan.get("per_term_load", [])}
    for term in terms.values():
        blk_cr = sum(float(r.get("credits_counted", 0)) for r in term["rows"])
        blk_cost = sum(float(r.get("cost_usd", 0)) for r in term["rows"])
        b = loads.get(term["label"], {})
        peak = f" · 峰值负荷 {b.get('peak_load_8wk')}" if b.get("peak_load_8wk") is not None else ""
        L.append(f"| | **{term['label']}** {term['start']} → {term['end']} | | | *本块 {len(term['rows'])} 门 · {fmt_cr(blk_cr)} 学分 · {fmt_usd(blk_cost)}{peak}* | | | | | | | | | |")
        for r in term["rows"]:
            title = r.get("title", "")
            if r.get("title_zh"):
                title += f"<br>{r['title_zh']}"
            tags = []
            if r.get("status") == "in-progress":
                tags.append("在读")
            if r.get("theme_tag") in THEME_ZH:
                tags.append(THEME_ZH[r["theme_tag"]])
            if tags:
                title += " <sub>" + " · ".join(tags) + "</sub>"
            if r.get("fallback"):
                title += f"<br><sub>备选：{r['fallback']}</sub>"
            when = f"{r.get('start','')}→{r.get('end','')}"
            if r.get("school_term"):
                when += f"<br><sub>{r['school_term']}"
                if r.get("duration_weeks"):
                    when += f" · {fmt_cr(r['duration_weeks'])} 周"
                when += "</sub>"
            L.append("| {seq} | {when} | {school} | `{code}` | {title} | {cr} | {lvl} | {req} | {pre} | {cost} | {ccr} | {ccost} | {load} | {conf} |".format(
                seq=r.get("seq", ""), when=when, school=canon(r.get("school")),
                code=r.get("code", ""), title=title, cr=fmt_cr(r.get("credits_counted", 0)), lvl=LEVEL_ZH.get(r.get("level", ""), r.get("level", "")),
                req=(r.get("requirement_bucket", "") + (f"<br><sub>{r['cluster_or_theme']}</sub>" if r.get("cluster_or_theme") else "")),
                pre=r.get("prereqs_satisfied_by", "") or "—",
                cost=fmt_usd(r.get("cost_usd", 0)), ccr=fmt_cr(r.get("cumulative_credits", 0)), ccost=fmt_usd(r.get("cumulative_cost_usd", 0)),
                load=r.get("load_8wk_at_start", ""), conf=r.get("confidence", "")))
    L.append("")
    L.append("## 每个时间块的负荷\n")
    L.append("| 时间块 | 名义起止 | 开课门数 | 开课学分 | 消费 | 峰值负荷（8 周当量） | 峰值日 | 同时在读 | 学校 |")
    L.append("|:--|:--|---:|---:|---:|---:|:--|---:|:--|")
    for b in plan.get("per_term_load", []):
        L.append(f"| {b.get('term_label','')} | {b.get('start','')} → {b.get('end','')} | {b.get('courses','')} | {fmt_cr(b.get('credits',0))} | {fmt_usd(b.get('cost_usd',0))} | {b.get('peak_load_8wk','')} | {b.get('peak_date','')} | {b.get('peak_concurrent','')} | {b.get('schools','')} |")
    L.append("")
    L.append("## ASU 101 / IDS 321 / IDS 402 抵课方案\n")
    for s in plan.get("substitutions", []):
        L.append(f"- **{s['asu_course']}** ← {s['substitute']} — {s['justification']}")
    L.append("")
    L.append("## 学位要求对照矩阵（ASU BA in General Studies · General Studies Gold）\n")
    L.append(plan.get("requirement_matrix", ""))
    L.append("")
    if plan.get("cluster_mapping"):
        L.append("## 四个 Topic Area 与两大主题的映射\n")
        L.append(plan["cluster_mapping"])
        L.append("")
    if plan.get("eighty_twenty"):
        L.append("## 80/20：取百家之长 vs 外校省钱\n")
        L.append(plan["eighty_twenty"])
        L.append("")
    L.append("## 假设\n")
    for a in plan.get("assumptions", []):
        L.append(f"- {a}")
    L.append("")
    L.append("## 风险与注意\n")
    for r in plan.get("risks", []):
        L.append(f"- {r}")
    if plan.get("verification_todo"):
        L.append("")
        L.append("## 报名前核对清单（按日期）\n")
        for i, v in enumerate(plan["verification_todo"], 1):
            L.append(f"{i}. {v}")
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
    if plan.get("reconciliation_notes"):
        L.append("")
        L.append("## 结算说明（审查意见如何取舍）\n")
        L.append(plan["reconciliation_notes"])
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
    L.append(f"方法：侦察（学位规则 / 校历与价格 / 各校强项）→ 第一轮六个学校子代理 → 第二轮三个审查子代理（学位要求 / 去重 / 前置时间线）+ 课程代码核验 → 结算 → 脚本确定性核算 + 三个对抗校验镜头（学位要求 / 排期可行性 / 价格与数据完整性），共 {plan.get('verify_rounds','')} 轮。本环境无法直接抓取学校网页（仅搜索摘要），所有课程代码、价格、日期均需在报名前到官网复核。")
    return "\n".join(L)


# ----------------------------------------------------------------------------
# SVG charts
# ----------------------------------------------------------------------------
def _d(s):
    return datetime.date.fromisoformat(s)


def svg_gantt(entries, today=TODAY):
    """One row per course, bar from start to end, colored by school; month grid; today marker."""
    es = [e for e in sorted(entries, key=lambda e: e.get("seq", 0)) if e.get("start") and e.get("end")]
    if not es:
        return ""
    d0 = min(_d(e["start"]) for e in es).replace(day=1)
    d1 = max(_d(e["end"]) for e in es)
    d1 = (d1.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
    span = (d1 - d0).days
    W = 1180
    padL, padR, padT, padB = 236, 56, 40, 10
    rowH = 17
    n = len(es)
    H = padT + n * rowH + padB
    plotW = W - padL - padR

    def x(date):
        return padL + (date - d0).days / span * plotW

    s = [f'<svg class="chart gantt" viewBox="0 0 {W} {H}" role="img" aria-label="全部课程的甘特图：每行一门课，条形为起止日期，颜色为学校">']
    # month grid + labels
    m = d0
    while m < d1:
        xx = x(m)
        first_of_year = m.month == 1
        s.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{padT-4}" y2="{H-padB}" class="{"axis" if first_of_year else "grid"}"/>')
        if m.month in (1, 4, 7, 10) or span < 500:
            s.append(f'<text x="{xx+3:.1f}" y="{padT-18}" class="tick">{m.strftime("%b")}</text>')
        if first_of_year or m == d0:
            s.append(f'<text x="{xx+3:.1f}" y="{padT-30}" class="tick year">{m.year}</text>')
        m = (m + datetime.timedelta(days=32)).replace(day=1)
    # block separators + labels
    prev_block = None
    for i, e in enumerate(es):
        y0 = padT + i * rowH
        blk = e.get("term_label")
        if blk != prev_block:
            s.append(f'<line x1="8" x2="{W-padR}" y1="{y0-0.5:.1f}" y2="{y0-0.5:.1f}" class="sep"/>')
            s.append(f'<text x="8" y="{y0+12:.1f}" class="blk">{esc(short_label(blk or ""))}</text>')
            prev_block = blk
    # today
    if today:
        td = _d(today)
        if d0 <= td <= d1:
            xt = x(td)
            s.append(f'<line x1="{xt:.1f}" x2="{xt:.1f}" y1="{padT-6}" y2="{H-padB}" class="today"/>')
            s.append(f'<text x="{xt+4:.1f}" y="{padT-6}" class="tick today-lbl">今天 {today}</text>')
    # rows
    for i, e in enumerate(es):
        y0 = padT + i * rowH
        sc = canon(e.get("school"))
        xs, xe = x(_d(e["start"])), x(_d(e["end"]) + datetime.timedelta(days=1))
        wbar = max(3, xe - xs)
        cls = "bar" + (" inprog" if e.get("status") == "in-progress" else "")
        tip = f'{e.get("code","")} · {e.get("title","")} · {e["start"]} → {e["end"]} · {fmt_cr(e.get("credits_counted",0))} 学分 · {fmt_usd(e.get("cost_usd",0))}'
        s.append(f'<text x="{padL-8}" y="{y0+12:.1f}" class="lbl" text-anchor="end"><tspan class="sch">{esc(SCHOOL_SHORT.get(sc, sc))}</tspan> {esc(e.get("code",""))}</text>')
        s.append(f'<rect x="{xs:.1f}" y="{y0+3:.1f}" width="{wbar:.1f}" height="{rowH-6}" rx="2.5" fill="var(--c-{slug(sc)})" class="{cls}"><title>{esc(tip)}</title></rect>')
        s.append(f'<text x="{xe+5:.1f}" y="{y0+12:.1f}" class="cr">{fmt_cr(e.get("credits_counted",0))}</text>')
    s.append("</svg>")
    return "\n".join(s)


def svg_peak_load(per_term_load, ceiling=15.0):
    """Peak 8-week-equivalent load per block, single series, with the 15 ceiling and 9-13 comfort band."""
    blocks = [b for b in per_term_load if b.get("peak_load_8wk") is not None]
    if not blocks:
        return ""
    n = len(blocks)
    W, H = max(640, 56 * n + 90), 300
    padL, padR, padT, padB = 44, 12, 22, 70
    top = max(18, int(max(float(b["peak_load_8wk"]) for b in blocks) // 3 * 3 + 3))
    plotH, plotW = H - padT - padB, W - padL - padR
    bw = plotW / n
    bar = min(34, bw * 0.62)

    def y(v):
        return padT + plotH - (v / top) * plotH

    s = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="每个时间块的峰值负荷（8 周当量学分），上限 15">']
    s.append(f'<rect x="{padL}" y="{y(13):.1f}" width="{plotW}" height="{y(9)-y(13):.1f}" class="band"/>')
    for g in range(0, top + 1, 3):
        yy = y(g)
        s.append(f'<line x1="{padL}" x2="{W-padR}" y1="{yy:.1f}" y2="{yy:.1f}" class="grid"/>')
        s.append(f'<text x="{padL-6}" y="{yy+4:.1f}" class="tick" text-anchor="end">{g}</text>')
    s.append(f'<line x1="{padL}" x2="{W-padR}" y1="{y(0):.1f}" y2="{y(0):.1f}" class="axis"/>')
    s.append(f'<line x1="{padL}" x2="{W-padR}" y1="{y(ceiling):.1f}" y2="{y(ceiling):.1f}" class="ceiling"/>')
    s.append(f'<text x="{W-padR}" y="{y(ceiling)-5:.1f}" class="tick ceil-lbl" text-anchor="end">上限 {fmt_cr(ceiling)}</text>')
    s.append(f'<text x="{padL+4}" y="{y(13)+11:.1f}" class="tick band-lbl">舒适区 9–13</text>')
    for i, b in enumerate(blocks):
        v = float(b["peak_load_8wk"])
        x0 = padL + i * bw + (bw - bar) / 2
        cls = "over" if v > ceiling else ""
        s.append(f'<rect x="{x0:.1f}" y="{y(v):.1f}" width="{bar:.1f}" height="{max(0, y(0)-y(v)):.1f}" rx="2" class="loadbar {cls}"><title>{esc(b.get("term_label",""))} · 峰值 {v} · {esc(b.get("peak_date",""))} · 同时 {esc(b.get("peak_concurrent",""))} 门</title></rect>')
        s.append(f'<text x="{x0+bar/2:.1f}" y="{y(v)-5:.1f}" class="val" text-anchor="middle">{v}</text>')
        s.append(f'<text x="{x0+bar/2:.1f}" y="{H-padB+16}" class="tick" text-anchor="end" transform="rotate(-38 {x0+bar/2:.1f} {H-padB+16})">{esc(short_label(b.get("term_label","")))}</text>')
    s.append("</svg>")
    return "\n".join(s)


def svg_stacked_credits(entries):
    """Credits started per block, stacked by school (fixed order, 2px gaps)."""
    order, per = [], OrderedDict()
    for e in sorted(entries, key=lambda e: e.get("seq", 0)):
        k = e.get("term_label", "?")
        if k not in per:
            per[k] = defaultdict(float); order.append(k)
        per[k][canon(e.get("school"))] += float(e.get("credits_counted", 0))
    n = len(order)
    if n == 0:
        return ""
    W, H = max(640, 56 * n + 90), 300
    padL, padR, padT, padB = 44, 12, 22, 70
    maxv = max(sum(v.values()) for v in per.values()) or 1
    top = int((maxv // 3 + 1) * 3)
    plotH, plotW = H - padT - padB, W - padL - padR
    bw = plotW / n
    bar = min(34, bw * 0.62)

    def y(v):
        return padT + plotH - (v / top) * plotH

    s = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="每个时间块开课的学分，按学校堆叠">']
    for g in range(0, top + 1, 3):
        yy = y(g)
        s.append(f'<line x1="{padL}" x2="{W-padR}" y1="{yy:.1f}" y2="{yy:.1f}" class="grid"/>')
        s.append(f'<text x="{padL-6}" y="{yy+4:.1f}" class="tick" text-anchor="end">{g}</text>')
    s.append(f'<line x1="{padL}" x2="{W-padR}" y1="{y(0):.1f}" y2="{y(0):.1f}" class="axis"/>')
    for i, k in enumerate(order):
        x0 = padL + i * bw + (bw - bar) / 2
        acc = 0.0
        for sc in SCHOOL_ORDER:
            v = per[k].get(sc, 0)
            if v <= 0:
                continue
            y1, y0 = y(acc), y(acc + v)
            h = max(0, y1 - y0 - 2)
            s.append(f'<rect x="{x0:.1f}" y="{y0+1:.1f}" width="{bar:.1f}" height="{h:.1f}" rx="2" fill="var(--c-{slug(sc)})"><title>{esc(k)} · {esc(sc)} · {fmt_cr(v)} 学分</title></rect>')
            acc += v
        s.append(f'<text x="{x0+bar/2:.1f}" y="{y(acc)-5:.1f}" class="val" text-anchor="middle">{fmt_cr(acc)}</text>')
        s.append(f'<text x="{x0+bar/2:.1f}" y="{H-padB+16}" class="tick" text-anchor="end" transform="rotate(-38 {x0+bar/2:.1f} {H-padB+16})">{esc(short_label(k))}</text>')
    s.append("</svg>")
    return "\n".join(s)


def svg_cumulative(entries, key, label, fmt):
    pts = [(e.get("term_label", "?"), float(e.get(key, 0))) for e in sorted(entries, key=lambda e: e.get("seq", 0))]
    if not pts:
        return ""
    per = OrderedDict()
    for k, v in pts:
        per[k] = v
    ks, vs = list(per.keys()), list(per.values())
    n = len(ks)
    W, H = max(640, 56 * n + 90), 300
    padL, padR, padT, padB = 66, 14, 22, 70
    maxv = max(vs) or 1
    plotH, plotW = H - padT - padB, W - padL - padR

    def x(i):
        return padL + (i + 0.5) * plotW / n

    def y(v):
        return padT + plotH - (v / maxv) * plotH

    s = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">']
    for g in range(5):
        v = maxv * g / 4
        s.append(f'<line x1="{padL}" x2="{W-padR}" y1="{y(v):.1f}" y2="{y(v):.1f}" class="grid"/>')
        s.append(f'<text x="{padL-6}" y="{y(v)+4:.1f}" class="tick" text-anchor="end">{fmt(v)}</text>')
    path = " ".join(("M" if i == 0 else "L") + f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vs))
    area = path + f" L{x(n-1):.1f},{y(0):.1f} L{x(0):.1f},{y(0):.1f} Z"
    s.append(f'<path d="{area}" class="area"/>')
    s.append(f'<path d="{path}" class="line"/>')
    for i, v in enumerate(vs):
        s.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="4" class="dot"><title>{esc(ks[i])} · {fmt(v)}</title></circle>')
        s.append(f'<text x="{x(i):.1f}" y="{H-padB+16}" class="tick" text-anchor="end" transform="rotate(-38 {x(i):.1f} {H-padB+16})">{esc(short_label(ks[i]))}</text>')
    s.append(f'<text x="{x(n-1)+2:.1f}" y="{y(vs[-1])-10:.1f}" class="val" text-anchor="end">{fmt(vs[-1])}</text>')
    s.append("</svg>")
    return "\n".join(s)


# ----------------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------------
CSS = """
:root {
  color-scheme: light;
  --bg: #f3f5f8; --surface: #ffffff; --surface-2: #eceff4; --surface-3: #e3e7ee;
  --ink: #141a24; --ink-2: #4a5462; --muted: #8791a0; --hair: #dde2e9; --hair-2: #c6cdd8;
  --accent: #2b3a67; --accent-soft: #e6eaf6; --accent-ink: #1f2b4d;
  --good: #0a7d0a; --warn: #b77700; --crit: #c93535; --crit-soft: #fbe9e9;
__SCHOOL_CSS__
  --font-display: "Archivo", "Noto Sans SC", system-ui, sans-serif;
  --font-body: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --bg: #0f1216; --surface: #171b21; --surface-2: #1e2430; --surface-3: #262d3a;
    --ink: #eef1f5; --ink-2: #b4bcc8; --muted: #8791a0; --hair: #2a313c; --hair-2: #3a4351;
    --accent: #9fb0e8; --accent-soft: #222a42; --accent-ink: #c7d2f5;
    --good: #4ec24e; --warn: #e2a021; --crit: #ef6b6b; --crit-soft: #3a1f1f;
__SCHOOL_CSS_DARK__
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0f1216; --surface: #171b21; --surface-2: #1e2430; --surface-3: #262d3a;
  --ink: #eef1f5; --ink-2: #b4bcc8; --muted: #8791a0; --hair: #2a313c; --hair-2: #3a4351;
  --accent: #9fb0e8; --accent-soft: #222a42; --accent-ink: #c7d2f5;
  --good: #4ec24e; --warn: #e2a021; --crit: #ef6b6b; --crit-soft: #3a1f1f;
__SCHOOL_CSS_DARK__
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font-family: var(--font-body); font-size: 14px; line-height: 1.55; padding-inline: clamp(16px, 4vw, 48px); padding-block: 28px 64px; }
.wrap { max-width: 1320px; margin: 0 auto; display: grid; gap: 30px; }
header.hero { display: grid; gap: 10px; }
.eyebrow { font-family: var(--font-display); font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--accent); font-weight: 600; }
h1 { font-family: var(--font-display); font-size: clamp(24px, 3.4vw, 38px); line-height: 1.15; margin: 0; text-wrap: balance; font-weight: 700; letter-spacing: -.01em; }
h1 .en { display: block; font-size: .55em; font-weight: 500; color: var(--ink-2); margin-top: 6px; letter-spacing: 0; }
.sub { color: var(--ink-2); max-width: 78ch; margin: 0; }
h2 { font-family: var(--font-display); font-size: 18px; margin: 0 0 12px; font-weight: 600; letter-spacing: .01em; display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
h2 small { font-family: var(--font-body); font-weight: 400; color: var(--muted); font-size: 12px; }
h4 { margin: 10px 0 4px; font-size: 13px; font-family: var(--font-display); }
section { display: grid; gap: 4px; }
.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 0; }
.kpi { background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; padding: 14px 16px; display: grid; gap: 2px; }
.kpi dt { font-size: 12px; color: var(--muted); letter-spacing: .06em; }
.kpi dd { margin: 0; font-family: var(--font-display); font-size: 28px; font-weight: 600; line-height: 1.1; font-variant-numeric: tabular-nums; }
.kpi dd small { font-size: 13px; font-weight: 500; color: var(--ink-2); margin-left: 4px; font-family: var(--font-body); }
.kpi dd.range { font-size: 14px; font-family: var(--font-mono); font-weight: 500; line-height: 1.4; }
.kpi.primary { border-color: var(--accent); background: var(--accent-soft); }
.kpi.primary dd { color: var(--accent-ink); }
ul.schools { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 10px; }
.school { display: grid; grid-template-columns: 10px 1fr auto; gap: 12px; align-items: center; background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; padding: 12px 14px; }
.school .chip { width: 10px; height: 38px; border-radius: 3px; display: block; }
.s-name { font-family: var(--font-display); font-weight: 600; }
.s-zh { color: var(--muted); font-size: 12px; }
.school dl { margin: 0; display: grid; grid-auto-flow: column; gap: 14px; }
.school dl div { display: grid; text-align: right; }
.school dt { font-size: 11px; color: var(--muted); }
.school dd { margin: 0; font-family: var(--font-mono); font-variant-numeric: tabular-nums; font-size: 13px; }
.charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }
figure { margin: 0; background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; padding: 14px 14px 10px; display: grid; gap: 6px; }
figure.wide { overflow-x: auto; }
figcaption { font-family: var(--font-display); font-weight: 600; font-size: 13px; color: var(--ink-2); display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 12px; font-size: 12px; color: var(--ink-2); font-weight: 400; }
.lg { display: inline-flex; align-items: center; gap: 6px; }
.lg .chip { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
svg.chart { width: 100%; height: auto; display: block; font-family: var(--font-mono); }
svg.gantt { min-width: 900px; }
svg .grid { stroke: var(--hair); stroke-width: 1; }
svg .axis { stroke: var(--hair-2); stroke-width: 1; }
svg .sep { stroke: var(--hair); stroke-width: 1; stroke-dasharray: 2 3; }
svg .tick { fill: var(--muted); font-size: 10.5px; }
svg .tick.year { fill: var(--ink-2); font-weight: 600; font-size: 11px; }
svg .blk { fill: var(--accent); font-size: 10px; font-weight: 600; font-family: var(--font-display); }
svg .lbl { fill: var(--ink); font-size: 10.5px; }
svg .lbl .sch { fill: var(--muted); font-size: 9.5px; }
svg .cr { fill: var(--ink-2); font-size: 10px; }
svg .val { fill: var(--ink-2); font-size: 11px; font-weight: 600; }
svg .line { fill: none; stroke: var(--accent); stroke-width: 2; stroke-linejoin: round; }
svg .area { fill: var(--accent); opacity: .10; }
svg .dot { fill: var(--accent); stroke: var(--surface); stroke-width: 2; }
svg .bar { stroke: var(--surface); stroke-width: 1; }
svg .bar.inprog { stroke: var(--ink); stroke-dasharray: 3 2; }
svg .today { stroke: var(--crit); stroke-width: 1.5; stroke-dasharray: 4 3; }
svg .today-lbl { fill: var(--crit); font-weight: 600; }
svg .band { fill: var(--accent); opacity: .07; }
svg .band-lbl { fill: var(--accent); }
svg .ceiling { stroke: var(--crit); stroke-width: 1.5; stroke-dasharray: 5 4; }
svg .ceil-lbl { fill: var(--crit); font-weight: 600; }
svg .loadbar { fill: var(--accent); stroke: var(--surface); stroke-width: 1; }
svg .loadbar.over { fill: var(--crit); }
svg rect:hover, svg .dot:hover { opacity: .8; }
.tablewrap { overflow-x: auto; background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; }
table { border-collapse: collapse; width: 100%; min-width: 1240px; font-size: 13px; }
thead th { position: sticky; top: 0; background: var(--surface-2); color: var(--ink-2); font-weight: 600; text-align: left; padding: 10px 10px; border-bottom: 1px solid var(--hair-2); font-size: 12px; letter-spacing: .04em; white-space: nowrap; z-index: 1; }
thead th.num { text-align: right; }
td { padding: 9px 10px; border-bottom: 1px solid var(--hair); vertical-align: top; }
td.num { text-align: right; font-family: var(--font-mono); font-variant-numeric: tabular-nums; white-space: nowrap; }
td.cum { color: var(--ink-2); }
td.code { font-family: var(--font-mono); font-weight: 600; white-space: nowrap; }
td.school-cell { white-space: nowrap; }
td .chip { display: inline-block; width: 8px; height: 14px; border-radius: 2px; vertical-align: -2px; margin-right: 7px; }
td.when { font-family: var(--font-mono); font-size: 12px; white-space: nowrap; font-variant-numeric: tabular-nums; }
td.when .st { display: block; color: var(--muted); font-family: var(--font-body); font-size: 11.5px; white-space: normal; max-width: 170px; }
td.title { min-width: 220px; }
td.title .en { display: block; font-weight: 500; }
td.title .zh { display: block; color: var(--ink-2); font-size: 12px; }
td.title .note, td.title .fb { display: block; color: var(--muted); font-size: 11.5px; margin-top: 2px; }
td.title .fb::before { content: "备选 · "; color: var(--warn); }
td.req { max-width: 220px; }
td.req .theme { display: block; color: var(--muted); font-size: 11.5px; }
td.pre { color: var(--ink-2); font-size: 12px; max-width: 220px; }
td.conf { color: var(--muted); font-size: 11px; white-space: nowrap; }
tr.conf-a td.conf { color: var(--crit); font-weight: 600; }
tr.conf-l td.conf { color: var(--warn); }
td.load.hot { color: var(--crit); font-weight: 600; }
.pill { display: inline-block; font-size: 11px; padding: 1px 7px; border-radius: 999px; border: 1px solid var(--hair-2); color: var(--ink-2); white-space: nowrap; margin-right: 4px; }
.pill.upper { background: var(--accent-soft); color: var(--accent-ink); border-color: transparent; }
.pill.inprog { background: var(--crit-soft); color: var(--crit); border-color: transparent; }
.pill.strength { border-style: dashed; }
.pill.savings { color: var(--muted); }
tr.term th { background: var(--surface-2); text-align: left; padding: 10px 10px; border-top: 2px solid var(--hair-2); border-bottom: 1px solid var(--hair); font-weight: 500; }
tr.term th span { margin-right: 18px; }
.t-label { font-family: var(--font-display); font-weight: 700; color: var(--accent-ink); font-size: 14px; }
.t-dates { color: var(--ink-2); font-family: var(--font-mono); font-size: 12px; }
.t-sum, .t-cum, .t-peak { color: var(--ink-2); font-size: 12px; }
.t-cum { color: var(--muted); }
.t-peak.hot { color: var(--crit); font-weight: 600; }
table.matrix, table.load { min-width: 0; }
table.matrix th, table.load th { position: static; }
table.matrix td, table.matrix th { font-size: 12.5px; vertical-align: top; }
.two { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }
.panel { background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; padding: 14px 16px; }
.panel ul, .panel ol { margin: 0; padding-left: 18px; display: grid; gap: 6px; }
.panel li p { margin: 2px 0 0; color: var(--ink-2); font-size: 12.5px; }
.panel p { margin: 6px 0; }
.arrow { color: var(--muted); margin: 0 4px; }
.warn { border-color: var(--crit); }
details { background: var(--surface); border: 1px solid var(--hair); border-radius: 8px; padding: 10px 16px; }
summary { cursor: pointer; font-family: var(--font-display); font-weight: 600; }
details > div { padding-top: 8px; color: var(--ink-2); }
code { font-family: var(--font-mono); font-size: .92em; }
footer { color: var(--muted); font-size: 12px; max-width: 100ch; border-top: 1px solid var(--hair); padding-top: 14px; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
@media (max-width: 640px) { .school { grid-template-columns: 10px 1fr; } .school dl { grid-column: 2; grid-auto-flow: row; grid-template-columns: repeat(4, 1fr); } .school dl div { text-align: left; } }
@media (prefers-reduced-motion: no-preference) { svg rect, svg .dot { transition: opacity .15s; } }
"""


def render_html(plan, meta):
    t = plan["totals"]
    entries = sorted(plan["entries"], key=lambda e: e.get("seq", 0))
    terms = group_terms(entries)
    loads = {b.get("term_label"): b for b in plan.get("per_term_load", [])}
    per_cr = t.get("per_credit_usd") or (float(t["cost_usd"]) / float(t["credits"]) if float(t.get("credits", 0)) else 0)
    css = CSS.replace("__SCHOOL_CSS_DARK__", "\n".join(f"    --c-{slug(k)}: {v[1]};" for k, v in SCHOOL_COLORS.items()))
    css = css.replace("__SCHOOL_CSS__", "\n".join(f"  --c-{slug(k)}: {v[0]};" for k, v in SCHOOL_COLORS.items()))

    cards = []
    by_school = {canon(s["school"]): s for s in plan.get("per_school_totals", [])}
    for sc in SCHOOL_ORDER:
        s = by_school.get(sc, {})
        cr = float(s.get("credits", 0)); cost = float(s.get("cost_usd", 0))
        pc = s.get("per_credit_usd") or (cost / cr if cr else 0)
        cards.append(f'''<li class="school"><span class="chip" style="background:var(--c-{slug(sc)})"></span>
      <div><div class="s-name">{esc(sc)}</div><div class="s-zh">{esc(SCHOOL_ZH.get(sc, ""))}</div></div>
      <dl><div><dt>门</dt><dd>{esc(s.get("courses", "–"))}</dd></div><div><dt>学分</dt><dd>{fmt_cr(cr)}</dd></div><div><dt>上层</dt><dd>{fmt_cr(s.get("upper_division_credits", 0))}</dd></div><div><dt>消费</dt><dd>{fmt_usd(cost)}</dd></div><div><dt>每学分</dt><dd>{fmt_usd(pc)}</dd></div></dl></li>''')

    rows = []
    for term in terms.values():
        blk_cr = sum(float(r.get("credits_counted", 0)) for r in term["rows"])
        blk_cost = sum(float(r.get("cost_usd", 0)) for r in term["rows"])
        last = term["rows"][-1]
        b = loads.get(term["label"], {})
        peak = b.get("peak_load_8wk")
        peak_html = f'<span class="t-peak{" hot" if (peak or 0) > 15 else ""}">峰值负荷 {peak}（{esc(b.get("peak_date",""))}，同时 {esc(b.get("peak_concurrent",""))} 门）</span>' if peak is not None else ""
        rows.append(f'''<tr class="term"><th colspan="14"><span class="t-label">{esc(term["label"])}</span><span class="t-dates">{esc(term["start"])} → {esc(term["end"])}</span><span class="t-sum">本块 {len(term["rows"])} 门 · {fmt_cr(blk_cr)} 学分 · {fmt_usd(blk_cost)}</span>{peak_html}<span class="t-cum">累计 {fmt_cr(last.get("cumulative_credits", 0))} 学分 · {fmt_usd(last.get("cumulative_cost_usd", 0))}</span></th></tr>''')
        for r in term["rows"]:
            sc = canon(r.get("school"))
            pills = f'<span class="pill {esc(r.get("level", ""))}">{esc(LEVEL_ZH.get(r.get("level", ""), r.get("level", "")))}</span>'
            if r.get("status") == "in-progress":
                pills += '<span class="pill inprog">在读</span>'
            tt = r.get("theme_tag")
            if tt in THEME_ZH:
                pills += f'<span class="pill {"strength" if tt == "primary-strength" else "savings"}">{THEME_ZH[tt]}</span>'
            when = f'{esc(r.get("start",""))} → {esc(r.get("end",""))}'
            st = " · ".join(x for x in [r.get("school_term", ""), (fmt_cr(r["duration_weeks"]) + " 周") if r.get("duration_weeks") else ""] if x)
            if st:
                when += f'<span class="st">{esc(st)}</span>'
            ld = r.get("load_8wk_at_start")
            rows.append(f'''<tr class="{conf_class(r)}">
  <td class="num">{esc(r.get("seq", ""))}</td>
  <td class="when">{when}</td>
  <td class="school-cell"><span class="chip" style="background:var(--c-{slug(sc)})"></span>{esc(sc)}</td>
  <td class="code">{esc(r.get("code", ""))}</td>
  <td class="title"><span class="en">{esc(r.get("title", ""))}</span>{('<span class="zh">' + esc(r.get("title_zh")) + '</span>') if r.get("title_zh") else ''}{('<span class="note">' + esc(r.get("note")) + '</span>') if r.get("note") else ''}{('<span class="fb">' + esc(r.get("fallback")) + '</span>') if r.get("fallback") else ''}</td>
  <td class="num">{fmt_cr(r.get("credits_counted", 0))}</td>
  <td class="lvl">{pills}</td>
  <td class="req">{esc(r.get("requirement_bucket", ""))}{('<span class="theme">' + esc(r.get("cluster_or_theme")) + '</span>') if r.get("cluster_or_theme") else ''}</td>
  <td class="pre">{esc(r.get("prereqs_satisfied_by") or "—")}</td>
  <td class="num">{fmt_usd(r.get("cost_usd", 0))}</td>
  <td class="num cum">{fmt_cr(r.get("cumulative_credits", 0))}</td>
  <td class="num cum">{fmt_usd(r.get("cumulative_cost_usd", 0))}</td>
  <td class="num load{" hot" if (ld or 0) > 15 else ""}">{esc(ld if ld is not None else "")}</td>
  <td class="conf">{esc(r.get("confidence", ""))}</td>
</tr>''')

    subs = "".join(f'<li><b>{esc(s["asu_course"])}</b> <span class="arrow">←</span> {esc(s["substitute"])}<p>{esc(s["justification"])}</p></li>' for s in plan.get("substitutions", []))
    assumptions = "".join(f"<li>{md_inline(a)}</li>" for a in plan.get("assumptions", []))
    risks = "".join(f"<li>{md_inline(a)}</li>" for a in plan.get("risks", []))
    todo = "".join(f"<li>{md_inline(a)}</li>" for a in plan.get("verification_todo", []) or [])
    minor = "".join(f"<li>{md_inline(a)}</li>" for a in plan.get("verifier_minor_notes", []) or [])
    unresolved = "".join(f"<li>{md_inline(a)}</li>" for a in plan.get("unresolved_blocking", []) or [])
    sources = "".join(f"<li>{md_inline(a)}</li>" for a in plan.get("sources", []) or [])
    legend = "".join(f'<span class="lg"><span class="chip" style="background:var(--c-{slug(sc)})"></span>{esc(sc)}</span>' for sc in SCHOOL_ORDER)
    load_rows = "".join(
        f'<tr><td>{esc(b.get("term_label",""))}</td><td class="when">{esc(b.get("start",""))} → {esc(b.get("end",""))}</td><td class="num">{esc(b.get("courses",""))}</td><td class="num">{fmt_cr(b.get("credits",0))}</td><td class="num">{fmt_usd(b.get("cost_usd",0))}</td>'
        f'<td class="num load{" hot" if (b.get("peak_load_8wk") or 0) > 15 else ""}">{esc(b.get("peak_load_8wk",""))}</td><td class="when">{esc(b.get("peak_date",""))}</td><td class="num">{esc(b.get("peak_concurrent",""))}</td><td>{esc(b.get("schools",""))}</td></tr>'
        for b in plan.get("per_term_load", []))
    verify_rounds = plan.get("verify_rounds", "")
    det_info = "".join(f"<li>{esc(a)}</li>" for a in plan.get("deterministic_info", []) or [])

    page = f'''<title>六校 150.334 学分时间线</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=JetBrains+Mono:wght@400;600&family=Noto+Sans+SC:wght@400;500;700&display=swap">
<style>{css}</style>
<div class="wrap">
<header class="hero">
  <div class="eyebrow">排课 · 结算版 · 爆学分臻享版 · {esc(meta["date"])}</div>
  <h1>六校 150.334 学分时间线<span class="en">ASU Online BA in General Studies · Technology &amp; Government / Socio-Technical Systems: Energy &amp; Environment (Power Electronics)</span></h1>
  <p class="sub">从 2026 秋 A（ULC 已在读）起：SNHU 12 · Harvard Extension 12 · ASU ULC 42 · UMPI YourPace 42（恰好三个 8 周 session）· UCLA Extension 21.334（32 quarter units）· BYU IS 21（每门 ≤15 周完成）。80% 取各校强项，20% 外校省钱；忽略 ASU 30 学分驻校要求；ASU 101 / IDS 321 / IDS 402 以六校课程抵替再塞回。负荷 = 开课当日在读课程的 学分×8/周数 之和，上限 15。</p>
</header>

<section>
  <dl class="kpis">
    <div class="kpi primary"><dt>总学分 · 计入</dt><dd>{fmt_cr(t["credits"])}</dd></div>
    <div class="kpi primary"><dt>总消费 · USD</dt><dd>{fmt_usd(t["cost_usd"])}</dd></div>
    <div class="kpi"><dt>上层（300+）学分</dt><dd>{fmt_cr(t.get("upper_division_credits", ""))}<small>/ 需 ≥45</small></dd></div>
    <div class="kpi"><dt>课程门数</dt><dd>{esc(t.get("courses", len(entries)))}</dd></div>
    <div class="kpi"><dt>起 → 止</dt><dd class="range">{esc(t.get("first_term",""))}<br>{esc(t.get("last_term",""))}</dd></div>
    <div class="kpi"><dt>时长</dt><dd>{esc(t.get("months",""))}<small>个月</small></dd></div>
    <div class="kpi"><dt>每学分均价</dt><dd>{fmt_usd(per_cr)}</dd></div>
  </dl>
</section>

<section>
  <h2>六校分摊 <small>门数 · 学分 · 上层学分 · 消费 · 每学分</small></h2>
  <ul class="schools">{"".join(cards)}</ul>
</section>

<section>
  <h2>一眼看完的时间线 <small>每行一门课，条形 = 起止日期，颜色 = 学校，虚线边框 = 在读；右侧数字为计入学分</small></h2>
  <figure class="wide"><figcaption><span class="legend">{legend}</span></figcaption>{svg_gantt(entries)}</figure>
</section>

<section>
  <h2>负荷与累计 <small>每块开课学分（按学校堆叠）· 每块峰值负荷（8 周当量，上限 15）· 累计消费</small></h2>
  <div class="charts">
    <figure><figcaption>每块开课学分 <span class="legend">{legend}</span></figcaption>{svg_stacked_credits(entries)}</figure>
    <figure><figcaption>每块峰值负荷（8 周当量）</figcaption>{svg_peak_load(plan.get("per_term_load", []))}</figure>
    <figure><figcaption>累计消费（USD）</figcaption>{svg_cumulative(entries, "cumulative_cost_usd", "累计消费", fmt_usd)}</figure>
  </div>
</section>

<section>
  <h2>时间线 · 选课名 · 计学分 · 总消费 <small>按 8 周时间块分组（以开课日期归块）；累计列为逐行滚动合计；置信 assumed 为红色</small></h2>
  <div class="tablewrap">
  <table>
    <thead><tr><th class="num">#</th><th>起止</th><th>学校</th><th>代码</th><th>选课名</th><th class="num">计学分</th><th>层级</th><th>满足要求</th><th>前置由</th><th class="num">费用</th><th class="num">累计学分</th><th class="num">累计消费</th><th class="num">负荷</th><th>置信</th></tr></thead>
    <tbody>{"".join(rows)}</tbody>
  </table>
  </div>
</section>

<section>
  <h2>每个时间块 <small>开课门数 · 开课学分 · 消费 · 峰值负荷</small></h2>
  <div class="tablewrap"><table class="load"><thead><tr><th>时间块</th><th>名义起止</th><th class="num">开课门数</th><th class="num">开课学分</th><th class="num">消费</th><th class="num">峰值负荷</th><th>峰值日</th><th class="num">同时在读</th><th>学校</th></tr></thead><tbody>{load_rows}</tbody></table></div>
</section>

<section class="two">
  <div class="panel"><h2>ASU 101 / IDS 321 / IDS 402 抵课</h2><ul>{subs}</ul></div>
  <div class="panel"><h2>假设</h2><ul>{assumptions}</ul></div>
</section>

<section>
  <h2>学位要求对照 <small>ASU BA in General Studies · General Studies Gold · 四个 topic area</small></h2>
  <div class="tablewrap" style="padding:8px 12px">{md_to_html(plan.get("requirement_matrix", ""))}</div>
</section>

<section class="two">
  <div class="panel"><h2>四个 Topic Area 与两大主题</h2>{md_to_html(plan.get("cluster_mapping", ""))}</div>
  <div class="panel"><h2>80 / 20 <small>取百家之长 vs 外校省钱</small></h2>{md_to_html(plan.get("eighty_twenty", ""))}</div>
</section>

<section class="two">
  <div class="panel"><h2>风险与注意</h2><ul>{risks}</ul></div>
  <div class="panel{' warn' if unresolved else ''}"><h2>校验备注 <small>{esc(verify_rounds)} 轮：脚本核算 + 学位要求 / 排期 / 价格三镜头</small></h2>{('<b>未解决的阻断问题</b><ul>' + unresolved + '</ul>') if unresolved else ''}<ul>{minor or "<li>无</li>"}</ul></div>
</section>

<section class="panel"><h2>报名前核对清单 <small>按日期顺序</small></h2><ol>{todo or "<li>见风险与注意</li>"}</ol></section>

<section><details><summary>结算说明 · 审查意见如何取舍</summary><div>{md_to_html(plan.get("reconciliation_notes", ""))}</div></details></section>
<section><details><summary>学位概述</summary><div>{md_to_html(plan.get("degree_summary", ""))}</div></details></section>
<section><details><summary>脚本核算记录</summary><div><ul>{det_info or "<li>—</li>"}</ul></div></details></section>
<section><details><summary>来源</summary><div><ul>{sources or "<li>见 data/*.json</li>"}</ul></div></details></section>

<footer>方法：侦察（学位规则 / 校历与价格 / 各校强项）→ 第一轮六个学校子代理 → 第二轮三个审查子代理（学位要求 / 去重 / 前置时间线）+ 课程代码核验 → 结算 → 脚本确定性核算 + 三个对抗校验镜头（学位要求 / 排期可行性 / 价格与数据完整性）。本环境无法直接抓取学校网页（仅搜索摘要），所有课程代码、价格、日期均需在报名前到官网复核；标为 assumed 的行以红色置信标出，并给出备选课程。</footer>
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
    print("wrote", os.path.join(a.out, "timeline.md"), "and", os.path.join(a.out, "timeline.html"))


if __name__ == "__main__":
    main()
