"""Independent audit of an evidence ledger.

Deliberately does NOT import dl_kpi / dl_evidence / dl_model: every aggregate,
delta, threshold and verdict is recomputed here from the raw dataset bytes with
a separate implementation. If the two disagree, the receipt says FAIL and the
report is not deliverable.
"""
import hashlib
import json
import math
from pathlib import Path

from .dl_canonical import canonical_sha256 as _canonical_sha256

AUDIT_VERSION = 'dl-audit-v1'
EXPECTED_METHOD = 'dl-rca-v1'
EXPECTED_SCHEMA = 1

# Re-declared on purpose: the auditor must not inherit the engine's constants.
RULES = {
    'rsrp_weak_dbm': -105.0,
    'rsrp_drop_db': 3.0,
    'rsrp_stable_db': 3.0,
    'sinr_drop_db': 4.0,
    'cqi_drop': 2.0,
    'prb_congested_pct': 85.0,
    'users_growth_ratio': 1.5,
    'per_user_drop_ratio': 0.6,
    'degradation_pct': 10.0,
    'throughput_to_expected_low': 0.55,
    'implementation_efficiency': 0.82,
}
VERDICTS = {'SUPPORTED', 'REFUTED', 'INCONCLUSIVE'}
CAUSE_BY_HYPOTHESIS = {
    'H1': 'COVERAGE_INSUFFICIENCY',
    'H2': 'INTERFERENCE',
    'H3': 'RESOURCE_CONGESTION',
    'H4': 'UNDETERMINED',
}


def _mean(values):
    return sum(values) / len(values) if values else float('nan')


def _median(values):
    ordered = sorted(values)
    n = len(ordered)
    if n == 0:
        return float('nan')
    mid = n // 2
    return ordered[mid] if n % 2 else (ordered[mid - 1] + ordered[mid]) / 2.0


def _shannon(bandwidth_mhz, sinr_db):
    linear = math.pow(10.0, sinr_db / 10.0)
    return bandwidth_mhz * math.log1p(linear) / math.log(2.0)


def _close(a, b, tol=1e-6):
    if a is None or b is None:
        return a is b
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def _verdict(hypothesis):
    checks = hypothesis['checks']
    gates = [c for c in checks if c['check_id'] in hypothesis['gate_checks']]
    failed = [c for c in gates if c['direction'] != 'supports']
    if failed:
        return 'REFUTED', 0.9
    corroborating = [c for c in checks
                     if c['check_id'] not in hypothesis['gate_checks'] and c['direction'] != 'neutral']
    if not corroborating:
        return 'SUPPORTED', 0.6
    share = sum(1 for c in corroborating if c['direction'] == 'supports') / len(corroborating)
    if share < 0.5:
        return 'INCONCLUSIVE', 0.5
    return 'SUPPORTED', round(0.6 + 0.35 * share, 2)


class _Report:
    def __init__(self):
        self.checks = []
        self.errors = []

    def check(self, check_id, ok, detail):
        self.checks.append({'check_id': check_id, 'ok': bool(ok), 'detail': detail})
        if not ok:
            self.errors.append(f'{check_id}: {detail}')
        return ok


def audit(dataset, ledger, *, dataset_path=None):
    """Recompute the ledger from the raw dataset and compare.

    `dataset` is the already-validated dataset dict, or None to re-read from
    `dataset_path`. Returns a deterministic receipt (no timestamps).
    """
    report = _Report()

    if dataset is None:
        if not dataset_path:
            raise ValueError('audit: dataset or dataset_path required')
        dataset = json.loads(Path(dataset_path).read_text(encoding='utf-8'))

    report.check('ledger.schema_version', ledger.get('schema_version') == EXPECTED_SCHEMA,
                 f"schema_version={ledger.get('schema_version')!r}")
    report.check('ledger.method_version', ledger.get('method_version') == EXPECTED_METHOD,
                 f"method_version={ledger.get('method_version')!r}")
    report.check('ledger.verification_status_present', 'verification_status' in ledger,
                 'ledger must declare verification_status')
    cells = ledger.get('cells')
    report.check('ledger.cells_array', isinstance(cells, list) and len(cells) > 0,
                 f'cells={type(cells).__name__}')

    source = (ledger.get('dataset') or {}).get('source') or {}
    if dataset_path:
        digest = hashlib.sha256(Path(dataset_path).read_bytes()).hexdigest()
        report.check('dataset.sha256', source.get('sha256') == digest,
                     'source hash does not match the bytes on disk')
    raw_cells = {c['cell_id']: c for c in dataset.get('cells', [])}
    report.check('dataset.cell_count', len(raw_cells) == len(cells or []),
                 f'raw={len(raw_cells)} ledger={len(cells or [])}')

    seen_ids = set()
    evidence_ids = []
    for cell in cells or []:
        cid = cell.get('cell_id')
        report.check(f'{cid}.unique', cid not in seen_ids, 'duplicate cell entry')
        seen_ids.add(cid)
        raw = raw_cells.get(cid)
        if not report.check(f'{cid}.in_dataset', raw is not None, 'cell missing from dataset'):
            continue
        _audit_cell(report, raw, cell, evidence_ids)

    report.check('evidence.ids_unique', len(evidence_ids) == len(set(evidence_ids)),
                 f'{len(evidence_ids)} evidence rows, {len(set(evidence_ids))} unique')

    status = 'PASS' if not report.errors else 'FAIL'
    return {
        'status': status,
        'audit_version': AUDIT_VERSION,
        'method_version': ledger.get('method_version'),
        'ledger_sha256': _canonical_sha256(cells or []),
        'checked_cells': len(cells or []),
        'checked_evidence': len(evidence_ids),
        'checks': report.checks,
        'errors': report.errors,
        'error_count': len(report.errors),
    }


