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



def _split_markdown_sections(text: str) -> List[tuple[str, str]]:
    """Split markdown into [(heading_without_hashes_or_empty, body), ...]."""
    if not text:
        return []
    parts = re.split(r"(?m)^(##\s+.+)$", text)
    sections: List[tuple[str, str]] = []
    # parts[0] is preamble before first ##
    if parts and parts[0].strip():
        sections.append(("", parts[0].strip()))
    i = 1
    while i < len(parts):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append((heading, body))
        i += 2
    return sections


def _section_kind(heading: str) -> str:
    h = heading.lower()
    # Prefer explicit direct-answer headings as glance (before broader rules).
    if re.search(r"直接答案|direct\s*answer|答案", h, re.I):
        return "glance"
    if re.search(r"tl;?\s*dr|结论|总览|executive summary|一句话", h, re.I):
        return "glance"
    if re.search(r"冲突|不确定|conflict|uncertaint", h, re.I):
        return "conflict"
    if re.search(r"references|参考文献|来源|引用", h, re.I):
        return "sources"
    if re.search(r"内容分析|content analysis|关系拓扑|relationship|mermaid|拓扑", h, re.I):
        return "analysis"
    if re.search(r"线索|lead trail|pending", h, re.I):
        return "leads"
    if re.search(r"证据|evidence|事实|timeline|时间线", h, re.I):
        return "evidence"
    if re.search(r"conclusion|总结|详述|分析", h, re.I):
        return "detail"
    return "other"


def _guess_confidence(text: str) -> tuple[str, str]:
    """Return (level, label) level in high|mid|low."""
    if re.search(r"(高\s*置信|confidence\s*[:=]?\s*high|\bhigh confidence\b)", text, re.I):
        return "high", "置信度：高"
    if re.search(r"(低\s*置信|confidence\s*[:=]?\s*low|\blow confidence\b)", text, re.I):
        return "low", "置信度：低"
    if re.search(r"(中\s*置信|confidence\s*[:=]?\s*medium|\bmedium confidence\b)", text, re.I):
        return "mid", "置信度：中"
    # heuristic from conflict density
    if re.search(r"冲突|不确定|存疑|未证实|谣言", text):
        return "mid", "置信度：中"
    return "mid", "置信度：中"


def _is_list_item(line: str) -> bool:
    """True for markdown list items; False for bold/italic that starts with *."""
    s = (line or "").strip()
    if not s:
        return False
    if s.startswith("**"):
        return False
    return bool(re.match(r"^([-•]|\*(?!\*)|\d+\.)\s+", s))


def _is_meta_confidence_line(s: str) -> bool:
    """True for confidence badges / HTML confidence markers — never the answer."""
    t = (s or "").strip()
    if not t:
        return False
    if re.match(r"<!--\s*confidence:(?:high|mid|low)\s*-->", t, re.I):
        return True
    if re.match(r"^\*{0,2}置信度\s*[：:]\s*[高中低]\*{0,2}$", t):
        return True
    if re.match(r"^\*{0,2}confidence\s*[:=]\s*(high|mid|medium|low)\*{0,2}$", t, re.I):
        return True
    return False


def _extract_direct_answer(text: str) -> str:
    """Prefer boxed / explicit 答案 lines over first-paragraph heuristics."""
    if not text:
        return ""
    # \boxed{...} or $\boxed{...}$
    m = re.search(r"\\boxed\{([^{}]+)\}", text)
    if m:
        return m.group(1).strip()
    # **答案：...** / 答案：...
    m = re.search(
        r"(?:\*\*)?答案\s*[：:]\s*(.+?)(?:\*\*)?\s*$",
        text,
        re.M,
    )
    if m:
        ans = m.group(1).strip().strip("*").strip()
        if ans and not _is_meta_confidence_line(ans) and not ans.startswith("置信度"):
            return ans
    # leading **...** one-liner that looks like a verdict (skip confidence badges)
    for m in re.finditer(r"^\*\*([^*]{2,120})\*\*\s*$", text, re.M):
        cand = m.group(1).strip()
        if _is_meta_confidence_line(cand) or cand.startswith("置信度"):
            continue
        if re.match(r"^confidence\s*[:=]", cand, re.I):
            continue
        return cand
    return ""


