> **历史设计提案**：此文件保存用户同意的 v2 设计，供差异检查；当前生效实现以 `docs/ARCHITECTURE.md` 与源码为准。

# Wireless Skill Lab v2：统一架构与八个 Skill 重设计

> 状态：**设计规范（Design Proposal）**，尚未应用到上一版代码仓库。本文记录明确的文件组织、职责、调用合同、验证指标和迁移步骤，可交给开发 Agent 按步骤实现。
>
> 本方案基于已有的 L1–L8 命名、Anthropic《Skill authoring best practices》（课程提供）、DeepSeek Harness `skill-filesystem`、`tool-skill` 的当前官方行为。

## 0. 设计目标和决策

**目标**：保持八关由浅入深的课程体验，同时把系统按职责拆成 `Skills / Knowledge / Tools / Contracts / Artifacts / Eval` 六个层面，并使 L8 成为可观察、可评测的跨 Skill 编排案例。

**七条强约束**：

1. L1–L7 是不同技能工程技术的独立教学案例；**教学先后不代表运行时依赖**。禁止在 SKILL.md 中写「沿用 L1 / L5」。
2. 只有很小且普遍的公式或定义可以重复。大块共享知识属于 `knowledge/`，与 Skill 指令分离。
3. 只有模型需要执行任务步骤时才按名称加载另一 Skill（通过 Harness `skill` 工具）。**加载指令不等于执行完工具**。
4. 共享代码抽取到 `src/wireless_lab/`，所有数值任务都由确定性 CLI 执行。单元测试不需要大模型或 DSH。
5. 所有可保存的中间结果服从明确的 JSON 合同，报告至少保留 schema_version、来源、数值、执行状态及审核状态。
6. 审计器从源输入重新计算，不能只相信报告内部一致性；原始数据只读。**独立复算能审计数值一致性，不能证明物理模型真实适用**。
7. 对用户与模型的调用权限是不同维度，允许教学与综合应用采用不同配置；模型适用与否需要真实轨迹验证。

## 1. 目标架构

```mermaid
flowchart TD
    U[用户任务] --> H[DeepSeek Harness Agent]
    C[Skill Catalog: name/description] --> H
    H --> O[L8 Orchestrator]
    O -->|skill(name)| S3[L3: 计算指令]
    O -->|skill(name)| S4[L4: 分支指令]
    O -->|skill(name)| S5[L5: 批量工作流]
    O -->|skill(name)| S6[L6: 诊断知识选择]
    O -->|skill(name)| S7[L7: 审计和恢复]
    S3 --> T[Tools: Python CLI]
    S4 --> T
    S5 --> T
    S6 --> K[Knowledge: 无线领域知识]
    S7 --> V[Verifier: 重新计算/检查]
    T --> A[Artifacts: JSON/报告/轨迹]
    V --> A
    O --> A
    X[Contracts: Schema/权限/停止条件] --> S5
    X --> S7
    X --> O
```

> 图中 `skill(name)` 是**对 Harness 模型可见 `skill` 工具的调用意图**，不是让 Markdown 自身执行函数。User 的 `/name` 则是另一种“直接注入”机制。若用户已用 `/name` 注入，模型不应重复加载同一个 Skill。

## 2. 建议仓库结构

```text
wireless-skill-lab/
├── .dsh/skills/                       # 仅本目录直接子目录的 SKILL.md 被发现
│   ├── wireless-capacity/SKILL.md     # L1: 最简指令
│   ├── wireless-capacity-examples/     # L2: 格式和示例
│   │   ├── SKILL.md
│   │   ├── templates/result.md
│   │   └── references/examples.md
│   ├── wireless-capacity-code/SKILL.md     # L3
│   ├── wireless-link-branch/SKILL.md       # L4
│   ├── wireless-link-workflow/SKILL.md     # L5
│   ├── wireless-ops-diagnosis/SKILL.md     # L6
│   ├── wireless-capacity-audit/SKILL.md    # L7
│   └── wireless-link-orchestrator/SKILL.md # L8
├── knowledge/                         # 领域事实与规则；不扫描为 Skill
│   └── wireless/
│       ├── shannon.md                 # 公式/单位/模型边界
│       ├── metrics.md                 # SNR/SINR/RSRP/BLER
│       ├── coverage.md                # 覆盖诊断
│       ├── throughput.md              # 吞吐诊断
│       └── stability.md               # 稳定性诊断
├── src/wireless_lab/                  # 共享执行实现；可由各个 Skill 使用
│   ├── __init__.py
│   ├── capacity.py                    # Shannon 确定性计算
│   ├── routing.py                     # 边界条件分支
│   ├── workflow.py                    # validate/compute/verify
│   ├── audit.py                       # 单独复算报告与源数据
│   └── cli.py                         # 统一 CLI: capacity/route/validate/compute/verify/audit
├── contracts/
│   ├── links-v1.schema.json          # 数据 schema（若无 jsonschema 库可手工验证）
│   ├── report-v1.schema.json         # 输出 schema
│   └── execution-status.md            # PASS/FAIL/NOT_RUN/UNVERIFIED
├── data/links.json                   # 原始只读测试数据
├── fixtures/bad_report.json          # 错误注入样本
├── outputs/                           # 中间和最终输出（gitignore）
├── tests/
│   ├── test_core.py
│   ├── test_cli.py
│   ├── test_audit.py
│   └── test_skill_contracts.py
├── eval/
│   ├── skill_selection.jsonl         # 触发/误触发
│   ├── orchestration_cases.jsonl     # 组合任务和必需步骤
│   └── trajectory_rubric.md           # 轨迹评分协议
├── lessons/                           # 对应八讲讲义
└── README.md
```

