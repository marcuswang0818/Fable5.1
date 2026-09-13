export const meta = {
  name: 'multi-school-course-plan',
  description: 'Six-school course plan for a credit-maxed ASU Online BA in General Studies: scout, 6 school planners, 3 reviewers, settlement, adversarial verify',
  phases: [
    { title: 'Scout', detail: 'ASU GenStu BA rules, calendars & pricing, subject strengths' },
    { title: 'Round 1', detail: 'six school-specific course planners' },
    { title: 'Round 2', detail: 'degree-requirements review, duplicate removal, prerequisite timeline' },
    { title: 'Settle', detail: 'merge into one term-by-term timeline with credits and cost' },
    { title: 'Verify', detail: 'three adversarial lenses; fix loop' },
  ],
}

// ---------------------------------------------------------------------------
// Shared brief (English for agents; user intent is Chinese, translated here)
// ---------------------------------------------------------------------------
const TOOLING = `
TOOLING NOTES (important):
- WebFetch is BLOCKED by the network egress proxy in this environment. Do NOT waste turns on it.
- WebSearch WORKS. First call ToolSearch with query "select:WebSearch" to load it, then run many targeted searches (10-25). Search snippets are your only live source; combine them with your own knowledge of these institutions.
- Mark every fact you could not confirm from a search snippet with confidence: "confirmed" (seen in snippet), "likely" (strong prior, consistent with snippets), or "assumed" (guess). Never silently invent course codes: prefer courses you have actually seen in catalogs; if unsure, say "assumed".
- Do not ask the user anything. Make assumptions explicit and continue. Return ONLY the structured output.
`

const BRIEF = `
PROJECT BRIEF — "爆学分臻享版" (credit-maxed premium edition) ASU Online BA in General Studies
Today is 2026-09-13. Student is employed and studies part-time, but sits in the top 20% for both available time and academic ability: sustained load of roughly 12-15 semester credits per 8-week block is acceptable at peak; ~9-12 is the comfortable norm. Prerequisites must be strictly sequenced.

TARGET DEGREE: Arizona State University, ASU Online, Bachelor of Arts in General Studies (degree search plan code LSGNSBGS; College of Integrative Sciences and Arts). 120 credits minimum to graduate, but the student deliberately accumulates EXACTLY 150.334 semester credits ("five-year-bachelor volume") drawn from six platforms, all of which must land on / transfer into the ASU degree audit:
  1. SNHU Online (Southern New Hampshire University): 12.000 semester credits = 4 x 3-credit courses. 8-week undergraduate terms (six starts per year).
  2. Harvard Extension School (HES): 12.000 semester credits = 3 x 4-credit courses. Fall / January / Spring / Summer terms.
  3. ASU Universal Learner Courses (ULC), SESSION-BASED format only (ASU sessions A = first 7.5 weeks, B = second 7.5 weeks, C = full 15 weeks): 42.000 credits = 14 x 3-credit courses. ULC credits are native ASU credits once converted ($25 to enroll + $400 to convert each course to ASU credit, unless search shows a newer price). The student ALREADY STARTED ULC courses in 2026 Fall session A (Fall A ≈ Aug 20 – Oct 9, 2026).
  4. UMPI YourPace (University of Maine at Presque Isle, competency-based, subscription per 8-week session): 42.000 credits completed in EXACTLY THREE 8-week sessions (14 credits ≈ 4-5 courses per session, feasible only because YourPace is self-paced and the student is top-20%).
  5. UCLA Extension: 21.334 semester credits = 32 quarter units = 8 x 4-quarter-unit courses (quarter units x 2/3 = semester credits; 21.334 is the rounded-up value the student uses). Quarters: Fall (late Sep–Dec), Winter (Jan–Mar), Spring (Apr–Jun), Summer (Jun–Sep).
  6. BYU Independent Study (BYU IS, university online courses): 21.000 credits = 7 x 3-credit courses. Each course is self-paced with a 12-month enrollment window, but the student will FINISH EACH COURSE WITHIN ONE SEMESTER-LENGTH WINDOW (≈15 weeks or less) so it slots cleanly on the timeline; do not stretch any BYU course to a year.
  TOTAL = 12 + 12 + 42 + 42 + 21.334 + 21 = 150.334.

THEMATIC EMPHASIS (the student's own labels for the two focus areas): "Technology & Government" and "Socio-Technical Systems: Energy & Environment", with a personal specialty in POWER ELECTRONICS. So physics, circuits/electronics, EE foundations, energy systems, electric grid/renewables, environmental science, technology policy, public administration, science-and-technology studies, and data/programming courses are all welcome, as long as ASU General Studies BA rules (General Studies Gold gen-ed, clusters, upper-division minimum) are satisfied by the union of all six plans.

80/20 RULE: about 80% of each school's picks must exploit that school's genuinely strong subjects (取百家之长); about 20% may be cheap general-education / elective filler chosen purely to save money.

USER INSTRUCTIONS THAT OVERRIDE NORMAL ADVISING:
- IGNORE ASU's 30-credit residency requirement (the user says to drop it; note anyway that the 42 ULC credits are native ASU credits and would cover it).
- Assume ASU 101 (The ASU Experience), IDS 321 and IDS 402 (the General Studies BA's required interdisciplinary courses) can each be SUBSTITUTED by an equivalent course from one of the six platforms; the plan must name the substitute for each and where it sits on the timeline, then the freed slots are refilled ("抵课掉再塞回去").
- No questions to the user. Produce the plan; state assumptions.
- The timeline starts 2026 Fall session 1 (ASU Fall A). Plan every term until the 150.334 credits are complete; aim for the earliest realistic completion, NOT a leisurely five-year pace.
- Cost = tuition/fees actually paid per course at each platform (use the most recent published price found; state the year of the price). Report USD.
`

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const SCOUT_SCHEMA = {
  type: 'object',
  properties: {
    topic: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      item: { type: 'string' }, detail: { type: 'string' }, confidence: { type: 'string', enum: ['confirmed', 'likely', 'assumed'] }, source: { type: 'string' } }, required: ['item', 'detail', 'confidence'] } },
    open_questions: { type: 'array', items: { type: 'string' } },
    brief_for_planners: { type: 'string', description: 'A dense 400-900 word paragraph a course planner can rely on directly.' },
  },
  required: ['topic', 'findings', 'brief_for_planners'],
}

