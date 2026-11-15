# Wireless Skill Lab v2｜完整八讲讲义

> L1–L8 分别位于 `lessons/`。本文为教师阅读和检索便利合并。


---

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

入口：[`.dsh/skills/wireless-capacity/SKILL.md`](.dsh/skills/wireless-capacity/SKILL.md)。

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


---

# L2 · 模板与示例：知识从 Skill 中分离

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

理解 **Progressive Disclosure**（目录元数据 → `SKILL.md` → 按需文件）；学习 Template 与 Few-shot 的区别；验证共享知识文件与 Skill 的独立性。

## 教程原则与原始例子

Anthropic 教程使用 PDF Skill 说明：主入口只包含快速开始，复杂填表资料放入 `FORMS.md`，API 放入 `REFERENCE.md`，示例放入 `EXAMPLES.md`。对 BigQuery，又按 finance/sales/product/marketing 拆分文档，避免无关上下文。同时建议从入口 **一跳直接引用所需最终文件**，尽量不做深层参考链接。

## v2 与旧版的关键区别

旧版写“沿用 L1 公式”是隐含运行时依赖。v2 在自身的 `SKILL.md` 中明确说明输入字段，并直接引用项目共享 [Shannon 知识规范](knowledge/wireless/shannon.md)：

```text
.dsh/skills/wireless-capacity-examples/
├── SKILL.md
├── templates/result.md
└── references/examples.md
knowledge/wireless/shannon.md
```

这里 **Knowledge ≠ Skill**：模型需要使用文件读取工具实际读取 `knowledge/wireless/shannon.md`，它不会因为在 Markdown 里出现路径就自动进入上下文。`templates/result.md` 只管输出字段，`references/examples.md` 只提供正反例。

## 本 Lab 与操作

入口：[L2 SKILL.md](.dsh/skills/wireless-capacity-examples/SKILL.md)。先输入：

```text
/wireless-capacity-examples 请用统一模板分析 20 MHz、15 dB 的理论容量。
```

观察是否读取共享 Shannon 文档与模板。再输入：

```text
/wireless-capacity-examples 按模板分析 10 MHz、0 dB，并对照典型和边界示例。
```

此时需要再读取 `references/examples.md`，而不能总是无条件读取所有文件。**结果容量 10 Mbps**；B=0 应被拒绝。

## 分组改造任务

把一个输入输出示例追加到 `references/examples.md`：`5 MHz, -10 dB` 对应约 `0.6875 Mbps`。不得把示例直接复制到入口，以免膨胀主指令。讨论为什么此处对小公式的复制也可能比跨 Skill 调用更可靠。

## 过程评测

记录三列：模板是否打开、示例是否打开、共享知识是否打开。验证“有需要才读”的精确率，不只统计最终数字对错。源文件丢失时，Agent 应说明缺失，不可假称已读。

## 思考题与验收

什么时候应保留自包含内容？什么时候应该共享 `knowledge/`？单独复制此 Skill 到其他仓库会缺什么？

**过关**：无需 L1 也能运行 L2；能够按需引用、输出模板字段完整；有真实文件访问证据。

## 参考资料

[1] Anthropic, *Skill authoring best practices*（用户提供的原始教程）。

[2] DeepSeek Harness, *dsh-skill-filesystem*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md

[3] DeepSeek Harness, *dsh-tool-skill*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md

[4] 本仓库 `docs/ARCHITECTURE.md`、`contracts/`、`eval/EVAL.md`。


---

# L3 · 通过 Skill 运行 Python CLI

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

把自然语言推理与**确定性代码**分开，学习工具参数、标准输出 JSON、stderr、退出码与失败处理。能说明“查看代码”与“执行代码”的区别。

## 教程原则与原始例子

Anthropic 的 *Provide utility scripts*：预置、测试过的脚本比每轮让模型重写代码更可靠、更节省上下文。PDF 表单示例通过 `analyze_form.py` 提取，再用 `validate_boxes.py` 检查结果。教程特别强调：指令应明确写 `Run` 还是 `See`。

## 本 Lab 文件和 CLI

入口：[L3 SKILL.md](.dsh/skills/wireless-capacity-code/SKILL.md)。代码被统一为 `src/wireless_lab/capacity.py`，由 `tools/wireless.py` 暴露；不再放一份 L3 私有计算脚本。

