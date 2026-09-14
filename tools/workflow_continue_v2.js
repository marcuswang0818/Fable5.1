export const meta = {
  name: 'six-school-plan-continue',
  description: 'Resume the six-school ASU General Studies plan from the repo checkpoint: prerequisite-timeline review + course-code verification, settlement, deterministic bookkeeping and three adversarial verify lenses with a fix loop',
  phases: [
    { title: 'Round 2', detail: 'prerequisite-timeline reviewer (reconciles reviews #1/#2) and course-code verification scout' },
    { title: 'Settle', detail: 'merge into one chronological plan: 时间线 · 选课名 · 计学分 · 总消费' },
    { title: 'Verify', detail: 'deterministic arithmetic/schedule checks + requirements, schedule and pricing lenses; fix loop' },
  ],
}

// ---------------------------------------------------------------------------
// Inputs on disk (checkpoint digest, three parts)
// ---------------------------------------------------------------------------
const REPO = '/home/user/Fable5.1'
const FILES = ['data/checkpoint/digest_1_scouts.md', 'data/checkpoint/digest_2_plans.md', 'data/checkpoint/digest_3_reviews.md'].map(f => REPO + '/' + f)
const READ_FIRST = 'FIRST, before anything else, read these three files IN FULL with the Read tool (one call each; they are Markdown with long lines, 43-123 KB each; if a Read result is truncated, re-read the remainder with offset/limit; do NOT use Bash cat - its output gets truncated):\n' + FILES.map(f => '- ' + f).join('\n') + '\nPart 1 = scout briefs (ASU degree rules, calendars 2026-2029, prices, per-school strengths). Part 2 = the six round-1 school plans (primary courses + alternates, as drafted BEFORE round-2 swaps). Part 3 = the two completed round-2 reviews (#1 degree-requirements audit, #2 duplicate removal). Treat them as ground truth unless you verify otherwise with WebSearch.'

const TOOLING = 'TOOLING NOTES:\n- WebFetch is BLOCKED by the egress proxy. Do not use it.\n- WebSearch may work: call ToolSearch with query "select:WebSearch" to load it. The per-session search budget may be limited; if a search errors with a budget/limit message, stop searching and rely on the checkpoint files. Never silently invent course codes: tag every fact confirmed / likely / assumed.\n- Do not ask the user anything. State assumptions and continue. Your final output is the structured object only.'

const BRIEF = `PROJECT BRIEF - 爆学分臻享版 ASU Online BA in General Studies (credit-maxed edition)
Today is 2026-09-14. The student works full-time and studies part-time but is in the top 20% for both available time and academic ability. Nothing except the ASU ULC 2026 Fall A / Fall C courses has started yet; every other course must start on or after 2026-09-14 (UCLA Fall 2026 quarter, starting Sep 21, is still enrollable; SNHU 26EW1, UMPI Fall 1 2026 and HES Fall 2026 already began Aug 31 and are NOT available - next SNHU term 26EW2 Oct 26, next UMPI session Fall 2 Oct 26, next HES terms January 2027 (Jan 4-23) / Spring 2027 (Jan 25-May 15); BYU IS starts any day).

TARGET: Arizona State University, ASU Online, Bachelor of Arts in General Studies (LSGNSBGS, College of Integrative Sciences and Arts). 120 credits graduate, but the student deliberately accumulates EXACTLY 150.334 semester credits across six platforms, all of which must land on the ASU degree audit:
  1. SNHU Online: 12.000 = 4 x 3-credit courses, 8-week terms ($1,062 each, 2026-27).
  2. Harvard Extension School (HES): 12.000 = 3 x 4-credit undergraduate-credit courses ($2,260 each, 2026-27); use Fall / January / Spring terms only (summer costs $3,980).
  3. ASU Universal Learner Courses (ULC), SESSION-BASED only (follow ASU A/B/C sessions): 42.000 native ASU credits; 13 or 14 courses (4-credit lab sciences allowed) at $425 each ($25 + $400 conversion). 2026 Fall A courses (ENG 101, CIS 105, Aug 20-Oct 9) and Fall C (MAT 265, Aug 20-Dec 4) are ALREADY IN PROGRESS.
  4. UMPI YourPace (competency-based, $1,800 flat per 8-week session, unlimited courses): 42.000 credits in EXACTLY THREE 8-week sessions (about 14 credits per session, 15 max). The three sessions need NOT be consecutive - pick them so the concurrent load stays within limits.
  5. UCLA Extension: 21.334 = 8 x 4-quarter-unit XL courses (4 qu x 2/3 = 2.667; book exactly one course at 2.665 so the eight sum to exactly 21.334). Quarters: Fall (Sep 21-~Dec 12), Winter (Jan 4-~Mar 19), Spring (Mar 29-~Jun 11), Summer (Jun 21-~Sep 10). Prefer XL 1-199 (degree credit); X 400-series needs prior ASU written approval - avoid.
  6. BYU Independent Study: 21.000 = 7 x 3-credit university online courses ($768 each, 2025-26 rate), self-paced 12-month window but the student FINISHES EACH within one window of at most 15 weeks that you state as concrete start/end dates.
  TOTAL = 12 + 12 + 42 + 42 + 21.334 + 21 = 150.334 exactly.

THEMES: "Technology & Government" and "Socio-Technical Systems: Energy & Environment", with a personal specialty in POWER ELECTRONICS (physics/E&M, circuits/electronics, engineering-math ladder, energy systems, environment, technology policy, public administration, data/programming). 80/20 RULE: about 80% of each school's picks exploit that school's genuine strengths (取百家之长); about 20% may be cheap gen-ed filler chosen to save money (省钱).

USER OVERRIDES: ignore ASU's 30-credit residency rule (the 42 native ULC credits would satisfy it anyway). ASU 101, IDS 321 and IDS 402 are each SUBSTITUTED by one named course from the six platforms (抵课), and the freed slots are refilled. No questions to the user. Earliest realistic completion, not a leisurely pace. Cost = tuition/fees actually paid per course (state the price year).

DEGREE RULES THE UNION MUST SATISFY (from the scout): General Studies Gold - HUAD 6, SOBE 3, SCIT 8 (lab), QTRS 3, MATH 3, AMIT 3, CIVI 3, GCSI 3, SUST 3; First-Year Composition ENG 101 + 102; 45 upper-division credits; four topic areas x 3 courses (36 credits) with >= 18 upper-division among them; no ASU course number posted twice (equivalents count once).

LOAD METRIC (the deterministic checker uses exactly this): for every course start date, load = sum over all courses active that day of credits x 8 / duration_weeks. Examples: an 8-week 3-credit course = 3.0; a 16-week 3-credit course = 1.5; an 11-week 2.667-credit UCLA course = 1.9; a 6-week 4-credit ULC summer lab = 5.3; a 14-credit 8-week UMPI session = 14.0; a 3-week 4-credit HES January course = 10.7. Ceiling 15 at every course start date (16 is the hard blocking threshold); 9-13 is the comfortable norm; do not leave long windows far below 9 unless a platform calendar forces it.

TIMELINE GRID: the deliverable groups courses into ASU-style 8-week blocks by START date: 春A Jan 1-Feb 28/29, 春B Mar 1-Apr 30, 夏A May 1-Jun 27, 夏B Jun 28-Aug 15, 秋A Aug 16-Oct 10, 秋B Oct 11-Dec 31. You supply exact ISO start/end dates per course; the script assigns blocks, sequence numbers, cumulative columns, per-block loads and per-school totals.`

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const SCHOOLS = ['ASU ULC', 'UMPI YourPace', 'UCLA Extension', 'BYU IS', 'Harvard Extension', 'SNHU']

