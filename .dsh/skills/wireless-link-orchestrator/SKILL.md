---
name: wireless-link-orchestrator
description: 执行完整无线链路任务，按需加载计算、分支、批量工作流、诊断和独立审计等子技能；用户要求多能力协同、可核验报告时使用。
user-invocable: true
disable-model-invocation: false
---

# L8 — 真正的跨 Skill 编排（Harness model `skill` 工具）

## 必须区分三类动作
- **加载 Skill**：调用模型可见的 `skill` 工具，并设置其 `name` 参数为精确的 kebab-case Skill 名；等待 `<skill_content>`。
- **执行 Tool**：按返回的子 Skill 指令调用 Bash/CLI、读取文件、获得退出码。
- **解释/报告**：根据真实 tool 输出给出结论，不得把「已加载 Skill」说成「已执行完子任务」。

## 任务路由
- 单链路精确计算：加载 `wireless-capacity-code`。
- SNR 条件分支：加载 `wireless-link-branch`。
- 批量数据分析：加载 `wireless-link-workflow`。
- 审计最终报告：加载 `wireless-capacity-audit`。
- 根因候选与证据：加载 `wireless-ops-diagnosis`。

### 核心流程
1. 根据任务类型建立最小计划，**只加载必要的 Skill**；已经由 `/name` 注入或此前加载的相同 Skill 不要重复加载。
2. 对每个尚未加载的 Skill，实际调用模型侧 `skill` 工具：`{"name":"wireless-link-workflow"}`（这里是**工具参数示例**，不是 Shell 命令）。等到 `<skill_content>` 再执行其工作流程。
3. 批量任务严格遵循 validate → compute → verify；如用户要求可信报告，再加载审计 Skill、执行 audit；需要诊断时再加载诊断 Skill 并读取相应领域知识。
4. 审计 FAIL 时最多两次修复；源数据只读。未真实运行时必须标记 `NOT_RUN`。
5. 汇总结果，包括**已加载 Skill 名称**、**实际 Bash 命令与退出码**、**容量及其局限**、**观测/假设/验证动作**、**审计 PASS/FAIL/NOT_RUN 真实依据**。

## 离线规划练习（不会加载 Harness Skill）
```bash
python3 tools/wireless.py plan --task batch-audit-diagnose
```
上面只生成**EXPECTED_PLAN_ONLY_NOT_AN_EXECUTION_TRACE**，用来对照真实 DSH 行为。它不是跨 Skill 的真实调用证据。

## 失败规则
若 Harness `skill` 工具不可用或被禁用，不能声称已完成多 Skill 装载；若 Bash 不可用，也不能声称计算或审计完成。不得自动修改真实无线设备参数。

示例：`/wireless-link-orchestrator 对 data/links.json 进行批量分析、审计及诊断。`
