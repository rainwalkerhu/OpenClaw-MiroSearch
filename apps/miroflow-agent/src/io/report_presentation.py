"""User-facing report presentation: strip diagnostics, fix refs, compact leads, optional topology."""

from __future__ import annotations

import re
from typing import List, Optional

# Final Answer header only — keep the body text that follows.
_FINAL_ANSWER_HEADER_RE = re.compile(
    r"(?m)^\s*={5,}\s*Final Answer\s*={5,}\s*\n?"
)
# Truncate from Extracted Result / Token Usage section headers through EOF
# (those sections duplicate or are CLI/billing noise).
_DIAGNOSTIC_TAIL_RE = re.compile(
    r"\n?[=\-]{5,}\s*(?:Extracted Result|Token Usage(?:\s*&\s*Cost)?)\s*[=\-]{5,}.*\Z",
    re.DOTALL,
)
_PRICING_NOISE_RE = re.compile(
    r"(?ms)"
    r"(?:^|\n)-{5,}.*?\b(?:Pricing is disabled|Total Input Tokens)\b.*"
)
_EXTRACTED_NOTE_RE = re.compile(
    r"(?m)^\(Note: model did not use "
    + re.escape(r"\boxed{}")
    + r" format;.*$\n?"
)
_INCOMPLETE_URL_RE = re.compile(
    r"(?i)https?://(?:www\.)?(?:[a-z0-9\-]+\.)*[a-z]{0,3}/?[^\s\]\)\>\"']*$"
)
_BARE_INCOMPLETE_REF_LINE_RE = re.compile(
    r"(?m)^(?:\d+\.\s*)?(?:https?://(?:www\.)?)$"
)
_PENDING_LEAD_BLOCK_RE = re.compile(
    r"(?ms)^### Lead \d+:.*?(?=^### Lead |\Z)"
)


def strip_diagnostic_noise(text: str) -> str:
    """Remove CLI/eval diagnostic wrappers from a final summary.

    Keeps the Final Answer *body* (the actual report). Only strips the
    ``===== Final Answer =====`` banner, then truncates from
    Extracted Result / Token Usage tails (duplicates + billing noise).
    """
    if not text:
        return text
    cleaned = _FINAL_ANSWER_HEADER_RE.sub("", text, count=1)
    cleaned = _DIAGNOSTIC_TAIL_RE.sub("", cleaned)
    cleaned = _PRICING_NOISE_RE.sub("\n", cleaned)
    cleaned = _EXTRACTED_NOTE_RE.sub("", cleaned)
    # Leftover bare headers if tail regex missed a variant
    cleaned = re.sub(
        r"(?m)^\s*={5,}\s*Final Answer\s*={5,}\s*$", "", cleaned
    )
    cleaned = re.sub(
        r"(?m)^\s*-{5,}\s*Extracted Result\s*-{5,}\s*$", "", cleaned
    )
    return cleaned.strip() + ("\n" if cleaned.strip() else "")


def drop_incomplete_reference_lines(text: str) -> str:
    """Drop reference lines that clearly truncated mid-URL."""
    if not text:
        return text
    lines = text.splitlines()
    kept: List[str] = []
    for line in lines:
        stripped = line.strip()
        # dangling "https://www" / "http://a." style stubs
        if re.search(r"https?://\S+$", stripped):
            url = re.search(r"https?://\S+$", stripped)
            u = url.group(0) if url else ""
            # incomplete if host missing TLD or ends with bare www.
            if re.fullmatch(r"https?://(?:www\.)?", u) or re.fullmatch(
                r"https?://[\w\-]+", u
            ):
                continue
            if u.rstrip("/").count(".") == 0 and "://" in u:
                continue
        if _BARE_INCOMPLETE_REF_LINE_RE.match(stripped):
            continue
        kept.append(line)
    # Also trim a trailing incomplete URL glued to Chinese text (seen in R8)
    out = "\n".join(kept)
    out = re.sub(r"(https?://www)$", r"\1（链接不完整，已省略）", out)
    out = re.sub(r"https?://www\s*$", "", out, flags=re.M)
    return out