const ENTRY = { type: 'object', properties: {
  school: { type: 'string', enum: SCHOOLS },
  school_term: { type: 'string', description: 'the platform\'s own term name, e.g. "ASU Spring B 2027", "SNHU 27EW4", "UMPI YourPace Summer 1 2027", "UCLA Winter 2027", "HES Spring 2027", "BYU IS window"' },
  start: { type: 'string', description: 'ISO date YYYY-MM-DD, first day of the course' },
  end: { type: 'string', description: 'ISO date YYYY-MM-DD, last day (BYU: planned finish, at most 15 weeks after start)' },
  code: { type: 'string' }, title: { type: 'string' }, title_zh: { type: 'string', description: 'short Chinese title' },
  native_credits: { type: 'number' }, native_unit: { type: 'string', enum: ['semester', 'quarter'] },
  credits_counted: { type: 'number', description: 'semester credits counted toward 150.334 (UCLA: 2.667, exactly one UCLA course at 2.665)' },
  level: { type: 'string', enum: ['lower', 'upper'] },
  requirement_bucket: { type: 'string', description: 'e.g. "Gold: SCIT", "FYC", "Gold: HUAD", "Topic area 1 (UD)", "IDS 321 substitute", "UD elective"' },
  cluster_or_theme: { type: 'string' },
  theme_tag: { type: 'string', enum: ['primary-strength', 'secondary-savings'] },
  prereqs_satisfied_by: { type: 'string', description: '"none" or which course/platform supplies each prerequisite and when its grade posts' },
  cost_usd: { type: 'number', description: 'USD paid for this course (UMPI: the $1,800 session fee split pro-rata so each session\'s rows sum to exactly 1800)' },
  cost_basis: { type: 'string' },
  status: { type: 'string', enum: ['in-progress', 'planned'] },
  confidence: { type: 'string', enum: ['confirmed', 'likely', 'assumed'] },
  fallback: { type: 'string', description: 'named replacement (same school, same credits) if this code/term is unavailable' },
  note: { type: 'string' } },
  required: ['school', 'school_term', 'start', 'end', 'code', 'title', 'title_zh', 'native_credits', 'native_unit', 'credits_counted', 'level', 'requirement_bucket', 'theme_tag', 'prereqs_satisfied_by', 'cost_usd', 'status', 'confidence'] }

const REVIEW3_SCHEMA = { type: 'object', properties: {
  reviewer: { type: 'string' }, verdict: { type: 'string' },
  conflict_resolutions: { type: 'array', items: { type: 'object', properties: { conflict: { type: 'string' }, chosen: { type: 'string' }, reason: { type: 'string' } }, required: ['conflict', 'chosen', 'reason'] } },
  findings: { type: 'array', items: { type: 'object', properties: { severity: { type: 'string', enum: ['blocking', 'major', 'minor'] }, school: { type: 'string' }, course: { type: 'string' }, issue: { type: 'string' }, action: { type: 'string' } }, required: ['severity', 'issue', 'action'] } },
  dependency_graph: { type: 'string', description: 'markdown list: dependent course <- prerequisite (supplier, grade-post date, how the receiving school verifies)' },
  ordered_timeline: { type: 'string', description: 'markdown table: start | end | block | school | code | title | credits | level | prereqs satisfied by | load at start | running credits' },
  reconciled_union: { type: 'array', items: ENTRY },
  notes: { type: 'string' } },
  required: ['reviewer', 'verdict', 'conflict_resolutions', 'findings', 'dependency_graph', 'ordered_timeline', 'reconciled_union', 'notes'] }

const CODECHECK_SCHEMA = { type: 'object', properties: {
  searches_run: { type: 'number' }, budget_exhausted: { type: 'boolean' },
  checks: { type: 'array', items: { type: 'object', properties: { school: { type: 'string' }, code: { type: 'string' }, title: { type: 'string' }, status: { type: 'string', enum: ['confirmed', 'likely', 'not_found', 'wrong'] }, evidence: { type: 'string' }, correction: { type: 'string', description: 'corrected code/title/credits/term/price, or a same-school same-credit on-theme replacement if not found' } }, required: ['school', 'code', 'status', 'evidence'] } },
  calendar_price_updates: { type: 'array', items: { type: 'string' } },
  transfer_rule_findings: { type: 'array', items: { type: 'string' } },
  notes: { type: 'string' } },
  required: ['searches_run', 'budget_exhausted', 'checks', 'notes'] }

