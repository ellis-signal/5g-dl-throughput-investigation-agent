# Phase A–D 实施与迁移记录

> 实施结果基于 v2 设计包 `wireless-skill-v2-design/ARCHITECTURE.md`，按其中四阶段的目标完成。由于当前会话中没有上一版完整 ZIP，v2 使用已给的名称、数据和设计合同进行**重建式迁移**，不声称逐文件保持上一版 Git 历史。

## Phase A — 知识和 Skill 解耦（已完成）

- 新建 `knowledge/wireless/shannon.md`（取自设计包的建议知识规范）、`metrics.md`、`coverage.md`、`throughput.md`、`stability.md`、三份分支资料。
- L2 不再写「沿用 L1」；改成直接读取共享 Shannon 规范和自身模板、示例。
- L4 与 L6 直接指向相关的最终知识文件，避免深链。
- L1 刻意保留最小公式，保证教学起点自包含。

## Phase B — 代码、合同与独立验证（已完成）

- 共享计算实现：`src/wireless_lab/capacity.py`。
- 共享路由：`src/wireless_lab/routing.py`，三种阈值仅用于课堂。
- 多链路计算工作流：`src/wireless_lab/workflow.py`。
- 独立审计：`src/wireless_lab/audit.py`，不导入报告计算函数。
- 统一 CLI：`python3 tools/wireless.py <subcommand>`，命令 `capacity/route/validate/compute/verify/audit/plan`。
- 源输入/结果输出的 JSON Schema 与执行状态合同。
- 输出报告引用源文件 SHA256；verify/audit 的回执写入独立文件。

**旧命令映射（从上一版讲义对应逻辑迁移）**：

| v1 形式 | v2 等价命令 |
|---|---|
| `.dsh/skills/wireless-capacity-code/scripts/capacity.py` | `tools/wireless.py capacity` |
| `.dsh/skills/wireless-link-branch/scripts/route.py` | `tools/wireless.py route` |
| `workflow.py validate/compute/verify` | `tools/wireless.py validate/compute/verify` |
| `audit.py --source ...` | `tools/wireless.py audit --input ...` |
| `references/{coverage,throughput,stability}.md` | `knowledge/wireless/{coverage,throughput,stability}.md` |

## Phase C — Multi-Skill、Profiles 与轨迹辅助（实现完成，Harness 需现场验证）

- L8 指令明确使用 Harness 模型侧 `skill` 工具，参数 `name` 为精确 Skill 名；不得当作 Bash 函数。
- 任务计划 `src/wireless_lab/planner.py` 供**离线期望路径对照**。`plan` 明确标为 NOT_AN_EXECUTION_TRACE。
- `tools/set_profile.py` 可切换 teaching/integrated 的 frontmatter 权限。
- `tools/evaluate_trace.py` 可审查归一化的轨迹是否含必需装载、操作、正确顺序和审计状态。
- `eval/synthetic-trace-*.json` 是**人造评测正反例**，不是任何真实 DSH 轨迹。

**未在本环境实测**：DSH 模型实际 `skill` 工具调用、Bash 工具权限、真实会话中文件读取行为。它们属于现场集成测试而不是单元测试。

## Phase D — 讲义、评测和回归测试（已完成）

- 更新 L1–L8 八篇 v2 Markdown 讲义、索引和教师指南；旧的文件路径不再使用。
- `tests/` 自动检查算法/边界、CLI、篡改、坏报告、前置权限、知识引用和合成轨迹。
- `tools/check_skills.py` 检查八个前置 YAML 字段、路径和课程序号依赖。
- `run-demo.sh` 演示正常报告与 bad_report 预期失败。

## 知识与能力分离的验收重点

1. L2 可不加载 L1 而独立读取 Shannon 规范。
2. L3 在 Bash 可用时必须执行 CLI，否则只能标记 NOT_RUN。
3. L4 使用确定性脚本路由，并读取匹配分支文件。
4. L5 报告的状态为 UNVERIFIED；真实 verify 后才有 PASS receipt。
5. L7 在篡改容量与 SHA256 错配时可靠 FAIL。
6. L8 仅以真实 Harness 工具轨迹计入跨 Skill 成功率。
