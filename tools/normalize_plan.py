#!/usr/bin/env python3
"""Deterministic bookkeeping for the settled plan (Python port of the workflow's
normalize()/check()). Given entries with ISO start/end dates it assigns 8-week
blocks, sequence numbers, cumulative columns, per-block loads, per-school totals and
grand totals, then reports rule violations.

Usage:
  python3 tools/normalize_plan.py --in data/final_plan.json --out data/final_plan.json
  python3 tools/normalize_plan.py --in plan.json --check-only
"""
import argparse, datetime as dt, json, re, sys
from collections import OrderedDict

SCHOOLS = ["ASU ULC", "UMPI YourPace", "UCLA Extension", "BYU IS", "Harvard Extension", "SNHU"]
SORD = {s: i for i, s in enumerate(SCHOOLS)}
TARGET = {"SNHU": (12, 4), "Harvard Extension": (12, 3), "ASU ULC": (42, None), "UMPI YourPace": (42, None), "UCLA Extension": (21.334, 8), "BYU IS": (21, 7)}
BLOCKS = [("春 A", "Spring A", "01-01", "02-29"), ("春 B", "Spring B", "03-01", "04-30"), ("夏 A", "Summer A", "05-01", "06-27"),
          ("夏 B", "Summer B", "06-28", "08-15"), ("秋 A", "Fall A", "08-16", "10-10"), ("秋 B", "Fall B", "10-11", "12-31")]
NOMINAL = {"2026 秋 A": ("2026-08-20", "2026-10-09"), "2026 秋 B": ("2026-10-14", "2026-12-04"), "2027 春 A": ("2027-01-11", "2027-03-02"),
           "2027 春 B": ("2027-03-15", "2027-04-30"), "2027 夏 A": ("2027-05-17", "2027-06-25"), "2027 夏 B": ("2027-06-30", "2027-08-10"),
           "2027 秋 A": ("2027-08-19", "2027-10-08"), "2027 秋 B": ("2027-10-13", "2027-12-03"), "2028 春 A": ("2028-01-10", "2028-03-01"),
           "2028 春 B": ("2028-03-13", "2028-04-28"), "2028 夏 A": ("2028-05-16", "2028-06-26"), "2028 夏 B": ("2028-06-29", "2028-08-09"),
           "2028 秋 A": ("2028-08-17", "2028-10-06"), "2028 秋 B": ("2028-10-11", "2028-12-01")}
TODAY = "2026-09-14"


def canon(s):
    t = (s or "").lower()
    if re.search(r"snhu|southern new hampshire", t): return "SNHU"
    if re.search(r"harvard|\bhes\b", t): return "Harvard Extension"
    if re.search(r"umpi|presque|yourpace", t): return "UMPI YourPace"
    if re.search(r"ucla", t): return "UCLA Extension"
    if re.search(r"byu|brigham", t): return "BYU IS"
    if re.search(r"asu|ulc|universal learner", t): return "ASU ULC"
    return s


def r3(x):
    return round(x * 1000) / 1000


def d(s):
    return dt.date.fromisoformat(s)


def days(a, b):
    return (d(b) - d(a)).days + 1


def is_iso(s):
    try:
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", s or "")) and d(s) is not None
    except Exception:
        return False


def block_of(start):
    y, md = start[:4], start[5:10]
    i = next((k for k, b in enumerate(BLOCKS) if md <= b[3]), 5)
    b = BLOCKS[i]
    key = f"{y} {b[0]}"
    nom = NOMINAL.get(key, (f"{y}-{b[2]}", f"{y}-{'02-28' if b[3] == '02-29' else b[3]}"))
    return {"key": key, "label": f"{key} ({b[1]} {y})", "order": int(y) * 10 + i, "start": nom[0], "end": nom[1]}