const FINAL_SCHEMA = { type: 'object', properties: {
  degree_summary: { type: 'string', description: 'English summary plus one Chinese paragraph' },
  assumptions: { type: 'array', items: { type: 'string' } },
  substitutions: { type: 'array', items: { type: 'object', properties: { asu_course: { type: 'string' }, substitute: { type: 'string' }, justification: { type: 'string' } }, required: ['asu_course', 'substitute', 'justification'] } },
  entries: { type: 'array', items: ENTRY },
  requirement_matrix: { type: 'string', description: 'markdown table: ASU requirement bucket -> satisfying course(s) -> status' },
  cluster_mapping: { type: 'string', description: 'how the two themes map to the four ASU topic areas and which 3 courses fill each' },
  reconciliation_notes: { type: 'string', description: 'how conflicts between reviewers #1, #2, #3 and the code scout were resolved' },
  eighty_twenty: { type: 'string', description: 'per-school primary-strength vs secondary-savings count and the theme coverage' },
  risks: { type: 'array', items: { type: 'string' } },
  verification_todo: { type: 'array', items: { type: 'string' }, description: 'things to confirm on official sites before enrolling, in date order' },
  sources: { type: 'array', items: { type: 'string' } } },
  required: ['degree_summary', 'assumptions', 'substitutions', 'entries', 'requirement_matrix', 'cluster_mapping', 'reconciliation_notes', 'eighty_twenty', 'risks', 'verification_todo'] }

const VERDICT_SCHEMA = { type: 'object', properties: {
  lens: { type: 'string' },
  refuted: { type: 'boolean', description: 'true if the plan has at least one BLOCKING defect under this lens' },
  blocking: { type: 'array', items: { type: 'object', properties: { issue: { type: 'string' }, fix: { type: 'string' } }, required: ['issue', 'fix'] } },
  minor: { type: 'array', items: { type: 'object', properties: { issue: { type: 'string' }, fix: { type: 'string' } }, required: ['issue', 'fix'] } },
  checked: { type: 'string', description: 'what you verified and found OK' } },
  required: ['lens', 'refuted', 'blocking', 'minor', 'checked'] }

// ---------------------------------------------------------------------------
// Deterministic bookkeeping: blocks, sequence, cumulative columns, loads, totals
// ---------------------------------------------------------------------------
const BLOCKS = [['春 A', 'Spring A', '01-01', '02-29'], ['春 B', 'Spring B', '03-01', '04-30'], ['夏 A', 'Summer A', '05-01', '06-27'], ['夏 B', 'Summer B', '06-28', '08-15'], ['秋 A', 'Fall A', '08-16', '10-10'], ['秋 B', 'Fall B', '10-11', '12-31']]
const NOMINAL = { '2026 秋 A': ['2026-08-20', '2026-10-09'], '2026 秋 B': ['2026-10-14', '2026-12-04'], '2027 春 A': ['2027-01-11', '2027-03-02'], '2027 春 B': ['2027-03-15', '2027-04-30'], '2027 夏 A': ['2027-05-17', '2027-06-25'], '2027 夏 B': ['2027-06-30', '2027-08-10'], '2027 秋 A': ['2027-08-19', '2027-10-08'], '2027 秋 B': ['2027-10-13', '2027-12-03'], '2028 春 A': ['2028-01-10', '2028-03-01'], '2028 春 B': ['2028-03-13', '2028-04-28'], '2028 夏 A': ['2028-05-16', '2028-06-26'], '2028 夏 B': ['2028-06-29', '2028-08-09'], '2028 秋 A': ['2028-08-17', '2028-10-06'], '2028 秋 B': ['2028-10-11', '2028-12-01'] }
function blockOf(start) {
  const y = start.slice(0, 4), md = start.slice(5, 10)
  let i = BLOCKS.findIndex(b => md <= b[3]); if (i < 0) i = 5
  const b = BLOCKS[i]; const key = y + ' ' + b[0]
  const nom = NOMINAL[key] || [y + '-' + b[2], y + '-' + (b[3] === '02-29' ? '02-28' : b[3])]
  return { key, label: key + ' (' + b[1] + ' ' + y + ')', order: Number(y) * 10 + i, start: nom[0], end: nom[1] }
}
const DAY = 86400000
const toDate = s => new Date(s + 'T00:00:00Z')
const days = (a, b) => Math.round((toDate(b) - toDate(a)) / DAY) + 1
const isIso = s => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(toDate(s).getTime())
const r3 = x => Math.round(x * 1000) / 1000
const SORD = { 'ASU ULC': 0, 'UMPI YourPace': 1, 'UCLA Extension': 2, 'BYU IS': 3, 'Harvard Extension': 4, 'SNHU': 5 }
const TARGET = { 'SNHU': [12, 4], 'Harvard Extension': [12, 3], 'ASU ULC': [42, null], 'UMPI YourPace': [42, null], 'UCLA Extension': [21.334, 8], 'BYU IS': [21, 7] }
function canon(s) { const t = (s || '').toLowerCase(); if (/snhu|southern new hampshire/.test(t)) return 'SNHU'; if (/harvard|\bhes\b/.test(t)) return 'Harvard Extension'; if (/umpi|presque|yourpace/.test(t)) return 'UMPI YourPace'; if (/ucla/.test(t)) return 'UCLA Extension'; if (/byu|brigham/.test(t)) return 'BYU IS'; if (/asu|ulc|universal learner/.test(t)) return 'ASU ULC'; return s }

