---
name: wireless-ops-diagnosis
description: 按弱覆盖、吞吐低和链路不稳定等症状选择无线运维参考知识，运行链路故障诊断，提出可检验假设；用户询问链路故障、指标、诊断、证据、调查计划时使用。
user-invocable: true
disable-model-invocation: false
---

# L6 — 按领域选择知识

## 知识导航（从 SKILL.md 直接链接目标文件）

- 弱覆盖、RSRP 弱：读取 [coverage.md](../../../knowledge/wireless/coverage.md)。
- 低吞吐/高 SINR 但速率慢：读取 [throughput.md](../../../knowledge/wireless/throughput.md)。
- 抖动、间歇断连、丢包：读取 [stability.md](../../../knowledge/wireless/stability.md)。
- 指标定义/单位不明时：读取 [metrics.md](../../../knowledge/wireless/metrics.md)。

用户提及多个领域时，可以读取多份**相关**知识；不应无目的加载所有文件。

## 输入与输出

可读取项目的 `data/diagnosis_cases.json`，或使用用户给定的只读 KPI、Trace、日志信息。

输出表格包括：**实际观测 / 至少两项候选假设 / 缺失证据 / 每个假设的只读检验**。

## 约束

- 必须区分 SNR、SINR、RSRP；不把相关性写成因果。
- 不能未经用户确认修改无线网络配置；不得把教学阈值当行业规范。
- 若需要读取的知识文件不可得，说明缺失而不是假装阅读成功。

示例：`/wireless-ops-diagnosis 诊断 unstable-link，提出三个可验证假设。`
