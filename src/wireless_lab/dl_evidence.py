"""Evidence engine: turn KPI deltas into per-hypothesis verdicts.

Rules are deterministic and readable on purpose. Every threshold is a teaching
heuristic, not a 3GPP/IEEE requirement; the report repeats that caveat and the
audit re-derives the same verdicts with an independent implementation.
"""

METHOD_VERSION = 'dl-rca-v1'

THRESHOLDS = {
    'rsrp_weak_dbm': -105.0,
    'rsrp_drop_db': 3.0,
    'rsrp_stable_db': 3.0,
    'sinr_drop_db': 4.0,
    'sinr_drop_corroborating_db': 2.0,
    'cqi_drop': 2.0,
    'bler_rise_pp': 5.0,
    'prb_congested_pct': 85.0,
    'users_growth_ratio': 1.5,
    'per_user_drop_ratio': 0.6,
    'degradation_pct': 10.0,
    'cqi_residual_limit': 2.0,
    'throughput_to_expected_low': 0.55,
}

THRESHOLD_NOTES = {
    'rsrp_weak_dbm': 'RSRP < -105 dBm；教学阈值，不是 3GPP 规定的弱覆盖门限',
    'rsrp_drop_db': '相对基线下降 >= 3 dB 视为覆盖变化',
    'rsrp_stable_db': '|ΔRSRP| <= 3 dB 视为覆盖未变化',
    'sinr_drop_db': 'ΔSINR <= -4 dB 视为干扰显著恶化',
    'cqi_drop': 'ΔCQI <= -2 视为链路质量下降',
    'bler_rise_pp': 'BLER 抬升 >= 5 个百分点',
    'prb_congested_pct': 'PRB 利用率 >= 85% 视为资源紧张',
    'users_growth_ratio': '并发用户增长 >= 1.5 倍',
    'degradation_pct': '小区下行吞吐下降 >= 10% 才判定为劣化事件',
}

CAUSE_LABELS = {
    'COVERAGE_INSUFFICIENCY': '无线覆盖不足',
    'INTERFERENCE': '信号干扰',
    'RESOURCE_CONGESTION': '小区资源拥塞',
    'NO_SIGNIFICANT_DEGRADATION': '无显著劣化',
    'UNDETERMINED': '现有证据不足以判定',
}

MISSING_EVIDENCE = {
    'H1': [
        '路测/众包 RSRP 与 TA 分布（按小时对齐）',
        '同站邻区同窗口 RSRP/SINR 对照',
        '上行 RSRP 与 PUSCH 功率余量',
        '切换/重建立统计与覆盖空洞的时段相关性',
    ],
    'H2': [
        '上行 RSSI/底噪按小时趋势',
        '带宽内干扰频谱分布',
        'PCI/mod-3 复用距离与邻区测量报告',
        '大气波导/远端干扰的时间与天气相关性',
        'MR 级 SINR 分布（而非仅小区中位数）',
    ],
    'H3': [
        '每用户 PRB 占用与调度 RB 数分布',
        'QoS 流数与业务类型构成',
        '回传/传输利用率与丢包',
        '调度器队列时延与丢弃计数',
    ],
    'H4': [
        '回传与核心网时延/丢包',
        'UPF/服务器侧吞吐与限速策略',
        '终端能力（CA、MIMO 层数）与 CQI 上报异常',
        '同一时段应用侧指标',
    ],
}

DISCRIMINATING_TESTS = {
    'H1': {
        'test': '同站邻区同窗口 RSRP/SINR 对照',
        'read_only': True,
        'expected_if_true': '仅目标扇区 RSRP 同步下降，邻区保持稳定',
    },
    'H2': {
        'test': '上行 RSSI 底噪与频域干扰扫描',
        'read_only': True,
        'expected_if_true': '底噪抬升 >= 3 dB，且与业务量变化不相关',
    },
    'H3': {
        'test': 'PRB 利用率与并发用户数归一化对比',
        'read_only': True,
        'expected_if_true': 'PRB 接近饱和，每用户吞吐随并发用户数上升而下降',
    },
    'H4': {
        'test': '同窗口端到端吞吐/时延分解',
        'read_only': True,
        'expected_if_true': '空口 KPI 正常但端到端吞吐或时延异常',
    },
}