**路径原则**：`SKILL.md` 的 Markdown 链接以技能目录为基底解析，因而从 `.dsh/skills/<name>/SKILL.md` 指向项目级知识可写 `../../../knowledge/wireless/shannon.md`（三个 `..`）；从仓库根目录运行 Python 或文件读取时用 `knowledge/wireless/shannon.md`。这些是两种不同的相对路径基准。跨项目分发单个 Skill 时，共享知识需要一起打包或复制到本 Skill 的 `references/`。

**一跳原则**：在 `SKILL.md` 内直接链接 `knowledge/wireless/coverage.md` 等最终所需资料，不建议先指向导航文件、再逐层指向最终文档。此处的一跳指文档引用关系，不是只能有一级文件夹。

## 3. L1–L8 的责任合同

| 实验 | 仅负责什么 | 可用知识/工具 | 不应该做什么 | 成功证据 |
|---|---|---|---|---|
| L1 `wireless-capacity` | 在对话中解释单链路容量 | 极简内嵌公式 | 引用 L2 或伪称已运行脚本 | 正确公式、单位、约束 |
| L2 `wireless-capacity-examples` | 模板化输出及例子对照 | `knowledge/shannon.md`、自身模板/示例 | 写「沿用 L1」或加载 L1 | 访问所需文档、字段齐全 |
| L3 `wireless-capacity-code` | 调用可执行计算 CLI | `src/wireless_lab/capacity.py` via CLI | 让模型心算替代工具 | Bash 实际调用 + stdout JSON + exit code |
| L4 `wireless-link-branch` | SNR 分类和匹配的分析知识 | route CLI + 对应的知识文档 | 读全部无关参考文件 | 分支正确、只读匹配文档 |
| L5 `wireless-link-workflow` | Validate→Compute→Verify | workflow CLI、合同与源文件 | 省略任一步/篡改源数据 | 中间 JSON + 三步骤轨迹 |
| L6 `wireless-ops-diagnosis` | 按问题域选知识、组织证据和假设 | `knowledge/wireless/{coverage,throughput,stability,metrics}.md` | 单一指标直接宣称根因 | 观测/假设/下一步验证分离 |
| L7 `wireless-capacity-audit` | 重新核验报告与源数据并有限恢复 | independent audit CLI、report contract；必要时复算 | 自己写 PASS；改原始数据 | 坏报告 FAIL；正确报告 PASS；恢复轨迹 |
| L8 `wireless-link-orchestrator` | 根据任务选择并加载子 Skill、编排验证 | Harness `skill` 工具 + 子 Skill 指令 | 假设说了「调用」就执行过；重复加载 | `skill` 加载轨迹 + 脚本轨迹 + 最终状态 |

L1 在教学中保留“最小公式内嵌”的刻意重复：它帮助学生学习自包含指令。L2 通过共享知识体验解耦；**两种方案都是有意识的教学设计，而不是强制一切公式统一外置**。

## 4. 三类复用、不要混淆

### A. 知识引用（Knowledge Reference）

- 适用：公式、术语、工程规则、候选根因资料。
- 接口：文件路径 + 明确“什么时候读”。
- 示例：L2 读取 `../../../knowledge/wireless/shannon.md`；L6 按症状读取三篇中的一篇或多篇。
- 不能认为“提到路径”就证明 Agent 阅读了它；需要检查文件读取轨迹。