def normalize(plan):
    problems = []
    es = []
    for e in plan.get("entries", []):
        e = dict(e)
        e["school"] = canon(e.get("school"))
        try:
            e["credits_counted"] = float(e.get("credits_counted"))
            e["cost_usd"] = float(e.get("cost_usd"))
        except Exception:
            problems.append(f"{e.get('school')} {e.get('code')}: credits/cost not numeric")
            continue
        if not is_iso(e.get("start")) or not is_iso(e.get("end")):
            problems.append(f"{e['school']} {e.get('code')}: start/end must be ISO YYYY-MM-DD (got {e.get('start')} / {e.get('end')})")
        elif e["end"] < e["start"]:
            problems.append(f"{e['school']} {e.get('code')}: end before start")
        es.append(e)
    if problems:
        return plan, problems
    es.sort(key=lambda e: (e["start"], e["end"], SORD.get(e["school"], 9), str(e.get("code"))))
    cc, cost = 0.0, 0.0
    blocks = OrderedDict()
    for i, e in enumerate(es):
        b = block_of(e["start"])
        e["seq"] = i + 1
        e["term_label"], e["block_key"], e["block_start"], e["block_end"] = b["label"], b["key"], b["start"], b["end"]
        e["duration_weeks"] = r3(days(e["start"], e["end"]) / 7)
        cc = r3(cc + e["credits_counted"]); cost += e["cost_usd"]
        e["cumulative_credits"] = cc; e["cumulative_cost_usd"] = round(cost)
        blk = blocks.setdefault(b["key"], {"term_label": b["label"], "block_key": b["key"], "order": b["order"], "start": b["start"], "end": b["end"],
                                            "courses": 0, "credits": 0.0, "cost_usd": 0.0, "schools": [], "peak_load": 0.0, "peak_date": "", "peak_concurrent": 0})
        blk["courses"] += 1; blk["credits"] = r3(blk["credits"] + e["credits_counted"]); blk["cost_usd"] += e["cost_usd"]
        if e["school"] not in blk["schools"]: blk["schools"].append(e["school"])

    def active(t):
        return [x for x in es if x["start"] <= t <= x["end"]]

    def load_at(t):
        return sum(x["credits_counted"] * 8 / max(1.0, days(x["start"], x["end"]) / 7) for x in active(t))

    for e in es:
        blk = blocks[e["block_key"]]
        l = load_at(e["start"])
        e["load_8wk_at_start"] = round(l * 10) / 10
        e["concurrent_at_start"] = len(active(e["start"]))
        if l > blk["peak_load"]:
            blk["peak_load"], blk["peak_date"] = l, e["start"]
        blk["peak_concurrent"] = max(blk["peak_concurrent"], len(active(e["start"])))
    per_term_load = [{"term_label": b["term_label"], "start": b["start"], "end": b["end"], "courses": b["courses"], "credits": b["credits"],
                      "cost_usd": round(b["cost_usd"]), "schools": " · ".join(b["schools"]), "peak_load_8wk": round(b["peak_load"] * 10) / 10,
                      "peak_date": b["peak_date"], "peak_concurrent": b["peak_concurrent"]} for b in sorted(blocks.values(), key=lambda b: b["order"])]
    per_school_totals = []
    for s in SCHOOLS:
        rows = [e for e in es if e["school"] == s]
        cr = r3(sum(e["credits_counted"] for e in rows)); c = round(sum(e["cost_usd"] for e in rows))
        per_school_totals.append({"school": s, "courses": len(rows), "credits": cr, "cost_usd": c, "per_credit_usd": round(c / cr) if cr else 0,
                                  "upper_division_credits": r3(sum(e["credits_counted"] for e in rows if "upper" in str(e.get("level", "")).lower()))})
    ud = r3(sum(e["credits_counted"] for e in es if "upper" in str(e.get("level", "")).lower()))
    first = es[0]; last = max(es, key=lambda e: e["end"])
    months = round(days(first["start"], last["end"]) / 30.44 * 10) / 10
    totals = {"credits": cc, "upper_division_credits": ud, "cost_usd": round(cost), "first_term": f"{first['term_label']} · {first['start']}",
              "last_term": f"{last['term_label']} · ends {last['end']}", "months": months, "courses": len(es), "per_credit_usd": round(cost / cc) if cc else 0}
    out = dict(plan); out.update({"entries": es, "per_term_load": per_term_load, "per_school_totals": per_school_totals, "totals": totals})
    return out, []