```bash
python3 tools/wireless.py capacity --bandwidth-mhz 20 --snr-db 15
```

期望 stdout JSON 包含 `snr_linear≈31.6228` 和 `capacity_mbps≈100.556`，以及 `method_version` 与 `model`。脚本的 Python 标准库实现使用 `math.log1p` 提高低 SNR 数值稳定性。

## 在 Harness 中实验

```text
/wireless-capacity-code 请通过 Bash 工具真正执行容量 CLI，计算 20 MHz、15 dB。
展示实际 stdout 的 JSON 和退出码，再解释工程意义。
```

要看 DSH 轨迹中有 Bash 命令，而不仅是模型回复“我执行了”。工具若不可用，状态必须是 `NOT_RUN`。

## 负例与边界

```bash
python3 tools/wireless.py capacity --bandwidth-mhz 0 --snr-db 10
```

预期退出码 `2`，stderr 说明带宽无效；`SNR=-10 dB` 则应正常计算。不要把错误输入硬转为默认值。

## 工程扩展

任务 A：修改 `capacity.py` 加入 `capacity_gbps` 字段并新增单测。任务 B：设计恶意 CLI 参数或超大 SNR 负例，检查是否安全拒绝。任务 C：比较 L1 与 L3 在正确答案/工具证据方面的差异。

## 思考题与验收

`capacity.py` 是否有必要读进模型上下文？为什么 JSON stdout 比自由文本更适合后续工作流？

**过关**：CLI 正常与负例均经过真实执行；Agent 能据工具结果解释；无工具时不虚构成功。

## 参考资料

[1] Anthropic, *Skill authoring best practices*（用户提供的原始教程）。

[2] DeepSeek Harness, *dsh-skill-filesystem*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md

[3] DeepSeek Harness, *dsh-tool-skill*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md

[4] 本仓库 `docs/ARCHITECTURE.md`、`contracts/`、`eval/EVAL.md`。


---

# L4 · 分支逻辑、边界条件与条件性知识加载

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

理解 **Conditional Workflow**：如何将决策点交给确定性工具，再按返回值选唯一相关参考文件；学会边界测试并区分经验阈值与行业标准。

## 教程原则与原始例子

Anthropic 教程用文档的“新建 vs 修改”任务展示分支：新建可能使用高层库，修改原文件可能要处理底层结构并立即验证。过多工作流不应堆进一份入口，应拆开且明确何时读取。

## 本 Lab 分支与共享知识

L4 的数值选择交给 `src/wireless_lab/routing.py`，不是让模型猜测：

| SNR | 分支 | 对应知识 |
|---|---|---|
| `<0 dB` | low | [low-snr](knowledge/wireless/low-snr.md) |
| `0≤SNR<20 dB` | mid | [mid-snr](knowledge/wireless/mid-snr.md) |
| `≥20 dB` | high | [high-snr](knowledge/wireless/high-snr.md) |

**阈值仅用于本课堂教学，不是 3GPP/IEEE 的统一规范。**

## 动手实验

```bash
python3 tools/wireless.py route --snr-db -5
python3 tools/wireless.py route --snr-db 10
python3 tools/wireless.py route --snr-db 25
```

DSH 输入：

```text
/wireless-link-branch 输入 SNR=-5 dB。请真实运行路由工具，
只读取 JSON 指明的那个知识文件，提出两项只读检查。
```

检查工具的 `branch`、`reference` 与真实文件读取轨迹，不能无理由加载其他两个分支。

## 边界训练

测试 `-0.01, 0, 19.99, 20`，对应 `low, mid, mid, high`。然后故意将 `snr_db < 20` 改成 `<= 20`，通过测试找出错误，再恢复。

## 运维推理边界

低 SNR 可以提示关注覆盖/干扰，但不能断言天线故障；高 SNR 也不保证业务吞吐较高。把每个回答区分为「观测—候选假设—只读下一步」。

## 思考题与验收

为什么分支判据适合放进代码而解释知识放进 Markdown？负 dB 是否非法？什么情况下应该同时读取多个知识文件？

**过关**：边界正确，读取匹配知识，有真实工具证据，不将教学阈值误称标准。

## 参考资料

[1] Anthropic, *Skill authoring best practices*（用户提供的原始教程）。

[2] DeepSeek Harness, *dsh-skill-filesystem*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md

[3] DeepSeek Harness, *dsh-tool-skill*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md