def compact_pending_lead_trail(text: str) -> str:
    """Rewrite pending-only lead trails into a short Chinese summary."""
    if not text:
        return text
    if "线索追踪" not in text and "Lead Trail" not in text:
        return text

    parts = re.split(r"(?m)(?=^##\s*(?:线索追踪|Lead Trail))", text, maxsplit=1)
    if len(parts) < 2:
        return text
    head, trail = parts[0], parts[1]

    pending = list(
        re.finditer(
            r"(?ms)^### Lead \d+:\s*(.+?)$.*?^\*\*状态\*\*:\s*pending\s*$",
            trail,
        )
    )
    followed = list(
        re.finditer(
            r"(?ms)^### Lead \d+:\s*(.+?)$.*?^\*\*状态\*\*:\s*followed\s*$",
            trail,
        )
    )

    # If there are followed leads, keep followed detail and compact pending
    if followed:
        # rebuild: keep followed blocks, summarize pending
        followed_blocks = []
        for m in re.finditer(
            r"(?ms)^### Lead \d+:.*?^\*\*状态\*\*:\s*followed\s*(?:\n\*\*追踪轮次\*\*:.*$)?(?:\n\n\*\*发现\*\*:.*?)?(?=\n### Lead |\Z)",
            trail,
        ):
            followed_blocks.append(m.group(0).strip())
        lines = ["## 线索追踪 / Lead Trail\n", "以下是已跟进线索；未跟进项已折叠。\n"]
        for b in followed_blocks:
            lines.append(b)
            lines.append("")
        if pending:
            lines.append("### 未跟进线索（摘要）")
            for i, m in enumerate(pending, 1):
                q = m.group(1).strip()
                if len(q) > 80:
                    q = q[:77] + "…"
                lines.append(f"{i}. {q} — **未跟进**")
            lines.append("")
        return head.rstrip() + "\n\n" + "\n".join(lines).rstrip() + "\n"

    # pending-only: replace whole trail
    if pending:
        lines = [
            "## 线索追踪 / Lead Trail\n",
            "本轮未实际跟进额外线索（种子线索仍为 pending，不视为报告未写完）。\n",
            "### 未跟进线索（摘要）",
        ]
        for i, m in enumerate(pending, 1):
            q = m.group(1).strip()
            if len(q) > 80:
                q = q[:77] + "…"
            lines.append(f"{i}. {q} — **未跟进**")
        lines.append("")
        return head.rstrip() + "\n\n" + "\n".join(lines).rstrip() + "\n"

    return text


def _extract_conflict_bullets(text: str, limit: int = 4) -> List[str]:
    m = re.search(
        r"(?ims)^##[^\n]*(?:冲突|Conflicts)[^\n]*\n(.*?)(?=^##\s|\Z)",
        text,
    )
    if not m:
        return []
    bullets = []
    for line in m.group(1).splitlines():
        s = line.strip()
        if s.startswith(("-", "*", "•")):
            bullets.append(re.sub(r"^[-*•]\s*", "", s))
        if len(bullets) >= limit:
            break
    return bullets


