"""5G downlink KPI dataset: contract validation and window aggregation.

Stdlib only. Aggregations are pure functions over an immutable, validated
sample list, so an independent verifier can recompute them from raw bytes.
"""
import hashlib
import json
import math
import statistics
from pathlib import Path

SCHEMA_VERSION = 1
WINDOWS = ('baseline', 'incident')
SAMPLE_FIELDS = (
    'timestamp', 'rsrp_dbm', 'sinr_db', 'cqi',
    'prb_utilization_pct', 'active_users',
    'dl_throughput_mbps', 'bler_pct',
)
RANGES = {
    'rsrp_dbm': (-140.0, -40.0),
    'sinr_db': (-30.0, 40.0),
    'cqi': (0.0, 15.0),
    'prb_utilization_pct': (0.0, 100.0),
    'active_users': (1.0, 5000.0),
    'dl_throughput_mbps': (0.0, 100000.0),
    'bler_pct': (0.0, 100.0),
}
MIN_SAMPLES_PER_WINDOW = 6
CASE_FIELDS = ('sector', 'complaint')


def json_file(path):
    """Strict JSON: reject NaN/Infinity instead of accepting Python extensions."""
    def reject(token):
        raise ValueError(f'{path}: invalid non-finite JSON literal {token}')
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject)


def _number(value, path, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{path}: expected a number')
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f'{path}: must be finite')
    if low is not None and value < low:
        raise ValueError(f'{path}: must be >= {low:g}')
    if high is not None and value > high:
        raise ValueError(f'{path}: must be <= {high:g}')
    return value


def _sample(raw, path):
    if not isinstance(raw, dict):
        raise ValueError(f'{path}: expected an object')
    extra = set(raw) - set(SAMPLE_FIELDS) - {'window'}
    if extra:
        raise ValueError(f'{path}: unexpected fields {sorted(extra)}')
    missing = [field for field in SAMPLE_FIELDS if field not in raw]
    if missing:
        raise ValueError(f'{path}: missing fields {missing}')
    window = raw.get('window')
    if window not in WINDOWS:
        raise ValueError(f'{path}.window: expected one of {list(WINDOWS)}')
    timestamp = raw.get('timestamp')
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError(f'{path}.timestamp: nonempty string required')
    sample = {'window': window, 'timestamp': timestamp}
    for field, (low, high) in RANGES.items():
        sample[field] = _number(raw.get(field), f'{path}.{field}', low, high)
    return sample