[4] 本仓库 `docs/ARCHITECTURE.md`、`contracts/`、`eval/EVAL.md`。


---

# L5 · Validate → Compute → Verify 的多步骤工作流

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

学生能够写出有顺序和退出条件的工作流，保存机器可检查的中间产物，理解输入校验、报告计算、结果验证之间的区别，并能定位“输出写成 PASS 但实际上没验过”的问题。

## 教程原则与原始例子

Anthropic 给出 PDF 表单五步示例：分析表单 → 建立字段映射 → 验证映射 → 填表 → 验证输出；并建议用 checklist 防止漏步。*Create verifiable intermediate outputs* 更进一步主张中间结构（如 `changes.json`）先验证后执行。

## 本 Lab 的 4 条无线链路

源数据：[data/links.json](data/links.json) 包含 link-a 到 link-d，每条具有 `case_id`, `bandwidth_mhz`, `snr_db`, `actual_throughput_mbps`。

接口统一由 `tools/wireless.py` 实现：

```bash
python3 tools/wireless.py validate --input data/links.json
python3 tools/wireless.py compute --input data/links.json --output outputs/link_report.json
python3 tools/wireless.py verify --input data/links.json --report outputs/link_report.json --receipt outputs/verify_receipt.json
```

每一步实际返回 JSON；第二步只生成 `UNVERIFIED` 报告，第三步才产生带 `PASS` 或 `FAIL` 的**独立验证回执**。不得把生成结果文件的状态直接写成 PASS。

## 本 Lab 的报告合同

`contracts/links-v1.schema.json`、`contracts/report-v1.schema.json` 描述字段；Python 代码执行跨记录的 ID 唯一性、报告关联性和 SHA256 等额外检验。

字段 `throughput_to_capacity_ratio` 是业务速率与 AWGN 上限之比，不等同资源利用率。报告同时标注 `method_version`、源文件 SHA256 和 case_count。

## DSH 实验

```text
/wireless-link-workflow 读取 data/links.json，按校验、计算、验证顺序真实调用 CLI。
输出 reports 的文件路径和验证 receipt。遇到错误请停止并说明。
```

查三条 CLI 的真实顺序、退出码，确认 `outputs/link_report.json` 真正创建。

## 错误注入

让学生先完成三步流程，再把**报告副本**的 `link-a.capacity_mbps` 改成 `999`，运行 `verify` 应失败。然后重新 `compute` 修复，重新 `verify`。不能修改源数据来让错误报告通过。

## 讨论与验收

1. 为什么 source hash 有意义？
2. report 固定 UNVERIFIED，而 receipt 才写 PASS，有什么好处？
3. 如果 validate 通过后源文件发生变化，verify 会检测什么？

**过关**：三步骤真实执行、正常报告 PASS、被篡改报告 FAIL、解释结果及验证范围。

## 参考资料

[1] Anthropic, *Skill authoring best practices*（用户提供的原始教程）。

[2] DeepSeek Harness, *dsh-skill-filesystem*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md

[3] DeepSeek Harness, *dsh-tool-skill*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md

[4] 本仓库 `docs/ARCHITECTURE.md`、`contracts/`、`eval/EVAL.md`。


---

# L6 · 按领域导航的无线运维知识库

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

通过无线覆盖、吞吐和稳定性三个领域训练 Skill 的一跳知识引用，避免把网络教材写入冗长的 `SKILL.md`。形成观测/假设/验证行动三段式诊断输出。

## 教程原则与原始例子

Anthropic 的 BigQuery 教程示例把 finance、sales、product、marketing 的 schema 分开放在 `reference/*.md`，入口只写在什么条件下访问哪一份；大量非相关资料无须进入模型上下文。教程也警告深层链式链接可能导致只读部分内容。

## 本 Lab 文件

入口：[L6 SKILL.md](.dsh/skills/wireless-ops-diagnosis/SKILL.md) 直接链接：

- [coverage.md](knowledge/wireless/coverage.md)：RSRP/SINR、弱覆盖。
- [throughput.md](knowledge/wireless/throughput.md)：吞吐、重传、负载。
- [stability.md](knowledge/wireless/stability.md)：日志/Trace、抖动和丢包。
- [metrics.md](knowledge/wireless/metrics.md)：SNR/SINR/RSRP/BLER 的术语合同。

所有参考文档位于项目共享 `knowledge/`，不是嵌套 Skill。

