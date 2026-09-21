# Verification Round 4 — Case D (Search Profile Divergence)

## Date: 2026-09-20

## Scope

Round 4 targets **Case D only**: same research query under two search profiles must show divergent routing.

| Run | Profile | Expected route |
|-----|---------|----------------|
| D1 | `searxng-only` | Provider order `searxng` only (strict) |
| D2 | `parallel-trusted` | `parallel_conf_fallback` with trusted order including Serper |

## Pre-flight

| Check | Result |
|-------|--------|
| Product LLM | glm-5.3-flash @ Zhipu OpenAI-compatible Chat Completions |
| `SERPER_API_KEY` | Present; probe `q=OpenAI` → HTTP 200, organic hits |
| Docker / compose searxng | **Unavailable** (`docker: command not found`, no docker.sock) |
| Local searxng `http://127.0.0.1:27080` | **Unreachable** (connect fail) |
| Coding model | Auto (Composer) |

Honest constraint: live SearXNG cannot be started in this environment. Case D still proves profile divergence with **Serper vs constrained searxng-only** (searxng attempted/failed; Serper live on parallel-trusted).

## Root Cause Found (blocking Case D with Serper present)

### CRITICAL-10: `resolve_order` silently expands `searxng-only`

`ProviderRegistry.resolve_order("searxng")` filtered unavailable names, then **appended every other available provider**. With `SERPER_API_KEY` set:

```text
configured: searxng
resolved (loose): [searxng, serper]   # BUG — "only" is not only
```

That made Round-4 Case D impossible to prove as different provider sets once Serper was loaded: both profiles could hit Serper.

### CRITICAL-11: Live harness did not load search credentials

`scripts/run_acceptance_live.py::_load_credentials` previously mapped only LLM keys. Round 3 Case D stayed PARTIAL partly because **SERPER was never injected** even when present in the credentials JSON.

### Gap: metrics hid failed / empty searches

`_record_search_evidence` only incremented `search_rounds` when organic links existed. A searxng-only failure left `search_rounds=0` with no provider attribution, so route divergence was invisible in `run_metrics`.

## Fixes Applied

| Area | Change |
|------|--------|
| `providers/registry.py` | `resolve_order(..., strict=False)`; strict skips append |
| `search_and_scrape_webpage.py` | Honors `SEARCH_PROVIDER_ORDER_STRICT` |
| `profile_resolver` + Gradio map | `searxng-only` sets `SEARCH_PROVIDER_ORDER_STRICT=1` |
| `settings.py` MCP env | Forwards ORDER_STRICT + searxng-only downgrade flags |
| `RunMetrics` / orchestrator | `search_attempts`, `search_provider_hits` from route_trace / provider fields |
| Live harness | Loads SERPER (+ other search keys); D1/D2 env mirrors `build_search_env`; captures route traces |

### Probe after fix

```text
D1_strict ['searxng']
D1_loose  ['searxng', 'serper']   # old behavior
D2_order  ['serper']              # only Serper available without SEARXNG_BASE_URL
serper_live_n 2                   # live Serper OK
```

## Live Case D Outcome (Round 4)

| Run | Result | Evidence |
|-----|--------|----------|
| D1 searxng-only | PASS | `search_provider_hits={searxng:5}`, `provider_order=["searxng"]`, searxng precheck failed (unreachable), answer `14,254,039` |
| D2 parallel-trusted | PASS | `search_provider_hits={serper:1}`, `search_rounds=1`, live Serper, answer `14.2 million` |

Tool error excerpt (D1, proves strict order — Serper **not** appended):

```json
{
  "success": false,
  "error": "searxng: precheck_failed::SearXNG 预检失败：All connection attempts failed",
  "searchParameters": {
    "provider": "searxng",
    "provider_mode": "fallback",
    "provider_order": ["searxng"]
  }
}
```

**Case D gate: PASS.** See `ACCEPTANCE_RESULTS_ROUND_4.md`.