const COURSE = { type: 'object', properties: {
  code: { type: 'string' }, title: { type: 'string' },
  native_credits: { type: 'number' }, native_unit: { type: 'string', enum: ['semester', 'quarter'] },
  semester_credits: { type: 'number' },
  level: { type: 'string', enum: ['lower', 'upper'] },
  cost_usd: { type: 'number' }, cost_basis: { type: 'string' },
  term_format: { type: 'string' }, duration_weeks: { type: 'number' },
  earliest_term: { type: 'string', description: 'e.g. "2026 Fall B (Oct 14 – Dec 4)"' },
  prerequisites: { type: 'array', items: { type: 'string' } },
  asu_requirement_mapped: { type: 'string', description: 'e.g. "Gold: SCIT", "Gold: MATH", "ENG 101 equiv", "Cluster: Technology & Government (upper)", "IDS 321 substitute", "Elective"' },
  theme: { type: 'string', enum: ['primary-strength', 'secondary-savings'] },
  rationale: { type: 'string' },
  transfer_risk: { type: 'string' },
  confidence: { type: 'string', enum: ['confirmed', 'likely', 'assumed'] },
  sources: { type: 'array', items: { type: 'string' } } },
  required: ['code', 'title', 'native_credits', 'native_unit', 'semester_credits', 'level', 'cost_usd', 'earliest_term', 'prerequisites', 'asu_requirement_mapped', 'theme', 'rationale', 'confidence'] }

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    school: { type: 'string' },
    required_semester_credits: { type: 'number' },
    total_semester_credits: { type: 'number' },
    total_cost_usd: { type: 'number' },
    courses: { type: 'array', items: COURSE },
    alternates: { type: 'array', items: COURSE },
    calendar: { type: 'array', items: { type: 'object', properties: { term: { type: 'string' }, start: { type: 'string' }, end: { type: 'string' }, confidence: { type: 'string' } }, required: ['term', 'start', 'end'] } },
    pricing_notes: { type: 'string' },
    strengths_rationale: { type: 'string' },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
  required: ['school', 'required_semester_credits', 'total_semester_credits', 'total_cost_usd', 'courses', 'alternates', 'calendar', 'pricing_notes', 'strengths_rationale'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    reviewer: { type: 'string' },
    verdict: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      severity: { type: 'string', enum: ['blocking', 'major', 'minor'] },
      school: { type: 'string' }, course: { type: 'string' },
      issue: { type: 'string' }, action: { type: 'string', description: 'Concrete swap/move: which course out, which course (with code, credits, cost, term) in, keeping the per-school credit totals exact.' } },
      required: ['severity', 'issue', 'action'] } },
    requirement_matrix: { type: 'string', description: 'Markdown table mapping every ASU requirement bucket to the courses that satisfy it (or "GAP").' },
    ordered_timeline: { type: 'string', description: 'For the prerequisite reviewer: a markdown term-by-term ordering with per-term credit load; others may leave empty.' },
    notes: { type: 'string' },
  },
  required: ['reviewer', 'verdict', 'findings', 'notes'],
}