def ensure_content_analysis_and_topology(
    text: str, *, detail_level: str = "detailed"
) -> str:
    """Append Content Analysis + Mermaid topology when conflicts exist and sections missing."""
    if not text or detail_level == "compact":
        return text
    lower = text.lower()
    has_analysis = (
        "内容分析" in text
        or "content analysis" in lower
        or re.search(r"(?im)^##\s*内容分析", text) is not None
    )
    has_topo = (
        "关系拓扑" in text
        or "relationship map" in lower
        or "```mermaid" in text
    )
    bullets = _extract_conflict_bullets(text)
    extras: List[str] = []

    if not has_analysis and bullets:
        extras.append("## 内容分析 / Content Analysis\n")
        extras.append(
            "围绕争议点拆解：各方主张、可核对证据、仍不确定处。"
            "下表为冲突要点摘要（由结构后处理生成，需结合正文证据阅读）。\n"
        )
        for i, b in enumerate(bullets, 1):
            extras.append(f"{i}. {b}")
        extras.append("")

    if not has_topo and bullets:
        # Build a small mermaid graph; sanitize node labels
        def nid(i: int) -> str:
            return f"C{i}"

        def lab(s: str) -> str:
            s = re.sub(r"[\"\[\]]", "", s)
            s = s.replace("\n", " ")
            return (s[:36] + "…") if len(s) > 36 else s

        extras.append("## 关系拓扑 / Relationship Map\n")
        extras.append("```mermaid")
        extras.append("flowchart TB")
        extras.append('  Q["议题争议"]')
        for i, b in enumerate(bullets, 1):
            extras.append(f'  {nid(i)}["{lab(b)}"]')
            extras.append(f"  Q --> {nid(i)}")
        extras.append('  G["证据缺口 / 待核实"]')
        if bullets:
            extras.append(f"  {nid(1)} -.-> G")
        extras.append("```")
        extras.append("")

    if not extras:
        return text
    # Insert before References / Lead Trail if present
    insert_at = None
    for marker in (
        r"(?im)^##\s*References\b",
        r"(?im)^##\s*参考文献\b",
        r"(?im)^##\s*线索追踪\b",
        r"(?im)^##\s*Lead Trail\b",
    ):
        m = re.search(marker, text)
        if m:
            insert_at = m.start()
            break
    block = "\n".join(extras).rstrip() + "\n\n"
    if insert_at is None:
        return text.rstrip() + "\n\n" + block
    return text[:insert_at].rstrip() + "\n\n" + block + text[insert_at:].lstrip()



def strip_duplicate_trailing_conclusion(text: str) -> str:
    """Remove a second Conclusion/结论 block that appears after References.

    Live Gradio runs sometimes append another ## Conclusion that mostly
    repeats the citation list (and may truncate the last URL). Keep the
    first conclusion body; drop trailing duplicates after References.
    """
    if not text:
        return text
    # Find References / 参考文献 heading
    ref_m = re.search(r"(?im)^##\s*(References|参考文献)\b.*$", text)
    if not ref_m:
        return text
    after = text[ref_m.end():]
    # Any Conclusion after References is treated as duplicate trailer
    dup = re.search(r"(?im)^##\s*(Conclusion|结论|总结)\b.*$", after)
    if not dup:
        return text
    # Keep References section up to (not including) the duplicate conclusion
    kept = text[: ref_m.end() + dup.start()].rstrip() + "\n"
    return kept



def renumber_citations(text: str) -> str:
    """Compact citation numbers to 1..N by first-appearance order.

    Keeps links usable when the model skips ids (e.g. missing [4]/[8]).
    Rewrites both body markers like [3] and matching References list markers.
    """
    if not text:
        return text
    # Collect ids in order of first appearance (body + refs)
    found: list[int] = []
    seen: set[int] = set()
    for m in re.finditer(r"\[(\d+)\]", text):
        n = int(m.group(1))
        if n not in seen:
            seen.add(n)
            found.append(n)
    if not found or found == list(range(1, len(found) + 1)):
        return text
    mapping = {old: i for i, old in enumerate(found, 1)}

    def _sub(m: re.Match[str]) -> str:
        old = int(m.group(1))
        return f"[{mapping.get(old, old)}]"

    return re.sub(r"\[(\d+)\]", _sub, text)


def prepare_user_facing_report(
    text: str, *, detail_level: str = "detailed"
) -> str:
    """Pipeline for Gradio/export/acceptance human-readable final report."""
    if not text:
        return text
    out = strip_diagnostic_noise(text)
    out = drop_incomplete_reference_lines(out)
    out = compact_pending_lead_trail(out)
    out = ensure_content_analysis_and_topology(out, detail_level=detail_level)
    out = strip_duplicate_trailing_conclusion(out)
    out = renumber_citations(out)
    # collapse excessive blank lines
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"
    return out