function normalize(plan) {
  const problems = []
  const es = (plan.entries || []).map(e => ({ ...e, school: canon(e.school), credits_counted: Number(e.credits_counted), cost_usd: Number(e.cost_usd) }))
  for (const e of es) {
    if (!isIso(e.start) || !isIso(e.end)) problems.push(e.school + ' ' + e.code + ': start/end must be ISO YYYY-MM-DD (got ' + e.start + ' / ' + e.end + ')')
    else if (e.end < e.start) problems.push(e.school + ' ' + e.code + ': end before start')
    if (!(e.credits_counted > 0)) problems.push(e.school + ' ' + e.code + ': credits_counted missing')
    if (!(e.cost_usd >= 0)) problems.push(e.school + ' ' + e.code + ': cost_usd missing')
  }
  if (problems.length) return { plan, problems }
  es.sort((a, b) => a.start.localeCompare(b.start) || a.end.localeCompare(b.end) || ((SORD[a.school] ?? 9) - (SORD[b.school] ?? 9)) || String(a.code).localeCompare(String(b.code)))
  let cc = 0, cost = 0
  const blocks = new Map()
  es.forEach((e, i) => {
    const b = blockOf(e.start)
    e.seq = i + 1; e.term_label = b.label; e.block_key = b.key; e.block_start = b.start; e.block_end = b.end
    e.duration_weeks = r3(days(e.start, e.end) / 7)
    cc = r3(cc + e.credits_counted); cost += e.cost_usd
    e.cumulative_credits = cc; e.cumulative_cost_usd = Math.round(cost)
    if (!blocks.has(b.key)) blocks.set(b.key, { term_label: b.label, block_key: b.key, order: b.order, start: b.start, end: b.end, courses: 0, credits: 0, cost_usd: 0, schools: new Set(), peak_load: 0, peak_date: '', peak_concurrent: 0 })
    const blk = blocks.get(b.key); blk.courses++; blk.credits = r3(blk.credits + e.credits_counted); blk.cost_usd += e.cost_usd; blk.schools.add(e.school)
  })
  const active = t => es.filter(x => x.start <= t && x.end >= t)
  const loadAt = t => active(t).reduce((n, x) => n + x.credits_counted * 8 / Math.max(1, days(x.start, x.end) / 7), 0)
  for (const e of es) {
    const blk = blocks.get(e.block_key); const l = loadAt(e.start)
    e.load_8wk_at_start = Math.round(l * 10) / 10; e.concurrent_at_start = active(e.start).length
    if (l > blk.peak_load) { blk.peak_load = l; blk.peak_date = e.start }
    blk.peak_concurrent = Math.max(blk.peak_concurrent, active(e.start).length)
  }
  const per_term_load = [...blocks.values()].sort((a, b) => a.order - b.order).map(b => ({ term_label: b.term_label, start: b.start, end: b.end, courses: b.courses, credits: b.credits, cost_usd: Math.round(b.cost_usd), schools: [...b.schools].join(' · '), peak_load_8wk: Math.round(b.peak_load * 10) / 10, peak_date: b.peak_date, peak_concurrent: b.peak_concurrent }))
  const per_school_totals = SCHOOLS.map(s => { const rows = es.filter(e => e.school === s); const cr = r3(rows.reduce((n, e) => n + e.credits_counted, 0)); const c = Math.round(rows.reduce((n, e) => n + e.cost_usd, 0)); return { school: s, courses: rows.length, credits: cr, cost_usd: c, per_credit_usd: cr ? Math.round(c / cr) : 0, upper_division_credits: r3(rows.filter(e => /upper/i.test(e.level)).reduce((n, e) => n + e.credits_counted, 0)) } })
  const ud = r3(es.filter(e => /upper/i.test(e.level)).reduce((n, e) => n + e.credits_counted, 0))
  const first = es[0], last = es.reduce((m, e) => e.end > m.end ? e : m, es[0])
  const months = Math.round(days(first.start, last.end) / 30.44 * 10) / 10
  const totals = { credits: cc, upper_division_credits: ud, cost_usd: Math.round(cost), first_term: first.term_label + ' · ' + first.start, last_term: last.term_label + ' · ' + last.end, months, courses: es.length, per_credit_usd: Math.round(cost / cc) }
  return { plan: { ...plan, entries: es, per_term_load, per_school_totals, totals }, problems: [] }
}