def check(plan):
    issues, info = [], []
    es = plan["entries"]
    by = lambda s: [e for e in es if e["school"] == s]
    for s, (cr, n) in TARGET.items():
        rows = by(s); tot = r3(sum(e["credits_counted"] for e in rows))
        if abs(tot - cr) > 0.0015: issues.append(f"{s}: credits sum to {tot}, must be exactly {cr}")
        if n is not None and len(rows) != n: issues.append(f"{s}: {len(rows)} rows, must be exactly {n} courses")
        info.append(f"{s}: {len(rows)} courses, {tot} credits, ${round(sum(e['cost_usd'] for e in rows))}")
    for e in es:
        if e["school"] not in SCHOOLS: issues.append(f"row {e.get('code')}: unrecognized school \"{e['school']}\"")
    if abs(plan["totals"]["credits"] - 150.334) > 0.0015: issues.append(f"grand total {plan['totals']['credits']}, must be exactly 150.334")
    for e in by("UCLA Extension"):
        if float(e.get("native_credits", 0)) != 4: issues.append(f"UCLA {e['code']}: native_credits {e.get('native_credits')}, every UCLA course must be 4 quarter units")
    for e in by("BYU IS"):
        w = days(e["start"], e["end"]) / 7
        if w > 15.2: issues.append(f"BYU {e['code']}: window {e['start']} -> {e['end']} is {r3(w)} weeks, must be <= 15")
        if e["credits_counted"] != 3: issues.append(f"BYU {e['code']}: credits {e['credits_counted']}, must be 3")
    for e in by("SNHU"):
        if e["credits_counted"] != 3: issues.append(f"SNHU {e['code']}: credits must be 3")
    for e in by("Harvard Extension"):
        if e["credits_counted"] != 4: issues.append(f"HES {e['code']}: credits must be 4")
        if "06-01" <= e["start"][5:10] <= "08-15": issues.append(f"HES {e['code']} starts {e['start']} in the summer term (expensive) - move to Fall (late Aug), January or Spring")
    sess = OrderedDict()
    for e in by("UMPI YourPace"):
        k = f"{e['start']}->{e['end']}"; v = sess.setdefault(k, {"cr": 0.0, "cost": 0.0, "n": 0})
        v["cr"] = r3(v["cr"] + e["credits_counted"]); v["cost"] += e["cost_usd"]; v["n"] += 1
    if len(sess) != 3: issues.append(f"UMPI: rows span {len(sess)} distinct session windows ({', '.join(sess)}), must be exactly 3 sessions")
    for k, v in sess.items():
        a, b = k.split("->"); w = days(a, b) / 7
        if w > 9 or w < 7: issues.append(f"UMPI session {k} is {r3(w)} weeks, must be an 8-week session")
        if v["cr"] > 15.001: issues.append(f"UMPI session {k} carries {v['cr']} credits (> 15)")
        if abs(v["cost"] - 1800) > 1: issues.append(f"UMPI session {k} rows cost ${round(v['cost'])}, must sum to exactly $1,800")
        info.append(f"UMPI session {k}: {v['n']} courses, {v['cr']} credits, ${round(v['cost'])}")
    seen = set()
    for e in es:
        k = e["school"] + "|" + re.sub(r"[\s-]+", "", str(e.get("code", "")).upper())
        if k in seen: issues.append(f"duplicate row {k}")
        seen.add(k)
    for b in plan["per_term_load"]:
        if b["peak_load_8wk"] > 16:
            issues.append(f"{b['term_label']}: peak load {b['peak_load_8wk']} on {b['peak_date']} ({b['peak_concurrent']} concurrent) exceeds the 15 ceiling (hard limit 16)")
        elif b["peak_load_8wk"] > 15:
            info.append(f"{b['term_label']}: peak load {b['peak_load_8wk']} on {b['peak_date']} (slightly above 15, tolerated)")
        else:
            info.append(f"{b['term_label']}: {b['courses']} courses start, {b['credits']} credits, ${b['cost_usd']}, peak load {b['peak_load_8wk']} on {b['peak_date']}")
    for e in es:
        if e["start"] < TODAY:
            if e["school"] != "ASU ULC": issues.append(f"{e['school']} {e['code']} starts {e['start']}, before today ({TODAY}); only ASU ULC Fall 2026 A/C were in progress")
            elif e.get("status") != "in-progress": issues.append(f"ASU ULC {e['code']} starts {e['start']} (already started) but status is not in-progress")
        elif e.get("status") == "in-progress":
            issues.append(f"{e['school']} {e['code']} starts {e['start']} (future) but is marked in-progress")
    if plan["totals"]["upper_division_credits"] < 45: issues.append(f"upper-division credits {plan['totals']['upper_division_credits']} < 45 minimum")
    for need in ("ASU101", "IDS321", "IDS402"):
        if not any(need in re.sub(r"\s+", "", str(s.get("asu_course", "")).upper()) for s in plan.get("substitutions", [])):
            issues.append(f"substitutions: no entry for {need}")
    for e in es:
        if not e.get("title_zh"): issues.append(f"{e['school']} {e['code']}: title_zh missing")
    t = plan["totals"]
    info.append(f"grand total {t['credits']} credits, {t['upper_division_credits']} upper-division, ${t['cost_usd']}, {t['first_term']} -> {t['last_term']} ({t['months']} months)")
    return issues, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    a = ap.parse_args()
    with open(a.inp, encoding="utf-8") as f:
        plan = json.load(f)
    plan, problems = normalize(plan)
    if problems:
        print("NORMALIZE PROBLEMS:"); [print(" -", p) for p in problems]; sys.exit(2)
    issues, info = check(plan)
    print("INFO:"); [print(" -", i) for i in info]
    print("ISSUES:" if issues else "ISSUES: none"); [print(" -", i) for i in issues]
    if a.out and not a.check_only:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=1)
        print("wrote", a.out)
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
