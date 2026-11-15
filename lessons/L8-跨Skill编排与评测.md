# L8 · Harness `skill` Loader 和多技能编排

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

将前七讲的知识/工具体系组织成一条可靠的综合任务流程。理解 **Instruction Reuse（加载子 Skill）**、**Tool Reuse（执行 CLI）** 与 **Knowledge Reference（读文件）** 的不同。能根据真实 DSH 轨迹区分遗漏装载、漏审计和过早结束。

## 教程原则与原始例子

Anthropic 的 *Workflow* 和 *Evaluation-driven development* 鼓励先设置可检验的代表性场景，再逐步添加最短指令并比较无 Skill 基线。教程建议使用两个 Agent 实例：Agent A 帮助编写 Skill，Agent B 用新的会话实际执行，再以观察结果修改文档。这与我们训练 Skill Selection / Tool Use / Recovery 的目标相符。

## 本 Lab 的跨 Skill 路由

入口：[L8 SKILL.md](../.dsh/skills/wireless-link-orchestrator/SKILL.md)。对于“批量计算 + 审计 + 诊断”应加载：

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
