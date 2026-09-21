# Live Acceptance Results — Layout L Cases

- **Date:** 2026-09-21 (UTC+8)
- **Commit:** `e3069d6dc86ea4c31b77c8eba29eb603492a7792`
- **Run:** `L1,L2,L3` with round6 credentials (secrets not included)

## Results

| Case | Topic | Verdict | Wall time | 内容分析 | Mermaid | No Token Usage noise | No truncated `https://www` | Pending folded as `未跟进` | Failures
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| L1 | Celebrity gossip | **PASS** | 333.2s | yes | yes | yes | yes | yes | none
| L2 | Public opinion | **FAIL** | 252.4s | no | no | yes | yes | yes | `missing_tldr`, `missing_conclusion`, `missing_conflicts`, `missing_timeline`, `missing_evidence`, `missing_confirmed`, `missing_conflicts_section`, `missing_confidence_marker`, `missing_content_analysis`, `missing_mermaid_topology`, `no_source_attribution`
| L3 | Tech rumor | **PASS** | 432.1s | yes | yes | yes | yes | yes | none

### L1 — PASS

Completed with a structured celebrity-gossip report, confidence markers, conflict analysis, content analysis, and Mermaid topology. The report contains no Token Usage noise or truncated `https://www` URL; the pending seed is explicitly folded into the `未跟进` lead-trail section.

### L2 — FAIL

The live case ran to completion but produced no usable report: final-summary generation exhausted retries after upstream rate limits/timeouts. It has only the lead trail, so required report sections, 内容分析, Mermaid topology, and source attribution are absent; pending is still folded as `未跟进`.

### L3 — PASS

Completed with the requested tech-rumor report, confidence markers, conflict analysis, content analysis, and Mermaid topology. The report contains no Token Usage noise or truncated `https://www` URL; the pending seed is explicitly folded into the `未跟进` lead-trail section.

## Overall verdict

**PARTIAL** — all three cases executed to completion, but L2 failed its report-quality gates. The main blocker was LLM/API instability: L2 recorded 2 rate-limit (429) events and 2 timeouts; L1 and L3 also encountered retries (L1: 2 timeouts; L3: 9 rate-limit events and 2 timeouts) but recovered and passed.

Artifacts: `docs/acceptance/artifacts/layout_live_L/acceptance_results.json` and per-case summaries in the same directory.