def validate_dataset(raw):
    """Return a normalized copy; raise ValueError on any contract violation."""
    if not isinstance(raw, dict):
        raise ValueError('dataset: expected an object')
    extra = set(raw) - {'schema_version', 'dataset_id', 'cells', 'description'}
    if extra:
        raise ValueError(f'dataset: unexpected fields {sorted(extra)}')
    if raw.get('schema_version') != SCHEMA_VERSION:
        raise ValueError(f'dataset.schema_version: expected {SCHEMA_VERSION}')
    dataset_id = raw.get('dataset_id')
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise ValueError('dataset.dataset_id: nonempty string required')
    cells = raw.get('cells')
    if not isinstance(cells, list) or not cells:
        raise ValueError('dataset.cells: nonempty array required')
    seen_cells = set()
    normalized = []
    for index, cell in enumerate(cells):
        path = f'cells[{index}]'
        if not isinstance(cell, dict):
            raise ValueError(f'{path}: expected an object')
        extra = set(cell) - {'cell_id', 'bandwidth_mhz', 'samples'} - set(CASE_FIELDS)
        if extra:
            raise ValueError(f'{path}: unexpected fields {sorted(extra)}')
        cell_id = cell.get('cell_id')
        if not isinstance(cell_id, str) or not cell_id.strip():
            raise ValueError(f'{path}.cell_id: nonempty string required')
        if cell_id in seen_cells:
            raise ValueError(f'{path}.cell_id: duplicate {cell_id!r}')
        seen_cells.add(cell_id)
        bandwidth_mhz = _number(cell.get('bandwidth_mhz'), f'{path}.bandwidth_mhz', 0.0, 1000.0)
        if bandwidth_mhz <= 0:
            raise ValueError(f'{path}.bandwidth_mhz: must be > 0')
        case = {}
        for field in CASE_FIELDS:
            value = cell.get(field)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f'{path}.{field}: nonempty string required when present')
            case[field] = value.strip() if isinstance(value, str) else None
        samples = cell.get('samples')
        if not isinstance(samples, list):
            raise ValueError(f'{path}.samples: expected an array')
        seen_keys = set()
        parsed = []
        for j, raw_sample in enumerate(samples):
            sample = _sample(raw_sample, f'{path}.samples[{j}]')
            key = (sample['window'], sample['timestamp'])
            if key in seen_keys:
                raise ValueError(f'{path}.samples[{j}]: duplicate sample {key}')
            seen_keys.add(key)
            parsed.append(sample)
        for window in WINDOWS:
            count = sum(1 for s in parsed if s['window'] == window)
            if count < MIN_SAMPLES_PER_WINDOW:
                raise ValueError(
                    f'{path}: window {window!r} needs >= {MIN_SAMPLES_PER_WINDOW} samples, got {count}')
        normalized.append({'cell_id': cell_id, 'bandwidth_mhz': bandwidth_mhz,
                           'sector': case['sector'], 'complaint': case['complaint'],
                           'samples': parsed})
    return {
        'schema_version': SCHEMA_VERSION,
        'dataset_id': dataset_id,
        'description': raw.get('description'),
        'cells': normalized,
    }


def load_dataset(path):
    """Validated dataset plus the exact source bytes identity used by the report."""
    dataset = validate_dataset(json_file(path))
    dataset['source'] = {
        'path': str(path),
        'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
    }
    return dataset


def window_samples(cell, window):
    return [s for s in cell['samples'] if s['window'] == window]


def aggregate_window(samples):
    """Descriptive statistics for one measurement window."""
    if not samples:
        raise ValueError('aggregate_window: no samples')
    tput = statistics.fmean(s['dl_throughput_mbps'] for s in samples)
    users = statistics.fmean(s['active_users'] for s in samples)
    return {
        'sample_count': len(samples),
        'rsrp_dbm_median': statistics.median(s['rsrp_dbm'] for s in samples),
        'sinr_db_median': statistics.median(s['sinr_db'] for s in samples),
        'cqi_mean': statistics.fmean(s['cqi'] for s in samples),
        'prb_utilization_pct_mean': statistics.fmean(s['prb_utilization_pct'] for s in samples),
        'active_users_mean': users,
        'dl_throughput_mbps_mean': tput,
        'bler_pct_mean': statistics.fmean(s['bler_pct'] for s in samples),
        'per_user_throughput_mbps': tput / users,
    }


def deltas(baseline, incident):
    """Baseline -> incident change, using units a RAN engineer reads directly."""
    def ratio(inc, base):
        return inc / base if base else 0.0

    return {
        'throughput_delta_pct': (incident['dl_throughput_mbps_mean'] / baseline['dl_throughput_mbps_mean'] - 1.0) * 100.0,
        'throughput_ratio': ratio(incident['dl_throughput_mbps_mean'], baseline['dl_throughput_mbps_mean']),
        'per_user_throughput_ratio': ratio(incident['per_user_throughput_mbps'], baseline['per_user_throughput_mbps']),
        'rsrp_delta_db': incident['rsrp_dbm_median'] - baseline['rsrp_dbm_median'],
        'sinr_delta_db': incident['sinr_db_median'] - baseline['sinr_db_median'],
        'cqi_delta': incident['cqi_mean'] - baseline['cqi_mean'],
        'prb_delta_pp': incident['prb_utilization_pct_mean'] - baseline['prb_utilization_pct_mean'],
        'users_ratio': ratio(incident['active_users_mean'], baseline['active_users_mean']),
        'bler_delta_pp': incident['bler_pct_mean'] - baseline['bler_pct_mean'],
    }