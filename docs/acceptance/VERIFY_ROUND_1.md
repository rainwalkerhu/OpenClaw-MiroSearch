# Verification Round 1 - Code Audit

## Date: 2026-09-20

## Summary
Comprehensive code audit reveals significant gaps between the implementation claims and actual integration. While foundational infrastructure is present, critical wiring to orchestrator is missing or incomplete.

---

## Critical Issues (Blocking E2E Tests)

### CRITICAL-1: LeadTracker Not Integrated into Orchestrator
**Severity**: CRITICAL
**File**: `apps/miroflow-agent/src/core/orchestrator.py`

**Evidence**:
- `LeadTracker` and `LeadTrackingManager` classes exist in `src/core/lead_tracker.py`
- No imports or usage found in orchestrator
- No initialization in `Orchestrator.__init__`
- No lead extraction from assistant responses
- No follow-up generation based on leads
- Acceptance Case C will FAIL: "≥1 follow-up search from a prior lead" cannot happen

**Impact**:
- `research_intensity=deep` enables lead tracking via config but nothing executes
- Lead trail section will never appear in reports
- Chained-clue research (Case C) is non-functional

**Root Cause**:
Implementation Summary states: "Full orchestrator integration can be completed in a follow-up PR to keep changes focused and reviewable" - but this means Case C cannot pass.

---

### CRITICAL-2: Scrape Counting Not Wired
**Severity**: CRITICAL
**File**: `apps/miroflow-agent/src/core/orchestrator.py`

**Evidence**:
```bash
$ grep -r "record_scrape" apps/miroflow-agent/src/core/orchestrator.py
# No results
```

- `RunMetrics.record_scrape()` method exists
- Never called when tools like `jina_reader`, `firecrawl`, or browser tools execute
- Acceptance tests check `metrics["scrape_count"]` but it will always be 0

**Impact**:
- Cannot verify intensity affects scraping behavior
- Metrics always show `scrape_count: 0` regardless of actual scraping

---

### CRITICAL-3: Follow-Up Search Counting Not Wired
**Severity**: CRITICAL
**File**: `apps/miroflow-agent/src/core/orchestrator.py`

**Evidence**:
```bash
$ grep -r "record_follow_up" apps/miroflow-agent/src/core/orchestrator.py
# No results
```

- `RunMetrics.record_follow_up_search()` method exists
- Never called even when searches happen
- Cannot distinguish follow-up searches from initial searches

**Impact**:
- Cannot verify lead-driven follow-ups
- Metrics misleading for deep research analysis

---

## Major Issues (Quality/Correctness)

### MAJOR-1: Structure Validation Only Active in Demo Mode
**Severity**: MAJOR
**File**: `apps/miroflow-agent/src/io/output_formatter.py:232-233`

**Evidence**:
```python
def format_final_summary_payload(
    self,
    final_answer_text: str,
    client=None,
    detail_level: str = "balanced",
    validate_structure: bool = True,  # Default True
) -> dict:
    # ...
    if validate_structure and display_text:
        struct_valid, struct_issues, struct_meta = ReportStructureValidator.validate_structure(
            display_text, detail_level
        )
```

But in `answer_generator.py:790`:
```python
payload = self.output_formatter.format_final_summary_payload(
    final_answer_text,
    self.llm_client,
    detail_level=self.output_detail_level,
    validate_structure=self.research_report_mode,  # <-- Conditional!
)
```

**Impact**:
- Structure validation disabled unless `research_report_mode=true`
- Acceptance Case E ("detailed full sections") may fail in default mode
- Cases A/B/E may not enforce required sections

**Root Cause**:
Conservative activation: validation tied to demo mode, not intensity/detail level

---

### MAJOR-2: Effective Config Not Passed to Agent
**Severity**: MAJOR
**Files**: 
- `apps/api-server/services/profile_resolver.py`
- `apps/api-server/services/pipeline_runtime.py`

**Evidence**:
- `effective_config` built in `resolve_effective_research_params()`
- Stored in `TaskMeta.effective_config`
- **Not passed down to orchestrator or agent config**
- Agent cannot see `research_intensity` to adjust behavior dynamically

**Impact**:
- LeadTracker (if integrated) wouldn't know to enable for `deep`
- Cannot log effective_config in RunMetrics at runtime
- Disconnect between API layer config and agent execution

---

### MAJOR-3: Intensity Adjustments Only Affect Hydra Overrides
**Severity**: MAJOR
**File**: `apps/api-server/services/profile_resolver.py`

**Evidence**:
Intensity multiplies `max_turns` and verification rounds via Hydra CLI overrides:
```python
def build_full_overrides(..., research_intensity="standard"):
    # ...
    if research_intensity == "deep":
        adjusted_turns = min(30, int(baseline_turns * 1.5))
    # ...
    overrides.append(f"main_agent.max_turns={adjusted_turns}")
```

**Impact**:
- Adjustments are static at pipeline launch
- No dynamic encouragement of scraping during execution
- "Scrape encouragement: HIGH" (from docs) has no implementation
- Cannot detect stalled research and push for more depth

---

## Minor Issues (Usability/Documentation)

### MINOR-1: Acceptance Tests Are Unit Tests, Not E2E
**Severity**: MINOR
**File**: `apps/api-server/tests/test_research_quality_acceptance.py`

**Evidence**:
- All tests check config plumbing, not real research outputs
- No actual `/v1/research` calls with real queries
- No validation of report structure, lead trails, or citations
- Titles say "acceptance" but behavior is unit-level

**Impact**:
- False confidence: tests pass but real features don't work
- Missing: actual queries like "Capital of France?" or "Global CO2 emissions 2023"

---