### B. Tool/代码复用（Executable Reuse）

- 适用：确定性计算、选择分支、文件校验、报告审计。
- 接口：CLI 参数、JSON stdout、stderr、退出码；以代码与 JSON schema 为合同。
- 示例：`python3 -m wireless_lab.cli capacity --bandwidth-mhz 20 --snr-db 15`（需要项目完成 `src` 包安装或配置 `PYTHONPATH`）。
- 不能因为已经看过 `capacity.py` 源码，就声称执行过它。

### C. Skill 编排（Instruction Reuse）

- 适用：完整任务需要多项相对独立的工作方法，例如综合诊断 + 审计。
- 接口：Harness `skill` 工具、精确的 Skill 名称、返回的 `<skill_content>` 指令。用户 `/name` 只是直接注入该 Skill 的另一个入口。
- 示例：L8 按需加载 `wireless-link-workflow`、`wireless-capacity-audit`、`wireless-ops-diagnosis`。
- 不能认为 `skill` 载入就意味着 Bash 执行完；Agent 仍必须根据载入的指令实际采取动作。

## 5. Skill 的最小写作合同

```yaml
---
name: wireless-capacity-examples
description: 使用模板生成无线香农容量分析。当用户要求统一格式、示例对照或容量说明时使用。
user-invocable: true
---
```

正文建议包含：`目标/触发条件` → `输入验证` → `选择性资源` → `操作步骤` → `输出合同` → `失败路径` → `示例调用`。不要写课程序号当作运行时依赖（如“参照 L1”）。具体 L2 模板见 `examples/L2-SKILL.md`。

对于 L8，明确：若某个子 Skill 已由直接 `/name` 注入或已在当前上下文中加载，就遵循已加载指令，不进行重复加载；否则通过 `skill` 工具加载。精确名称不能写成自然语言标题。完整模板见 `examples/L8-SKILL.md`。

## 6. 一份关键的统一数据合同

源数据的最小记录：

```json
{
  "case_id": "link-a",
  "bandwidth_mhz": 20,
  "snr_db": 15,
  "actual_throughput_mbps": 74
}
```

单条记录应满足：`case_id` 非空且唯一，`bandwidth_mhz > 0`、`snr_db` 为有限实数、`actual_throughput_mbps >= 0`。

结果应包含 `capacity_mbps` 与 `throughput_to_capacity_ratio`，并保留原始字段。真实吞吐/理想上限的比例不是「信道负载率」，只能是模型 sanity check。为了方便审计，可补充 `schema_version`、`source_path` 或内容摘要、`method_version`、`case_count`。

**状态建议**：

- `PASS`：要求的验证器已运行并且通过。
- `FAIL`：已经运行，但检出错误或失败。
- `NOT_RUN`：没有运行/无法运行，不准声称通过。
- `UNVERIFIED`：已计算但尚未执行所需验证。（可选，用于区分计算完成与验证完成。）

记录每个必需步骤的实际工具调用、退出码、结果文件路径。恢复次数有上限（教学默认最多 2 次），失败则终止并报告缺失证据。

## 7. L8 的跨 Skill 调用方案

L8 是唯一重点演示**多 Skill 装载**的实验，但它**不是**一个“调用其他 Skill 的函数库”。建议按任务动态选择：

```text
单链路数值任务          → skill('wireless-capacity-code') → 真正运行容量 CLI
SNR 条件分析           → skill('wireless-link-branch') → 运行 route CLI → 阅读匹配参考
批量链路计算           → skill('wireless-link-workflow') → validate/compute/verify
批量结果可信度审核      → skill('wireless-capacity-audit') → audit
需要根因候选与证据组织  → skill('wireless-ops-diagnosis') → 领域知识与验证计划
```

例如对完整任务“批量计算 + 审计 + 诊断”应加载 L5/L7/L6，而不是无目的地把八个 Skill 全部读一遍。模型可能因目录提示同时加载多个适用 Skill，因此需要以轨迹确认实际行为并统计多余加载。

### 审核优先级

`audit` 的实际输出与 exit code 优先于模型自然语言陈述。报告必须写 `PASS / FAIL / NOT_RUN`，无法执行工具时主动降级，不得虚构 stdout 或成功状态。

## 8. 两个使用模式（同样八个 Skill）

### 教学模式（Teaching Profile）

- 八个 Skill 都 `user-invocable: true`，便于 `/name` 显式比较。
- 八个都可由模型自动发现，便于测量“自动路由”的准确率；描述必须避免过度重叠。
- 对基础能力的对照评测应隔离其他 Skill，否则选中 L3 而不是 L1 不一定说明模型有问题。

