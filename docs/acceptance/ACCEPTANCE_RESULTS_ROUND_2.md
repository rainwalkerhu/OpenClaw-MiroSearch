# Acceptance Results - Round 2 (LIVE E2E)

## Date: 2026-09-20

## Summary
First LIVE end-to-end execution of acceptance tests A-C using glm-5.3-flash model. Tests completed successfully and produced valid research outputs, demonstrating the agent's core functionality. However, discovered critical metrics recording failure that prevents validation of research quality improvements.

---

## Test Environment

### Execution Mode
- **Direct Pipeline**: Ran miroflow-agent directly via Hydra CLI
- **Bypassed**: API server, Redis/Valkey queue (not needed for local testing)
- **LLM**: glm-5.3-flash (Zhipu BigModel API)
- **Cost**: ~$0.38 for all tests

### Limitations
- ❌ No search API keys (SERPER/SERPAPI/SEARXNG)
- ❌ No E2B sandbox API key (but not required for these tests)
- ✅ Scraping worked via Trafilatura
- ✅ LLM API functional

---

## Case A: Simple Fact (Light + Compact)

### Configuration
```json
{
  "query": "What is the capital of France?",
  "research_intensity": "light",
  "output_detail_level": "compact",
  "max_turns": 5
}
```

### Execution
- **Status**: ✅ completed
- **Duration**: 7.5 seconds
- **Turns**: 1
- **Tool Calls**: 0 (answered from knowledge)

### Final Output
```
============================== Final Answer ==============================
\boxed{Paris}

-------------------- Extracted Result --------------------
Paris

-------------------- Token Usage --------------------
Total Input Tokens: 8070
Total Cache Input Tokens: 0
Total Output Tokens: 43
```

### Observed Metrics (from task log)
```json
{
  "search_rounds": 0,
  "scrape_count": 0,
  "follow_up_searches": 0,
  "effective_config": {}
}
```

### Evaluation

**Pass Criteria**:
- ✅ Completed in ≤2 turns (1 turn)
- ✅ Provided clear, correct answer
- ✅ Compact output (43 tokens)
- ⚠️ Cannot verify metrics (no tools used)
- ❌ effective_config empty

**Overall**: ✅ **PASS** (requirements met despite missing metrics)

---

## Case B: Contested Numeric (Verified + Deep + Detailed)

### Configuration
```json
{
  "query": "What were the global CO2 emissions in 2023?",
  "research_intensity": "deep",
  "research_mode": "verified",
  "output_detail_level": "detailed",
  "verification_min_search_rounds": 3,
  "max_turns": 10
}
```

### Execution
- **Status**: ✅ completed
- **Duration**: 74.7 seconds (1.2 minutes)
- **Turns**: 4
- **Tool Calls**: 6 total
  - 4× `google_search` failed (no API keys) + rollbacks
  - 1× `google_search` succeeded with empty results
  - 2× `scrape_url` succeeded ✅

### Scraping Activity
**Scrape 1**: https://www.iea.org/reports/co2-emissions-in-2023
- Duration: 1.9 seconds
- Content: 1,282 chars (table of contents)
- Success: ✅

**Scrape 2**: https://www.iea.org/reports/co2-emissions-in-2023/executive-summary  
- Duration: 1.6 seconds
- Content: 2,446 chars (full executive summary with data)
- Success: ✅

### Final Output

```
============================== Final Answer ==============================
## TL;DR

The conversation established, via the IEA's "CO2 Emissions in 2023" report, that global energy-related CO2 emissions reached a record high of 37.4 billion tonnes in 2023.

The conversation established, via the IEA's "CO2 Emissions in 2023" report, that global energy-related CO2 emissions reached a record high of 37.4 billion tonnes in 2023.

\boxed{37.4\ \text{Gt}}

## Conclusion

The conversation established, via the IEA's "CO2 Emissions in 2023" report, that global energy-related CO2 emissions reached a record high of 37.4 billion tonnes in 2023.

-------------------- Extracted Result --------------------
37.4\ \text{Gt}

-------------------- Token Usage --------------------
Total Input Tokens: 46541
Total Cache Input Tokens: 0
Total Output Tokens: 1106
```