### MINOR-2: Documentation Claims vs Reality
**Severity**: MINOR
**File**: `IMPLEMENTATION_SUMMARY.md`, `../RESEARCH_INTENSITY.md`

**Evidence**:
Documentation states:
- "Lead tracking enabled by default" for deep
- "Scrape encouragement: HIGH"
- "Verification rounds: 130% of requested"

Reality:
- LeadTracker not integrated → no lead tracking
- No scrape encouragement code found
- Verification rounds adjusted but no enforcement of scraping

---

## Additional Observations

### OBS-1: Search Round Tracking Works
**Status**: ✅ WORKING
**File**: `apps/miroflow-agent/src/core/orchestrator.py:407`

```python
self.task_log.run_metrics.search_rounds += 1
```

- This is called correctly
- Verification logic tracks `self.verification_search_rounds`
- Acceptance Case A/B can partially verify this

---

### OBS-2: Report Structure Validator Implementation is Solid
**Status**: ✅ GOOD QUALITY
**File**: `apps/miroflow-agent/src/io/report_structure.py`

- Well-designed section templates per detail level
- Auto-fix capability for missing sections
- Citation counting
- Just needs to be consistently activated

---

### OBS-3: RunMetrics Schema Complete
**Status**: ✅ COMPLETE
**File**: `apps/miroflow-agent/src/logging/task_logger.py`

- All new fields present: `search_rounds`, `scrape_count`, `follow_up_searches`, `effective_config`
- Helper methods defined correctly
- Just not called from orchestrator

---

## Impact Assessment by Acceptance Case

| Case | Criteria | Status | Reason |
|------|----------|--------|--------|
| A | ≤2 search rounds, light+compact | ⚠️ PARTIAL | Rounds track, but structure validation off by default |
| B | Min verification rounds, multi-source | ⚠️ PARTIAL | Rounds adjusted, but scrape_count always 0 |
| C | Lead trail present, ≥1 follow-up from lead | ❌ FAIL | LeadTracker not integrated |
| D | effective_config differs, metrics show route | ⚠️ PARTIAL | Config built but not passed to agent |
| E | Compact scannable, detailed full sections | ⚠️ PARTIAL | Structure validation off in default mode |

---

## Recommended Fix Priority

### Phase 1: Critical Wiring (Enables E2E Testing)
1. **Integrate LeadTracker into Orchestrator** (CRITICAL-1)
   - Import LeadTrackingManager
   - Initialize in `__init__` based on config
   - Extract leads from assistant responses each turn
   - Inject follow-up prompts from top leads
   - Append trail section to final report

2. **Wire record_scrape() calls** (CRITICAL-2)
   - Identify all scraping tool calls (jina_reader, browser tools, etc.)
   - Call `self.task_log.run_metrics.record_scrape()` after successful execution

3. **Wire record_follow_up_search() calls** (CRITICAL-3)
   - Identify searches triggered by lead questions
   - Call `self.task_log.run_metrics.record_follow_up_search()`

### Phase 2: Config Flow (Enables Intensity Control)
4. **Pass effective_config to orchestrator** (MAJOR-2)
   - Add `effective_config` param to orchestrator init or runtime
   - Make LeadTracker check `effective_config['research_intensity']` at runtime
   - Log effective_config in RunMetrics

5. **Enable structure validation by default** (MAJOR-1)
   - Change `validate_structure=True` unconditionally or key off `detail_level != "compact"`
   - Remove research_report_mode gate

### Phase 3: Polish (Quality Improvements)
6. **Create real acceptance E2E tests** (MINOR-1)
   - Real queries for A-E
   - Fixture-based or live API calls
   - Validate actual report outputs

7. **Update documentation** (MINOR-2)
   - Mark LeadTracker as "Phase 4 infrastructure ready, integration in progress"
   - Remove "scrape encouragement" claims until implemented

---

## Testing Gaps

Cannot run real E2E tests currently because:
- ❌ No `docker` or `uv` available in environment
- ❌ No API keys configured for live searches
- ✅ Can still audit code and propose fixes
- ✅ Can create acceptance test structure for future runs

**Recommendation**: Fix CRITICAL-1, CRITICAL-2, CRITICAL-3 first, then retry with real acceptance queries.

---

## Next Steps for Round 2

1. Fix CRITICAL-1: Integrate LeadTracker
2. Fix CRITICAL-2: Wire scrape counting
3. Fix CRITICAL-3: Wire follow-up counting
4. Fix MAJOR-2: Pass effective_config
5. Fix MAJOR-1: Enable structure validation
6. Commit fixes
7. Document changes in ACCEPTANCE_RESULTS_ROUND_1.md (noting partial fixes, still need runtime)
8. If environment allows, attempt real acceptance queries

---

## Files Needing Changes

### Must Change (Critical Path):
- `apps/miroflow-agent/src/core/orchestrator.py` (integrate LeadTracker, wire metrics)
- `apps/api-server/services/pipeline_runtime.py` (pass effective_config)

### Should Change (Quality):
- `apps/miroflow-agent/src/core/answer_generator.py` (structure validation default)
- `apps/api-server/tests/test_research_quality_acceptance.py` (add real E2E)

### Documentation Updates:
- `IMPLEMENTATION_SUMMARY.md` (mark integration status accurately)
- `../RESEARCH_INTENSITY.md` (clarify what's implemented vs planned)

---

## Conclusion

The implementation has excellent **infrastructure** (classes, schemas, methods) but **poor wiring**. It's 60% done:
- ✅ Data models complete
- ✅ Config pipeline mostly works
- ✅ Report validation logic solid
- ❌ Orchestrator integration incomplete
- ❌ Metrics recording missing
- ❌ No real E2E validation

**Estimated work**: 4-6 hours of focused integration work to complete critical wiring, then real acceptance testing becomes possible.

