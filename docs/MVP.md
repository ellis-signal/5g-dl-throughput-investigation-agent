# 5G 下行吞吐率根因调查 · 第一阶段 MVP 实现说明

配套文档：[后端 HLD](../../1-design/5g-dl-rca-backend-hld.md) · [前端设计](../../1-design/5g-dl-rca-frontend-design.md)

## 1. 交付范围

| 能力 | 状态 | 位置 |
|---|---|---|
| KPI 数据合同校验与窗口聚合 | ✅ | `src/wireless_lab/dl_kpi.py` |
| 香农标尺 / CQI 一致性 | ✅ | `src/wireless_lab/dl_model.py` |
| 四假设判定 + 处置建议目录 | ✅ | `src/wireless_lab/dl_evidence.py` |
| 账本组装 | ✅ | `src/wireless_lab/dl_rca.py` |
| 独立审计（另写一套实现） | ✅ | `src/wireless_lab/dl_audit.py` |
| Markdown 报告 | ✅ | `src/wireless_lab/dl_render.py` |
| CLI 4 个子命令 | ✅ | `src/wireless_lab/cli.py` |
| 只读 HTTP API + 静态托管 | ✅ | `backend/app.py` |
| 合成数据与注入规则 | ✅ | `tools/make_dl_dataset.py` |
| 前端联调（账本驱动） | ✅ | `frontend/app.js` |

不含：LLM 调用、trace 评测、多租户、鉴权、写操作。

## 2. 快速开始

```bash
cd 3-repo

# 1) 生成数据（可重复，seed 固定）
python tools/make_dl_dataset.py

# 2) 命令行跑一遍完整链路
python tools/wireless.py dl-validate    --input data/dl_cells_kpi.json
python tools/wireless.py dl-investigate --input data/dl_cells_kpi.json --output out/ledger.json
python tools/wireless.py dl-audit       --input data/dl_cells_kpi.json --ledger out/ledger.json --receipt out/receipt.json
python tools/wireless.py dl-render      --input data/dl_cells_kpi.json --cell NR-CELL-1002 --output out/report-1002.md --receipt out/receipt.json

# 3) 启动服务（前端 + API）
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8765
# 浏览器打开 http://127.0.0.1:8765/
```

> Windows 上用完整解释器路径，例如 `"D:\Program Files\Python310\python" -m uvicorn ...`；
> `python3` 在部分机器上指向 Microsoft Store 占位程序，会以退出码 49 失败。

`tools/wireless.py` 会自动把 `src/` 加入 `sys.path`，无需 `PYTHONPATH` 或 `pip install`。

## 3. 目录

```text
3-repo/
├── backend/app.py            FastAPI 路由与静态托管
├── data/dl_cells_kpi.json    4 小区 × 48 样本（合成）
├── src/wireless_lab/
│   ├── dl_kpi.py             合同校验 + 聚合 + 差值
│   ├── dl_model.py           香农期望吞吐 + CQI/SINR 表
│   ├── dl_evidence.py        四假设判定 + 建议目录
│   ├── dl_rca.py             账本组装 + PRB 缺失降级
│   ├── dl_audit.py           独立审计（不 import 判定模块）
│   ├── dl_render.py          Markdown 报告
│   └── dl_canonical.py       规范化 JSON 哈希
├── tools/make_dl_dataset.py  数据生成（注入规则前置）
├── tools/embed_ledger.py     离线账本嵌入前端
├── frontend/                 前端（API 优先，file:// 回退）
├── tests/test_dl_rca.py      17 项领域测试
└── out/                      运行产物（账本、回执、报告）
```

## 4. 数据流

```text
KPI JSON ──validate──> 样本
                      │
        baseline/incident 聚合 ──> 差值 + 香农期望
                      │
             四假设（必要条件 / 佐证）──> 判定 + 置信度
                      │
                  账本 ledger（cells[]
                      │              ├─> Markdown 报告
                      │              ├─> GET /api/ledger ──> 前端
                      └─> dl-audit：从原始字节重算 → 回执 PASS/FAIL
```

## 5. 注入规则（先于数据固定）

| 小区 | 故障 | 关键变化 | 干扰项 |
|---|---|---|---|
| NR-CELL-1001 | 覆盖 | RSRP −92→−108，SINR 14→8.5 | 用户数、PRB 不变 |
| NR-CELL-1002 | 干扰 | SINR 18→1.5，CQI 12→5，BLER +15 pp | RSRP 稳定（+0.4 dB） |
| NR-CELL-1003 | 拥塞 | PRB 42→97%，用户 30→130 | 无线指标稳定 |
| NR-CELL-1004 | 对照 | 各指标 ±1% 噪声 | 无 |

## 6. 实现要点

- **确定性**：无时间戳、无随机（数据生成固定 seed），同字节输入两次运行 `ledger_sha256` 相同。
- **哈希可跨语言**：`dl_canonical` 把 int/float 统一为 float 再序列化，
  避免浏览器 `JSON.stringify` 把 `24.0` 写成 `24` 导致回执哈希漂移（已由测试固化）。
- **判定与解释分离**：账本给结论，`dl_render` 只排版；前端不改判。
- **审计独立性**：`dl_audit.py` 自己实现均值/中位数/香农/阈值/判定，不 import `dl_kpi`、`dl_evidence`、`dl_model`。
- **缺失即不确定**：`omit_prb` 让"拥塞"假设的必要条件无法验证，结论强制降级为 `UNDETERMINED`，审计不可执行。

## 7. 验收证据

| 项 | 命令 | 结果 |
|---|---|---|
| 全量测试 | `python -m unittest discover -s tests` | 47 passed |
| 领域测试 | `python -m unittest tests.test_dl_rca` | 17 passed |
| 审计通过 | `dl-audit` | PASS，294 项检查，68 条证据 |
| 审计拦截篡改 | 改判定后 POST `/api/audit` | FAIL，报 `H1.verdict: expected REFUTED` |
| 前端联调 | 无头 Chrome | 账本渲染、切小区、审计、PRB 降级、报告导出全部通过，无脚本错误 |
| 响应式 | 1440 / 1024 / 390 | 无横向溢出 |

## 8. 已知限制

1. 数据为合成，结论正确性只对"注入规则"负责，不代表真实网络。
2. 未实现 trace 与 LLM 循环，因此没有 A/B/C 对照数据。
3. 未生成 JSON Schema 文件，合同由代码校验与单测保证。
4. 单进程、无鉴权、无并发压测，仅限本机只读演示。
5. 阈值是教学启发式，报告已显式声明，不可直接用于现网判决。