# Verification Round 3 — Lead Trail Root Cause + Live Proof

## Date: 2026-09-20

## Summary

Round 3 started by **proving `lead_tracker.enabled` in the live Hydra harness before any code changes**. The probe shows Case C’s Round 2 overrides never enabled the tracker. That, plus weak English lead extraction and a trail formatter that only emits followed leads, explains Case C FAIL (`no lead trail`, `follow_up_searches=0`).

---

## Probe: `tracker.enabled` BEFORE Fixes

Harness: Hydra `compose` with `agent=mirothinker_v1.5_keep5_max200`, `llm=glm-flash`, same override shapes as Round 2 / API.

### Result 1 — Round 2 Case C overrides → **enabled=False**

Overrides (exactly as Round 2 harness):

```text
+agent.main_agent.research_intensity=deep
+agent.main_agent.enable_lead_tracking=true
+agent.main_agent.max_lead_follow_ups=2
```

Observed:

| Field | Value |
|-------|-------|
| `cfg.agent.enable_lead_tracking` | **MISSING** |
| `cfg.agent.main_agent.enable_lead_tracking` | `True` |
| `cfg.agent.research_intensity` | **MISSING** |
| `cfg.agent.main_agent.research_intensity` | `deep` |
| Orchestrator `LeadTrackingManager(enabled=...)` | **`False`** |

**Root cause (CRITICAL-7):** Orchestrator reads `cfg.agent.get("enable_lead_tracking")` (agent **root**). Round 2 CLI put the flag under `agent.main_agent.*`. Tracker never initialized a trail; no extraction; no follow-ups; no trail section.

### Result 2 — API `profile_resolver` style → **enabled=True**

Overrides (matches `apply_intensity_adjustments` / `build_full_overrides`):

```text
++agent.research_intensity=deep
++agent.enable_lead_tracking=true
++agent.max_lead_follow_ups=2
```

Observed: `cfg.agent.enable_lead_tracking=True` → orchestrator would set **`enabled=True`**.

### Result 3 — Deep intensity alone (no enable flag) → **enabled=False**

```text
++agent.research_intensity=deep
```

Observed: intensity is on agent root, but without `enable_lead_tracking` or `effective_config`, orchestrator stays **`enabled=False`**.

Pipeline auto-enable only runs when `effective_config` is passed into `execute_task_pipeline`. Hydra `main.py` / Round 2 harness **do not pass `effective_config`**, so deep-intensity auto-enable never fires on the CLI path.

---

## Additional Root Causes (Case C)

### CRITICAL-8: Trail section only lists **followed** leads

`LeadTrail.format_trail_section()`:

```python
if not self.leads or all(not l.followed_up for l in self.leads):
    return ""
```

Even with leads extracted, if none are marked followed up, the final report gets **no** `## 线索追踪 / Lead Trail` section.

### CRITICAL-9: English flash answer extraction is too weak

Patterns require markers like `investigate:`, `further research needed`, `uncertain:`. glm-5.3-flash Case C answers were narrative English without those markers, so extraction yields `[]` even when enabled.

Also: early `should_break and tool_calls: break` can exit **before** the lead follow-up injection block.

### CRITICAL-4 status (Round 2 metrics)

`scrape_url` was already added to `SCRAPE_TOOL_NAMES` in Round 2 commit `70151d3`. Round 3 must **re-verify** Case B `scrape_count > 0` live (not invent a pass).

---

## Required Fixes

1. Resolve enable from agent root **or** `main_agent`, and auto-enable when `research_intensity==deep`.
2. Strengthen English/Chinese lead extraction; optionally seed deep-query leads.
3. Emit trail for all leads (followed + pending); keep follow-up injection before final break.
4. Live harness: use `++agent.enable_lead_tracking=true` (or rely on fixed resolver); pass/build `effective_config` for metrics.
5. Re-run live A–E with glm-5.3-flash; record real excerpts in `ACCEPTANCE_RESULTS_ROUND_3.md`.

---

## Probe: `tracker.enabled` AFTER Fixes

Same Round 2 Case C overrides (`+agent.main_agent.enable_lead_tracking=true`, …):

| Field | Before | After |
|-------|--------|-------|
| `resolve_lead_tracking_config(...).enabled` | False | **True** |
| `max_follow_ups` | 3 (ignored main_agent=2) | **2** |
| Query-seeded leads for DNA→CRISPR | n/a | **2** |
| `get_trail_section()` contains `Lead Trail` | no | **yes** (pending leads) |

Deep intensity alone (`++agent.research_intensity=deep`, no explicit flag) → **enabled=True**.  
Light intensity → **enabled=False**.

Unit tests: `apps/miroflow-agent/tests/test_lead_tracker.py` — 7 passed.

---

## Code Changes

| File | Change |
|------|--------|
| `lead_tracker.py` | `resolve_lead_tracking_config`, stronger EN extraction, query seeding, trail lists all leads |
| `orchestrator.py` | use resolver; `_inject_lead_followup` before early break |
| `pipeline.py` | enable tracking on CLI path without `effective_config` |
| `scripts/run_acceptance_live.py` | live A–E harness with glm-5.3-flash + effective_config |
| `conf/llm/glm-flash.yaml` | OpenAI-compatible glm-5.3-flash config (no secrets) |

---

## Acceptance Gate for Round 3

| Case | Must show |
|------|-----------|
| A | Correct quick answer; light intensity |
| B | `scrape_count > 0` (or search_rounds > 0) after SCRAPE fix |
| C | `lead_tracker.enabled=True`, trail section present, `follow_up_searches ≥ 1` |
| D | First live profile comparison (honest if search keys missing) |
| E | First live compact vs detailed comparison |

**No invented passes.** Live results → `ACCEPTANCE_RESULTS_ROUND_3.md`.

---

## Live A–E Outcome (Round 3)

| Case | Result | Evidence |
|------|--------|----------|
| A | PASS | Paris; tracker.enabled=False; 9s |
| B | PASS | scrape_count=**10**; boxed 37.4 |
| C | PASS | trail=True; follow_up_searches=**2**; tracker.enabled=True on main_agent path |
| D | PARTIAL | effective_config profiles differ; search_rounds=0 (no keys) |
| E | PASS | compact vs detailed recorded; both completed |

Round 3 gate for lead-trail **met**. See `ACCEPTANCE_RESULTS_ROUND_3.md` and `artifacts/round3/acceptance_results_round3.json`.