RECOMMENDATIONS = {
    'COVERAGE_INSUFFICIENCY': [
        {
            'recommendation_id': 'R1',
            'area': '无线参数优化',
            'action': '按扇区核查天线下倾角/方位角，每次以 0.5–1° 步进调整，单次只改一个扇区',
            'precondition': '确认劣化由覆盖变化引起，且邻区未受同等影响',
            'expected_effect': 'RSRP 中位数回升，SINR 与 CQI 随之改善',
            'verification_kpi': 'RSRP p10、SINR 中位数、每用户下行吞吐',
            'risk': '过度下压会造成越区覆盖与邻区干扰',
            'rollback': '恢复原下倾角/方位角配置',
            'requires_change_approval': True,
        },
        {
            'recommendation_id': 'R2',
            'area': '无线参数优化',
            'action': '核查 SSB/PDSCH 功率配置与波束方向，确认功率余量后再考虑功率偏置',
            'precondition': '功率余量充足且覆盖下降不是由功率配置变更导致',
            'expected_effect': '边缘 RSRP 提升，弱覆盖比例下降',
            'verification_kpi': 'RSRP 分布、PUSCH 功率余量、邻区干扰抬升',
            'risk': '提升功率会抬高对邻区干扰',
            'rollback': '恢复原功率配置',
            'requires_change_approval': True,
        },
        {
            'recommendation_id': 'R3',
            'area': '覆盖规划',
            'action': '若参数调整无法闭合覆盖空洞，进入规划流程评估新增站点/RRH 或调整邻区承担',
            'precondition': '路测确认存在持续性覆盖空洞',
            'expected_effect': '覆盖与容量同步改善',
            'verification_kpi': '弱覆盖采样占比、切换成功率',
            'risk': '投资与工期较长，需容量与站址评估',
            'rollback': '规划方案审批前不实施',
            'requires_change_approval': True,
        },
    ],
    'INTERFERENCE': [
        {
            'recommendation_id': 'R1',
            'area': '干扰治理',
            'action': '核查 PCI/mod-3 与 SSB 波束冲突，必要时在变更窗口内做 PCI 重规划',
            'precondition': '干扰与特定邻区/PCI 组合相关',
            'expected_effect': 'SINR 与 CQI 恢复，BLER 回落',
            'verification_kpi': 'SINR 中位数、CQI、BLER、每用户吞吐',
            'risk': 'PCI 变更会引起短暂切换与重建',
            'rollback': '回退 PCI 规划脚本',
            'requires_change_approval': True,
        },
        {
            'recommendation_id': 'R2',
            'area': '干扰治理',
            'action': '执行上行 RSSI 底噪扫描，定位外部干扰源（非法直放站/设备），联合排查处置',
            'precondition': '底噪在无业务时段仍抬升',
            'expected_effect': '消除外部干扰后 SINR 回升',
            'verification_kpi': '上行 RSSI、SINR、BLER',
            'risk': '涉及外部单位协调，周期不可控',
            'rollback': '不涉及网络配置变更',
            'requires_change_approval': False,
        },
        {
            'recommendation_id': 'R3',
            'area': '干扰治理',
            'action': '核查 TDD 时隙配比与远端干扰特征（大气波导），启用相应干扰抑制特性',
            'precondition': '干扰呈时段性且与天气/传播条件相关',
            'expected_effect': '远端干扰时段 SINR 提升',
            'verification_kpi': '分时段 SINR、上行干扰电平',
            'risk': '特性开关可能影响容量与兼容性',
            'rollback': '关闭该特性并恢复原时隙配比',
            'requires_change_approval': True,
        },
        {
            'recommendation_id': 'R4',
            'area': '调度与链路自适应',
            'action': '评估 ICIC/协调调度与 MCS 保守回退的收益与容量代价，作为过渡手段',
            'precondition': '干扰源短期无法消除',
            'expected_effect': 'BLER 下降、稳定性提升，峰值吞吐可能下降',
            'verification_kpi': 'BLER、CQI 波动、边缘用户吞吐',
            'risk': '过度保守会牺牲峰值速率',
            'rollback': '恢复原调度/链路自适应参数',
            'requires_change_approval': True,
        },
    ],
    'RESOURCE_CONGESTION': [
        {
            'recommendation_id': 'R1',
            'area': '资源调度',
            'action': '执行负荷均衡：调整移动性/重选参数，把边缘用户迁往同覆盖低负荷小区',
            'precondition': '邻区存在可用容量且覆盖重叠充分',
            'expected_effect': '目标小区 PRB 利用率下降，每用户吞吐回升',
            'verification_kpi': 'PRB 利用率、并发用户数、每用户吞吐、切换成功率',
            'risk': '参数过激会引起乒乓切换',
            'rollback': '恢复原移动性参数',
            'requires_change_approval': True,
        },
        {
            'recommendation_id': 'R2',
            'area': '容量扩容',
            'action': '评估新增载波/扇区或开启 CA/双连接分流（规划级，需容量与站址评估）',
            'precondition': '忙时 PRB 长期饱和且负荷均衡无法缓解',
            'expected_effect': '可用 PRB 增加，忙时吞吐上限提升',
            'verification_kpi': '忙时 PRB 利用率、小区下行吞吐、用户感知速率',
            'risk': '投资较大，需频谱与站址资源',
            'rollback': '规划方案审批前不实施',
            'requires_change_approval': True,
        },
        {
            'recommendation_id': 'R3',
            'area': '资源调度',
            'action': '按业务分级调整调度权重与准入策略，保障 VoNR 与关键业务，抑制大流量抢占',
            'precondition': '业务构成显示少量用户占用大量 PRB',
            'expected_effect': '关键业务时延与丢包改善，公平性提升',
            'verification_kpi': '分 QoS 流吞吐、调度队列时延、丢包率',
            'risk': '限速策略可能影响部分用户体验',
            'rollback': '恢复原调度与准入策略',
            'requires_change_approval': True,
        },
        {
            'recommendation_id': 'R4',
            'area': '传输核查',
            'action': '核查回传/传输带宽与丢包，排除传输瓶颈与无线拥塞叠加',
            'precondition': 'PRB 未饱和但吞吐仍低，或传输利用率接近上限',
            'expected_effect': '避免把传输瓶颈误判为无线拥塞',
            'verification_kpi': '回传利用率、传输丢包、端到端时延',
            'risk': '仅观测，无变更风险',
            'rollback': '不涉及配置变更',
            'requires_change_approval': False,
        },
    ],
    'NO_SIGNIFICANT_DEGRADATION': [],
    'UNDETERMINED': [],
}


