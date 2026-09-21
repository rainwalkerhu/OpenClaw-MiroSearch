# Acceptance / verify artifacts

Research-quality acceptance rounds for OpenClaw-MiroSearch. Process docs and live-run artifacts live here (not at repo root).

Product feature docs: [`../RESEARCH_INTENSITY.md`](../RESEARCH_INTENSITY.md), [`../DEEP_EFFICIENCY.md`](../DEEP_EFFICIENCY.md).

## Rounds overview

| Round | Focus | Verify | Results | Artifacts |
|-------|--------|--------|---------|-----------|
| 1 | Initial implementation audit | [VERIFY_ROUND_1.md](./VERIFY_ROUND_1.md) | [ACCEPTANCE_RESULTS_ROUND_1.md](./ACCEPTANCE_RESULTS_ROUND_1.md) | — |
| 2 | First live E2E (A–C) | [VERIFY_ROUND_2.md](./VERIFY_ROUND_2.md) | [ACCEPTANCE_RESULTS_ROUND_2.md](./ACCEPTANCE_RESULTS_ROUND_2.md) | [artifacts/round2/](./artifacts/round2/) |
| 3 | Lead-trail fix + live A–E | [VERIFY_ROUND_3.md](./VERIFY_ROUND_3.md) | [ACCEPTANCE_RESULTS_ROUND_3.md](./ACCEPTANCE_RESULTS_ROUND_3.md) | [artifacts/round3/](./artifacts/round3/) |
| 4 | Case D search-profile PASS | [VERIFY_ROUND_4.md](./VERIFY_ROUND_4.md) | [ACCEPTANCE_RESULTS_ROUND_4.md](./ACCEPTANCE_RESULTS_ROUND_4.md) | [artifacts/round4/](./artifacts/round4/) |
| 5 | Hotspot cross-verification (anti-pollution) | [VERIFY_ROUND_5.md](./VERIFY_ROUND_5.md) | [ACCEPTANCE_RESULTS_ROUND_5.md](./ACCEPTANCE_RESULTS_ROUND_5.md) | [artifacts/round5/](./artifacts/round5/) |
| 6 | Evidence gate fix + deep efficiency | [VERIFY_ROUND_6.md](./VERIFY_ROUND_6.md) | [ACCEPTANCE_RESULTS_ROUND_6.md](./ACCEPTANCE_RESULTS_ROUND_6.md) | [artifacts/round6/](./artifacts/round6/) |

- [VERIFY_FINAL.md](./VERIFY_FINAL.md) — consolidated verify notes
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) — implementation summary
- [ROUND_2_SUMMARY.md](./ROUND_2_SUMMARY.md) — Round 2 short summary

## Live harness

```bash
cd apps/miroflow-agent
uv run python scripts/run_acceptance_live.py --cases H3,H1
# or full hotspot set: --cases H
# or legacy: --cases A,B,C,D,E
```

Default `--out-dir` still points at `docs/acceptance/artifacts/round5/`;
for Round 6 use `--out-dir ../../docs/acceptance/artifacts/round6`.
