"""Tests for user-facing report presentation cleanup."""

from src.io.report_presentation import (
    compact_pending_lead_trail,
    drop_incomplete_reference_lines,
    ensure_content_analysis_and_topology,
    prepare_user_facing_report,
    strip_diagnostic_noise,
)


MESSY = """
============================== Final Answer ==============================
## TL;DR / 结论（标明置信度）

双方说法冲突；置信度：中。

## Conclusions

综合公开报道，袭击是否造成实质破坏仍有争议，需要更多来源交叉核验。

## 冲突与不确定 / Conflicts & Uncertainties

- 甲方宣称命中能源设施并引发火灾。
- 乙方称拦截成功、设施运转正常。
- 伤亡数字各方不一，尚无独立核实。

## Evidence

据路透社报道 [1]。

## References

1. https://example.com/reuters-2026-09-18
2. https://www

--------------------- Extracted Result ---------------------
boxed text

--------------------- Token Usage & Cost ---------------------
Total Input Tokens: 123
Pricing is disabled - no cost information available
-----------------------------------------------------

## 线索追踪 / Lead Trail

### Lead 1: What are the most important unresolved aspects of the attack?
**来源**: query_seed (Turn 0)
**优先级**: 0.65
**状态**: pending
"""


def test_strip_diagnostic_noise_removes_token_blocks():
    cleaned = strip_diagnostic_noise(MESSY)
    assert "Token Usage" not in cleaned
    assert "Pricing is disabled" not in cleaned
    assert "Extracted Result" not in cleaned
    assert "TL;DR" in cleaned


def test_drop_incomplete_reference_lines():
    text = "## References\n\n1. https://example.com/ok\n2. https://www\n"
    out = drop_incomplete_reference_lines(text)
    assert "example.com/ok" in out
    assert "https://www\n" not in out + "\n" or out.strip().endswith("ok")


def test_compact_pending_only_trail():
    trail = """## body

## 线索追踪 / Lead Trail

### Lead 1: Long English seed question about unresolved conflicts?
**来源**: query_seed (Turn 0)
**优先级**: 0.65
**状态**: pending
"""
    out = compact_pending_lead_trail(trail)
    assert "未跟进" in out
    assert "**状态**: pending" not in out


def test_topology_added_when_conflicts_present():
    body = """## TL;DR

结论足够长用于测试。

## 冲突与不确定 / Conflicts & Uncertainties

- 甲方宣称命中。
- 乙方称拦截成功。

## References

1. https://example.com/a
"""
    out = ensure_content_analysis_and_topology(body, detail_level="detailed")
    assert "内容分析" in out
    assert "```mermaid" in out
    assert "flowchart" in out


def test_prepare_user_facing_report_end_to_end():
    out = prepare_user_facing_report(MESSY, detail_level="detailed")
    assert "Token Usage" not in out
    assert "Pricing is disabled" not in out
    assert "https://www\n" not in out
    assert "未跟进" in out
    assert "内容分析" in out
    assert "```mermaid" in out
    assert out.strip().endswith((".", "。", "`", "进", "）", ")")) or "未跟进" in out