### Observed Metrics (from task log)
```json
{
  "search_rounds": 0,     ❌ WRONG (should be ≥1)
  "scrape_count": 0,      ❌ WRONG (actually scraped 2 URLs)
  "follow_up_searches": 0,
  "effective_config": {}  ❌ WRONG
}
```

### Actual Tool Execution (from logs)
```
Turn 1:
- Attempt google_search → FAIL (no API key)
- Rollback, retry → FAIL
- Rollback, retry → FAIL
- Rollback, retry → FAIL
- Allow duplicate after 4 rollbacks → SUCCESS (empty results)

Turn 2:
- scrape_url(https://www.iea.org/reports/co2-emissions-in-2023) → SUCCESS ✅
  Result: Found report overview

Turn 3:
- scrape_url(https://www.iea.org/reports/co2-emissions-in-2023/executive-summary) → SUCCESS ✅
  Result: Found "37.4 billion tonnes (Gt)"

Turn 4:
- LLM synthesizes answer from scraped data
```

### Evaluation

**Pass Criteria**:
- ✅ Found authoritative source (IEA official report)
- ✅ Extracted correct numeric answer (37.4 Gt)
- ✅ Multi-source verification approach (scraped 2 pages)
- ✅ Answer cites data source explicitly
- ❌ **CRITICAL**: Metrics not recorded (scrape_count=0 despite 2 scrapes)
- ❌ Report structure incomplete (missing Evidence, References sections for detailed mode)
- ❌ Duplicate content in TL;DR/Conclusion sections

**Overall**: ⚠️ **PARTIAL PASS**  
- Answer quality: ✅ Excellent
- Metrics validation: ❌ Failed
- Structure compliance: ❌ Failed

---

## Case C: Chained Research (Deep + Lead Tracking)

### Configuration
```json
{
  "query": "How did the discovery of DNA structure lead to CRISPR technology?",
  "research_intensity": "deep",
  "enable_lead_tracking": true,
  "max_lead_follow_ups": 2,
  "output_detail_level": "balanced",
  "max_turns": 10
}
```

### Execution
- **Status**: ✅ completed
- **Duration**: 134 seconds (2.2 minutes)
- **Turns**: 2
- **Tool Calls**: 6 total
  - 4× `google_search` failed + rollbacks
  - 2× `google_search` succeeded with empty results

### Final Output (truncated)

```
============================== Final Answer ==============================
## TL;DR

\boxed{\text{The 1953 discovery of the DNA double helix revealed that genetic information is stored in base sequences recognized by complementary base pairing (A-T, G-C). This insight enabled the tools of molecular biology — restriction enzymes, recombinant DNA, Sanger sequencing, PCR, and genome sequencing — which allowed scientists to discover CRISPR repeats in bacterial genomes (1987) and identify them as a bacterial adaptive immune system (2005-2007). CRISPR editing is itself programmable because of base pairing: a guide RNA targets a chosen DNA sequence by Watson-Crick complementarity, directing Cas9 to cut there (Doudna and Charpentier, 2012; Nobel Prize 2020)}}

## Conclusion

[Same detailed explanation repeated...]

-------------------- Extracted Result --------------------
\text{The 1953 discovery of the DNA double helix revealed that genetic information is stored in base sequences recognized by complementary base pairing (A-T, G-C). This insight enabled the tools of molecular biology — restriction enzymes, recombinant DNA, Sanger sequencing, PCR, and genome sequencing — which allowed scientists to discover CRISPR repeats in bacterial genomes (1987) and identify them as a bacterial adaptive immune system (2005-2007). CRISPR editing is itself programmable because of base pairing: a guide RNA targets a chosen DNA sequence by Watson-Crick complementarity, directing Cas9 to cut there (Doudna and Charpentier, 2012; Nobel Prize 2020)}

-------------------- Token Usage --------------------
Total Input Tokens: 35224
Total Cache Input Tokens: 0
Total Output Tokens: 4822
```

### Observed Metrics (from task log)
```json
{
  "search_rounds": 0,        ❌ WRONG
  "scrape_count": 0,
  "follow_up_searches": 0,   ❌ WRONG (no leads extracted/followed)
  "effective_config": {}     ❌ WRONG
}
```

### Missing: Lead Trail Section

**Expected** (from Case C requirements):
```markdown
## 线索追踪 / Lead Trail

### Lead 1: [question extracted from agent reasoning]
**来源**: assistant_response (Turn X)
**优先级**: 1.00
**追踪轮次**: Turn Y
**发现**: [findings from follow-up search]
```

