---
name: wireless-capacity
description: 计算单条无线信道的 Shannon AWGN 理论容量；当用户只需要公式、单位及工程解释时使用，不需要脚本执行。
user-invocable: true
disable-model-invocation: false
---

# L1 — 最小独立指令型 Skill

## 输入
- `bandwidth_mhz`：MHz，正的有限实数。
- `snr_db`：dB，有限实数，可为负。

## 任务
1. 将 dB 转成线性 SNR：`snr_linear = 10 ** (snr_db/10)`。
2. 理论容量：`capacity_mbps = bandwidth_mhz * log2(1 + snr_linear)`。
3. 输出输入、公式、容量（Mbps）、模型限制（AWGN 理论上限不是吞吐量承诺）。

## 完成条件
- 不直接把 dB 代入 log2。
- 输入非法时指出错误；若未使用工具，不得声称运行 Python。
- 本 Skill 完整自包含；不要引用或假设任何“前一课”已被加载。

示例：`/wireless-capacity 20 MHz、15 dB 的 Shannon 容量是多少？`
