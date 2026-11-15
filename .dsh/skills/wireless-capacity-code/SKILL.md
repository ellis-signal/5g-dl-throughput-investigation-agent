---
name: wireless-capacity-code
description: 调用可复现的 Python CLI 精确计算单条链路 Shannon 容量；用户要求运行代码、机器可读 JSON、精确复算时使用。
user-invocable: true
disable-model-invocation: false
---

# L3 — 代码工具调用

## 必须真实执行
从仓库根目录运行（Python 3.9+，仅标准库；需要 DSH Bash 工具）：

```bash
python3 tools/wireless.py capacity --bandwidth-mhz 20 --snr-db 15
```

必须用用户提供的两个数字替换样例参数，不得拼接未经校验的自由文本到 shell。`capacity` 的标准输出为 JSON，包含 `capacity_mbps`、`snr_linear`、`spectral_efficiency_bps_hz`。

## 工具输出合同
- 退出码 0：计算成功；报告原始 JSON 的重要字段与模型假设。
- 退出码 2：参数无效/数值溢出；报告 stderr，勿编造容量。
- Bash 不可用：明确 `NOT_RUN`，给出可本地执行的命令，不能声称实际执行。

计算工具的实现位于项目 `src/wireless_lab/capacity.py`。**执行** CLI 而不是只读取源代码。

示例：`/wireless-capacity-code 请真实运行代码计算 20 MHz 15 dB 并展示 stdout。`
