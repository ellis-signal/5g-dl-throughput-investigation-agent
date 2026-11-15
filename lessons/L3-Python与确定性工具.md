# L3 · 通过 Skill 运行 Python CLI

> **《人工智能的网络应用》** · Wireless Skill Lab v2 · 教师/学生两用讲义。
>
> **来源区分**：「教程原则」来自你上传的 Anthropic *Skill authoring best practices* [1]；「本 Lab」是我们重新实现的无线链路示例。DeepSeek Harness 的运行约束参照官方插件说明 [2][3]。所有离线计划/合成轨迹都不代表真实 DSH 工具运行。

## 教学目标

把自然语言推理与**确定性代码**分开，学习工具参数、标准输出 JSON、stderr、退出码与失败处理。能说明“查看代码”与“执行代码”的区别。

## 教程原则与原始例子

Anthropic 的 *Provide utility scripts*：预置、测试过的脚本比每轮让模型重写代码更可靠、更节省上下文。PDF 表单示例通过 `analyze_form.py` 提取，再用 `validate_boxes.py` 检查结果。教程特别强调：指令应明确写 `Run` 还是 `See`。

## 本 Lab 文件和 CLI

入口：[L3 SKILL.md](../.dsh/skills/wireless-capacity-code/SKILL.md)。代码被统一为 `src/wireless_lab/capacity.py`，由 `tools/wireless.py` 暴露；不再放一份 L3 私有计算脚本。

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
