# VERIFY Round 8 — Squeeze final-draft / multi-summary path (wall-clock)

## Goal

Cut H3 wall-clock vs Round 7 (**782s PASS**) while keeping Conflicts + bilingual
Evidence + Timeline + Confirmed gates. Prefer one-shot structured final report
and surgical local structure repair over narrative rewrite loops.

H1 (~126s R7) is optional regression — should stay near that band.

## Root cause (from Round 7 artifacts)

H3 `case_H3.json` stage timings:

| Stage | ms | Note |
|-------|-----|------|
| `pipeline.total` | 782397 | Wall-clock |
| `answer_generator.llm_call.main` | 216483 | Research turns (+ HTTP timeouts) |
| `llm.request.final_summary` | 77796 | Already **1×** summary (R7 win) |
| `timeout_count` / `http_timeout_count` | 5 | Provider waits still dominate residual |

Remaining final-draft cost is **prompt size into the one summary call**
(full dumps + “禁止压缩” ideology) and optional verify/expand paths — not a
3× rewrite loop. Structure repair was append-stub only.

## Code changes to verify

1. **Oneshot skeleton prompt** (`answer_generator.py`): deep+detailed fills
   `ReportStructureValidator.get_structure_template("detailed")` once;
   skips expand rewrite; folds verification constraints into the same prompt
   (no separate verification LLM when oneshot).
2. **Summary context cap**: `summary_keep_tool_result=2` for `final_summary`
   only; strip `"Tool result is omitted…"` stubs before summary.
3. **`summary_max_tokens` cap** 4096 for deep oneshot.
4. **Surgical `enforce_structure`**: rename near-miss headings; inject
   Timeline/Conflicts heading above existing body (not full regenerate).
5. **`deep_post_early_stop_turns=1`** (was 2) to exit research sooner after agreement.

Knobs: see [`../DEEP_EFFICIENCY.md`](../DEEP_EFFICIENCY.md).

## Unit tests

```bash
cd apps/miroflow-agent
uv run pytest \
  tests/test_oneshot_final_report.py \
  tests/test_deep_efficiency.py \
  tests/test_report_structure_conflicts.py \
  tests/test_answer_generator_summary_passes.py \
  tests/test_deep_early_stop_exit.py \
  tests/test_answer_generator_outcome.py -q
```

Expected: all pass.

## Live acceptance

```bash
cd apps/miroflow-agent
uv run python scripts/run_acceptance_live.py \
  --credentials /path/to/creds.json \
  --cases H3,H1 \
  --out-dir ../../docs/acceptance/artifacts/round8
```

### Pass criteria

| Case | Must |
|------|------|
| H3 | `hotspot_detailed` PASS (Conflicts + Evidence + Timeline + Confirmed + confidence) |
| H3 | Wall-clock **< 782s** if not blocked by provider HTTP timeout latency alone |
| H1 | PASS; duration near ~126s (± large variance OK if gates hold) |

Honest reporting: if H3 still slow, attribute residual to `timeout_count` /
`http_timeout_count` vs `llm.request.final_summary` separately.

## Artifacts

- `docs/acceptance/artifacts/round8/case_H3.json` (+ summary md)
- `docs/acceptance/artifacts/round8/case_H1.json` (optional)
- `docs/acceptance/ACCEPTANCE_RESULTS_ROUND_8.md`
