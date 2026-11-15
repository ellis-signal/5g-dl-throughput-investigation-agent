"""Radio baseline for the 5G DL investigation: Shannon bound, practical
efficiency factor, and a CQI/SINR consistency table.

The Shannon figure is an optimistic single-link AWGN bound. Multiplying by
IMPLEMENTATION_EFFICIENCY yields a coarse *expected cell throughput* that is a
teaching calibration, not a vendor or 3GPP throughput model.
"""
import math

from .capacity import calculate, finite_number

METHOD_VERSION = 'dl-rca-v1'
IMPLEMENTATION_EFFICIENCY = 0.82

# TS 38.214-style 64QAM CQI table, quantized to this teaching model.
CQI_SINR_DB = {
    1: -6.0, 2: -4.0, 3: -2.0, 4: 0.0, 5: 2.0, 6: 4.0, 7: 6.0, 8: 8.0,
    9: 10.0, 10: 12.0, 11: 14.0, 12: 16.0, 13: 18.0, 14: 20.0, 15: 22.0,
}
CQI_SPECTRAL_EFFICIENCY = {
    1: 0.1523, 2: 0.2344, 3: 0.3770, 4: 0.6016, 5: 0.8770, 6: 1.1758,
    7: 1.4766, 8: 1.9141, 9: 2.4063, 10: 2.7305, 11: 3.3223, 12: 3.9023,
    13: 4.5234, 14: 5.1152, 15: 5.5547,
}


def sinr_linear(sinr_db):
    return 10.0 ** (sinr_db / 10.0)


def shannon_capacity_mbps(bandwidth_mhz, sinr_db):
    """Reuse the lab's canonical Shannon implementation (single source of truth)."""
    return calculate(bandwidth_mhz, sinr_db)['capacity_mbps']


def expected_throughput_mbps(bandwidth_mhz, sinr_db):
    return shannon_capacity_mbps(bandwidth_mhz, sinr_db) * IMPLEMENTATION_EFFICIENCY


def _interpolate(table, value):
    keys = sorted(table)
    if value <= keys[0]:
        return float(table[keys[0]])
    if value >= keys[-1]:
        return float(table[keys[-1]])
    for low, high in zip(keys, keys[1:]):
        if low <= value <= high:
            share = (value - low) / (high - low)
            return table[low] + share * (table[high] - table[low])
    raise ValueError('interpolation: unreachable')


def expected_cqi(sinr_db):
    """CQI a well-behaved link would report at this SINR (teaching mapping)."""
    inverse = {cqi: db for cqi, db in CQI_SINR_DB.items()}
    return round(_interpolate(inverse, finite_number(sinr_db, 'sinr_db')), 2)


def cqi_spectral_efficiency(cqi):
    return _interpolate(CQI_SPECTRAL_EFFICIENCY, finite_number(cqi, 'cqi'))


def radio_assessment(bandwidth_mhz, aggregate):
    """Compare measured throughput with the radio-derived expectation."""
    bandwidth_mhz = finite_number(bandwidth_mhz, 'bandwidth_mhz', positive=True)
    sinr_db = aggregate['sinr_db_median']
    shannon = shannon_capacity_mbps(bandwidth_mhz, sinr_db)
    expected = shannon * IMPLEMENTATION_EFFICIENCY
    actual = aggregate['dl_throughput_mbps_mean']
    reported_cqi = aggregate['cqi_mean']
    model_cqi = expected_cqi(sinr_db)
    ratio = actual / expected
    if ratio < 0.55:
        interpretation = '实际吞吐显著低于同 SINR 的期望值：无线基线本身不足以解释损失，优先排查调度/资源/端到端瓶颈'
    elif ratio > 1.05:
        interpretation = '实际吞吐高于单层 AWGN 期望：多天线/多用户增益或口径差异，期望值只能作下界参考'
    else:
        interpretation = '实际吞吐与无线基线同一量级：降级与无线质量变化方向一致'
    return {
        'shannon_capacity_mbps': shannon,
        'implementation_efficiency': IMPLEMENTATION_EFFICIENCY,
        'expected_throughput_mbps': expected,
        'actual_throughput_mbps': actual,
        'actual_to_expected_ratio': ratio,
        'actual_to_shannon_ratio': actual / shannon,
        'expected_cqi': model_cqi,
        'reported_cqi': reported_cqi,
        'cqi_residual': reported_cqi - model_cqi,
        'cqi_implied_efficiency_bps_hz': cqi_spectral_efficiency(reported_cqi),
        'interpretation': interpretation,
        'notes': [
            'Shannon 为乐观上界（单链路 AWGN，忽略多用户调度、控制开销与重传）',
            '期望吞吐 = Shannon × 实现效率，仅为教学标定，不是设备厂家吞吐模型',
        ],
    }


def per_hz(throughput_mbps, bandwidth_mhz):
    """bps/Hz helper used by narrative sections."""
    return throughput_mbps / bandwidth_mhz if bandwidth_mhz else math.nan