# Verification Round 5 — LIVE hotspot cross-verification (anti-pollution)

## Date: 2026-09-20

## Scope

Round 5 abandons textbook Paris/Tokyo queries. Focus is **hotspot-event
cross-verification** so users are not confused by information pollution.

| Case | Query theme | Config | Hard gates |
|------|-------------|--------|------------|
| H1 | 智谱 ZCode 静默上传争议 | deep + verified + detailed | Conflicts / Timeline / Evidence / Confirmed vs Unconfirmed + confidence |
| H2 | 韩国 Re2O「尸皮针」 | deep + detailed | same |
| H3 | 2026-09 胡塞 vs 沙特袭击说法 | deep + verified + detailed | same |
| H4 | Same as H1 | light + compact | shorter; still hedge uncertainty; no invented certainty |
| H5A/H5B | Same as H3 | searxng-only vs parallel-trusted | profile + `search_provider_hits` diverge |

Product LLM: **glm-5.3-flash only** (Zhipu OpenAI-compatible Chat Completions).

## Pre-flight

| Check | Result |
|-------|--------|
| Credentials | Loaded from uploaded Round-5 JSON (never committed/printed) |
| Serper probe `q=OpenAI` | HTTP 200, organic hits |
| GLM `glm-5.3-flash` | Chat Completions OK (needs adequate `max_tokens`; reasoning tokens present) |
| Docker / SearXNG `127.0.0.1:27080` | Unavailable / unreachable (document honestly for H5A) |

## Code changes before live runs

### Conflicts section is now a hard requirement for `detailed`

Previously `ReportStructureValidator` only *suggested* a
`Disagreements / Uncertainty` block in the detailed template; it was **not**
required, so reports could pass without surfacing multi-source conflict.

| File | Change |
|------|--------|
| `apps/miroflow-agent/src/io/report_structure.py` | Require `conflicts`, `timeline`, `confirmed` for `detailed`; CN/EN heading aliases; soft unsourced-number warnings; enforce placeholder (never invent certainty) |
| `apps/miroflow-agent/src/core/answer_generator.py` | Detailed prompts mandate Conflicts / Timeline / Confirmed headings + confidence |
| `apps/miroflow-agent/scripts/run_acceptance_live.py` | Cases H1–H5; gate evaluation; full summary artifacts under `docs/acceptance/artifacts/round5/` |
| `apps/miroflow-agent/tests/test_report_structure_conflicts.py` | Unit coverage for Conflicts hard gate |

### Gate rules (fail case if missing on deep/detailed)

1. TL;DR / 结论 with **confidence** marker
2. **冲突与不确定 / Conflicts & Uncertainties**
3. Timeline / 时间线
4. Evidence with sources + dates
5. 已确认 vs 未确认 / Confirmed vs Unconfirmed
6. Numbers without a nearby source cue → recorded as soft warnings (do not invent PASS)

## How to re-run

```bash
cd apps/miroflow-agent
uv run python scripts/run_acceptance_live.py \
  --credentials /path/to/round5_credentials.json \
  --out-dir ../../docs/acceptance/artifacts/round5 \
  --cases H
```

## Live outcome

| Case | Verdict | Key evidence |
|------|---------|--------------|
| H1 ZCode deep/detailed | **PASS** | Conflicts + Timeline + Evidence + Confirmed; Serper `hits=5` |
| H2 Re2O deep/detailed | **PASS** | Conflicts present; Chinese `临床证据` heading accepted |
| H3 Houthis/Saudi deep/verified | **FAIL** | Conflicts excellent; **missing Evidence heading** |
| H4 ZCode light/compact | **PASS** | 2937 chars / 58s vs H1 6229 / 446s; still hedges |
| H5A searxng-only | **PASS** | `hits={searxng:6}`, `rounds=0` (unreachable, strict) |
| H5B parallel-trusted | **PASS** | `hits={serper:4}`, `rounds=4` |

**Overall: PARTIAL** (H3 Evidence gate fail). See `ACCEPTANCE_RESULTS_ROUND_5.md`.
