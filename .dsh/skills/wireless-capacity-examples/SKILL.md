---
name: wireless-capacity-examples
description: 将 Shannon 信道容量计算，写成统一模板报告，并在需要时对照 Few-shot 例子；用户明确要求模板、对照或边界示例时使用。
user-invocable: true
disable-model-invocation: false
---

# L2 — 独立的模板与示例 Skill

## 必需资源与输入

- 带宽 `bandwidth_mhz` 必须为正的有限实数；`snr_db` 是有限实数，允许负数。
- 计算前**实际读取**项目共享公式文档：[Shannon 知识规范](../../../knowledge/wireless/shannon.md)，工作区路径 `knowledge/wireless/shannon.md`。
- 每次报告都要读取 [输出模板](templates/result.md)。
- 仅在用户明确要求示例比较、遇到边界/单位混淆时读取 [Few-shot 示例](references/examples.md)。

## 执行

1. 确认输入单位；按知识规范中的公式计算，勿直接将 SNR(dB) 代入 log2。
2. 使用模板的完整字段输出结果，允许补充简短工程解释。
3. 区分 Shannon 理论上限与业务吞吐；不得凭空声称已运行脚本。

## 失败

知识文件或模板无法读取时，明确报告缺失资源，不要假称读过或静默转去加载其他 Skill。

示例：`/wireless-capacity-examples 使用统一模板分析 10 MHz、0 dB，并与示例对照。`
