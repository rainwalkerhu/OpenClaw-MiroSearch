# Acceptance Results — Round 8 (oneshot final-draft / wall-clock)

## Date: 2026-09-20

## Summary

Round 8 targets residual H3 wall-clock after Round 7’s single-summary +
timeout fail-fast. Levers: oneshot skeleton final report, summary-stage tool
retention (keep 2), strip omitted stubs, surgical structure repair, and
`deep_post_early_stop_turns=1`.

| Case | Config | Round 5 | Round 6 | Round 7 | Round 8 | Verdict |
|------|--------|---------|---------|---------|---------|---------|
| H1 ZCode | deep + verified + detailed | **446.4s** PASS | **401.9s** PASS | **126.2s** PASS | **293.4s** PASS | **PASS** gates; slower than R7 (2× HTTP timeouts) |
| H3 Houthis/Saudi | deep + verified + detailed | **533.2s** FAIL Evidence | **965.2s** PASS | **782.4s** PASS | **479.4s** PASS | **PASS** Evidence; **−303.0s (−39%) vs R7** |

**Overall Round 8: PASS on gates. H3 well under R7 782s.** H1 remains PASS but
regressed vs R7’s clean 126s run because this live attempt hit **2** provider
HTTP timeouts (~90s-class waits); not a final-draft rewrite regression
(`summary_passes=1`, `final_summary` ≈62s).

Raw artifacts: [`artifacts/round8/`](./artifacts/round8/).

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

1. **Oneshot skeleton** (`answer_generator.py`): deep+detailed fills
   `get_structure_template("detailed")` once; skips length-expand rewrite;
   folds verification constraints into the same prompt (no separate
   verification LLM when oneshot).
2. **Summary context cap**: `summary_keep_tool_result=2` for `final_summary`
   only (research still uses `keep_tool_result=5`); strip omitted stubs before
   summary; `summary_max_tokens=4096`.
3. **Surgical `enforce_structure`**: rename near-miss headings; inject
   Timeline/Conflicts heading above existing body.
4. **`deep_post_early_stop_turns=1`** (was 2).

Docs: [`../DEEP_EFFICIENCY.md`](../DEEP_EFFICIENCY.md), [`VERIFY_ROUND_8.md`](./VERIFY_ROUND_8.md).

---

## H3 — Houthis vs Saudi (PASS, −39% vs R7)

**Query:** 2026年9月胡塞武装称袭击沙特首都及延布能源设施：…能确认什么、不能确认什么？

| Metric | Round 5 | Round 6 | Round 7 | Round 8 | Δ R8−R7 |
|--------|---------|---------|---------|---------|---------|
| duration | 533.2s (FAIL) | **965.2s** | **782.4s** | **479.4s** | **−303.0s** |
| gates | FAIL `missing_evidence` | PASS | PASS | **PASS** | — |
| `summary_passes` | — | ~3 | **1** | **1** | — |
| `timeout_count` | — | — | **5** | **3** | −2 |
| `llm_retry_count` | — | — | **4** | **2** | −2 |
| `early_stop_triggered` | — | — | True @ 7 | **True @ 6** | earlier exit |
| `llm.request.main` | — | 345s | **216s** | **118s** | −98s |
| `llm.request.final_summary` | — | 215s (3×) | **78s** (1×) | **75s** (1×) | −3s |
| search_rounds / scrape / follow_ups | 11 / high / 2 | 8 / 8 / 1 | **8 / 8 / 1** | **4 / 4 / 0** | fewer rounds |

### Gate scoreboard (H3)

| Gate | Result |
|------|--------|
| TL;DR + confidence | ✓ |
| Conflicts & Uncertainties | ✓ |
| Timeline | ✓ |
| Evidence (+ sources) | ✓ |
| Confirmed vs Unconfirmed | ✓ |

`structure_issues`: none. Soft failures: none.

### Where the time went (honest)

Final-summary LLM is still ~75s (model latency on a long structured draft) —
Round 8 did not magically shrink provider generation time. The **−303s** win
is mostly earlier research exit (`post_turns=1`, early-stop @6, fewer search/
scrape rounds) plus **2 fewer** HTTP timeouts than R7. Residual burn if
provider timeouts spike again remains outside the oneshot path.

Proof that summary retention worked: live log shows
`Total tool results: 6, Keeping last 2` on the `final_summary` call.

---

## H1 — ZCode (PASS, slower than R7 clean run)

**Query:** 智谱 ZCode 被指静默上传代码仓库：…各方说法有何冲突？

| Metric | Round 5 | Round 6 | Round 7 | Round 8 | Δ R8−R7 |
|--------|---------|---------|---------|---------|---------|
| duration | 446.4s | **401.9s** | **126.2s** | **293.4s** | **+167.2s** |
| gates | PASS | PASS | PASS | **PASS** | — |
| `summary_passes` | — | ~multi | **1** | **1** | — |
| `early_stop_triggered` | — | — | True @ 4 | **True @ 3** | — |
| timeouts / retries | — | — | **0 / 0** | **2 / 1** | provider waits |
| `llm.request.final_summary` | — | — | ~64s | **62s** | ~flat |
| search_rounds / scrape / follow_ups | 5 / 11 / — | 3 / 5 / 0 | **4 / 4 / 0** | **4 / 6 / 0** | — |

Soft only: `insufficient_citations` (not a hard fail). Hard gates all present.

### Why slower than R7 (honest)

R7 H1 was a clean run (0 timeouts). This R8 attempt paid for **2 HTTP
timeouts**. Final-summary stage is essentially unchanged (~62s). Not a
oneshot/skeleton regression — variance dominated by provider latency.

---

## Metrics proof (Round 8 fields)

| Field | H3 | H1 |
|-------|----|----|
| `timeout_count` | 3 | 2 |
| `http_timeout_count` | 3 | 2 |
| `llm_retry_count` | 2 | 1 |
| `summary_passes` | 1 | 1 |
| `early_stop_triggered` | true | true |
| `early_stop_turn` | 6 | 3 |

---

## Conclusion

Round 8 meets the primary goal: **H3 PASS under 782s (479s)**. Final-draft path
is oneshot + local surgical repair; remaining wall-clock risk is still
**provider HTTP timeout waits**, not multi-pass rewrite loops.
