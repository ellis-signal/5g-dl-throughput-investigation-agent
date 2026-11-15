# L1 · 最小 Skill：自包含指令

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

理解 Skill 与一次性 Prompt 的区别；编写必需的 `name`/`description` frontmatter；观察 `/name` 显式调用和自然语言自动匹配的区别；用 Shannon 容量公式识别单位错误。

## 教程原则及原始例子

Anthropic 强调 **Concise is key**：模型已经懂 PDF 是什么，提取 PDF 文本的指南直接写使用 `pdfplumber` 的短代码即可，不必长篇解释 PDF 背景。类似地，通信模型通常知道 Shannon 公式，我们只需写清楚参数、单位、必须遵守的限制和输出形式。

另一个原则是 `description` 既要说 **做什么**，也要说 **何时触发**。对比：`帮助通信` 不如 `计算无线 Shannon 容量，用户询问带宽和 SNR 时使用`。

## 本 Lab 文件

入口：[`.dsh/skills/wireless-capacity/SKILL.md`](../.dsh/skills/wireless-capacity/SKILL.md)。

```yaml
---
name: wireless-capacity
description: 计算单条无线信道的 Shannon AWGN 理论容量；当用户只需要公式、单位及工程解释时使用，不需要脚本执行。
user-invocable: true
disable-model-invocation: false
---
```

Shannon AWGN 容量：

\[\gamma =10^{\mathrm{SNR}_{dB}/10},\quad C_{\mathrm{Mbps}}=B_{\mathrm{MHz}}\log_2(1+\gamma).\]

20 MHz, 15 dB → **约 100.556 Mbps**；10 MHz, 0 dB → **10 Mbps**。负 dB 合法，带宽为 0 无效。这里的理论上限不是真实吞吐保证。

## 学生操作

在项目根目录启动 `npx @deepseek-ai/dsh web`，确保新会话 workspace 指向本仓库。输入：

```text
/wireless-capacity 请计算 B=20 MHz、SNR=15 dB 的 Shannon 容量，说明计算步骤与模型局限。
```

然后不带 `/` 提问一次。判断：显式调用是否成功、自然语言触发了什么 Skill、结果是否正确。**仅凭答案正确不能证明自动加载了指定 Skill**；需要查看模型轨迹。

## 失败与边界练习

让学生测试 `B=0 MHz` 和 `SNR=-5 dB`；再修改 description 为笼统版本比较触发情况。保留一次错误触发的记录。

## 思考题

1. `user-invocable` 和模型可调用权限是否同一概念？
2. 为什么本讲允许少量公式重复，而不是要求引用 L2？
3. 正确答案与正确执行路径分别如何证明？

## 验收

能从 `/` 列表找到 Skill、显式执行、公式及单位正确、对非法带宽拒绝；**L1 不应宣称运行 Python**。

## 参考资料

[1] Anthropic, *Skill authoring best practices*（用户提供的原始教程）。

[2] DeepSeek Harness, *dsh-skill-filesystem*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md

[3] DeepSeek Harness, *dsh-tool-skill*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md

[4] 本仓库 `docs/ARCHITECTURE.md`、`contracts/`、`eval/EVAL.md`。