def _fmt(value):
    return f'{value:.2f}' if isinstance(value, float) else str(value)


def _evidence(cell_id, hid, check_id, metric, baseline, incident, delta, threshold, direction, observation):
    return {
        'evidence_id': f'EV-{cell_id}-{hid}-{check_id}',
        'check_id': check_id,
        'hypothesis_id': hid,
        'metric': metric,
        'baseline': baseline,
        'incident': incident,
        'delta': delta,
        'threshold': threshold,
        'direction': direction,
        'observation': observation,
    }


def _decide(checks, gate_ids):
    """Gate = necessary conditions; corroboration only scales confidence.

    A failed gate refutes the hypothesis outright, which is what stops a cell
    with a 16 dB RSRP drop from being labelled 'interference'.
    """
    gates = [c for c in checks if c['check_id'] in gate_ids]
    failed = [c for c in gates if c['direction'] != 'supports']
    if failed:
        reason = '；'.join(c['observation'] for c in failed)
        return {
            'verdict': 'REFUTED',
            'confidence': 0.9,
            'basis': '必要条件不满足：' + reason,
            'gate_passed': False,
        }
    corroborating = [
        c for c in checks
        if c['check_id'] not in gate_ids and c['direction'] != 'neutral'
    ]
    if not corroborating:
        return {'verdict': 'SUPPORTED', 'confidence': 0.6,
                'basis': '必要条件满足；缺少独立佐证指标', 'gate_passed': True}
    support = sum(1 for c in corroborating if c['direction'] == 'supports')
    share = support / len(corroborating)
    if share < 0.5:
        return {'verdict': 'INCONCLUSIVE', 'confidence': 0.5,
                'basis': f'必要条件满足，但仅 {support}/{len(corroborating)} 项佐证支持，证据冲突',
                'gate_passed': True}
    return {'verdict': 'SUPPORTED', 'confidence': round(0.6 + 0.35 * share, 2),
            'basis': f'必要条件满足，{support}/{len(corroborating)} 项佐证一致',
            'gate_passed': True}