const ENTRY = { type: 'object', properties: {
  seq: { type: 'number' },
  term_label: { type: 'string', description: 'e.g. "2026 秋 A (Fall A)"' },
  start: { type: 'string' }, end: { type: 'string' },
  school: { type: 'string' },
  code: { type: 'string' }, title: { type: 'string' }, title_zh: { type: 'string' },
  native_credits: { type: 'number' }, native_unit: { type: 'string' },
  credits_counted: { type: 'number' },
  level: { type: 'string' },
  requirement_bucket: { type: 'string' },
  cluster_or_theme: { type: 'string' },
  prereqs_satisfied_by: { type: 'string' },
  cost_usd: { type: 'number' },
  cumulative_credits: { type: 'number' },
  cumulative_cost_usd: { type: 'number' },
  confidence: { type: 'string' },
  note: { type: 'string' } },
  required: ['seq', 'term_label', 'start', 'end', 'school', 'code', 'title', 'credits_counted', 'level', 'requirement_bucket', 'cost_usd', 'cumulative_credits', 'cumulative_cost_usd'] }

const FINAL_SCHEMA = {
  type: 'object',
  properties: {
    degree_summary: { type: 'string' },
    assumptions: { type: 'array', items: { type: 'string' } },
    substitutions: { type: 'array', items: { type: 'object', properties: { asu_course: { type: 'string' }, substitute: { type: 'string' }, justification: { type: 'string' } }, required: ['asu_course', 'substitute', 'justification'] } },
    entries: { type: 'array', items: ENTRY },
    per_term_load: { type: 'array', items: { type: 'object', properties: { term_label: { type: 'string' }, start: { type: 'string' }, end: { type: 'string' }, credits: { type: 'number' }, cost_usd: { type: 'number' }, courses: { type: 'number' }, schools: { type: 'string' } }, required: ['term_label', 'credits', 'cost_usd', 'courses'] } },
    per_school_totals: { type: 'array', items: { type: 'object', properties: { school: { type: 'string' }, courses: { type: 'number' }, credits: { type: 'number' }, cost_usd: { type: 'number' }, per_credit_usd: { type: 'number' } }, required: ['school', 'courses', 'credits', 'cost_usd'] } },
    requirement_matrix: { type: 'string', description: 'Markdown table: ASU requirement bucket → satisfying course(s) → status.' },
    totals: { type: 'object', properties: { credits: { type: 'number' }, upper_division_credits: { type: 'number' }, cost_usd: { type: 'number' }, first_term: { type: 'string' }, last_term: { type: 'string' }, months: { type: 'number' } }, required: ['credits', 'upper_division_credits', 'cost_usd', 'first_term', 'last_term'] },
    risks: { type: 'array', items: { type: 'string' } },
    sources: { type: 'array', items: { type: 'string' } },
  },
  required: ['degree_summary', 'assumptions', 'substitutions', 'entries', 'per_term_load', 'per_school_totals', 'requirement_matrix', 'totals', 'risks'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    lens: { type: 'string' },
    refuted: { type: 'boolean', description: 'true if the plan has at least one BLOCKING defect under this lens' },
    blocking: { type: 'array', items: { type: 'object', properties: { issue: { type: 'string' }, fix: { type: 'string' } }, required: ['issue', 'fix'] } },
    minor: { type: 'array', items: { type: 'object', properties: { issue: { type: 'string' }, fix: { type: 'string' } }, required: ['issue', 'fix'] } },
    arithmetic_check: { type: 'string' },
  },
  required: ['lens', 'refuted', 'blocking', 'minor'],
}

