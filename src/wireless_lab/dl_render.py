"""Render a ledger cell as a deterministic Markdown report."""
from .dl_evidence import THRESHOLD_NOTES

VERDICT_CN = {'SUPPORTED': '成立', 'REFUTED': '已否定', 'INCONCLUSIVE': '不可判定'}
DIRECTION_CN = {'supports': '支持', 'refutes': '否定', 'neutral': '中性'}


def _num(value, digits=2):
    if value is None:
        return '—'
    if isinstance(value, int):
        return str(value)
    return f'{value:.{digits}f}'


def _signed(value, digits=2):
    if value is None:
        return '—'
    return f'{value:+.{digits}f}'


def render_cell(cell, dataset=None, receipt=None):
    lines = []
    add = lines.append
    cause = cell['dominant_cause']
    add(f"# 5G 下行吞吐率根因调查 · {cell['cell_id']}")
    add('')
    if cell.get('sector'):
        add(f"**场景**：{cell['sector']}  ")
    if cell.get('complaint'):
        add(f"**投诉**：{cell['complaint']}  ")
    status = '已审计 PASS（报告可交付）' if receipt and receipt['status'] == 'PASS' \
        else 'UNVERIFIED（未经独立审计，不可交付）'
    add(f"**结论**：{cause['code']}（{cause['label']}），置信度 {cause['confidence']:.2f}  ")
    add(f"**验证状态**：{status}  ")
    add('')

    if dataset:
        add('## 1. 数据来源')
        add('')
        add('| 项 | 值 |')
        add('|---|---|')
        add(f"| 数据集 | `{dataset.get('dataset_id')}` |")
        add(f"| 方法版本 | `{cell.get('method_version', 'dl-rca-v1')}` |")
        source = (dataset.get('source') or {})
        add(f"| 源文件 | `{source.get('path', '—')}` |")
        add(f"| SHA-256 | `{source.get('sha256', '—')}` |")
        add('')

    add('## 2. 指标对比')
    add('')
    add('| 指标 | 基线 | 事发 | 变化 |')
    add('|---|---:|---:|---:|')
    base, inc, sig = cell['baseline'], cell['incident'], cell['signals']
    rows = [
        ('下行吞吐', f"{_num(base['dl_throughput_mbps_mean'], 1)} Mbps",
         f"{_num(inc['dl_throughput_mbps_mean'], 1)} Mbps", f"{sig['throughput_delta_pct']:+.2f}%"),
        ('RSRP 中位数', f"{_num(base['rsrp_dbm_median'], 1)} dBm",
         f"{_num(inc['rsrp_dbm_median'], 1)} dBm", f"{sig['rsrp_delta_db']:+.2f} dB"),
        ('SINR 中位数', f"{_num(base['sinr_db_median'], 1)} dB",
         f"{_num(inc['sinr_db_median'], 1)} dB", f"{sig['sinr_delta_db']:+.2f} dB"),
        ('CQI 均值', _num(base['cqi_mean'], 1), _num(inc['cqi_mean'], 1), _signed(sig['cqi_delta'], 1)),
        ('PRB 利用率', f"{_num(base['prb_utilization_pct_mean'], 1)}%",
         f"{_num(inc['prb_utilization_pct_mean'], 1)}%", f"{sig['prb_delta_pp']:+.1f} pp"),
        ('并发用户', _num(base['active_users_mean'], 1), _num(inc['active_users_mean'], 1),
         f"{sig['users_ratio']:.2f}×"),
        ('BLER', f"{_num(base['bler_pct_mean'], 1)}%", f"{_num(inc['bler_pct_mean'], 1)}%",
         f"{sig['bler_delta_pp']:+.1f} pp"),
    ]
    for row in rows:
        add('| ' + ' | '.join(row) + ' |')
    add('')

    radio = cell['radio']
    add(f"**香农标尺**：同 SINR 期望吞吐 {_num(radio['expected_throughput_mbps'], 1)} Mbps，"
        f"实际/期望 = {radio['actual_to_expected_ratio']:.2f}。{radio['interpretation']}。")
    add('')

    add('## 3. 假设判定')
    add('')
    add('| 假设 | 判定 | 置信度 | 依据 |')
    add('|---|---|---:|---|')
    for hypothesis in cell['hypotheses']:
        add(f"| {hypothesis['hypothesis_id']} {hypothesis['label']} | "
            f"{VERDICT_CN.get(hypothesis['verdict'], hypothesis['verdict'])} | "
            f"{hypothesis['confidence']:.2f} | {hypothesis['basis']} |")
    add('')

    add('## 4. 证据明细')
    add('')
    for hypothesis in cell['hypotheses']:
        add(f"### {hypothesis['hypothesis_id']} · {hypothesis['label']}")
        add('')
        add(f"{hypothesis['statement']}。判定：**{VERDICT_CN.get(hypothesis['verdict'])}**"
            f"（必要条件 {', '.join(hypothesis['gate_checks'])}）。")
        add('')
        add('| 证据 ID | 指标 | 基线 | 事发 | 变化 | 阈值 | 判定 |')
        add('|---|---|---:|---:|---:|---|---|')
        for check in hypothesis['checks']:
            add(f"| `{check['evidence_id']}` | {check['metric']} | {_num(check['baseline'])} | "
                f"{_num(check['incident'])} | {_signed(check['delta'])} | {check['threshold']} | "
                f"{DIRECTION_CN.get(check['direction'], check['direction'])} |")
        add('')

    add('## 5. 缺失证据')
    add('')
    gaps = cell.get('missing_evidence') or []
    for gap in gaps:
        add(f'- {gap}')
    if not gaps:
        add('- 无')
    add('')

    add('## 6. 处置建议')
    add('')
    recs = cell.get('recommendations') or []
    if not recs:
        add('- 当前结论下不建议做任何网络变更。')
    for rec in recs:
        approval = '需变更审批' if rec['requires_change_approval'] else '只读操作，无需变更审批'
        add(f"**{rec['recommendation_id']} · {rec['area']}**（{approval}）")
        add('')
        add(f"- 动作：{rec['action']}")
        add(f"- 前提：{rec['precondition']}")
        add(f"- 预期：{rec['expected_effect']}")
        add(f"- 验证指标：{rec['verification_kpi']}")
        add(f"- 风险：{rec['risk']}")
        add(f"- 回退：{rec['rollback']}")
        add('')

    add('## 7. 阈值口径')
    add('')
    add('以下阈值是教学启发式，不是 3GPP 规范值；每条证据都使用同一份口径。')
    add('')
    add('| 阈值 | 取值 | 说明 |')
    add('|---|---:|---|')
    for key, note in THRESHOLD_NOTES.items():
        add(f"| `{key}` | — | {note} |")
    add('')

    if receipt:
        add('## 8. 审计回执')
        add('')
        add(f"- 状态：**{receipt['status']}**")
        add(f"- 审计版本：`{receipt['audit_version']}`")
        add(f"- 账本哈希：`{receipt['ledger_sha256']}`")
        add(f"- 检查项：{len(receipt['checks'])} 项，失败 {receipt['error_count']} 项")
        for error in receipt['errors'][:10]:
            add(f"  - {error}")
        add('')
    return '\n'.join(lines).rstrip() + '\n'