# Acceptance Results — Round 6 (Evidence gate + deep efficiency)

## Date: 2026-09-20

## Summary

Round 6 delivers the Round-5 H3 Evidence-gate fix **and** deep-run efficiency knobs, then re-measures H1/H3 live on **glm-5.3-flash** + Serper.

| Case | Config | Round 5 | Round 6 | Verdict |
|------|--------|---------|---------|---------|
| H1 ZCode | deep + verified + detailed | **446.4s** PASS | **401.9s** PASS | **PASS** (~10% faster) |
| H3 Houthis/Saudi | deep + verified + detailed | **533.2s** **FAIL** (`missing_evidence`) | **965.2s** PASS | **PASS** Evidence gate; wall-clock **worse** (see honesty notes) |

**Overall Round 6: PASS on Evidence gate.** Deep-efficiency knobs are live and measurable; H1 wall-clock improved; H3 wall-clock did **not** improve (timeouts + max-turns + 3× summary) — documented honestly below.

Raw artifacts: [`artifacts/round6/`](./artifacts/round6/).

---

## Environment

| Item | Value |
|------|-------|
| Harness | `scripts/run_acceptance_live.py --cases H3,H1` |
| LLM | glm-5.3-flash @ Zhipu OpenAI-compatible Chat Completions |
| Serper | Live OK |
| Credentials | Uploaded Round-6 JSON (never committed) |
| Branch | `cursor/research-quality-improvements-e664` |

---

## Part A — Evidence gate

### Code

1. Broader bilingual `_EVIDENCE` aliases (`证据`, `证据与来源`, `临床证据`, numbered CN headings, …)
2. `enforce_structure` **auto-repairs** Evidence when inline sources/URLs exist but heading is missing
3. Conflicts / Timeline / Confirmed gates unchanged

### Offline (Round-5 H3 artifact)

| | Before | After enforce |
|--|--------|---------------|
| valid | False | **True** |
| missing | includes `evidence` | `[]` |
| evidence_len | — | 1646 |

See `artifacts/round6/h3_offline_evidence_repair.json`.

### Live H3 Evidence

- Gate: **PASS** (`failures=[]`, `evidence` in `found_sections`)
- Heading present: `## Evidence（证据含来源与日期）` (auto-repair path; body promoted from Conflicts/Timeline source cues)
- Soft issues only: `timeline_too_short`, `insufficient_citations` (do not fail hard gate)

---

## Part B — Deep efficiency (observed)

| Knob | Observed on live runs |
|------|------------------------|
| Parallel tool calls | Log: `Parallel Tools: Executing 2 tool calls in parallel` (H3 turns 1–3, 6–9) |
| Scrape budget | H3 hit cap: `scrape_budget … (8/8 used)` → further scrapes skipped |
| Clue Top-K | `max_follow_ups=2`; H3 `follow_up_searches=1`; H1 `follow_up_searches=0` |
| Early-stop | H1 turn 7: `Deep Early-Stop: ≥2 independent sources (19 domains) and search_rounds=3` |

Knobs documented in [`../DEEP_EFFICIENCY.md`](../DEEP_EFFICIENCY.md).

---

## H1 — ZCode (PASS, faster)

**Query:** 智谱 ZCode 被指静默上传代码仓库：上传了哪些内容？是否跨境？官方如何回应？各方说法有何冲突？

| Metric | Round 5 | Round 6 | Δ |
|--------|---------|---------|---|
| duration | 446.4s | **401.9s** | **−44.5s (−10%)** |
| search_rounds | 5 | **3** | −2 |
| scrape_count | 11 | **5** | −6 |
| follow_up_searches | (present) | **0** | early-stop |
| search_provider_hits | `{serper:5}` | `{serper:3}` | — |
| gates | PASS | **PASS** | — |
| Evidence heading | `## Evidence（…）` | `## 证据与来源 / Evidence` | bilingual OK |

Early-stop + lower scrape/search volume correlate with the wall-clock win. Conflicts / Timeline / Confirmed still present.

---

## H3 — Houthis vs Saudi (PASS Evidence; slower wall-clock)

**Query:** 2026年9月胡塞武装称袭击沙特首都及延布能源设施：…能确认什么、不能确认什么？

| Metric | Round 5 | Round 6 | Δ |
|--------|---------|---------|---|
| duration | 533.2s | **965.2s** | **+432s (worse)** |
| search_rounds | 11 | **8** | −3 |
| scrape_count | (high) | **8** (cap) | capped |
| follow_up_searches | 2 | **1** | −1 |
| gates | **FAIL** `missing_evidence` | **PASS** | fixed |
| Evidence | missing heading | present (auto-repair) | fixed |

### Why wall-clock got worse (honest)

Efficiency knobs reduced search/scrape/follow-ups, but wall-clock rose because:

1. Hit **max_turns=12** (full budget) before summary
2. **LLM request timeouts** mid-run (retries on turn 12)
3. **3 final-summary attempts** (~215s of summary LLM time alone)

So Round 6 proves Evidence PASS + knobs firing; it does **not** claim H3 wall-clock regression is solved. Next leverage is summary retry policy / earlier loop exit when early-stop already fired with enough Conflicts material — out of Round-6 scope unless follow-up.

---

## Gate scoreboard (hard gates)

| Gate | H1 R6 | H3 R6 |
|------|-------|-------|
| TL;DR + confidence | ✓ | ✓ |
| Conflicts & Uncertainties | ✓ | ✓ |
| Timeline | ✓ | ✓ (short soft warn) |
| Evidence (+ sources) | ✓ | ✓ |
| Confirmed vs Unconfirmed | ✓ | ✓ |

---

## Honest bottom line

- **Evidence gate FAIL from Round 5 is fixed** (offline + live H3 PASS).
- **Deep efficiency knobs work** (parallel, scrape cap, Top-K=2, early-stop) and helped **H1 (−10% wall-clock)**.
- **H3 wall-clock did not improve** this run — dominated by LLM timeout/summary retries despite fewer searches/scrapes.
- No invented passes; soft citation/timeline warnings recorded but not waved as hard fails.
