# Acceptance Results — Round 7 (LLM timeout & retry path / wall-clock)

## Date: 2026-09-20

## Summary

Round 7 targets the Round-6 H3 wall-clock regression (LLM timeouts + identical
retries + 3× summary + full `max_turns` after early-stop). Quality gates from
Rounds 5–6 are unchanged.

| Case | Config | Round 5 | Round 6 | Round 7 | Verdict |
|------|--------|---------|---------|---------|---------|
| H1 ZCode | deep + verified + detailed | **446.4s** PASS | **401.9s** PASS | **126.2s** PASS | **PASS** (−69% vs R6) |
| H3 Houthis/Saudi | deep + verified + detailed | **533.2s** FAIL (`missing_evidence`) | **965.2s** PASS | **782.4s** PASS | **PASS** Evidence; **−182.8s (−19%) vs R6** |

**Overall Round 7: PASS on gates + measurable H3 wall-clock improvement vs Round 6.**
H3 is still slower than Round 5’s failing run (533s) because provider HTTP
timeouts (~90s each) still consume wall-clock before fail-fast aborts retries;
that remaining burn is documented honestly below.

Raw artifacts: [`artifacts/round7/`](./artifacts/round7/).

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

## Code levers shipped

1. **Timeout fail-fast** (`openai_client.py`): detect APITimeoutError/httpx timeouts;
   one shorter-context degrade retry; then raise. Metrics: `timeout_count`,
   `http_timeout_count`, `llm_retry_count`.
2. **Single summary** (`max_final_answer_retries=1` for deep): skip length-expand
   LLM retry when Conflicts/Evidence/Confirmed already present; `summary_passes`.
3. **Early-stop exit** (`deep_exit_on_early_stop`, `post_turns=2`): nudge once then
   force summary; also exit on LLM failure after nudge (follow-up fix).
4. **glm-flash**: `max_retries=2`, `retry_wait_seconds=2`, `timeout_fail_fast=true`.

Docs: [`../DEEP_EFFICIENCY.md`](../DEEP_EFFICIENCY.md), [`VERIFY_ROUND_7.md`](./VERIFY_ROUND_7.md).

---

## H3 — Houthis vs Saudi (PASS, faster than R6)

**Query:** 2026年9月胡塞武装称袭击沙特首都及延布能源设施：…能确认什么、不能确认什么？

| Metric | Round 5 | Round 6 | Round 7 | Δ R7−R6 |
|--------|---------|---------|---------|---------|
| duration | 533.2s (FAIL) | **965.2s** | **782.4s** | **−182.8s** |
| gates | FAIL `missing_evidence` | PASS | **PASS** | — |
| `summary_passes` | (n/a) | ~3 (stage timing) | **1** | −2 LLM summaries |
| `timeout_count` | (under-counted 0) | 0 (bug) | **5** | metrics fixed |
| `llm_retry_count` | — | — | **4** | visible |
| `early_stop_triggered` | — | (follow-ups only) | **True @ turn 7** | exit path live |
| `llm.request.main` | — | 345s (+~385s retry gap) | **216s** (≈ outer wall) | retry gap closed |
| `llm.request.final_summary` | — | 215s (3×) | **78s** (1×) | −137s |
| search_rounds / scrape / follow_ups | 11 / high / 2 | 8 / 8 / 1 | **8 / 8 / 1** | same retrieval caps |

### Gate scoreboard (H3)

| Gate | Result |
|------|--------|
| TL;DR + confidence | ✓ |
| Conflicts & Uncertainties | ✓ |
| Timeline | ✓ |
| Evidence (+ sources) | ✓ |
| Confirmed vs Unconfirmed | ✓ |

Soft only: `insufficient_citations` (not a hard fail).

### Why not back to Round-5 533s (honest)

Fail-fast stops *identical* timeout retries, but each provider timeout still waits
~`LLM_HTTP_TIMEOUT_SECONDS` (90s) before returning. H3 recorded **5** HTTP timeouts
≈ several minutes of unavoidable wait. Remaining lever: lower HTTP timeout and/or
exit-to-summary immediately on first post-nudge timeout (follow-up patch landed
after this live run for the empty-response path).

---

## H1 — ZCode (PASS, large wall-clock win)

**Query:** 智谱 ZCode 被指静默上传代码仓库：…各方说法有何冲突？

| Metric | Round 5 | Round 6 | Round 7 | Δ R7−R6 |
|--------|---------|---------|---------|---------|
| duration | 446.4s | **401.9s** | **126.2s** | **−275.7s (−69%)** |
| gates | PASS | PASS | **PASS** | — |
| `summary_passes` | — | ~multi | **1** | — |
| `early_stop_triggered` | — | turn 7 follow-ups | **True @ turn 4** | exit path |
| timeouts / retries | — | — | **0 / 0** | clean |
| search_rounds / scrape / follow_ups | 5 / 11 / — | 3 / 5 / 0 | **4 / 4 / 0** | — |

Early-stop @ turn 4 + single summary (~64s) drove the large win. No invented certainty
markers required beyond existing Confirmed/Conflicts sections.

---

## Metrics proof (Round 7 fields)

| Field | H3 | H1 |
|-------|----|----|
| `timeout_count` | 5 | 0 |
| `http_timeout_count` | 5 | 0 |
| `llm_retry_count` | 4 | 0 |
| `summary_passes` | 1 | 1 |
| `early_stop_triggered` | true | true |
| `early_stop_turn` | 7 | 4 |

---

## Honest bottom line

- **H3 Evidence PASS retained**; wall-clock **improved vs Round 6** (−19%) but still
  above Round 5’s *failing* baseline due to provider timeout waits.
- **H1 substantially faster** (−69% vs R6) with early-stop exit + single summary.
- **Metrics now tell the truth** about timeouts/retries/summary passes (Round 6
  showed `timeout_count=0` despite timeout burn).
- No invented passes; soft citation warning on H3 recorded.