function check(plan) {
  const issues = [], info = []
  const es = plan.entries
  const bySchool = s => es.filter(e => e.school === s)
  for (const [s, tgt] of Object.entries(TARGET)) {
    const rows = bySchool(s); const sum = r3(rows.reduce((a, e) => a + e.credits_counted, 0))
    if (Math.abs(sum - tgt[0]) > 0.0015) issues.push(s + ': credits sum to ' + sum + ', must be exactly ' + tgt[0])
    if (tgt[1] !== null && rows.length !== tgt[1]) issues.push(s + ': ' + rows.length + ' rows, must be exactly ' + tgt[1] + ' courses')
    const c = Math.round(rows.reduce((a, e) => a + e.cost_usd, 0)); info.push(s + ': ' + rows.length + ' courses, ' + sum + ' credits, $' + c)
  }
  for (const e of es) if (!SCHOOLS.includes(e.school)) issues.push('row ' + e.code + ': unrecognized school "' + e.school + '"')
  if (Math.abs(plan.totals.credits - 150.334) > 0.0015) issues.push('grand total ' + plan.totals.credits + ', must be exactly 150.334')
  for (const e of bySchool('UCLA Extension')) if (Number(e.native_credits) !== 4) issues.push('UCLA ' + e.code + ': native_credits ' + e.native_credits + ', every UCLA course must be 4 quarter units')
  for (const e of bySchool('BYU IS')) { const w = days(e.start, e.end) / 7; if (w > 15.2) issues.push('BYU ' + e.code + ': window ' + e.start + ' -> ' + e.end + ' is ' + r3(w) + ' weeks, must be <= 15'); if (e.credits_counted !== 3) issues.push('BYU ' + e.code + ': credits ' + e.credits_counted + ', must be 3') }
  for (const e of bySchool('SNHU')) if (e.credits_counted !== 3) issues.push('SNHU ' + e.code + ': credits must be 3')
  for (const e of bySchool('Harvard Extension')) { if (e.credits_counted !== 4) issues.push('HES ' + e.code + ': credits must be 4'); const md = e.start.slice(5, 10); if (md >= '06-01' && md <= '08-15') issues.push('HES ' + e.code + ' starts ' + e.start + ' in the summer term (expensive $3,980) - move to Fall (late Aug), January or Spring') }
  const sess = new Map(); for (const e of bySchool('UMPI YourPace')) { const k = e.start + '->' + e.end; const v = sess.get(k) || { cr: 0, cost: 0, n: 0 }; v.cr = r3(v.cr + e.credits_counted); v.cost += e.cost_usd; v.n++; sess.set(k, v) }
  if (sess.size !== 3) issues.push('UMPI: rows span ' + sess.size + ' distinct session windows (' + [...sess.keys()].join(', ') + '), must be exactly 3 sessions (need not be consecutive)')
  for (const [k, v] of sess) { const w = days(k.split('->')[0], k.split('->')[1]) / 7; if (w > 9 || w < 7) issues.push('UMPI session ' + k + ' is ' + r3(w) + ' weeks, must be an 8-week session'); if (v.cr > 15.001) issues.push('UMPI session ' + k + ' carries ' + v.cr + ' credits (> 15)'); if (Math.abs(v.cost - 1800) > 1) issues.push('UMPI session ' + k + ' rows cost $' + Math.round(v.cost) + ', must sum to exactly $1,800'); info.push('UMPI session ' + k + ': ' + v.n + ' courses, ' + v.cr + ' credits, $' + Math.round(v.cost)) }
  const seen = new Set(); for (const e of es) { const k = e.school + '|' + String(e.code).toUpperCase().replace(/[\s-]+/g, ''); if (seen.has(k)) issues.push('duplicate row ' + k); seen.add(k) }
  for (const b of plan.per_term_load) { if (b.peak_load_8wk > 16) issues.push(b.term_label + ': peak load ' + b.peak_load_8wk + ' 8-week-equivalent credits on ' + b.peak_date + ' (' + b.peak_concurrent + ' concurrent courses) exceeds the 15 ceiling (hard limit 16) - move a course out of this window'); else if (b.peak_load_8wk > 15) info.push(b.term_label + ': peak load ' + b.peak_load_8wk + ' on ' + b.peak_date + ' (slightly above 15, tolerated)'); else info.push(b.term_label + ': ' + b.courses + ' courses start, ' + b.credits + ' credits, $' + b.cost_usd + ', peak load ' + b.peak_load_8wk + ' on ' + b.peak_date) }
  for (const e of es) {
    if (e.start < '2026-09-14') {
      if (e.school !== 'ASU ULC') issues.push(e.school + ' ' + e.code + ' starts ' + e.start + ', before today (2026-09-14); only ASU ULC 2026 Fall A/C courses were already in progress - everything else must start on or after 2026-09-14')
      else if (e.status !== 'in-progress') issues.push('ASU ULC ' + e.code + ' starts ' + e.start + ' (already started) but status is not in-progress')
    } else if (e.status === 'in-progress') issues.push(e.school + ' ' + e.code + ' starts ' + e.start + ' (future) but is marked in-progress')
  }
  if (plan.totals.upper_division_credits < 45) issues.push('upper-division credits ' + plan.totals.upper_division_credits + ' < 45 minimum')
  for (const need of ['ASU101', 'IDS321', 'IDS402']) if (!(plan.substitutions || []).some(s => String(s.asu_course || '').toUpperCase().replace(/\s+/g, '').includes(need))) issues.push('substitutions: no entry for ' + need)
  for (const e of es) if (!e.title_zh) issues.push(e.school + ' ' + e.code + ': title_zh missing')
  info.push('grand total ' + plan.totals.credits + ' credits, ' + plan.totals.upper_division_credits + ' upper-division, $' + plan.totals.cost_usd + ', ' + plan.totals.first_term + ' -> ' + plan.totals.last_term + ' (' + plan.totals.months + ' months)')
  return { issues, info }
}

