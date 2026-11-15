---
name: wireless-link-workflow
description: 按 validate、compute、verify 的固定顺序批量处理无线链路测量 JSON 数据；用户请求批量计算、生成报告或验证报告时使用。
user-invocable: true
disable-model-invocation: false
---

# L5 — 多步工作流

输入无线链路测量 JSON 数据：`data/links.json`（只读），输出：`outputs/link_report.json`。
输入和输出合同：[links-v1 schema](../../../contracts/links-v1.schema.json)、[report-v1 schema](../../../contracts/report-v1.schema.json)。

## 必须按顺序执行的三个步骤

- [ ] 校验输入：

```bash
python3 tools/wireless.py validate --input data/links.json
```

- [ ] 计算写入 `UNVERIFIED` 报告：

```bash
python3 tools/wireless.py compute --input data/links.json --output outputs/link_report.json
```

- [ ] 验证文件并保存独立验证回执：

```bash
python3 tools/wireless.py verify --input data/links.json --report outputs/link_report.json --receipt outputs/verify_receipt.json
```

必须以当前任务的实际输入路径替换示例值；以上命令均从项目根目录运行，Python 3.9+ 标准库。

## 完成条件和错误处理

- 只在第三步真实退出 0 且 stdout `PASS` 后写“验证通过”；中途 FAIL 不能跳过。
- 生成的 `report.json` 永远标记 `UNVERIFIED`，**只有独立 receipt** 可记录验证结果。
- 退出码 1 = 验证未通过，2 = 输入/文件/参数错误；最多重算两次，不修改源数据。
- Bash 不可用时报告 `NOT_RUN`，不要捏造 PASS。

示例：`/wireless-link-workflow 请处理 data/links.json，输出可核验的 JSON。`
