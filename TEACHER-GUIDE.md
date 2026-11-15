# 教师手册：Wireless Skill Lab v2

## 教学理念

八关不是必须互相加载的 Skill 继承树，而是**八种复用/可靠性工程能力**。组织学生比较自然语言正确率与工具真实执行；“模型回答对”不代表“选择了正确 Skill”。

## 建议三次课堂（每次 90 分钟）

- 第 1 次：L1–L3。Skill 定义、自包含/共享知识、确定性 CLI；比较无 Skill、L1、L3。
- 第 2 次：L4–L6。分支条件、批处理工作流、按需读取多领域知识。
- 第 3 次：L7–L8。独立审计、错误注入与恢复；多 Skill 真实编排及轨迹评测。

## 评分（100 分）

| 项目 | 分值 | 主要证据 |
|---|---:|---|
| L1–L2 YAML 与知识引用 | 15 | Skill 触发、共享文件真实读取与模板遵循 |
| L3 CLI 执行与错误处理 | 15 | 实际 Bash stdout/stderr、非法输入 |
| L4 分支边界 | 10 | -0.01/0/19.99/20 及匹配文件 |
| L5 工作流 | 20 | validate/compute/verify、报告和 receipt |
| L6 知识导航 | 10 | 精准加载、观测/假设/验证三分法 |
| L7 恢复与审计 | 15 | 坏报告 FAIL、正确报告 PASS、有限重试 |
| L8 编排与综合评测 | 15 | 真实 `skill` 载入证据、工具轨迹、停止判断 |

## 现场测试的边界

Python 的单元测试可证明 CLI 与静态 Skill 结构，但**不能证明 DeepSeek Harness 的模型遵守了指令**。必须在有 `skill`、Bash 和文件工具的会话中取证。评测脚本只能对归一化日志评分，且合成日志不可作为真实运行成绩。

## 难点练习

1. 故意禁用 Bash，观察 L3/L8 是否报告 NOT_RUN。
2. 在 integrated profile 下让 L8 加载 L5/L7/L6，检查权限设置是否正确。
3. 篡改 `outputs/link_report.json` 里的容量与 SHA256，验证审计器是否拦截。
4. 修改 L2 的 description 与 L6 的参考导航，对比错误触发/无关读取率。

## 延伸研究

- Atomic Capability：Skill Selection、Reference Selection、Tool Use、Workflow Execution、Verification、Recovery、Stop Decision。
- 将无线实验迁移到微服务 RCA 的 Metrics/Logs/Traces，构建基于 trajectory 的过程评测。
- 比较 Base Prompt / Instruction Skill / Executable Skill / Verifier-guided Orchestration，隔离模型、数据、工具权限等混杂因素。