def build_hypotheses(cell_id, baseline, incident, delta, radio):
    """Four hypothesis cards; H4 is the residual 'not radio' explanation."""
    t = THRESHOLDS
    rsrp_delta = delta['rsrp_delta_db']
    sinr_delta = delta['sinr_delta_db']
    cqi_delta = delta['cqi_delta']
    rsrp_incident = incident['rsrp_dbm_median']
    prb_incident = incident['prb_utilization_pct_mean']
    bler_delta = delta['bler_delta_pp']
    users_ratio = delta['users_ratio']
    per_user_ratio = delta['per_user_throughput_ratio']
    ratio = radio['actual_to_expected_ratio']

    h1 = [
        _evidence(cell_id, 'H1', 'C1', 'rsrp_dbm_median', baseline['rsrp_dbm_median'], rsrp_incident,
                  rsrp_delta, f'< {t["rsrp_weak_dbm"]:.0f} dBm',
                  'supports' if rsrp_incident < t['rsrp_weak_dbm'] else 'refutes',
                  f'incident RSRP {_fmt(rsrp_incident)} dBm ' +
                  ('低于' if rsrp_incident < t['rsrp_weak_dbm'] else '不低于') + '弱覆盖门限'),
        _evidence(cell_id, 'H1', 'C2', 'rsrp_delta_db', baseline['rsrp_dbm_median'], rsrp_incident,
                  rsrp_delta, f'<= -{t["rsrp_drop_db"]:.0f} dB',
                  'supports' if rsrp_delta <= -t['rsrp_drop_db'] else 'refutes',
                  f'RSRP 变化 {rsrp_delta:+.2f} dB，' +
                  ('达到' if rsrp_delta <= -t['rsrp_drop_db'] else '未达到') + '覆盖劣化幅度'),
        _evidence(cell_id, 'H1', 'C3', 'sinr_db_median', baseline['sinr_db_median'], incident['sinr_db_median'],
                  sinr_delta, f'<= -{t["sinr_drop_corroborating_db"]:.0f} dB',
                  'supports' if sinr_delta <= -t['sinr_drop_corroborating_db'] else 'neutral',
                  f'SINR 变化 {sinr_delta:+.2f} dB（覆盖下降的伴随效应，非独立判据）'),
        _evidence(cell_id, 'H1', 'C4', 'cqi_mean', baseline['cqi_mean'], incident['cqi_mean'],
                  cqi_delta, f'<= -{t["cqi_drop"]:.0f}',
                  'supports' if cqi_delta <= -t['cqi_drop'] else 'neutral',
                  f'CQI 变化 {cqi_delta:+.2f}（调制阶数随覆盖下降）'),
    ]

    h2 = [
        _evidence(cell_id, 'H2', 'C1', 'rsrp_delta_db', baseline['rsrp_dbm_median'], rsrp_incident,
                  rsrp_delta, f'|Δ| <= {t["rsrp_stable_db"]:.0f} dB',
                  'supports' if abs(rsrp_delta) <= t['rsrp_stable_db'] else 'refutes',
                  f'RSRP 变化 {rsrp_delta:+.2f} dB，' +
                  ('覆盖稳定' if abs(rsrp_delta) <= t['rsrp_stable_db'] else '覆盖同时变化，干扰假设被削弱')),
        _evidence(cell_id, 'H2', 'C2', 'sinr_db_median', baseline['sinr_db_median'], incident['sinr_db_median'],
                  sinr_delta, f'<= -{t["sinr_drop_db"]:.0f} dB',
                  'supports' if sinr_delta <= -t['sinr_drop_db'] else 'refutes',
                  f'SINR 变化 {sinr_delta:+.2f} dB，' +
                  ('达到' if sinr_delta <= -t['sinr_drop_db'] else '未达到') + '干扰恶化判据'),
        _evidence(cell_id, 'H2', 'C3', 'cqi_mean', baseline['cqi_mean'], incident['cqi_mean'],
                  cqi_delta, f'<= -{t["cqi_drop"]:.0f}',
                  'supports' if cqi_delta <= -t['cqi_drop'] else 'neutral',
                  f'CQI 变化 {cqi_delta:+.2f}（链路质量下降的直接证据）'),
        _evidence(cell_id, 'H2', 'C4', 'prb_utilization_pct_mean', baseline['prb_utilization_pct_mean'],
                  prb_incident, delta['prb_delta_pp'], f'< {t["prb_congested_pct"]:.0f}%',
                  'supports' if prb_incident < t['prb_congested_pct'] else 'neutral',
                  f'PRB 利用率 {_fmt(prb_incident)}%，' +
                  ('未饱和，排除拥塞主导' if prb_incident < t['prb_congested_pct'] else '接近饱和，需与拥塞假设竞争')),
        _evidence(cell_id, 'H2', 'C5', 'bler_pct_mean', baseline['bler_pct_mean'], incident['bler_pct_mean'],
                  bler_delta, f'>= +{t["bler_rise_pp"]:.0f} pp',
                  'supports' if bler_delta >= t['bler_rise_pp'] else 'neutral',
                  f'BLER 变化 {bler_delta:+.2f} pp（重传上升伴随干扰）'),
    ]

    h3 = [
        _evidence(cell_id, 'H3', 'C1', 'prb_utilization_pct_mean', baseline['prb_utilization_pct_mean'],
                  prb_incident, delta['prb_delta_pp'], f'>= {t["prb_congested_pct"]:.0f}%',
                  'supports' if prb_incident >= t['prb_congested_pct'] else 'refutes',
                  f'PRB 利用率 {_fmt(prb_incident)}%，' +
                  ('达到' if prb_incident >= t['prb_congested_pct'] else '未达到') + '资源紧张门限'),
        _evidence(cell_id, 'H3', 'C2', 'active_users_mean', baseline['active_users_mean'],
                  incident['active_users_mean'], users_ratio, f'>= {t["users_growth_ratio"]:.1f}x',
                  'supports' if users_ratio >= t['users_growth_ratio'] else 'refutes',
                  f'并发用户变化 {users_ratio:.2f}x，' +
                  ('达到' if users_ratio >= t['users_growth_ratio'] else '未达到') + '负荷增长判据'),
        _evidence(cell_id, 'H3', 'C3', 'sinr_db_median', baseline['sinr_db_median'], incident['sinr_db_median'],
                  sinr_delta, f'> -{t["sinr_drop_db"]:.0f} dB 且 ΔRSRP > -{t["rsrp_stable_db"]:.0f} dB',
                  'supports' if (sinr_delta > -t['sinr_drop_db'] and rsrp_delta > -t['rsrp_stable_db']) else 'refutes',
                  f'无线质量变化 SINR {sinr_delta:+.2f} dB / RSRP {rsrp_delta:+.2f} dB（拥塞假设要求无线侧稳定）'),
        _evidence(cell_id, 'H3', 'C4', 'per_user_throughput_mbps', baseline['per_user_throughput_mbps'],
                  incident['per_user_throughput_mbps'], per_user_ratio, f'<= {t["per_user_drop_ratio"]:.1f}x',
                  'supports' if per_user_ratio <= t['per_user_drop_ratio'] else 'neutral',
                  f'每用户吞吐变化 {per_user_ratio:.2f}x（资源被摊薄）'),
        _evidence(cell_id, 'H3', 'C5', 'cqi_residual', radio['expected_cqi'], radio['reported_cqi'],
                  radio['cqi_residual'], f'|residual| <= {t["cqi_residual_limit"]:.0f}',
                  'supports' if abs(radio['cqi_residual']) <= t['cqi_residual_limit'] else 'neutral',
                  f'实测 CQI 与同 SINR 期望 CQI 偏差 {radio["cqi_residual"]:+.2f}（CQI 未见异常则支持纯拥塞）'),
    ]

    h4 = [
        _evidence(cell_id, 'H4', 'C1', 'rsrp_delta_db', baseline['rsrp_dbm_median'], rsrp_incident,
                  rsrp_delta, f'> -{t["rsrp_stable_db"]:.0f} dB',
                  'supports' if rsrp_delta > -t['rsrp_stable_db'] else 'refutes',
                  f'RSRP 变化 {rsrp_delta:+.2f} dB（无线侧是否稳定）'),
        _evidence(cell_id, 'H4', 'C2', 'prb_utilization_pct_mean', baseline['prb_utilization_pct_mean'],
                  prb_incident, delta['prb_delta_pp'], f'< {t["prb_congested_pct"]:.0f}%',
                  'supports' if prb_incident < t['prb_congested_pct'] else 'refutes',
                  f'PRB 利用率 {_fmt(prb_incident)}%（是否排除资源拥塞）'),
        _evidence(cell_id, 'H4', 'C3', 'actual_to_expected_ratio', None, ratio, None,
                  f'< {t["throughput_to_expected_low"]:.2f}',
                  'supports' if ratio < t['throughput_to_expected_low'] else 'refutes',
                  f'实际/期望吞吐 {ratio:.2f}（阈值 < 0.55：低于该值说明无线基线无法解释损失）'),
    ]

    hypotheses = [
        {
            'hypothesis_id': 'H1',
            'label': CAUSE_LABELS['COVERAGE_INSUFFICIENCY'],
            'statement': '覆盖变化导致接收电平下降，进而拉低 SINR/CQI 与下行吞吐',
            'gate_checks': ['C1', 'C2'],
            'checks': h1,
            'missing_evidence': MISSING_EVIDENCE['H1'],
            'discriminating_test': DISCRIMINATING_TESTS['H1'],
        },
        {
            'hypothesis_id': 'H2',
            'label': CAUSE_LABELS['INTERFERENCE'],
            'statement': '覆盖不变但干扰抬升，SINR/CQI 恶化并伴随 BLER 与重传上升',
            'gate_checks': ['C1', 'C2'],
            'checks': h2,
            'missing_evidence': MISSING_EVIDENCE['H2'],
            'discriminating_test': DISCRIMINATING_TESTS['H2'],
        },
        {
            'hypothesis_id': 'H3',
            'label': CAUSE_LABELS['RESOURCE_CONGESTION'],
            'statement': '无线质量稳定但 PRB 接近饱和、并发用户激增，每用户吞吐被摊薄',
            'gate_checks': ['C1', 'C2'],
            'checks': h3,
            'missing_evidence': MISSING_EVIDENCE['H3'],
            'discriminating_test': DISCRIMINATING_TESTS['H3'],
        },
        {
            'hypothesis_id': 'H4',
            'label': '非无线侧瓶颈（回传/核心网/终端/应用）',
            'statement': '空口指标稳定且资源未饱和，吞吐损失来自端到端其他环节',
            'gate_checks': ['C1', 'C3'],
            'checks': h4,
            'missing_evidence': MISSING_EVIDENCE['H4'],
            'discriminating_test': DISCRIMINATING_TESTS['H4'],
        },
    ]
    for item in hypotheses:
        item.update(_decide(item['checks'], item['gate_checks']))
        item['supporting_evidence_ids'] = [c['evidence_id'] for c in item['checks'] if c['direction'] == 'supports']
        item['refuting_evidence_ids'] = [c['evidence_id'] for c in item['checks'] if c['direction'] == 'refutes']
    return hypotheses