**Actual**: ❌ **No lead trail section present**

### Evaluation

**Pass Criteria**:
- ✅ Comprehensive, accurate answer content
- ✅ Cites specific discoveries (1953, 1987, 2005-2007, 2012)
- ✅ Explains causal pathway clearly
- ❌ **CRITICAL**: No lead trail section (required for Case C)
- ❌ **CRITICAL**: follow_up_searches = 0 (no leads extracted or followed)
- ❌ Lead tracking feature did not activate despite config

**Overall**: ❌ **FAIL**  
- Answer quality: ✅ Excellent
- Lead tracking functionality: ❌ Not working
- Metrics validation: ❌ Failed

**Root Cause**: Lead extraction may not be triggering on English-language agent responses, or lead tracking initialization is failing silently.

---

## Summary by Case

| Case | Config | Answer Quality | Metrics | Structure | Lead Trail | Overall |
|------|--------|----------------|---------|-----------|------------|---------|
| A | light+compact | ✅ Correct | ⚠️ N/A (no tools) | ✅ Simple | N/A | ✅ PASS |
| B | deep+detailed | ✅ Excellent | ❌ Not recorded | ❌ Incomplete | N/A | ⚠️ PARTIAL |
| C | deep+balanced+leads | ✅ Excellent | ❌ Not recorded | ✅ OK | ❌ Missing | ❌ FAIL |

---

## Key Findings

### ✅ Positive Outcomes

1. **LLM Integration Works**: glm-5.3-flash successfully handles research queries
2. **Scraping Works**: Trafilatura successfully extracted content from IEA website
3. **Intelligent Fallback**: Agent adapted to missing search APIs by scraping known sources directly
4. **Answer Quality**: All three answers were factually correct and well-explained
5. **Structure Basics**: TL;DR and Conclusion sections present
6. **Cost Effective**: $0.38 for 3 research tasks is very reasonable

### ❌ Critical Issues

1. **Metrics Recording Failure**: All metrics remain at 0 despite actual tool usage
   - Root Cause: `scrape_url` not in `SCRAPE_TOOL_NAMES` set
   - Impact: Cannot validate research quality improvements

2. **Lead Tracking Not Functioning**: Case C failed to extract/follow leads
   - Root Cause: Unknown (requires investigation)
   - Impact: Cannot demonstrate chained research capability

3. **effective_config Empty**: Configuration metadata not populated
   - Root Cause: Expected when bypassing API server
   - Impact: Cannot verify intensity-driven behavior

4. **Structure Validation Weak**: Detailed mode missing required sections
   - Root Cause: Auto-fix may be too lenient
   - Impact: Reports don't meet quality standards

---

## Detailed Metric Analysis

### Expected vs Actual Metrics

**Case B (Contested Numeric)**:

| Metric | Expected | Actual | Gap |
|--------|----------|--------|-----|
| search_rounds | ≥3 (verified mode) | 0 | -3 |
| scrape_count | 2 (IEA pages) | 0 | -2 |
| follow_up_searches | 0 (no leads mode) | 0 | ✅ |
| effective_config | `{intensity: "deep", ...}` | `{}` | Missing |

**Case C (Chained Research)**:

| Metric | Expected | Actual | Gap |
|--------|----------|--------|-----|
| search_rounds | ≥1 | 0 | -1 |
| scrape_count | 0 (used knowledge) | 0 | ✅ |
| follow_up_searches | ≥1 (lead-driven) | 0 | -1 |
| effective_config | `{intensity: "deep", ...}` | `{}` | Missing |

---

## Report Structure Compliance

### Case B: Expected vs Actual (detailed mode)

**Required Sections** (from ReportStructureValidator):
- ✅ TL;DR (min 30 chars)
- ✅ Conclusion (min 150 chars)
- ❌ Evidence (min 200 chars) - **MISSING**
- ❌ References (min 50 chars) - **MISSING**

**Quality Issues**:
- Duplicate content in TL;DR/Conclusion
- No citations section despite scraping authoritative sources

### Case C: Expected vs Actual (balanced mode)

**Required Sections**:
- ✅ TL;DR (min 30 chars)
- ✅ Conclusion (min 100 chars)
- ❌ Lead Trail - **MISSING** (critical for Case C)

