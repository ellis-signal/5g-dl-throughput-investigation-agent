"""Review aligned synthetic KPI windows using declared teaching thresholds."""

THRESHOLDS = {
    'drop_pct': 10, 'rsrp_drop_db': 6, 'rsrp_stable_db': 3,
    'sinr_drop_db': 5, 'cqi_drop': 2, 'bler_rise_pp': 5,
    'prb_high_pct': 85, 'prb_rise_pp': 15, 'users_rise_pct': 35,
}


def review(case, delta):
    incident = case['incident']
    fields = {
        'E1': ('吞吐变化 (%)', delta['throughput_change_percent']),
        'E2': ('RSRP变化 (dB)', delta['rsrp_dbm_median']),
        'E3': ('SINR变化 (dB)', delta['sinr_db_median']),
        'E4': ('CQI变化', delta['cqi_mean']),
        'E5': ('事发PRB (%)', incident.get('prb_utilization_pct_mean')),
        'E6': ('PRB变化 (百分点)', delta['prb_utilization_pct_mean']),
        'E7': ('活跃用户数变化 (%)', delta['users_change_percent']),
        'E8': ('BLER变化 (百分点)', delta['bler_pct_mean']),
    }
    evidence = {k: {'metric': name, 'value': value} for k, (name, value) in fields.items()}
    t = THRESHOLDS
    rules = {
        'COVERAGE': [
            ('E2', 'RSRP下降至少6 dB', lambda x: x <= -t['rsrp_drop_db']),
            ('E3', 'SINR下降至少5 dB', lambda x: x <= -t['sinr_drop_db']),
        ],
        'INTERFERENCE': [
            ('E2', 'RSRP变化绝对值至多3 dB', lambda x: abs(x) <= t['rsrp_stable_db']),
            ('E3', 'SINR下降至少5 dB', lambda x: x <= -t['sinr_drop_db']),
            ('E4', 'CQI下降至少2', lambda x: x <= -t['cqi_drop']),
            ('E8', 'BLER增加至少5个百分点', lambda x: x >= t['bler_rise_pp']),
        ],
        'CONGESTION': [
            ('E5', '事发PRB至少85%', lambda x: x >= t['prb_high_pct']),
            ('E6', 'PRB增加至少15个百分点', lambda x: x >= t['prb_rise_pp']),
            ('E7', '活跃用户数增加至少35%', lambda x: x >= t['users_rise_pct']),
        ],
    }
    hypotheses = {}
    for label, ruleset in rules.items():
        checks = []
        for key, criterion, matches in ruleset:
            value = fields[key][1]
            status = '缺失' if value is None else ('支持' if matches(value) else '削弱')
            checks.append({'evidence': key, 'criterion': criterion, 'status': status})
        hypotheses[label] = checks

    candidates = [label for label, checks in hypotheses.items()
                  if all(check['status'] == '支持' for check in checks)]
    missing = [key for key, (_, value) in fields.items() if value is None]
    drop = fields['E1'][1]
    label = 'INSUFFICIENT'
    if drop is not None and drop > -t['drop_pct']:
        label = 'NORMAL'
        reason = '吞吐变化未达到本实验异常门槛（E1）。'
    elif missing:
        reason = '关键观测缺失，先补齐对应窗口再判断。'
    elif len(candidates) == 1:
        label = candidates[0]
        reason = '该方向满足本实验的组合条件，可优先复核。'
    elif candidates:
        reason = '同时存在多个候选方向，需要分时或分区复核。'
    else:
        reason = '已观测指标尚未支持明确方向，需要补充其他观测。'
    next_steps = {
        'NORMAL': '复查窗口对齐，并继续观察吞吐趋势。',
        'COVERAGE': '对齐邻区窗口，查看小区边缘RSRP分布和覆盖变化。',
        'INTERFERENCE': '对比邻区同窗SINR、BLER及可用干扰测量。',
        'CONGESTION': '按时段核查调度队列、负荷与单用户吞吐。',
        'INSUFFICIENT': '补齐缺失指标，或按时段拆分窗口并核查回传时延和丢包。',
    }
    return {'label': label, 'reason': reason, 'next_step': next_steps[label],
            'candidates': candidates, 'missing': missing, 'evidence': evidence,
            'hypotheses': hypotheses}