def _first_paragraph(body: str, max_chars: int = 160) -> str:
    direct = _extract_direct_answer(body)
    if direct:
        if len(direct) > max_chars:
            return direct[: max_chars - 1].rstrip() + "…"
        return direct
    lines = []
    heading_fallback = ""
    for line in (body or "").splitlines():
        s = line.strip()
        if not s or s.startswith("```"):
            if lines:
                break
            continue
        if _is_meta_confidence_line(s) or s.startswith("<!--"):
            continue
        if s.startswith("#"):
            if not lines and not heading_fallback:
                heading_fallback = re.sub(r"^#+\s*", "", s).strip()
            if lines:
                break
            continue
        if _is_list_item(s) or s.startswith("|"):
            break
        # unwrap bold wrappers for readability
        s = re.sub(r"^\*\*(.+?)\*\*$", r"\1", s).strip()
        if not s:
            continue
        lines.append(s)
        if sum(len(x) for x in lines) >= max_chars:
            break
    text = " ".join(lines).strip() or heading_fallback
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def _bullet_points(body: str, limit: int = 3) -> List[str]:
    bullets: List[str] = []
    for line in (body or "").splitlines():
        s = line.strip()
        if _is_list_item(s):
            bullets.append(re.sub(r"^([-•]|\*(?!\*)|\d+\.)\s*", "", s))
        if len(bullets) >= limit:
            break
    if bullets:
        return bullets
    # fallback: first short sentences (skip if body is just the direct answer)
    para = _first_paragraph(body, max_chars=240)
    direct = _extract_direct_answer(body)
    if direct and para == direct:
        return []
    if not para:
        return []
    chunks = re.split(r"(?<=[。！？.!?])\s*", para)
    return [c.strip() for c in chunks if c.strip()][:limit]