// ---------------------------------------------------------------------------
// Phase: Round 2 — reviewer #3 + code-verification scout (settle needs both → barrier)
// ---------------------------------------------------------------------------
phase('Round 2')
const REVIEW3_PROMPT = `${TOOLING}\n\n${READ_FIRST}\n\n${BRIEF}\n\n=== YOUR ROLE: Round-2 reviewer #3 - CLARIFY THE TIMELINE OF PREREQUISITES NEEDED, and produce the reconciled union ===
1. Start from the six round-1 plans (part 2) and APPLY the round-2 swaps (part 3). Reviewers #1 and #2 disagree in places, e.g.: HES PHYS E-1bx -> GOVT E-1820 (#1) vs -> PHYS E-123 Laboratory Electronics (#2); economics: drop ULC ECN 212 -> HST 102 and keep UMPI ECO 208 (#1) vs keep ULC ECN 212, UMPI ECO 208 -> ECO 207, UCLA ECON XL 2 -> COM SCI XL 32 (#2); BYU ECON 110 -> HIST 201 (#1) vs -> GEOL 101 (#2); UCLA ENVIRON X 400 -> MATH XL 61 (#1) vs -> PSYCH XL 10 (#2); the three linear-algebra courses; ULC CSE 110 -> RAS 210 (#1) vs -> HST 102 (#2); UMPI POS 201 / SOC 100 -> 300-level (#1). For EACH conflict choose ONE option by this priority: (a) power-electronics / theme value, (b) upper-division margin and Gold coverage, (c) prerequisite feasibility on the calendar, (d) cost. Record every choice in conflict_resolutions. Keep every school's credit total exact (12 / 12 / 42 / 42 / 21.334 / 21) and the 80/20 balance.
2. Build the prerequisite dependency graph across all platforms: which course supplies which prerequisite and how the receiving school verifies it (SNHU needs an official transcript for MAT-350's Calculus I; ASU ULC checks placement for MAT/PHY/CHM; UCLA Extension XL math enforces its own sequence 31B -> 32A / 33A -> 33B; HES and BYU IS mostly do not enforce; UMPI YourPace enforces within its catalog). Grade-posting lags matter: ASU Fall B/C grades post about Dec 7-14, 2026; UCLA quarter grades about two weeks after quarter end; SNHU about one week after term end.
3. Place EVERY course on concrete ISO dates (start/end) using the platform calendars in part 1. Constraints: prerequisites complete (grade posted) BEFORE the dependent course starts; UMPI = exactly three 8-week sessions (not necessarily consecutive; about 14 credits each, 15 max; each session's rows cost $1,800 split pro-rata); each BYU course at most 15 weeks with stated dates; HES Fall/January/Spring only; nothing except ULC 2026 Fall A/C starts before 2026-09-14 (those rows are status in-progress); load <= 15 by the LOAD METRIC at every course start date; earliest realistic completion under that ceiling.
4. Compute the load at every course start date yourself (show it in the ordered_timeline) and list any window above 15 with a concrete move.
Output: conflict_resolutions; findings (severity + concrete OUT/IN or MOVE actions); dependency_graph; ordered_timeline (markdown table: start | end | block | school | code | title | credits | level | prereqs satisfied by | load at start | running credits); reconciled_union (one entry per course with every ENTRY field, ISO dates, per-course cost, confidence tag, fallback for every assumed/likely code); notes (grade-posting timing, registration deadlines, open risks). Be exhaustive and concrete.`

const CODECHECK_PROMPT = `${TOOLING}\n\n${READ_FIRST}\n\n${BRIEF}\n\n=== YOUR ROLE: course-code, calendar and price VERIFICATION scout ===
The previous session's search budget ran out before the round-2 reviews, so many codes are 'assumed' or 'likely'. Use WebSearch (load it with ToolSearch "select:WebSearch"); aim for 40-70 targeted searches, stop when the budget errors. Work in this priority order and record every result:
 A. UMPI YourPace official undergraduate course list (search terms like "YourPace" "course offerings" umpi.edu, catalog.umpi.edu "BUS 100", "YourPace Business Administration courses"): confirm or correct each of BUS 100, ECO 207, ECO 208, HTY 162, PHI 151, BUS 301, BUS 315, BUS 343, BUS 355, BUS 371, BUS 340, BUS 385, BUS 470, ENV 110, SOC 100, POS 201, MAT 180; note which are actually offered in YourPace (competency-based) vs only the traditional catalog; the flat per-session price ($1,800?) and 2027 session dates; whether non-degree/visiting students may enroll and how many courses per session are allowed.
 B. UCLA Extension 2026-27: availability, term and fee of COM SCI XL 31, COM SCI XL 32, MATH XL 31B, MATH XL 32A, MATH XL 32B, MATH XL 33A, MATH XL 33B, MATH XL 61, MATH XL 115A, PSYCH XL 10, ECON XL 1, ECON XL 2, PHYSICS XL 10, PHYSICS XL 6B; the enforced prerequisite of MATH XL 33B (31B only, or 33A?); Fall 2026 / Winter 2027 quarter dates.
 C. Harvard Extension 2026-27 (and 2027-28 if listed): PHYS E-123 Laboratory Electronics (undergraduate-credit option? which term? lab-kit cost), GOVT E-1820, CSCI E-45b, ENVR E-101 (undergraduate credit?), GOVT E-1113, GOVT E-1897, PHYS E-1bx; per-course undergraduate-credit tuition 2026-27; January-session 4-credit courses on technology/government/energy.
 D. BYU Independent Study university courses currently offered: POLI 170, GEOL 101, HIST 201, HIST 202, PHSCS 105, PHSCS 106, STAT 121, GEOG 120, ENGL 316, PHIL 213, CS 142, POLI 110, ECON 110; price per credit 2026.
 E. ASU ULC session-based catalog: HST 102, RAS 210, TEL 111 (credit value), CIS 308, PHY 194, AST 111, BIO 100, CHM 114, SOS 100, POS 110, HST 110, HST 101, GCU 102, MAT 142, ECN 211, ECN 212 - which are offered session-based in Spring / Summer / Fall 2027; current price.
 F. SNHU: IDS-401, IDS-403, IDS-400, MAT-350 (prerequisite MAT-225?), SCI-220; can a non-degree/visiting student register for IDS-4xx; 2026-27 term dates; tuition $354/credit?
 G. ASU transfer rules: 'credit is allowed for only CSE 100 or CSE 110'; 'MAT 342 or MAT 343'; whether General Studies Gold allows one course to satisfy two Gold designations; ASU treatment of UCLA Extension X 400-series and of competency-based transfer credit; ASU 101 waiver for transfer students.
For every code report status confirmed / likely / not_found / wrong with the snippet evidence and a correction or replacement (same school, same credits, on-theme). Put price/calendar updates and transfer-rule findings in their own arrays. Be honest about what you could not verify and report searches_run and budget_exhausted.`

const [review3, codecheck] = await parallel([
  () => agent(REVIEW3_PROMPT, { label: 'review:prerequisite-timeline', phase: 'Round 2', schema: REVIEW3_SCHEMA, effort: 'xhigh' }),
  () => agent(CODECHECK_PROMPT, { label: 'scout:verify-codes', phase: 'Round 2', schema: CODECHECK_SCHEMA, effort: 'high' }),
])
if (!review3) throw new Error('reviewer #3 returned null')
log(`Round 2 done: reviewer #3 ${review3.findings.length} findings, ${review3.reconciled_union.length} union rows; code scout ${codecheck ? codecheck.checks.length + ' checks, ' + codecheck.searches_run + ' searches' : 'FAILED'}`)
const REVIEW3_JSON = JSON.stringify(review3, null, 1)
const CODECHECK_JSON = codecheck ? JSON.stringify(codecheck, null, 1) : '(code-verification scout failed; rely on the checkpoint confidence tags)'