// ---------------------------------------------------------------------------
// Phase 0: Scout
// ---------------------------------------------------------------------------
phase('Scout')
const SCOUTS = [
  { key: 'degree-rules', prompt: `${TOOLING}\n${BRIEF}\nYOUR TOPIC: the ASU Bachelor of Arts in General Studies (LSGNSBGS) degree rules as of the 2025-2026 and 2026-2027 catalogs. Establish: (a) total credits (120), upper-division minimum (usually 45), residency (30 — to be ignored but note it), max transfer rules (community-college caps vs 4-year universities; quarter-unit conversion 2/3; how UCLA Extension "XL" vs "X" vs "XLC" course numbers transfer), (b) General Studies Gold requirements and their codes (HUAD, SOBE, SCIT, QTRS, MATH, AMIT, GCSI, SUST... list each with credits and whether lab is required) and ENG 101/102/105 first-year composition, (c) the General Studies BA structure: how many clusters, 3 courses each, 36 cluster credits with 18 upper-division; list ALL currently offered cluster names you can find (search cisa.asu.edu/degree-clusters, degrees.asu.edu checksheet 2026 CLS LSGNSBGS, major map PDFs). Identify whether the user's labels "Technology & Government" and "Socio-Technical Systems: Energy & Environment" match official cluster names; if not, name the closest official clusters and list example ASU courses in them, (d) ASU 101, IDS 321 and IDS 402: their titles, credits, and what they cover (so substitutes can be argued), (e) which ULC courses (session-based) exist at 100-400 level that satisfy Gold or cluster requirements — search "Universal Learner Courses" catalog course lists 2026, including any 300-level ULC offered for the General Studies degree, (f) transfer-credit evaluation facts for SNHU, Harvard Extension School, UMPI, UCLA Extension, and BYU Independent Study into ASU (accreditation, how ASU treats competency-based credits, pass/fail issues). Output the brief_for_planners as the authoritative rule sheet.` },
  { key: 'calendar-pricing', prompt: `${TOOLING}\n${BRIEF}\nYOUR TOPIC: exact-as-possible ACADEMIC CALENDARS (2026-2027 through 2028-2029, extrapolate with stated confidence when a year is not yet published) and CURRENT PRICES for the six platforms. For each platform give: term/session names, start and end dates (ASU Fall 2026 A/B/C, Spring 2027 A/B/C, Summer 2027 A/B/C and onward; SNHU 8-week undergraduate term starts; HES fall/January/spring/summer term dates and undergraduate-credit tuition per 4-credit course incl. registration fees; UMPI YourPace 8-week session start dates and the per-session flat price plus any fees; UCLA Extension quarter dates and typical per-course fees for engineering/tech vs general courses (quarter units per course), plus transcript/credit nuances; BYU Independent Study per-credit tuition for university courses, proctoring fees, and enrollment window). Also ULC: $25 enrollment + $400 credit-conversion fee (verify), any bundle discounts, session-based ULC alignment with ASU A/B/C sessions. Give USD figures with the year they were published and confidence. brief_for_planners must be a compact calendar+price sheet.` },
  { key: 'strengths-inventory', prompt: `${TOOLING}\n${BRIEF}\nYOUR TOPIC: an INVENTORY OF STRONG SUBJECTS per platform relevant to the themes (technology policy / government / public administration, energy & environment, socio-technical systems, science-technology-society, electrical circuits / electronics / power electronics / physics / calculus / linear algebra / programming / data), plus the cheapest gen-ed filler per platform. For each of the six platforms list 10-20 concrete ONLINE undergraduate-credit courses (code, title, credits, level, prerequisites, typical term) that a planner should consider, with confidence flags. Specifically look for: HES courses in government (GOVT), environmental studies (ENVR), computer science (CSCI), physics, statistics, economics, public policy; UCLA Extension XL / X 4xx courses in electrical engineering, electronics, power systems, sustainability, environmental studies, project management, data science (and which are transferable undergraduate credit); BYU IS university courses in physics (PHSCS), math (MATH 112/113/213/290), statistics (STAT 121), economics, political science, geography/environment, EC EN if any; SNHU strong areas (IT, business, environmental science, history/humanities, PHY/MAT online); UMPI YourPace catalog (business, gen-ed, criminal justice, liberal studies, environmental?) with the courses available in YourPace; ASU ULC session-based catalog (MAT 117-267, PHY 121/122?, CHM, BIO, FSE 100, EEE 120?, CSE 110, ECN 211/212, POS 110?, SOS?, SGS?, HST, ENG 101/102/105, ASU 101?). Output the brief_for_planners as a per-school shortlist ranked by fit to the themes.` },
]
const scoutOut = await parallel(SCOUTS.map(s => () => agent(s.prompt, { label: `scout:${s.key}`, phase: 'Scout', schema: SCOUT_SCHEMA, effort: 'high' })))
const scouts = scoutOut.filter(Boolean)
log(`Scout done: ${scouts.length}/3 briefs`)
const SCOUT_BRIEF = scouts.map(s => `### ${s.topic}\n${s.brief_for_planners}\n\nKey findings:\n${s.findings.map(f => `- [${f.confidence}] ${f.item}: ${f.detail}`).join('\n')}\nOpen questions: ${(s.open_questions || []).join(' | ')}`).join('\n\n')

