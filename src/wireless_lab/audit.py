"""An independent formula implementation for source-to-report audit.

No imports from workflow.py or capacity.calculate: catches corruption and some
implementation mistakes, not scientific/model mis-specification.
"""
import hashlib
import math
from pathlib import Path


def _valid_numeric(value, path):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{path}: expected finite number')
    return float(value)


def _capacity_independently(bandwidth, snr):
    """Independent log2 variant, handles extreme low SNR via log1p."""
    ratio = math.pow(10.0, snr / 10.0)
    if not math.isfinite(ratio):
        raise ValueError('SNR overflow')
    result = bandwidth * (math.log1p(ratio) / math.log(2))
    if not math.isfinite(result) or result <= 0:
        raise ValueError('capacity underflow/overflow')
    return result


def audit(source_path, source_data, report):
    errors = []
    if not isinstance(source_data, list) or not source_data:
        return ['source must be a nonempty list']
    if not isinstance(report, dict):
        return ['report must be an object']
    if report.get('schema_version') != 1: errors.append('schema_version != 1')
    if report.get('method_version') != 'shannon-awgn-v1': errors.append('method_version mismatch')
    if report.get('verification_status') != 'UNVERIFIED': errors.append('report may not self-certify PASS')
    if report.get('case_count') != len(source_data): errors.append('case_count mismatch')
    source_meta = report.get('source')
    expected_digest = hashlib.sha256(Path(source_path).read_bytes()).hexdigest()
    if not isinstance(source_meta, dict) or source_meta.get('sha256') != expected_digest or source_meta.get('path') != str(source_path):
        errors.append('source.path/sha256 mismatches supplied source')
    rows = report.get('cases')
    if not isinstance(rows, list):
        return errors + ['report.cases must be an array']
    source_by_id = {}
    for i, row in enumerate(source_data):
        if not isinstance(row, dict):
            errors.append(f'source[{i}]: not object')
            continue
        k = row.get('case_id')
        if not isinstance(k, str) or not k.strip() or k in source_by_id:
            errors.append(f'source[{i}]: duplicate or invalid ID')
        else:
            source_by_id[k] = row
    seen = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f'cases[{i}]: not object')
            continue
        k = row.get('case_id')
        if not isinstance(k, str) or k not in source_by_id or k in seen:
            errors.append(f'cases[{i}]: unknown/duplicate ID {k!r}')
            continue
        seen.add(k)
        source = source_by_id[k]
        try:
            b = _valid_numeric(source.get('bandwidth_mhz'), f'{k}.bandwidth_mhz')
            snr = _valid_numeric(source.get('snr_db'), f'{k}.snr_db')
            actual = _valid_numeric(source.get('actual_throughput_mbps'), f'{k}.actual_throughput_mbps')
            if b <= 0 or actual < 0:
                raise ValueError('bandwidth must >0; throughput must >=0')
            cap = _capacity_independently(b, snr)
            expected = dict(bandwidth_mhz=b, snr_db=snr, actual_throughput_mbps=actual,
                            capacity_mbps=cap, throughput_to_capacity_ratio=actual/cap)
            for field, correct in expected.items():
                got = row.get(field)
                if isinstance(got, bool) or not isinstance(got, (int,float)) or not math.isfinite(got):
                    errors.append(f'{k}.{field}: invalid number')
                elif not math.isclose(correct, got, rel_tol=1e-9, abs_tol=1e-9):
                    errors.append(f'{k}.{field}: mismatch expected {correct:.10g}, got {got}')
            if actual > cap*1.01:
                errors.append(f'{k}: actual throughput >1.01x theoretical bound; check data/model assumptions')
        except (ValueError, OverflowError) as exc:
            errors.append(f'{k}: invalid source: {exc}')
    for k in source_by_id.keys() - seen:
        errors.append(f'missing report case {k}')
    if len(rows) != len(source_by_id):
        errors.append('case list length mismatch')
    return errors