def reshape_report_for_consumer(text: str, *, detail_level: str = "detailed") -> str:
    """Reorder a research report into glance-first consumer layout.

    Structure:
      1) ## 结论 (short) + confidence hint line
      2) ## 要点 (≤3) when available
      3) ## 争议与不确定 (only if present, short)
      4) ## 证据与来源 (marker for UI to fold)
      5) ## 深入了解 (analysis / topology / long detail) — skipped/minimized for compact
    """
    if not text or not text.strip():
        return text
    level = (detail_level or "detailed").strip().lower()
    if level not in {"compact", "balanced", "detailed"}:
        level = "detailed"

    sections = _split_markdown_sections(text)
    if not sections:
        return text

    glance_bodies: List[str] = []
    conflict_bodies: List[str] = []
    evidence_parts: List[str] = []
    source_parts: List[str] = []
    analysis_parts: List[str] = []
    other_parts: List[str] = []

    for heading, body in sections:
        if not heading:
            # preamble — treat as glance candidate
            if body.strip():
                glance_bodies.append(body.strip())
            continue
        kind = _section_kind(heading)
        block = f"{heading}\n\n{body}".strip()
        if kind == "glance":
            glance_bodies.append(body.strip())
        elif kind == "conflict":
            conflict_bodies.append(body.strip())
        elif kind == "sources":
            source_parts.append(block)
        elif kind == "evidence":
            evidence_parts.append(block)
        elif kind == "analysis":
            analysis_parts.append(block)
        elif kind == "leads":
            if level == "compact":
                continue
            other_parts.append(block)
        elif kind == "detail":
            if level == "compact":
                # keep only a short paragraph for glance if needed
                glance_bodies.append(body.strip())
            else:
                other_parts.append(block)
        else:
            other_parts.append(block)

    glance_text = "\n\n".join(b for b in glance_bodies if b).strip()
    if not glance_text and other_parts:
        # fall back to first other body
        first = other_parts[0]
        glance_text = re.sub(r"^##\s+.+\n+", "", first).strip()

    conf_level, conf_label = _guess_confidence(text)
    if _extract_direct_answer(text) and not re.search(r"冲突|不确定|存疑|未证实|谣言", text):
        # Clear arithmetic / factual one-liners should not stay mid by default
        if conf_level == "mid" and not re.search(
            r"(中\s*置信|confidence\s*[:=]?\s*medium)", text, re.I
        ):
            conf_level, conf_label = "high", "置信度：高"
    if level == "compact":
        answer = _first_paragraph(glance_text, max_chars=140)
        bullets = _bullet_points(glance_text, limit=2)
        conflict_limit = 2
    elif level == "balanced":
        answer = _first_paragraph(glance_text, max_chars=180)
        bullets = _bullet_points(glance_text, limit=3)
        conflict_limit = 3
    else:  # detailed
        answer = _first_paragraph(glance_text, max_chars=280)
        bullets = _bullet_points(glance_text, limit=5)
        conflict_limit = 5

    out: List[str] = []
    out.append("## 结论\n")
    if answer:
        out.append(answer)
    else:
        out.append("暂无法给出明确结论，请展开来源查看原始材料。")
    out.append("")
    out.append(f"<!-- confidence:{conf_level} -->")
    out.append(f"**{conf_label}**")
    out.append("")

    # Drop bullets that merely repeat the one-line conclusion
    bullets = [b for b in bullets if b.strip() and b.strip() != answer.strip()]
    if bullets:
        out.append("## 要点\n")
        for b in bullets:
            out.append(f"- {b}")
        out.append("")

    if conflict_bodies:
        out.append("## 争议与不确定\n")
        # keep at most conflict_limit bullets total
        collected: List[str] = []
        for body in conflict_bodies:
            for b in _bullet_points(body, limit=conflict_limit):
                collected.append(b)
                if len(collected) >= conflict_limit:
                    break
            if len(collected) >= conflict_limit:
                break
        if collected:
            for b in collected:
                out.append(f"- {b}")
        else:
            # short paragraph fallback
            out.append(_first_paragraph(conflict_bodies[0], max_chars=120))
        out.append("")

    # Evidence + sources fold target
    fold_evidence: List[str] = []
    fold_evidence.extend(evidence_parts)
    fold_evidence.extend(source_parts)
    def _demote_headings(block: str) -> str:
        # Keep only one H2 per fold region so Gradio can wrap it cleanly.
        return re.sub(r"(?m)^##\s+", "### ", block)

    if fold_evidence:
        cleaned_bits: List[str] = []
        for block in fold_evidence:
            cleaned = re.sub(
                r"(?m)^##\s*(References|参考文献|来源|引用)\s*$",
                "",
                block,
                count=1,
            ).strip()
            if cleaned:
                cleaned_bits.append(_demote_headings(cleaned))
        if cleaned_bits:
            out.append("## 证据与来源\n")
            out.append("\n\n".join(cleaned_bits))
            out.append("")

    # Deep dive
    deep: List[str] = []
    if level == "balanced":
        deep.extend(analysis_parts)
        # keep other detail shorter in balanced
        for block in other_parts[:2]:
            body = re.sub(r"^##\s+.+", "", block).strip()
            if len(body) > 600:
                body = body[:600].rstrip() + "…"
                # reattach demoted heading if any
                hm = re.match(r"(##\s+.+)", block)
                deep.append((hm.group(1) + "\n\n" + body) if hm else body)
            else:
                deep.append(block)
    elif level == "detailed":
        deep.extend(analysis_parts)
        deep.extend(other_parts)
    if deep:
        deep_bits = [_demote_headings(b) for b in deep if str(b).strip()]
        if deep_bits:
            out.append("## 深入了解\n")
            out.append("\n\n".join(deep_bits))
            out.append("")

    result = "\n".join(out).strip() + "\n"
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


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
    out = reshape_report_for_consumer(out, detail_level=detail_level)
    # collapse excessive blank lines
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"
    return out