// ---------------------------------------------------------------------------
// Phase 1: Round 1 — six school planners
// ---------------------------------------------------------------------------
phase('Round 1')
const SCHOOLS = [
  { key: 'SNHU', credits: 12, spec: `SNHU Online, 12.000 semester credits = 4 x 3-credit courses. 8-week terms. Use the undergraduate per-credit price. Exploit SNHU strengths (IT / cybersecurity / business / environmental science / history / cheap fast gen-ed). Prefer 300-400 level courses that can fill CLUSTER upper-division slots or Gold buckets the other schools cannot fill cheaply.` },
  { key: 'HES', credits: 12, spec: `Harvard Extension School, 12.000 semester credits = 3 x 4-credit courses (undergraduate credit status). Exploit HES strengths: government / public policy / technology policy (GOVT), environmental studies & sustainability (ENVR), computer science (CSCI), physics / engineering-adjacent, statistics. Prefer upper-division-equivalent courses (HES course numbers below E-100 are undergraduate; those E-100+ can be graduate/undergraduate — pick ones that transfer as upper-division undergrad credit). One HES course should be argued as the IDS 402 (capstone-like interdisciplinary) substitute if plausible. Note term options: Fall, January session (3 weeks, intensive), Spring, Summer (3- and 7-week).` },
  { key: 'ASU-ULC', credits: 42, spec: `ASU Universal Learner Courses, SESSION-BASED only, 42.000 credits = 14 x 3-credit courses ($25 + $400 each unless newer pricing found). These are native ASU credits. Load the foundations here: ENG 101/102 (or ENG 105), MAT 265/266/267 (calculus) or MAT 170/210 if needed, MAT 275 (ODE) if offered, PHY 121/122/131/132 (University Physics + labs) or PHY 111/112, CHM 113/114? or BIO 100 (Gold SCIT with lab), FSE 100, EEE 120 (Digital Design) if offered, CSE 110, ECN 211/212, POS 110/POS 310 if offered, HST, ASU 101 if offered via ULC (then no substitute needed). The student ALREADY STARTED some ULC courses in 2026 Fall A — pick 2-3 of the 14 as "in progress 2026 Fall A" (the most foundational: e.g. ENG 101, MAT 265 or MAT 170, PHY?). Spread the remaining 11-12 over Fall B 2026, Spring A/B 2027, Summer 2027, Fall 2027 respecting prerequisites (MAT 265 → 266 → 267 → 275; PHY 121 needs MAT 265 corequisite; EEE 120 no prereq; ENG 101 → 102). Verify each course actually appears in the ULC session-based catalog; mark confidence.` },
  { key: 'UMPI-YourPace', credits: 42, spec: `UMPI YourPace (competency-based, subscription per 8-week session), 42.000 credits in EXACTLY three sessions: 14 credits per session (e.g., 4 x 3-credit + one 2-credit, or 5 x 3-credit = 15 is NOT allowed; make the three sessions sum exactly to 42 using courses that exist in YourPace — if only 3-credit courses exist, use 5+5+4 courses = 15+15+12 = 42). Only courses that are actually offered in the YourPace format (BA Liberal Studies / BS Business Administration / BA Criminal Justice / BA English / BA History / BA Psychology? / BS Computer Information Systems? and their gen-ed) — verify. YourPace is the cheapest bulk credit source, so put the cheap gen-ed filler and lower-division breadth here (Gold HUAD, SOBE, AMIT, GCSI, SUST, some QTRS) plus any project-management / business / policy-adjacent upper-division courses that fit Technology & Government. Choose the three sessions so they do not collide with UCLA Extension or HES peak weeks, and state a per-session pace plan (which 4-5 courses in each session, with an order).` },
  { key: 'UCLA-Extension', credits: 21.334, spec: `UCLA Extension, 21.334 semester credits = 32 quarter units = 8 x 4-quarter-unit courses. Exploit UCLA Extension strengths: engineering & technology (electrical engineering, electronics, power electronics / power systems, embedded systems, control), sustainability / environmental studies / energy efficiency, public policy, project management, data science. Prefer XL-numbered (UCLA-equivalent, transferable undergraduate credit; XL 100+ = upper division) and X 4xx professional-credit courses only where transferable; state transfer_risk honestly for each. Include the power-electronics-adjacent courses if they exist online. Quarter dates: Fall (late Sep–Dec), Winter (Jan–Mar), Spring (Apr–Jun), Summer (late Jun–Sep). One or two of these should be arguable as the IDS 321 substitute (an interdisciplinary/systems course) if plausible.` },
  { key: 'BYU-IS', credits: 21, spec: `BYU Independent Study university courses, 21.000 credits = 7 x 3-credit courses. Each course must be finished within ONE semester-length window (≤ 15 weeks) — assign each a start month and finish month accordingly; never spread a course over 12 months. Exploit BYU IS strengths: physics (PHSCS 105/106/121/123?), calculus/linear algebra (MATH 112/113/213/215/290), statistics (STAT 121), economics (ECON 110), political science (POLI 110/170?), geography/environment (GEOG 120?), chemistry (CHEM 101/105), CS (CS 142) — check which are actually in the BYU IS university catalog online now. Price = per-credit university tuition (confirm the 2026 rate) plus proctoring fees where required. BYU IS courses require proctored exams — note it.` },
]
const planOut = await parallel(SCHOOLS.map(s => () => agent(
  `${TOOLING}\n${BRIEF}\n\n=== SCOUT BRIEFS (authoritative rule sheet; verify anything critical with your own searches) ===\n${SCOUT_BRIEF}\n\n=== YOUR ASSIGNMENT (Round 1, sub-agent for ${s.key}) ===\n${s.spec}\n\nDELIVER: exactly the number of courses whose semester_credits sum to ${s.credits} (UCLA: 8 courses x 4 quarter units, semester_credits 2.667 each, total 21.334 — use 2.667 for seven and 2.665 for the last so the sum is exactly 21.334, or simply state 2.6667 each and total 21.334). For every course: code, title, credits, level, cost (USD, with basis and price year), earliest_term with dates, prerequisites (name the course and which platform will have supplied it), the ASU requirement bucket it is meant to satisfy, theme tag (primary-strength vs secondary-savings — aim for ~80/20), rationale (why this school is the best place for this course), transfer_risk, confidence, sources. Also give 3-5 alternates, the platform's calendar for 2026-2028 with confidence, pricing notes, and the strengths rationale. Search the live catalog names via WebSearch (e.g. "site:snhu.edu <course code>", "Harvard Extension GOVT E-", "UCLA Extension XL electrical engineering online", "BYU Independent Study university courses PHSCS", "UMPI YourPace courses list", "ASU ULC session based <code>").`,
  { label: `plan:${s.key}`, phase: 'Round 1', schema: PLAN_SCHEMA, effort: 'high' })))