// ---------------------------------------------------------------------------
// Phase: Settle → deterministic check + three lenses → fix loop
// ---------------------------------------------------------------------------
phase('Settle')
const SETTLE_RULES = `=== YOUR ROLE: SETTLEMENT (结算) ===
Merge everything into ONE final plan. Inputs: the three checkpoint files (read them first), reviewer #3's reconciled union / ordered timeline / conflict resolutions, and the code-verification scout's results (apply its corrections: a 'wrong' or 'not_found' code must be replaced by its correction or by an on-theme same-credit course at the same school; update prices/dates it corrected).
Hard rules:
- Per-school credits exact: SNHU 12 (4 courses) / HES 12 (3) / ASU ULC 42 (13-14) / UMPI 42 in exactly three 8-week sessions (need not be consecutive; <= 15 credits per session; each session's rows cost exactly $1,800 in total, split pro-rata) / UCLA 21.334 (8 x 4 qu; exactly one course booked at 2.665) / BYU 21 (7 x 3, each window <= 15 weeks). Grand total 150.334.
- Only ASU ULC 2026 Fall A/C rows may start before 2026-09-14; mark them status in-progress; everything else status planned and starting on/after 2026-09-14 on a real term start date of that platform.
- Prerequisites (grade posted) strictly before the dependent course starts; UCLA math sequence in order; SNHU MAT-350 only after the ASU MAT 265 grade posts (mid-Dec 2026).
- LOAD <= 15 at every course start date by the LOAD METRIC (hard limit 16). Earliest realistic completion under that ceiling; no idle windows unless a calendar forces them.
- HES Fall/January/Spring only. Prices: ULC $425, SNHU $1,062, HES $2,260, BYU $768, UCLA per the 2026 fee tier of each course (state it), UMPI $1,800 per session.
- Exactly one substitute each for ASU 101, IDS 321 and IDS 402, listed in substitutions AND present as a row whose requirement_bucket names the substitution; a substitute is not also counted as a topic-area course.
- Gold buckets (HUAD 6, SOBE 3, SCIT 8 lab, QTRS 3, MATH 3, AMIT 3, CIVI 3, GCSI 3, SUST 3), FYC, 45 upper-division credits, four topic areas x 3 courses with >= 18 UD, all covered; no ASU equivalent posted twice.
- Every row carries: ISO start/end, school_term, title_zh (short Chinese), requirement_bucket, cluster_or_theme, theme_tag (about 80% primary-strength per school), prereqs_satisfied_by, cost_usd, cost_basis, status, confidence, and a fallback for every assumed/likely code.
Output all FINAL_SCHEMA fields: degree_summary (English + one Chinese paragraph), assumptions (with price years), substitutions, entries, requirement_matrix (markdown), cluster_mapping, reconciliation_notes, eighty_twenty, risks, verification_todo (date-ordered), sources.
Do NOT compute seq / cumulative / per-block totals - the script derives them from your ISO dates. DO compute and double-check before returning: per-school credit sums, the 150.334 grand total, each UMPI session's credit and cost sums, and the load at every course start date.`

const settlePrompt = (feedback) => `${TOOLING}\n\n${READ_FIRST}\n\n${BRIEF}\n\n=== ROUND-2 REVIEWER #3 (prerequisite timeline, reconciled union) ===\n${REVIEW3_JSON}\n\n=== CODE / CALENDAR / PRICE VERIFICATION SCOUT ===\n${CODECHECK_JSON}\n\n${SETTLE_RULES}${feedback ? '\n\n' + feedback : ''}`

const feedbackBlock = (plan, blocking, minor) => `=== PREVIOUS PLAN (JSON, normalized by the script: seq, blocks, cumulative columns, loads and totals were derived from your dates) ===\n${JSON.stringify(plan, null, 1)}\n\n=== DEFECTS TO FIX (mandatory, all of them) ===\n${blocking.join('\n')}\n\n=== MINOR (fix if cheap) ===\n${minor.join('\n') || '(none)'}\n\nReturn the COMPLETE corrected plan (every field, every row). Change as little as necessary: keep rows that are not implicated; when a fix needs a swap, take the replacement from the checkpoint alternates or the scout corrections and keep the school's credit total exact. Re-check per-school sums, UMPI sessions, prerequisite ordering and the load at every start date before returning.`

