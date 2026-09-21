# Acceptance Results — Round 5 (LIVE hotspot cross-verification)

## Date: 2026-09-20

## Summary

Round 5 stresses **multi-source conflict, attribution, timelines, and contested numbers** — not textbook Paris/Tokyo facts. Product LLM stayed **glm-5.3-flash** throughout.

| Case | Theme | Config | Verdict | Notes |
|------|-------|--------|---------|-------|
| H1 | 智谱 ZCode 静默上传 | deep + verified + detailed | **PASS** | Conflicts / Timeline / Evidence / Confirmed present; Serper live |
| H2 | 韩国 Re2O「尸皮针」 | deep + detailed | **PASS** | Conflicts present; Evidence matched via `临床证据` heading; named sources |
| H3 | 胡塞 vs 沙特袭击说法 | deep + verified + detailed | **FAIL** | Strong Conflicts section, but **missing dedicated Evidence heading** |
| H4 | Same as H1 | light + compact | **PASS** | Much shorter (2937 vs 6229 chars; 58s vs 446s); hedges uncertainty |
| H5A | Same as H3 | searxng-only | **PASS** | `search_provider_hits={searxng:6}`, `search_rounds=0` (unreachable) |
| H5B | Same as H3 | parallel-trusted | **PASS** | `search_provider_hits={serper:4}`, `search_rounds=4` |

**Overall Round 5: PARTIAL** — Conflicts hard-gate works on live hotspot queries; H3 fails the Evidence section gate (honest, not waved).

Raw artifacts: [`artifacts/round5/`](./artifacts/round5/).

---

## Environment

| Item | Value |
|------|-------|
| Harness | `apps/miroflow-agent/scripts/run_acceptance_live.py --cases H` |
| LLM | glm-5.3-flash @ Zhipu OpenAI-compatible Chat Completions |
| Serper | Live OK |
| SearXNG `127.0.0.1:27080` | Unreachable (no docker) — H5A documented honestly |
| Credentials | Uploaded Round-5 JSON (never committed) |

---

## Code changes that enabled the Conflicts gate

1. `ReportStructureValidator` now **requires** Conflicts / Timeline / Confirmed for `detailed`
2. Answer-generator prompts mandate those headings + confidence
3. Pipeline syncs `output_detail_level` / `research_report_mode` from `effective_config`
4. Live harness adds H1–H5 + gate evaluation

See `VERIFY_ROUND_5.md`.

---

## H1 — ZCode (PASS)

**Query:** 智谱 ZCode 被指静默上传代码仓库：上传了哪些内容？是否跨境？官方如何回应？各方说法有何冲突？

| Metric | Value |
|--------|-------|
| duration | 446.4s |
| summary_chars | 6229 |
| search_provider_hits | `{serper: 5}` |
| search_rounds | 5 |
| scrape_count | 11 |
| gates | PASS |
| sections found | tldr, conclusion, conflicts, timeline, evidence, confirmed, references |

### Conflicts excerpt (real)

```text
## 冲突与不确定 / Conflicts & Uncertainties

**1. 上传范围之争（官方 vs 逆向证据）——直接冲突**
- 官方口径：仅“云端生成 Wiki 页面时可能触发上传仓库数据”…
- 博主审计口径（3.12.3）：全工作区快照，约 87% 体积为 `.git`；
  `captureBeforePrompt` 在每次用户提问之前都会触发上传…

**2. 用户可控性之争（开关是否有效）——直接冲突**
- 博主证据：关闭“优化体验”和“仓库快照索引”后仍会打包直传 OSS…

**5. 是否跨境——无法核实**
- 已确认上传目标是阿里云 OSS；官方对存储地理位置只字未提。
- 结论：跨境与否暂无法下结论。
```

Surfaces: default-on vs awareness; snippets vs full repo/git/secrets; China vs Singapore entity claims; fix/opensource/audit promises — with explicit unresolved gaps.

---

## H2 — Re2O (PASS)

**Query:** 韩国 Re2O 抗衰针原料是否含逝者皮肤？…列出冲突点。

| Metric | Value |
|--------|-------|
| duration | 949.3s |
| summary_chars | 12122 |
| search_provider_hits | `{serper: 9}` |
| search_rounds | 9 |
| gates | PASS (after Chinese Evidence-heading alias) |

