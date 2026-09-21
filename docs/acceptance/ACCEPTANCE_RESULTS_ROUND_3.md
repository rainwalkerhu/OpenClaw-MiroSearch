# Acceptance Results — Round 3 (LIVE E2E)

## Date: 2026-09-20

## Summary

Live A–E with **glm-5.3-flash** (Zhipu OpenAI-compatible Chat Completions). Lead-tracking enable-path fix verified in harness and in Case C live output.

| Case | Verdict | Key evidence |
|------|---------|--------------|
| A | **PASS** | `Paris`, 9.0s, intensity=light, tracker.enabled=False |
| B | **PASS** | `37.4` Gt, **scrape_count=10** (>0), effective_config populated |
| C | **PASS** | **Lead Trail present**, **follow_up_searches=2**, tracker.enabled=True |
| D | **PARTIAL** | effective_config search_profile differs (searxng-only vs parallel-trusted); no search API keys → search_rounds=0 |
| E | **PASS** | Same deep query; compact vs detailed both completed; detail_level recorded in effective_config |

**Product LLM**: glm-5.3-flash throughout (`model_route_hits` confirm).  
**Raw artifacts**: `artifacts/round3/` (`acceptance_results_round3.json`).

---

## Environment

- Harness: `apps/miroflow-agent/scripts/run_acceptance_live.py`
- LLM: glm-5.3-flash @ `open.bigmodel.cn/api/coding/paas/v4`
- Search providers: **not configured** (same limitation as Round 2)
- Scraping: Trafilatura / scrape_url worked

---

## Pre-flight: tracker.enabled

Round-2-style Case C overrides (`+agent.main_agent.enable_lead_tracking=true`):

| | Before fix | After fix (live) |
|--|------------|------------------|
| `tracker.enabled` | False | **True** (`tracker_enabled_at_compose=true`) |
| `max_lead_follow_ups` | ignored (default 3) | **2** |

See `VERIFY_ROUND_3.md`.

---

## Case A — Simple fact (light + compact)

**Query:** What is the capital of France?

```json
{
  "status": "completed",
  "duration_seconds": 8.99,
  "tracker_enabled_at_compose": false,
  "final_boxed_answer": "Paris",
  "metrics": {
    "search_rounds": 0,
    "scrape_count": 0,
    "follow_up_searches": 0,
    "effective_config": {
      "research_intensity": "light",
      "output_detail_level": "compact"
    }
  }
}
```

**Verdict: PASS** — correct answer, light intensity, tracker off.

---

## Case B — Contested numeric (verified + deep + detailed)

**Query:** What were the global CO2 emissions in 2023?

```json
{
  "status": "completed",
  "duration_seconds": 241.9,
  "tracker_enabled_at_compose": true,
  "final_boxed_answer": "37.4",
  "metrics": {
    "search_rounds": 0,
    "scrape_count": 10,
    "follow_up_searches": 1,
    "effective_config": {
      "mode": "verified",
      "research_intensity": "deep",
      "output_detail_level": "detailed",
      "verification_min_search_rounds": 3
    }
  }
}
```

**Excerpt (TL;DR):**
> IEA report (*CO2 Emissions in 2023*): Global energy-related CO2 emissions rose 1.1% (+410 Mt) in 2023, reaching a record high of **37.4 Gt**.

**Verdict: PASS** for Round-3 gate (`scrape_count > 0`).  
Note: `search_rounds` still 0 because google_search had no provider keys (agent fell back to scraping). Lead trail also present (deep auto-enable) — not required for Case B.

---

## Case C — Chained research (deep + lead tracking) — **primary Round 3 target**

**Query:** How did the discovery of DNA structure lead to CRISPR technology?

**Overrides (Round-2 main_agent path intentionally retained):**
```text
+agent.main_agent.research_intensity=deep
+agent.main_agent.enable_lead_tracking=true
+agent.main_agent.max_lead_follow_ups=2
```

```json
{
  "status": "completed",
  "duration_seconds": 228.8,
  "tracker_enabled_at_compose": true,
  "tracker_max_follow_ups": 2,
  "has_lead_trail": true,
  "metrics": {
    "search_rounds": 0,
    "scrape_count": 10,
    "follow_up_searches": 2,
    "effective_config": {
      "mode": "research",
      "research_intensity": "deep",
      "output_detail_level": "balanced"
    }
  },
  "lead_steps_count": 14
}
```

**Lead Trail excerpt (from final summary):**
```markdown
## 线索追踪 / Lead Trail

### Lead 1: What intermediate scientific discoveries connected the discovery of DNA structure to CRISPR technology?
**来源**: query_seed (Turn 0)
**优先级**: 0.95
**状态**: followed
**追踪轮次**: Turn 4
```

Log also recorded: `Total leads: 6, Followed up: 2, Unfollowed: 4` and `Appended lead trail section (1129 chars)`.

**Verdict: PASS** — trail present + `follow_up_searches ≥ 1` (actual **2**).

---

## Case D — Search profile comparison (first live)

Same query: *What is the current population of Tokyo?*

| | D1 searxng-only | D2 parallel-trusted |
|--|-----------------|---------------------|
| status | completed | completed |
| boxed | `14254039` | `14254039` |
| duration | 117.2s | 78.5s |
| scrape_count | 5 | 6 |
| search_rounds | 0 | 0 |
| effective_config.search_profile | **searxng-only** | **parallel-trusted** |
| SEARCH_PROVIDER_ORDER env | searxng | serper,serpapi,searxng |

**Verdict: PARTIAL** — `effective_config` differs as required; live provider-route difference could not be proven without SERPER/SEARXNG keys (both paths fell back to scraping).

---

## Case E — Detail level comparison (first live)

Same query: *Summarize the main causes of the 2008 financial crisis.*  
Both deep intensity.

| | E1 compact | E2 detailed |
|--|------------|-------------|
| status | completed | completed |
| duration | 296.5s | 324.7s |
| scrape_count | 16 | 15 |
| follow_up_searches | 1 | 1 |
| output_detail_level | **compact** | **detailed** |
| trail | yes (deep) | yes (deep) |

E1 boxed opens with a shorter cause list; E2 boxed includes extended contested-aspects discussion (FCIC dissent, CRA/GSE debate, savings glut vs Taylor rule).

**Verdict: PASS** for first live comparison — detail_level correctly recorded; outputs differ in breadth. Structure enforcement for detailed Evidence/References sections remains imperfect (same theme as Round 2).

---

## Metrics re-verification (Round 2 SCRAPE fix)

| Case | scrape_count | Notes |
|------|--------------|-------|
| A | 0 | Expected (no tools) |
| B | **10** | Was 0 in Round 2 → **fixed** |
| C | **10** | Recorded |
| D1/D2 | 5 / 6 | Recorded |
| E1/E2 | 16 / 15 | Recorded (`scrape_url` + `scrape_and_extract_info`) |

`search_rounds` remains 0 across cases without search API keys — honest limitation, not a metrics-wiring failure for scrapes.

---

## Overall Round 3

| Gate | Result |
|------|--------|
| Prove tracker.enabled | ✅ |
| Fix enable + extraction + trail | ✅ |
| Case A | ✅ PASS |
| Case B scrape_count>0 | ✅ PASS |
| Case C trail + follow_up≥1 | ✅ PASS |
| Case D first live | ⚠️ PARTIAL (config differs; no search keys) |
| Case E first live | ✅ PASS (with structure caveat) |

**Round status: CLEAN enough to stop** (Case D partial is environment-limited, not a regression). No invented passes.