const LENSES = [
  { key: 'requirements', prompt: 'DEGREE-REQUIREMENTS lens: try to REFUTE that this plan graduates the student with an ASU BA in General Studies (ignoring residency). Check against the scout degree rules: General Studies Gold HUAD 6 / SOBE 3 / SCIT 8 lab / QTRS 3 / MATH 3 / AMIT 3 / CIVI 3 / GCSI 3 / SUST 3 (one course per Gold designation unless the plan documents otherwise), FYC ENG 101+102, 45 upper-division credits (only rows plausibly posted as 300/400-level by ASU count - question HES/UCLA/UMPI level claims), four topic areas x 3 courses with >= 18 UD, exactly one substitute each for ASU 101 / IDS 321 / IDS 402 that is not double-used as a topic-area course, no ASU equivalent posted twice (economics, physics, government, programming, linear algebra, sustainability, statistics), nothing likely non-transferable (UCLA X 400-series, pass/fail, professional credit). Also check the 80/20 strengths-vs-savings intent per school and that both themes plus power electronics are visibly served. A missing bucket, a double count, or a non-transferable row is BLOCKING with a concrete swap keeping per-school totals exact; everything else is minor.' },
  { key: 'schedule', prompt: 'SCHEDULE-FEASIBILITY lens: try to REFUTE the timeline. For every row check: the start/end dates are real term dates of that platform per the scout calendar (ASU A/B/C sessions, SNHU 8-week terms, HES Fall/January/Spring, UMPI 8-week sessions, UCLA quarters, BYU self-chosen windows <= 15 weeks); every prerequisite is complete WITH GRADE POSTED before the dependent course starts (across platforms, including transcript-delivery time for SNHU MAT-350 and the UCLA math sequence); registration is still possible (nothing except ULC Fall 2026 A/C starts before 2026-09-14; UCLA Fall 2026 enrollment by Sep 21 is fine); the UMPI 42 credits sit in exactly three 8-week sessions with a stated per-session pace; HES rows avoid summer; the per-start-date loads reported by the deterministic checker stay <= 15 and the plan has no needless idle windows (earliest realistic completion). A prerequisite violation, an impossible date, or an overload is BLOCKING with a concrete move; everything else is minor.' },
  { key: 'pricing-integrity', prompt: 'PRICING & DATA-INTEGRITY lens: try to REFUTE the numbers and labels. Check every row\'s cost against the scout price sheet (ULC $425 = $25 + $400; SNHU $1,062 at $354/credit 2026-27; HES $2,260 per 4-credit UG-credit course 2026-27; BYU $768 at $256/credit; UCLA per-course 2026 fee tiers $848-$1,330 by subject - flag any UCLA row priced outside its tier; UMPI $1,800 flat per session split pro-rata so each session sums to exactly $1,800), that price years are stated in assumptions, that UCLA credits are 4 qu = 2.667 with exactly one 2.665, that every row has a sensible title_zh, requirement_bucket, cluster_or_theme, theme_tag, confidence and (for assumed/likely) a fallback, that codes marked wrong/not_found by the code scout were replaced, that the requirement_matrix and cluster_mapping agree with the rows, and that the verification_todo is complete and date-ordered. Wrong price, missing session-sum, wrong credit value, or a row contradicting the scout corrections is BLOCKING; cosmetic problems are minor.' },
]
const lensPrompt = (l, plan, det) => `${TOOLING}\n\n${READ_FIRST}\n\n${BRIEF}\n\n=== FINAL PLAN UNDER TEST (JSON; seq, blocks, cumulative columns, per-block loads and totals were computed deterministically by the script) ===\n${JSON.stringify(plan, null, 1)}\n\n=== DETERMINISTIC CHECK RESULTS ===\nIssues: ${det.issues.length ? '\n- ' + det.issues.join('\n- ') : '(none)'}\nInfo:\n- ${det.info.join('\n- ')}\n\n=== YOUR LENS ===\n${l.prompt}\nDo not repeat the deterministic issues above; find what a script cannot. Set refuted=true only for genuine BLOCKING defects; list minor issues separately; describe what you checked and found OK.`

const history = []
let final = null
let settled = await agent(settlePrompt(''), { label: 'settle:v1', phase: 'Settle', schema: FINAL_SCHEMA, effort: 'xhigh' })
if (!settled) settled = await agent(settlePrompt(''), { label: 'settle:v1-retry', phase: 'Settle', schema: FINAL_SCHEMA, effort: 'xhigh' })
if (!settled) throw new Error('settlement agent returned null twice')
let norm = normalize(settled)

phase('Verify')
const MAX_ROUNDS = 4
for (let round = 1; round <= MAX_ROUNDS; round++) {
  const det = norm.problems.length ? { issues: norm.problems, info: [] } : check(norm.plan)
  const blocking = det.issues.map(i => '[deterministic] ' + i)
  const minor = []
  let verdicts = []
  if (!norm.problems.length) {
    verdicts = (await parallel(LENSES.map(l => () => agent(lensPrompt(l, norm.plan, det), { label: 'verify:' + l.key + ':r' + round, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'high' })))).filter(Boolean)
    blocking.push(...verdicts.flatMap(v => v.blocking.map(b => '[' + v.lens + '] ' + b.issue + ' -> FIX: ' + b.fix)))
    minor.push(...verdicts.flatMap(v => v.minor.map(m => '[' + v.lens + '] ' + m.issue + ' -> ' + m.fix)))
  }
  history.push({ round, deterministic_issues: det.issues, deterministic_info: det.info, lens_blocking: blocking.filter(b => !b.startsWith('[deterministic]')), minor, lenses_checked: verdicts.map(v => ({ lens: v.lens, refuted: v.refuted, checked: v.checked })) })
  log(`Verify round ${round}: ${det.issues.length} deterministic + ${blocking.length - det.issues.length} lens blocking, ${minor.length} minor`)
  if (!blocking.length) { final = { ...norm.plan, verifier_minor_notes: minor, verify_rounds: round, deterministic_info: det.info }; break }
  if (round === MAX_ROUNDS) { final = { ...norm.plan, unresolved_blocking: blocking, verifier_minor_notes: minor, verify_rounds: round, deterministic_info: det.info }; log('Max fix rounds reached; ' + blocking.length + ' blocking issues remain unresolved'); break }
  let fixed = await agent(settlePrompt(feedbackBlock(norm.plan, blocking, minor)), { label: 'settle:v' + (round + 1), phase: 'Settle', schema: FINAL_SCHEMA, effort: 'xhigh' })
  if (!fixed) fixed = await agent(settlePrompt(feedbackBlock(norm.plan, blocking, minor)), { label: 'settle:v' + (round + 1) + '-retry', phase: 'Settle', schema: FINAL_SCHEMA, effort: 'xhigh' })
  if (!fixed) { final = { ...norm.plan, unresolved_blocking: blocking, verifier_minor_notes: minor, verify_rounds: round, deterministic_info: det.info }; log('fix agent failed; keeping previous plan with unresolved issues'); break }
  norm = normalize(fixed)
}

return { review3, codecheck, final, history }