### Conflicts excerpt (real)

```text
## 冲突与不确定 / Conflicts & Uncertainties

1. **原料确含逝者皮肤**（置信度：极高，95%+）。Elravie Re2O 系韩国 L&C BIO
   产品…核心原料为已故捐献者皮肤经脱细胞处理制成的 hADM…
   争议的实质不在“是否含”，而在“是否正当、是否安全、如何监管”。
```

Also covers informed consent, Korean regulatory tightening, clinical/safety gaps, and China compliance status in thematic sections.

---

## H3 — Houthis vs Saudi (FAIL — Evidence heading)

**Query:** 2026年9月胡塞武装称袭击沙特首都及延布能源设施：…能确认什么、不能确认什么？

| Metric | Value |
|--------|-------|
| duration | 533.2s |
| summary_chars | 11755 |
| search_provider_hits | `{serper: 11}` |
| search_rounds | 11 |
| follow_up_searches | 2 |
| gates | **FAIL** — `missing_evidence` |

Conflicts / Timeline / Confirmed / confidence **are present**. Gate fails solely because the model omitted a dedicated `## Evidence` heading (evidence is woven into Conflicts/Timeline instead).

### Conflicts excerpt (real) — still valuable

```text
## 冲突与不确定 / Conflicts & Uncertainties

### 1. 袭击是否得手——最根本的对立叙事
- **胡塞说法：** …利雅得方向击中“敏感目标”，延布方向击中阿美“敏感设施”并引发“大火”。
- **沙特说法：** …射向利雅得的一枚弹道导弹于凌晨被“成功拦截摧毁”；…延布等地袭击企图在抵达目标前被挫败。
- **裁决状态：** 无法裁决。双方说法正面冲突…
```

Does not take one side; casualties remain unconfirmed in Confirmed vs Unconfirmed.

---

## H4 — Same query as H1, light + compact (PASS)

| | H4 light/compact | H1 deep/detailed |
|--|------------------|------------------|
| duration | **57.9s** | 446.4s |
| summary_chars | **2937** | 6229 |
| search_rounds | 4 | 5 |
| sections | tldr, conclusion | full hotspot set |
| gates | PASS | PASS |

Intensity clearly changes length/depth. Compact answer still surfaces conflict language (snippets vs full archive; China vs Singapore; official vs auditor) and marks跨境 as 尚未证实 — does not invent certainty.

---

## H5 — searxng-only vs parallel-trusted (PASS)

Same H3 query under two profiles:

| Field | H5A searxng-only | H5B parallel-trusted |
|-------|------------------|----------------------|
| search_profile | **searxng-only** | **parallel-trusted** |
| SEARCH_PROVIDER_ORDER_STRICT | 1 | 0 |
| search_provider_hits | **`{searxng: 6}`** | **`{serper: 4}`** |
| search_rounds (organic) | **0** | **4** |
| search_attempts | 19 | 12 |
| gates (structure) | PASS | PASS |

Provider sets **differ**. SearXNG is unreachable in this VM (no docker); H5A correctly stays strict (no silent Serper append) and records failed searxng attempts — same honesty pattern as Round 4 Case D.

---

## Gate scoreboard (hard gates)

| Gate | H1 | H2 | H3 | H4 | H5A | H5B |
|------|----|----|----|----|-----|-----|
| TL;DR + confidence | ✓ | ✓ | ✓ | compact OK | ✓ | ✓ |
| Conflicts & Uncertainties | ✓ | ✓ | ✓ | n/a compact | ✓ | ✓ |
| Timeline | ✓ | ✓ | ✓ | n/a | ✓ | ✓ |
| Evidence (+ sources) | ✓ | ✓ | **✗** | n/a | ✓ | ✓ |
| Confirmed vs Unconfirmed | ✓ | ✓ | ✓ | n/a | ✓ | ✓ |
| No invented certainty | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Honest bottom line

- Conflicts section is now a **real** detailed-report requirement (code + live).
- Hotspot queries produce multi-source disagreement tables instead of fake consensus.
- Round 5 is **PARTIAL** because H3 missed the Evidence heading despite strong Conflicts content.
- H5 proves search-profile divergence with Serper live on trusted profile.