## 三个诊断案例

[data/diagnosis_cases.json](data/diagnosis_cases.json) 包含：`weak-coverage`、`slow-throughput`、`unstable-link`。

课堂提问：

```text
/wireless-ops-diagnosis 请读取 unstable-link 案例。
根据症状按需选择知识，给出三个候选根因、各自缺少什么证据、
下一步只读采集什么指标，不要直接断言因果。
```

示例候选：间歇性干扰、切换异常、排队拥塞；要使用对齐的丢包、RTT、KPI、切换日志或 Trace 判断，不可依据一次 SINR 测量就断言根因。

## 过程指标与错误模式

参考文件选择准确率、无关读取量；是否混淆 SNR 与 SINR；是否提出可证伪的只读观测。缺文件应报告未读，而不是自称“已经参照资料”。

## 进阶题

用户同时报告弱覆盖与丢包，应该选择一份还是两份领域文档？请解释“按需”并不等于“最多一份”。如何让模型用时间轴对齐日志、Trace、Metrics？

**过关**：三个案例能按症状选择知识，证据/假设/动作分开，不凭相关性武断证明因果。

## 参考资料

[1] Anthropic, *Skill authoring best practices*（用户提供的原始教程）。

[2] DeepSeek Harness, *dsh-skill-filesystem*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md

[3] DeepSeek Harness, *dsh-tool-skill*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md

[4] 本仓库 `docs/ARCHITECTURE.md`、`contracts/`、`eval/EVAL.md`。


---

# L7 · 独立审计、失败修复和有界反馈

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

从“模型输出看着正确”转向 `Verifier` 的实际工具结果。学会错误注入、独立复算、失败后有限次数重试、无法执行时标记 `NOT_RUN`。

## 教程原则与原始例子

Anthropic 的 *Implement feedback loops* 强调 `Run validator → fix errors → repeat`。原教程中的 OOXML 编辑示例是：修改文件、立即验证、失败则修复，再验证通过后打包。重要的是验证器的错误要足够具体，让 Agent 能修正流程，而不是仅给出“错误”两个字。

## 本 Lab 的独立性

计算器代码位于 `src/wireless_lab/capacity.py`，但审计器在 `src/wireless_lab/audit.py` 里**独立实现公式**、独立读取源数据与报告。这可以识别公式结果不匹配、缺失 ID 和 SHA256 错配；但不能证明 Shannon AWGN 模型适用于真实生产环境。

## 审计好报告

先运行 L5 的计算以得到报告，然后：

```bash
python3 tools/wireless.py audit --input data/links.json --report outputs/link_report.json --receipt outputs/audit_receipt.json
```

**只有**实际 `audit` stdout `PASS` 且 exit code 0 才可以宣布审计通过。

## 审计坏报告：故意失败

```bash
python3 tools/wireless.py audit --input data/links.json --report fixtures/bad_report.json
```

`bad_report.json` 故意有容量 999、缺少 case、无效源 hash。期望 `FAIL`（exit code 1），出现具体错误列表。用被篡改的报告做教学，不得直接修改源数据。

## DSH 反馈循环

```text
/wireless-capacity-audit 请先审计 fixtures/bad_report.json，记录 FAIL 原因；
用 compute 工具从 data/links.json 重新生成 outputs/link_report.json，
再真实运行 audit，最多重试两次。不可更改源数据。
```

`FAIL → 修复计算 → 再审计 → PASS` 是可能成功的目标路径；若没权限运行或超过两轮，输出 FAIL/NOT_RUN。**不允许用自己口述的 PASS 替代实际工具回执**。

## 过程评分

比较验证覆盖率、修复成功率、缺失步骤、错误审计及过早结束率。讨论模型自检与独立程序校验的边界。

## 思考题与验收

如果计算器和审计器使用了同一个错误物理假设，会产生什么假阳性？如果报告不变但源文件 hash 变化，审计应怎样表现？

**过关**：真实 bad-report FAIL、正常 PASS、限次恢复、有错误日志和最终状态证据。

## 参考资料

[1] Anthropic, *Skill authoring best practices*（用户提供的原始教程）。

[2] DeepSeek Harness, *dsh-skill-filesystem*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md

[3] DeepSeek Harness, *dsh-tool-skill*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md

[4] 本仓库 `docs/ARCHITECTURE.md`、`contracts/`、`eval/EVAL.md`。


