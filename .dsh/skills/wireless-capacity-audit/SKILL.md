---
name: wireless-capacity-audit
description: 对链路测量报告和数据，执行独立重算、审计，在审计失败时，有限重试；用户要求审计检查报告、验证输出、错误注入或恢复时使用。
user-invocable: true
disable-model-invocation: false
---

# L7 — 独立 Verifier 与恢复循环

报告合同：[report-v1 schema](../../../contracts/report-v1.schema.json)；状态合同：[execution-status](../../../contracts/execution-status.md)。

## 先执行真实审计
```bash
python3 tools/wireless.py audit --input data/links.json --report outputs/link_report.json --receipt outputs/audit_receipt.json
```

## 审计失败的处理
1. 读取审计工具返回的错误（stdout JSON 或 stderr）。
2. **最多重试两次**：使用本项目 `compute` CLI 从只读原始数据重新生成报告（不需要假设已加载其他 Skill）：
```bash
python3 tools/wireless.py compute --input data/links.json --output outputs/link_report.json
```
3. 再运行 `audit`；只有真实收到 `PASS` 才能宣布审计成功。
4. 若源输入无效、工具不可用、重试耗尽：输出 `FAIL` 或 `NOT_RUN`，说明具体原因。

## 教学反例
```bash
python3 tools/wireless.py audit --input data/links.json --report fixtures/bad_report.json
```
预期 `FAIL`（exit code 1）：错误容量、缺少 case、数据摘要不一致。

验证的对象是数值/文件合同；审计通过**不**证明真实系统适合 AWGN 假设。
禁止改原始数据、禁止修改 Verifier 迎合错误报告。

示例：`/wireless-capacity-audit 先审计坏报告，再恢复并重新审计。`
