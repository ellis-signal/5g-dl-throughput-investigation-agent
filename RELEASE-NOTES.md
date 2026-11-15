# Wireless Skill Lab v2 — Release Notes

## 完成情况（2026-10-31）

- **Phase A: 已实现** —— 共享无线知识拆分、L2 消除「沿用 L1」隐式依赖、L4/L6 知识按需加载。
- **Phase B: 已实现** —— Python 标准库计算/路由/批处理/独立审计、统一 CLI、源文件 SHA256、JSON Schema、验证回执、错误注入。
- **Phase C: 已实现可交付资源** —— L8 的模型侧跨 Skill 加载指令、两种 profile 配置、离线执行计划和轨迹评分工具。**模型运行时的 DSH 实际效果尚未在本环境现场验证**，不作成功声明。
- **Phase D: 已实现** —— 八讲 v2 讲义、教师手册、评测说明、30 项本地自动化测试、演示脚本。

## 本地验证

从仓库根目录运行：

```bash
bash run-demo.sh
python3 -m unittest discover -s tests -v
```

已验证容量 20MHz 15dB ≈100.556153 Mbps；4 条链路的 validate/compute/verify/audit 正常 PASS；`fixtures/bad_report.json` 返回 FAIL；缺审计的 synthetic trace 返回 FAIL；30 项回归测试通过。

**证据边界**：不存在真实 DSH 会话日志。`tools/evaluate_trace.py` 的 synthetic 测试只能证明评分规则可执行，而不是已验证 L8 在真实 Harness 中成功加载其他 Skill。

## 兼容与迁移

v1 目录中的 `scripts/capacity.py` 等私有脚本改由 `tools/wireless.py` 统一 CLI 替代。项目包为根据设计包进行的重建式迁移，而非上一版仓库的原地修改。详细迁移见 `docs/IMPLEMENTATION.md`。