---

# L8 · Harness `skill` Loader 和多技能编排

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

将前七讲的知识/工具体系组织成一条可靠的综合任务流程。理解 **Instruction Reuse（加载子 Skill）**、**Tool Reuse（执行 CLI）** 与 **Knowledge Reference（读文件）** 的不同。能根据真实 DSH 轨迹区分遗漏装载、漏审计和过早结束。

## 教程原则与原始例子

Anthropic 的 *Workflow* 和 *Evaluation-driven development* 鼓励先设置可检验的代表性场景，再逐步添加最短指令并比较无 Skill 基线。教程建议使用两个 Agent 实例：Agent A 帮助编写 Skill，Agent B 用新的会话实际执行，再以观察结果修改文档。这与我们训练 Skill Selection / Tool Use / Recovery 的目标相符。

## 本 Lab 的跨 Skill 路由

入口：[L8 SKILL.md](.dsh/skills/wireless-link-orchestrator/SKILL.md)。对于“批量计算 + 审计 + 诊断”应加载：

1. `skill` 工具，`name=wireless-link-workflow`；执行 Validate、Compute、Verify。
2. `skill` 工具，`name=wireless-capacity-audit`；执行独立 audit。
3. `skill` 工具，`name=wireless-ops-diagnosis`；按需读取相关知识，给出只读验证建议。

这里的 `skill` 是模型可见的**工具**，不是 Shell 函数；写 `/wireless-link-workflow` 到 `SKILL.md` 也不等于模型已经执行该用户命令。只有工具返回 `<skill_content>` 才说明它已读取指令；子 Skill 的脚本还需额外执行并观察退出码。[3]

## 先看离线期望，不要把它当真实调用

```bash
python3 tools/wireless.py plan --task batch-audit-diagnose
```

输出明确写 `EXPECTED_PLAN_ONLY_NOT_AN_EXECUTION_TRACE`，其含义是**应该**调用 L5/L7/L6，而不是已经调用它们。

## DSH 综合任务演示

```text
/wireless-link-orchestrator 请对 data/links.json 执行真实的批量分析、审计与诊断。
只加载必要的子 Skill；按真实 CLI 的 stdout/stderr 报告结果。
在没有审计 PASS 时，不得说最终报告验证成功。
```

在 DSH 轨迹中检查模型侧 skill 装载名称、Bash 真实工具调用、文件读取和顺序。若 Bash 或 `skill` 工具不可用，应该标记 `NOT_RUN`，不得发明成功记录。

## 两种运行 Profile

```bash
python3 tools/set_profile.py --set teaching
python3 tools/set_profile.py --set integrated
```

Teaching：八个全可显式调用；Integrated：L1/L2 用户仍可 `/name` 但不参与模型自动目录，L3–L7 对模型开放而不可用户显式调用，L8 两者开放。**切换后的实际效果需在 Harness Session 中验证**。

## 过程评测

`eval/EVAL.md` 提供真实轨迹归一化协议；`eval/synthetic-trace-pass.json` 与 `eval/synthetic-trace-missing-audit.json` 是明确标注的合成正反例；以下命令只测试评分器：

```bash
python3 tools/evaluate_trace.py --input eval/synthetic-trace-pass.json
python3 tools/evaluate_trace.py --input eval/synthetic-trace-missing-audit.json
```

检查 Skill Load Coverage、Tool Coverage、Workflow Completeness、Verification Fidelity、Premature Completion。**通过合成轨迹评分不证明真实 DSH 运行成功。**

## 研究扩展与验收

分别比较无 Skill、仅 L5、L8 组合的任务成功率、工具覆盖率、过程完整性、失败恢复与上下文开销。将每个失误转成能力分解的 atomic case，例如“没有实际调用 audit 但声称 PASS”。

**过关**：真实 Harness 轨迹中有相应 skill 加载、执行步骤和审计结果；若工具禁用则明确 NOT_RUN；提交一份过程级失败案例和改进建议。

## 参考资料

[1] Anthropic, *Skill authoring best practices*（用户提供的原始教程）。

[2] DeepSeek Harness, *dsh-skill-filesystem*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md

[3] DeepSeek Harness, *dsh-tool-skill*, https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md

[4] 本仓库 `docs/ARCHITECTURE.md`、`contracts/`、`eval/EVAL.md`。