const plans = planOut.filter(Boolean)
log(`Round 1 done: ${plans.length}/6 school plans (${plans.map(p => `${p.school}=${p.total_semester_credits}cr/$${p.total_cost_usd}`).join(', ')})`)
const PLANS_JSON = JSON.stringify(plans, null, 1)

// ---------------------------------------------------------------------------
// Phase 2: Round 2 — three reviewers (need all six plans → barrier is correct)
// ---------------------------------------------------------------------------
phase('Round 2')
const REVIEWERS = [
  { key: 'degree-requirements', prompt: `You are Round-2 reviewer #1: REVIEW OF DEGREE REQUIREMENTS. Audit the UNION of the six school plans against the ASU BA in General Studies rules (120 min; 45 upper-division; General Studies Gold buckets incl. lab science, MATH, QTRS, HUAD, SOBE, AMIT, GCSI, SUST; ENG 101+102 or 105; four clusters x 3 courses with >=18 upper-division cluster credits — map the student's two themes to the closest official clusters and pick two more clusters that the plans already cover; ASU 101 / IDS 321 / IDS 402 substitutes named and justified; residency ignored per user). Produce a requirement_matrix markdown table (bucket → course(s) → status OK/GAP/RISK) and for every GAP or RISK give a concrete swap that keeps each school's credit total exact (12 / 12 / 42 / 42 / 21.334 / 21). Also verify credit arithmetic per school and the 150.334 grand total, and flag any course that likely will NOT transfer (e.g. UCLA Extension X 4xx professional credit, competency-based pass/fail concerns) with a replacement.` },
  { key: 'remove-duplicates', prompt: `You are Round-2 reviewer #2: REMOVE DUPLICATE CLASSES. Find every pair/group of courses across the six plans that ASU would treat as equivalent or overlapping (same subject/level: two intro statistics, two Calc I, two first-year composition, two intro microeconomics, two intro physics I, two intro programming, two 'intro to environmental science', etc.) — ASU grants credit only once for equivalents. For each duplicate group: keep the course at the school where it is strongest/cheapest/best-timed and REPLACE the other(s) with a concrete non-overlapping course at the same school with the same credits and a real course code (verify with WebSearch), so every school's credit total stays exact (12 / 12 / 42 / 42 / 21.334 / 21) and the 80/20 strength-vs-savings balance is preserved. Also flag near-duplicates that still add value (e.g. Calculus III vs Linear Algebra are NOT duplicates). Output findings with severity and precise actions.` },
  { key: 'prerequisite-timeline', prompt: `You are Round-2 reviewer #3: CLARIFY THE TIMELINE OF PREREQUISITES NEEDED. Build the prerequisite dependency graph across ALL six plans (a prerequisite may be satisfied at a different platform — note that the receiving school may require an official transcript or may accept self-attestation; HES and UCLA Extension typically do not enforce prereqs strictly, ASU ULC enforces via placement/prereq check for MAT/PHY, BYU IS mostly does not enforce, SNHU enforces within its own catalog, UMPI YourPace enforces within its catalog). Then lay out a term-by-term ordering from 2026 Fall A (already in progress) to completion, with EVERY course placed in a concrete term whose dates you state, prerequisites completed BEFORE the term starts, the UMPI YourPace 42 credits confined to exactly three 8-week sessions, each BYU IS course finished within <=15 weeks, and per-8-week-block loads within 9-15 semester credits (peak 15). Compute the load per block and flag overloads with a fix (move course X to term Y). Output ordered_timeline as a markdown table: term | dates | school | course | credits | prereqs satisfied by | running credits.` },
]
const reviewOut = await parallel(REVIEWERS.map(r => () => agent(
  `${TOOLING}\n${BRIEF}\n\n=== SCOUT BRIEFS ===\n${SCOUT_BRIEF}\n\n=== ROUND 1: SIX SCHOOL PLANS (JSON) ===\n${PLANS_JSON}\n\n=== YOUR ROLE ===\n${r.prompt}\n\nBe exhaustive and concrete. Every action must name the course going OUT and the course coming IN with code, credits, cost and term.`,
  { label: `review:${r.key}`, phase: 'Round 2', schema: REVIEW_SCHEMA, effort: 'high' })))