def _dominant_cause(hypotheses, delta):
    supported = [h for h in hypotheses if h['verdict'] == 'SUPPORTED']
    dropped = delta['throughput_delta_pct'] <= -THRESHOLDS['degradation_pct']
    if not supported:
        if not dropped:
            return {
                'code': 'NO_SIGNIFICANT_DEGRADATION',
                'label': CAUSE_LABELS['NO_SIGNIFICANT_DEGRADATION'],
                'confidence': 0.9,
                'reason': f'吞吐变化 {delta["throughput_delta_pct"]:+.2f}%，未达到劣化门限，且无假设被证据支持',
                'evidence_ids': [],
            }
        return {
            'code': 'UNDETERMINED',
            'label': CAUSE_LABELS['UNDETERMINED'],
            'confidence': 0.4,
            'reason': '吞吐已劣化，但四个假设均未被支持；需补齐缺失证据后再判定',
            'evidence_ids': [],
        }
    supported.sort(key=lambda h: h['confidence'], reverse=True)
    best = supported[0]
    code = {'H1': 'COVERAGE_INSUFFICIENCY', 'H2': 'INTERFERENCE',
            'H3': 'RESOURCE_CONGESTION', 'H4': 'UNDETERMINED'}[best['hypothesis_id']]
    conflicting = [h['hypothesis_id'] for h in supported[1:]]
    return {
        'code': code,
        'label': CAUSE_LABELS[code],
        'confidence': best['confidence'],
        'reason': best['basis'],
        'hypothesis_id': best['hypothesis_id'],
        'evidence_ids': best['supporting_evidence_ids'],
        'conflicting_hypotheses': conflicting,
    }


def recommendations_for(code, evidence_ids):
    items = []
    for item in RECOMMENDATIONS.get(code, []):
        entry = dict(item)
        entry['evidence_refs'] = list(evidence_ids)
        items.append(entry)
    return items


def build_cell_analysis(cell, baseline, incident, delta, radio):
    hypotheses = build_hypotheses(cell['cell_id'], baseline, incident, delta, radio)
    dominant = _dominant_cause(hypotheses, delta)
    degraded = delta['throughput_delta_pct'] <= -THRESHOLDS['degradation_pct']
    return {
        'cell_id': cell['cell_id'],
        'bandwidth_mhz': cell['bandwidth_mhz'],
        'degraded': degraded,
        'signals': delta,
        'radio_baseline': radio,
        'hypotheses': hypotheses,
        'dominant_cause': dominant,
        'recommendations': recommendations_for(dominant['code'], dominant['evidence_ids']),
        'missing_evidence': sorted({m for h in hypotheses if h['verdict'] != 'REFUTED'
                                    for m in h['missing_evidence']}),
        'next_discriminating_test': next(
            (h['discriminating_test'] for h in hypotheses
             if h['hypothesis_id'] == dominant.get('hypothesis_id')), None),
    }