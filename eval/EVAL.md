# Harness Skill 过程评测协议

**核心规则**：只从原始工具事件提取信息，不能根据 Agent 自述补填。当前 `synthetic-trace-pass.json` 和 `synthetic-trace-missing-audit.json` 是合成测试夹具，不是实际执行日志。

## 一、测试入口

```bash
python3 tools/wireless.py plan --task batch-audit-diagnose
python3 tools/evaluate_trace.py --input eval/synthetic-trace-pass.json
python3 tools/evaluate_trace.py --input eval/synthetic-trace-missing-audit.json  # 预期 FAIL
```

`tools/evaluate_trace.py` 只检查**已归一化**的记录：不会从 DSH 获取会话，也不会核实记录是否曾被篡改。因此这是教学评分辅助工具，而非可证明真实工具执行的审计系统。

## 二、从真实 DSH 轨迹提取的字段

| 原始事件 | 归一化格式 | 必需证据 |
|---|---|---|
| `skill` 工具返回 `<skill_content>` | `{"kind":"skill_load","name":"wireless-link-workflow"}` | 工具调用名及成功返回 |
| Bash CLI 调用 | `{"kind":"tool","action":"validate","status":"PASS","exit_code":0}` | 真实命令、stdout/exit code |
| 文件工具读取知识 | `{"kind":"file_read","action":"read-reference","path":"knowledge/wireless/throughput.md"}` | 确认读取成功 |
| 最终输出 | `{"kind":"final","status":"PASS"}` | 与 verifier/audit 结果一致 |

按时间顺序写入 `events` 数组，并标明 `task_type`。真实会话可补充 `trace_id`、`command`、`raw_event_ref`、`timestamp`、`source=REAL_DSH` 等字段供审阅。**不要把 synthetic 夹具改名为 real 交作业**。

## 三、评测能力

- Skill Load Coverage：需要的子 Skill 是否真的加载；多余加载数。
- Tool Use Compliance：需要的 CLI 是否真实运行（不能由自然语言替代）。
- Workflow Completeness/Order：validate→compute→verify→audit 是否齐全与有序。
- Verification Fidelity：坏报告 FAIL，正确报告 PASS；无工具为 NOT_RUN。
- Reference Precision：L4 和 L6 是否只读相关资料。
- Recovery Success：失败时最多两轮重算再审计。
- Premature Completion：没有验证、就写 PASS 的行为算错误。

## 四、推荐现场实验（需 DSH 环境）

A. 禁用 Bash：L8 必须标记 NOT_RUN，不得假装报告已执行。

B. 将 `wireless-capacity-audit` 设置为 `disable-model-invocation: true`：L8 需要明确表示 Skill 不可加载/无法完成，而不是绕过该要求假装调用成功。

C. 把 `fixtures/bad_report.json` 交给 L7：必须给出审计 FAIL 与具体错误，重算后再审计，不改源数据。

D. 多 Skill 混淆测试：提问只需容量的任务，不应无差别加载 L1–L8；综合任务应选择 L5+L7+L6。

### 注意

本地的 `plan` 与 synthetic trace 只能验证**协议和评分器**，不是“DSH 已成功触发全部 Skill”。