def _audit_cell(report, raw, cell, evidence_ids):
    cid = raw['cell_id']
    bandwidth = float(raw['bandwidth_mhz'])
    base_rows = [s for s in raw['samples'] if s.get('window') == 'baseline']
    inc_rows = [s for s in raw['samples'] if s.get('window') == 'incident']
    if not report.check(f'{cid}.windows', bool(base_rows) and bool(inc_rows),
                        'baseline/incident samples missing'):
        return

    def aggregate(rows):
        tput = _mean([float(s['dl_throughput_mbps']) for s in rows])
        users = _mean([float(s['active_users']) for s in rows])
        return {
            'rsrp_dbm_median': _median([float(s['rsrp_dbm']) for s in rows]),
            'sinr_db_median': _median([float(s['sinr_db']) for s in rows]),
            'cqi_mean': _mean([float(s['cqi']) for s in rows]),
            'prb_utilization_pct_mean': _mean([float(s['prb_utilization_pct']) for s in rows]),
            'active_users_mean': users,
            'dl_throughput_mbps_mean': tput,
            'bler_pct_mean': _mean([float(s['bler_pct']) for s in rows]),
            'per_user_throughput_mbps': tput / users,
        }

    base = aggregate(base_rows)
    inc = aggregate(inc_rows)
    for name, value in base.items():
        report.check(f'{cid}.baseline.{name}', _close(value, cell.get('baseline', {}).get(name)),
                     f'expected {value:.6f}, ledger {cell.get("baseline", {}).get(name)}')
    for name, value in inc.items():
        report.check(f'{cid}.incident.{name}', _close(value, cell.get('incident', {}).get(name)),
                     f'expected {value:.6f}, ledger {cell.get("incident", {}).get(name)}')

    delta = {
        'throughput_delta_pct': (inc['dl_throughput_mbps_mean'] / base['dl_throughput_mbps_mean'] - 1) * 100,
        'rsrp_delta_db': inc['rsrp_dbm_median'] - base['rsrp_dbm_median'],
        'sinr_delta_db': inc['sinr_db_median'] - base['sinr_db_median'],
        'cqi_delta': inc['cqi_mean'] - base['cqi_mean'],
        'prb_delta_pp': inc['prb_utilization_pct_mean'] - base['prb_utilization_pct_mean'],
        'users_ratio': inc['active_users_mean'] / base['active_users_mean'],
        'per_user_throughput_ratio': inc['per_user_throughput_mbps'] / base['per_user_throughput_mbps'],
    }
    for name, value in delta.items():
        report.check(f'{cid}.signals.{name}', _close(value, cell.get('signals', {}).get(name)),
                     f'expected {value:.6f}, ledger {cell.get("signals", {}).get(name)}')

    expected = _shannon(bandwidth, inc['sinr_db_median']) * RULES['implementation_efficiency']
    ratio = inc['dl_throughput_mbps_mean'] / expected
    report.check(f'{cid}.radio.actual_to_expected_ratio',
                 _close(ratio, (cell.get('radio') or {}).get('actual_to_expected_ratio')),
                 f'expected {ratio:.6f}')

    hypotheses = {h['hypothesis_id']: h for h in cell.get('hypotheses', [])}
    report.check(f'{cid}.hypotheses.count', set(hypotheses) == {'H1', 'H2', 'H3', 'H4'},
                 f'found {sorted(hypotheses)}')
    for hid, hypothesis in sorted(hypotheses.items()):
        expected_verdict, expected_conf = _verdict(hypothesis)
        report.check(f'{cid}.{hid}.verdict', hypothesis.get('verdict') == expected_verdict,
                     f'expected {expected_verdict}, ledger {hypothesis.get("verdict")}')
        report.check(f'{cid}.{hid}.confidence', _close(expected_conf, hypothesis.get('confidence')),
                     f'expected {expected_conf}, ledger {hypothesis.get("confidence")}')
        for check in hypothesis.get('checks', []):
            evidence_ids.append(check.get('evidence_id'))
            prefix = f'EV-{cid}-{hid}-'
            report.check(f"{check.get('evidence_id')}.id", str(check.get('evidence_id', '')).startswith(prefix),
                         'evidence id does not match cell/hypothesis')
            report.check(f"{check.get('evidence_id')}.finite",
                         all(isinstance(check.get(f), (int, float)) and math.isfinite(check.get(f))
                             for f in ('baseline', 'incident', 'delta') if check.get(f) is not None),
                         'non-finite evidence number')

    supported = [h for h in hypotheses.values() if h.get('verdict') == 'SUPPORTED']
    dominant = cell.get('dominant_cause') or {}
    if supported:
        supported.sort(key=lambda h: h.get('confidence', 0), reverse=True)
        expected_code = CAUSE_BY_HYPOTHESIS[supported[0]['hypothesis_id']]
    elif delta['throughput_delta_pct'] <= -RULES['degradation_pct']:
        expected_code = 'UNDETERMINED'
    else:
        expected_code = 'NO_SIGNIFICANT_DEGRADATION'
    report.check(f'{cid}.dominant_cause', dominant.get('code') == expected_code,
                 f'expected {expected_code}, ledger {dominant.get("code")}')

    if expected_code in ('COVERAGE_INSUFFICIENCY', 'INTERFERENCE', 'RESOURCE_CONGESTION'):
        recs = cell.get('recommendations') or []
        report.check(f'{cid}.recommendations', len(recs) >= 1 and
                     all(r.get('requires_change_approval') is not None for r in recs),
                     'supported cause must ship at least one recommendation with an approval flag')