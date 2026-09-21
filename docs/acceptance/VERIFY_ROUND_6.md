# Verification Round 6 — Evidence gate fix + deep efficiency

## Date: 2026-09-20

## Scope

Round 6 ships **both**:

1. **Evidence gate fix** (must-fix from Round 5 H3 FAIL)
2. **Deep efficiency** knobs (parallel tools, early-stop, scrape/clue budgets)

Product LLM: **glm-5.3-flash** only. Live hotspot cases: **H1** (ZCode) and **H3** (Houthis/Saudi).

## Pre-flight

| Check | Result |
|-------|--------|
| Credentials | Loaded from uploaded Round-6 JSON (never committed/printed) |
| Serper probe `q=OpenAI` | HTTP 200, organic hits |
| GLM `glm-5.3-flash` | Chat Completions OK |
| Branch | `cursor/research-quality-improvements-e664` (PR #1) |

## Part A — Evidence gate

### Code

| File | Change |
|------|--------|
| `apps/miroflow-agent/src/io/report_structure.py` | Broader bilingual `_EVIDENCE` aliases; **auto-repair** Evidence from inline sources/URLs when heading missing |
| `apps/miroflow-agent/src/core/answer_generator.py` | Prompt lists CN/EN Evidence headings |
| `apps/miroflow-agent/tests/test_report_structure_conflicts.py` | Bilingual acceptance + auto-repair unit tests |

### Offline re-check (Round-5 H3 artifact)

Against `docs/acceptance/artifacts/round5/case_H3_summary.md`:

| Step | Result |
|------|--------|
| Before `enforce_structure` | `missing_required` includes `evidence` (and truncated `conclusion`/`confirmed`) |
| After `enforce_structure` | **PASS** — Evidence section length 1646; found `tldr, conclusion, conflicts, timeline, evidence, confirmed, references` |

Artifacts: `docs/acceptance/artifacts/round6/h3_offline_evidence_repair.{json,md}`

### Live H3 (target)

Must **PASS** Evidence gate (was FAIL in Round 5 solely for missing Evidence heading).

## Part B — Deep efficiency

Documented in [`docs/DEEP_EFFICIENCY.md`](../DEEP_EFFICIENCY.md).

| Knob | Deep default |
|------|----------------|
| `parallel_tool_calls` | true |
| `deep_early_stop_on_agreement` | true (≥2 independent domains + min search rounds) |
| `max_scrape_per_task` | 8 |
| `max_lead_follow_ups` (clue Top-K) | 2 |

Wired in `deep_efficiency.py`, `orchestrator.py`, `lead_tracker.py`, `profile_resolver.apply_intensity_adjustments`.

## Part C — Live benchmark

```bash
cd apps/miroflow-agent
uv run python scripts/run_acceptance_live.py \
  --credentials /path/to/round6_credentials.json \
  --out-dir ../../docs/acceptance/artifacts/round6 \
  --cases H3,H1
```

### Round-5 baselines (before)

| Case | Duration | Verdict |
|------|----------|---------|
| H1 ZCode deep+detailed | **446.4s** | PASS |
| H3 Houthis deep+verified | **533.2s** | **FAIL** (`missing_evidence`) |

### Round-6 results

| Case | Duration | Verdict | Notes |
|------|----------|---------|-------|
| H3 Houthis/Saudi | **965.2s** | **PASS** | Evidence heading present (auto-repair); search_rounds 8, scrape 8 (capped), follow_ups 1. Wall-clock **worse** than R5 533s (LLM timeouts + 3× summary + max turns) |
| H1 ZCode | **401.9s** | **PASS** | vs R5 446.4s (−10%); early-stop at turn 7 (19 domains); scrape 5; follow_ups 0 |

See `ACCEPTANCE_RESULTS_ROUND_6.md`.

## How to re-run

Same harness as Round 5; cases `H3,H1` (optional `H2`).
