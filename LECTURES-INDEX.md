# Wireless Skill Lab v2｜L1–L8 讲义索引

讲义与 `.dsh/skills/` 完全同步，所有旧版脚本路径均替换为统一 `tools/wireless.py` CLI。

| 讲次 | 讲义 | 概念 |
|---|---|---|
| L1 | [L1-最小Skill与自包含指令](lessons/L1-最小Skill与自包含指令.md) | 最小 Skill / YAML |
| L2 | [L2-模板示例与共享知识](lessons/L2-模板示例与共享知识.md) | 模板与 Examples / 知识分离 |
| L3 | [L3-Python与确定性工具](lessons/L3-Python与确定性工具.md) | Script / Tool |
| L4 | [L4-条件分支与知识选择](lessons/L4-条件分支与知识选择.md) | 分支 / Selective loading |
| L5 | [L5-多步骤可验证工作流](lessons/L5-多步骤可验证工作流.md) | Workflow / Artifacts |
| L6 | [L6-运维知识导航与证据](lessons/L6-运维知识导航与证据.md) | Knowledge / RCA |
| L7 | [L7-独立审计与恢复](lessons/L7-独立审计与恢复.md) | Verifier / Feedback |
| L8 | [L8-跨Skill编排与评测](lessons/L8-跨Skill编排与评测.md) | Orchestration / Evaluation |

## 建议授课
L1–L3 第一讲，L4–L6 第二讲，L7–L8 第三讲。每讲均要求工具轨迹、正确结果和一个失败/边界测试。

## 一键验证
```bash
bash run-demo.sh
python3 -m unittest discover -s tests -v
```

详细教学评分见 [TEACHER-GUIDE.md](TEACHER-GUIDE.md)。