---

## Token Usage Breakdown

| Case | Agent Type | Input | Output | Reasoning* |
|------|-----------|--------|--------|-----------|
| A | main | 4,991 | 36 | ~15% |
| A | final_summary | 8,070 | 43 | N/A |
| B | main (8 calls) | 195,546 | 3,424 | ~35% |
| B | final_summary | 46,541 | 1,106 | ~25% |
| C | main (6 calls) | 135,732 | 9,525 | ~40% |
| C | final_summary | 35,224 | 4,822 | ~30% |

*Reasoning token % estimated based on glm-5.3-flash's thinking model characteristics

**Observations**:
- Case C had highest reasoning usage (complex causal question)
- Case A was very efficient (simple fact)
- Flash model's reasoning overhead reasonable for research tasks

---

## Comparison: Acceptance Tests vs Actual Behavior

### Case A (Light + Compact)
- **Goal**: Fast, simple answer
- **Actual**: ✅ 1 turn, 7.5 seconds, correct answer
- **Match**: ✅ Perfect alignment

### Case B (Deep + Detailed)
- **Goal**: Multi-source, verified, detailed report
- **Actual**: ⚠️ Multi-page scraping ✅, detailed report ❌ (missing sections)
- **Match**: ⚠️ Partial (answer good, structure incomplete)

### Case C (Chained Research + Lead Tracking)
- **Goal**: Follow leads, show research trail
- **Actual**: ❌ No leads extracted, no trail section
- **Match**: ❌ Core feature not working

---

## Next Actions (Round 3)

### 1. Fix Metrics Recording (5 minutes)
```python
# orchestrator.py, line ~60
SCRAPE_TOOL_NAMES = {
    ...,
    "scrape_url",  # ← ADD THIS
    "scrape_and_extract_info",  # ← AND THIS
}
```

### 2. Debug Lead Tracking (30 minutes)
- Add logging to LeadTrackingManager.initialize()
- Add logging to process_turn_response()
- Test with English responses
- Verify regex patterns match agent output format

### 3. Re-run Tests (10 minutes)
- Re-run Cases A, B, C with fixes
- Verify metrics populate correctly
- Capture real metric values for comparison

### 4. If Tests Pass, Continue to D & E (30 minutes)
- Case D: Same query, different search profiles
- Case E: Same query, different detail levels

---

## Confidence Assessment

### What We Know Works ✅
- LLM API integration (100%)
- Tool execution (scraping: 100%)
- Answer generation (100%)
- Basic report structure (80%)

### What Needs Fixing ❌
- Metrics recording (95% confidence in fix)
- Lead tracking (60% confidence - needs investigation)
- Structure validation enforcement (70% confidence)

### Overall Round 2 Success Rate
- **Technical Execution**: 90% (LLM + tools working)
- **Validation Capability**: 30% (metrics broken)
- **Feature Completeness**: 60% (lead tracking not working)

---

## Estimated Time to Full Pass

| Task | Est. Time | Confidence |
|------|-----------|------------|
| Fix scrape_url metrics | 5 min | 95% |
| Re-run A, B, C | 5 min | 95% |
| Debug lead tracking | 30 min | 60% |
| Fix structure validation | 20 min | 70% |
| Run Cases D & E | 20 min | 80% |
| Document Round 3 | 20 min | 100% |
| **Total** | **~100 min** | **~75%** |

---

## Conclusion

Round 2 successfully demonstrated **end-to-end execution** with live LLM and tools. The agent produced valid, accurate research outputs and showed intelligent adaptation to constraints.

However, the **critical metrics recording failure** prevents validation of the research quality improvements that Round 1 code claimed to implement. The root cause is a simple oversight (missing tool name in a set), but it blocks acceptance criteria verification.

**Recommendation**: Apply the trivial metrics fix, debug lead tracking, re-run tests, and proceed to Cases D & E only if metrics validate correctly.

---

## Appendix: Raw Task Logs

Task logs saved to:
- `/workspace/logs/debug/task_acceptance_a_2026-09-20-10-53-34.json`
- `/workspace/logs/debug/task_acceptance_b_2026-09-20-10-53-42.json`
- `/workspace/logs/debug/task_acceptance_c_2026-09-20-10-54-56.json`

Full results JSON:
- `artifacts/round2/acceptance_results_round2.json`
