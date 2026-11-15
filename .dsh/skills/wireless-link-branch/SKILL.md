---
name: wireless-link-branch
description: 将给定 SNR 分成低中高三个教学分支并按需加载相应知识；用户要求分支分析或根据 SNR 选择下一步观测时使用。
user-invocable: true
disable-model-invocation: false
---

# L4 — 条件分支与资源选择

## 教学分支（不代表 3GPP/IEEE 规定阈值）
- `snr_db < 0`：低 SNR；[low-snr.md](../../../knowledge/wireless/low-snr.md)。
- `0 <= snr_db < 20`：中 SNR；[mid-snr.md](../../../knowledge/wireless/mid-snr.md)。
- `snr_db >= 20`：高 SNR；[high-snr.md](../../../knowledge/wireless/high-snr.md)。

## 执行步骤
1. 先验证输入并实际执行：
```bash
python3 tools/wireless.py route --snr-db -5
```
2. 读取 stdout JSON 的 `branch` 和 `reference`；从仓库根目录按 `reference` 文件路径**仅读取匹配的一个**分支文件。
3. 说明分支、阈值及优先采集的只读证据；不得由单一 SNR 断言根因。

## 失败规则
- 工具不可用标记 `NOT_RUN`，可仅说明静态分支判据，但不得声称脚本已执行。
- 超出分支分析的复杂诊断应报告还缺哪些观测；本 Skill 不自动操作网络设备。

示例：`/wireless-link-branch SNR=-5 dB，应选择什么分析路径？`
