# 消费者结论优先布局验收（fixture 并排）

## 预期

| 档位 | 一眼结论卡 | 争议短列表 | 证据与来源折叠 | 深入了解 |
|------|------------|------------|----------------|----------|
| compact | 有 | 有（若存在） | 有 | 无 |
| balanced | 有 | 有 | 有 | 有 |
| detailed | 有 | 有 | 有 | 有 |

## 实测

| 档位 | chars | deep | glance | folds |
|------|-------|------|--------|-------|
| compact | 315 | False | True | 1 |
| balanced | 723 | True | True | 2 |
| detailed | 723 | True | True | 2 |

产物目录：`docs/acceptance/artifacts/consumer_layout_L/`

分享：https://6f2a083350bc0653ae.gradio.live （用户 hu）