const reviews = reviewOut.filter(Boolean)
log(`Round 2 done: ${reviews.length}/3 reviews, ${reviews.reduce((n, r) => n + r.findings.length, 0)} findings`)
const REVIEWS_JSON = JSON.stringify(reviews, null, 1)

// ---------------------------------------------------------------------------
// Phase 3: Settle — one synthesizer, then adversarial verify + fix loop
// ---------------------------------------------------------------------------
phase('Settle')
const settlePrompt = (feedback) => `${TOOLING}\n${BRIEF}\n\n=== SCOUT BRIEFS ===\n${SCOUT_BRIEF}\n\n=== ROUND 1: SIX SCHOOL PLANS (JSON) ===\n${PLANS_JSON}\n\n=== ROUND 2: THREE REVIEWS (JSON) ===\n${REVIEWS_JSON}\n${feedback ? `\n=== VERIFIER FEEDBACK TO FIX (mandatory) ===\n${feedback}\n` : ''}
=== YOUR ROLE: SETTLEMENT (结算) ===
Merge everything into ONE final plan: apply every blocking/major action from the three reviews (degree gaps, duplicate removals, prerequisite re-ordering), keep per-school credit totals EXACT (SNHU 12 / HES 12 / ASU ULC 42 / UMPI 42 in exactly three 8-week sessions / UCLA Ext 21.334 as 8 x 4 quarter units / BYU IS 21, each BYU course <=15 weeks), grand total EXACTLY 150.334.
Produce the entries array as the term-by-term timeline (chronological; seq ascending; one row per course; cumulative_credits and cumulative_cost_usd computed row by row, rounded to 3 decimals for credits and whole dollars for cost). Rows must include a short Chinese title_zh. Include per_term_load (每个 8 周块的学分与花费), per_school_totals, substitutions for ASU 101 / IDS 321 / IDS 402, a full requirement_matrix, totals (credits, upper-division credits, cost, first/last term, months), assumptions, risks, sources.
Rules: first rows are the 2026 Fall A ULC courses already in progress; earliest realistic completion; 9-15 credits per 8-week block; prerequisites strictly before; cost per course = the price found for that platform (state price year in assumptions). Do the arithmetic carefully: sum of credits_counted must equal 150.334 and sum of cost_usd must equal totals.cost_usd; per-school sums must match the six required totals.`

