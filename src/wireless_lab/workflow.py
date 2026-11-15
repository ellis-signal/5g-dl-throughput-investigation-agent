"""Validated immutable source -> computed report -> verification receipt."""
import hashlib
import json
import math
from pathlib import Path
from .capacity import calculate, finite_number, METHOD_VERSION, MODEL


def json_file(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=lambda s: (_ for _ in ()).throw(ValueError(f'invalid nonfinite literal {s}')))


def source_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_source(path):
    data = json_file(path)
    if not isinstance(data, list) or not data:
        raise ValueError('source must be a nonempty JSON array')
    seen = set()
    result = []
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f'source[{i}]: expected JSON object')
        name = row.get('case_id')
        if not isinstance(name, str) or not name.strip() or name in seen:
            raise ValueError(f'source[{i}]: case_id required, nonempty and unique')
        seen.add(name)
        allowed = {'case_id','bandwidth_mhz','snr_db','actual_throughput_mbps'}
        extra = set(row)-allowed
        if extra:
            raise ValueError(f'{name}: unexpected fields: {sorted(extra)}')
        result.append({
            'case_id': name,
            'bandwidth_mhz': finite_number(row.get('bandwidth_mhz'), f'{name}.bandwidth_mhz', positive=True),
            'snr_db': finite_number(row.get('snr_db'), f'{name}.snr_db'),
            'actual_throughput_mbps': finite_number(row.get('actual_throughput_mbps'), f'{name}.actual_throughput_mbps', nonnegative=True),
        })
    return result


def compute_report(source_path):
    cases = load_source(source_path)
    rows = []
    for case in cases:
        result = calculate(case['bandwidth_mhz'], case['snr_db'])
        rows.append({
            **case,
            'capacity_mbps': result['capacity_mbps'],
            'throughput_to_capacity_ratio': case['actual_throughput_mbps'] / result['capacity_mbps'],
        })
    return {
        'schema_version': 1,
        'method_version': METHOD_VERSION,
        'model': MODEL,
        'source': {'path': str(source_path), 'sha256': source_sha256(source_path)},
        'case_count': len(cases),
        'verification_status': 'UNVERIFIED',
        'cases': rows,
    }


def write_json(path, payload):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    # No partial document left behind if a serialization error happens.
    text = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    temp = output.with_name(output.name + '.tmp')
    temp.write_text(text, encoding='utf-8')
    temp.replace(output)
    return str(output)


def verify_report(source_path, report):
    """Generate-and-verify contract (independent audit is in audit.py)."""
    expected = compute_report(source_path)
    errors = []
    if not isinstance(report, dict):
        return ['report must be an object']
    for key in ('schema_version', 'method_version', 'case_count', 'verification_status'):
        if report.get(key) != expected[key]:
            errors.append(f'{key}: expected {expected[key]!r}, got {report.get(key)!r}')
    if report.get('model') != expected['model']:
        errors.append('model: unexpected value')
    if report.get('source') != expected['source']:
        errors.append('source: path or sha256 does not match input bytes')
    rows = report.get('cases')
    if not isinstance(rows, list):
        return errors + ['cases: expected array']
    if len(rows) != len(expected['cases']):
        errors.append('cases: wrong length')
    expected_by_id = {r['case_id']: r for r in expected['cases']}
    seen = set()
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f'cases[{i}]: expected object')
            continue
        k = row.get('case_id')
        if not isinstance(k, str) or k not in expected_by_id or k in seen:
            errors.append(f'cases[{i}]: missing/unknown/duplicate case_id {k!r}')
            continue
        seen.add(k)
        expected_row = expected_by_id[k]
        for field in ('bandwidth_mhz', 'snr_db', 'actual_throughput_mbps', 'capacity_mbps', 'throughput_to_capacity_ratio'):
            value = row.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                errors.append(f'{k}.{field}: missing or nonfinite number')
            elif not math.isclose(value, expected_row[field], rel_tol=1e-9, abs_tol=1e-9):
                errors.append(f'{k}.{field}: expected {expected_row[field]:.10g}, got {value}')
    for k in expected_by_id.keys() - seen:
        errors.append(f'cases: missing case_id {k}')
    return errors
