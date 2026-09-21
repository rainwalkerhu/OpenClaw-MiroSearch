# VERIFY Round 7 — Optimize LLM timeout & retry path (wall-clock)

## Goal

Cut H3 wall-clock regression from Round 6 (965s PASS Evidence) without
losing Round 5/6 quality gates (Conflicts, bilingual Evidence, Timeline,
Confirmed; no invented certainty). Primary: live H3; secondary: H1.

## Root cause (from Round 6 artifacts)

H3 `case_H3.json` metrics:

| Stage | ms | Note |
|-------|-----|------|
| `answer_generator.llm_call.main` | 729539 | Outer wall incl. failed attempts |
| `llm.request.main` | 344638 | Successful requests only |
| **Δ retry/fail burn** | **~385s** | Silent HTTP timeouts retried identically; `timeout_count=0` (metrics gap) |
| `llm.request.final_summary` | 215305 | **3×** summary passes |
| `max_turns` | 12 | Full budget; early-stop only stopped lead follow-ups |

## Code changes to verify

1. **Timeout fail-fast** (`openai_client.py`): detect APITimeoutError/httpx timeouts;
   one shorter-context degrade retry; then raise. Metrics: `timeout_count`,
   `http_timeout_count`, `llm_retry_count`.
2. **Single summary** (`answer_generator.py` + deep defaults): 
   `max_final_answer_retries=1` for deep; skip length-expand LLM retry when
   Conflicts/Evidence/Confirmed already present; `summary_passes` metric;
   wall timeout increments `wall_timeout_count`.
3. **Early-stop exit** (`orchestrator.py`): after early-stop + `post_turns=2`,
   nudge once then force summary; record `early_stop_triggered` / `early_stop_turn`.
4. **glm-flash.yaml**: `max_retries=2`, `retry_wait_seconds=2`, `timeout_fail_fast=true`.

## Unit tests

```bash
cd apps/miroflow-agent
uv run pytest \
  tests/test_llm_timeout_fail_fast.py \
  tests/test_deep_efficiency.py \
  tests/test_deep_early_stop_exit.py \
  tests/test_answer_generator_summary_passes.py \
  tests/test_handle_llm_call_wall_timeout.py \
  tests/test_answer_generator_outcome.py -q
```

Expected: all pass.

## Live acceptance

Credentials: uploaded Round 6 JSON → glm-5.3-flash + Serper (never commit/print).

```bash
cd apps/miroflow-agent
# load creds into env (local only)
uv run python scripts/run_acceptance_live.py --cases H3,H1 \
  --out-dir ../../docs/acceptance/artifacts/round7
```

### Pass criteria (honest)

| Case | Must | Wall-clock |
|------|------|------------|
| H3 | Gate PASS (Conflicts + Evidence + Timeline + Confirmed) | Prefer **&lt; Round6 965s**; report honestly if not |
| H1 | Gate PASS | Prefer ≤ Round6 402s or better |

Also record: `summary_passes`, `timeout_count`, `llm_retry_count`,
`early_stop_triggered`, stage timing gaps.

## Deliverables

- [x] Code + unit tests
- [x] `docs/acceptance/VERIFY_ROUND_7.md` (this file)
- [x] `docs/acceptance/ACCEPTANCE_RESULTS_ROUND_7.md`
- [x] `docs/acceptance/artifacts/round7/`
- [x] Updated `docs/DEEP_EFFICIENCY.md`
- [x] Push `cursor/research-quality-improvements-e664` / update PR #1

## Live results (2026-09-20)

| Case | Duration | Gates | Notes |
|------|----------|-------|-------|
| H3 | **782.4s** | PASS | vs R6 965.2s (−19%); `summary_passes=1`, early-stop@7, `timeout_count=5` |
| H1 | **126.2s** | PASS | vs R6 401.9s (−69%); early-stop@4, zero timeouts |

See `ACCEPTANCE_RESULTS_ROUND_7.md`.