let final = await agent(settlePrompt(''), { label: 'settle:v1', phase: 'Settle', schema: FINAL_SCHEMA, effort: 'xhigh' })
if (!final) throw new Error('settlement agent returned null')

phase('Verify')
const LENSES = [
  { key: 'arithmetic', prompt: 'ARITHMETIC & STRUCTURE lens: recompute every number yourself. Sum credits_counted (must equal 150.334 ± 0.001), sum per school (12 / 12 / 42 / 42 / 21.334 / 21), UMPI rows must fall in exactly three distinct 8-week sessions, UCLA rows must be exactly 8 with 4 quarter units each, BYU rows exactly 7 x 3 credits each with duration <= 15 weeks, cumulative columns must be monotone and correct row by row, cost sum must equal totals.cost_usd, per_term_load must agree with entries, per_school_totals must agree with entries. Any mismatch is BLOCKING; give the exact corrected numbers.' },
  { key: 'requirements', prompt: 'DEGREE-REQUIREMENTS lens: try to REFUTE that this plan graduates the student with an ASU BA in General Studies (ignoring residency): General Studies Gold buckets incl. lab science, MATH, QTRS, HUAD, SOBE, AMIT, GCSI, SUST; ENG 101/102 or 105; 45 upper-division credits; four clusters x 3 courses with >= 18 upper-division cluster credits; ASU 101 / IDS 321 / IDS 402 substitutes each named; no duplicated equivalents counted twice; nothing likely non-transferable (UCLA X 4xx professional credit, pass/fail). Also check the 80/20 strengths-vs-savings intent and the two themes (Technology & Government; Socio-Technical Systems: Energy & Environment / power electronics) are visibly served. Missing bucket or double-count = BLOCKING with a concrete swap keeping per-school totals exact.' },
  { key: 'schedule', prompt: 'SCHEDULE-FEASIBILITY lens: try to REFUTE the timeline. Check every prerequisite is completed before its dependent course starts (across platforms), term dates are plausible for each platform (ASU A/B/C sessions, SNHU 8-week terms, HES fall/January/spring/summer, UMPI 8-week sessions, UCLA quarters, BYU windows), per-8-week-block load stays 9-15 credits (top-20% part-time student), no BYU course spans > 15 weeks, UMPI 42 credits in exactly 3 sessions with a stated pace, 2026 Fall A ULC rows are marked in progress, and completion is as early as realistically possible. Overload, prerequisite violation, or impossible date = BLOCKING with a concrete move.' },
]
let round = 0
while (round < 3) {
  const verdicts = (await parallel(LENSES.map(l => () => agent(
    `${TOOLING}\n${BRIEF}\n\n=== FINAL PLAN (JSON) ===\n${JSON.stringify(final, null, 1)}\n\n=== YOUR LENS ===\n${l.prompt}\nDefault to refuted=true only for genuine BLOCKING defects; list minor issues separately.`,
    { label: `verify:${l.key}:r${round + 1}`, phase: 'Verify', schema: VERDICT_SCHEMA, effort: 'high' })))).filter(Boolean)
  const blocking = verdicts.flatMap(v => v.blocking.map(b => `[${v.lens}] ${b.issue} → FIX: ${b.fix}`))
  const minor = verdicts.flatMap(v => v.minor.map(m => `[${v.lens}] ${m.issue} → ${m.fix}`))
  log(`Verify round ${round + 1}: ${blocking.length} blocking, ${minor.length} minor`)
  if (blocking.length === 0) { final.verifier_minor_notes = minor; final.verify_rounds = round + 1; break }
  round++
  if (round >= 3) { final.unresolved_blocking = blocking; final.verifier_minor_notes = minor; final.verify_rounds = round; break }
  final = await agent(settlePrompt(`BLOCKING (must all be fixed):\n${blocking.join('\n')}\n\nMINOR (fix if cheap):\n${minor.join('\n')}`), { label: `settle:v${round + 1}`, phase: 'Settle', schema: FINAL_SCHEMA, effort: 'xhigh' })
  if (!final) throw new Error('settlement fix agent returned null')
}

return { scouts, plans, reviews, final }