### 综合应用模式（Integrated Profile）

- L1/L2 作为纯教学演示：可设置 `disable-model-invocation: true`、`user-invocable: true`，从模型目录排除但仍可直接 `/name`。
- L3–L7 作为可由模型加载的子能力：可设置 `user-invocable: false`，减少用户命令入口；保留模型调用。
- L8 `user-invocable: true` 且模型可调用，成为主要综合入口。
- 这是**部署建议**，不是当前八个 Skill 自动具备的多模式开关；切换 profile 需要分别改 frontmatter、配置或采用隔离工作区，完成后通过会话目录检查。

## 9. Evaluation：至少覆盖哪些能力

| 指标 | 单元/过程级证据 | 主要实验 |
|---|---|---|
| Skill Selection Accuracy | skill 工具加载的名称与标注 | L1/L2/L8 |
| Knowledge Selection Precision | 被读取的知识文件是否必要 | L2/L4/L6 |
| Tool Execution Compliance | 实际 CLI 调用及退出码 | L3/L5/L7/L8 |
| Branch Boundary Accuracy | `-0.01, 0, 19.99, 20` dB | L4 |
| Workflow Completeness | validate→compute→verify 全执行 | L5 |
| Audit Fidelity | 错报告 FAIL、好报告 PASS | L7 |
| Recovery Success | 在 2 次以内修复且复审 PASS | L7/L8 |
| Premature Completion | 无核验却宣称完成的比例 | L7/L8 |
| Unnecessary Loading | 多余的 Skill / reference 加载量 | L6/L8 |

每项至少一条成功、一条失败、一条边界样本；L8 另加 **无 Bash、缺失子 Skill、数据损坏** 三个对抗性样本。评测报告应区分「答案正确」与「执行路径正确」，避免从自然语言推断工具是否被真实调用。

## 10. 迁移实施次序

**Phase A — 解耦（不改变行为）**
1. 创建 `knowledge/wireless/*.md`，迁移 L4/L6 参考资料，统一指标术语。
2. 修改 L2：删除“沿用 L1”，增加共享公式的直接链接与独立输入合同。
3. 明确 L1 保留最小公式，避免多余依赖。

**Phase B — 统一代码与合同**
4. 把 L3/L4/L5 的数学、路由、报告逻辑统一到 `src/wireless_lab/`，各自 Skill 只写“执行哪些 CLI 命令”。
5. 引入 schema 与 `PASS/FAIL/NOT_RUN` 状态，源文件只读。
6. 将 L7 的独立复算从共享生成逻辑分离，确保坏报告能被识别。

**Phase C — 真正跨 Skill 编排**
7. 重写 L8 的 `SKILL.md`：任务路由、按名称调用 `skill`、读取 `<skill_content>`、执行子能力、验证、终止。
8. 建立生产/教学 profile 与技能选择冲突评测；不要误用 `disable-model-invocation` 导致 L8 无法调用子技能。

**Phase D — 更新文档与评测**
9. 同步修改 L1–L8 讲义中所有文件路径与命令；不能只改代码不改讲义。
10. 对已有 6 个 Python 单测做回归；增加 Skill 引用路径、描述冲突、加载轨迹和错误注入的测试。
11. 在真实 DSH 中核验加载、Bash 实际执行、`NOT_RUN` 状态和失败恢复。**不能仅用 Python 单测推断 Harness 层正确。**

## 11. 哪些是当前产品行为，哪些是本项目设计？

**来自官方文档的行为**：`skill-filesystem` 发现一级技能包，`tool-skill` 创建目录与模型 `skill` Loader，`/name` 由用户消息直接注入指令，`skill` 加载后的内容本身并不会执行外部脚本。[2–4]

**本项目制定的约定**：八个 Skill 的职责划分、`knowledge/`/`src/` 目录、统一 CLI 与 JSON 合同、两个运行 profile、最多 2 次重试、轨迹评测指标。它们是我们的工程方案，不属于 Harness 强制规定的行为。

## 参考文献

[1] Anthropic. *Skill authoring best practices*（用户提供教程）。
[2] DeepSeek Harness. *tool-skill 官方文档*. https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/tool-skill/README.zh.md
[3] DeepSeek Harness. *skill-filesystem 官方文档*. https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.zh.md
[4] DeepSeek Harness. *skill 注册表官方文档*. https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill/README.zh.md
