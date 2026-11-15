"""Investigation orchestrator: dataset -> evidence ledger.

The ledger is the single machine-readable contract between the analysis layer
and everything downstream (report, HTTP API, web UI). It is deliberately flat,
JSON-native and free of timestamps so two runs on the same bytes are identical.
"""
from . import dl_kpi
from .dl_canonical import canonical_sha256
from .dl_evidence import METHOD_VERSION, build_cell_analysis
from .dl_model import radio_assessment

LEDGER_SCHEMA_VERSION = 1
VERDICTS = ('SUPPORTED', 'REFUTED', 'INCONCLUSIVE')


def investigate_cell(cell):
    baseline = dl_kpi.aggregate_window(dl_kpi.window_samples(cell, 'baseline'))
    incident = dl_kpi.aggregate_window(dl_kpi.window_samples(cell, 'incident'))
    delta = dl_kpi.deltas(baseline, incident)
    radio = radio_assessment(cell['bandwidth_mhz'], incident)
    analysis = build_cell_analysis(cell, baseline, incident, delta, radio)
    analysis.update({
        'sector': cell.get('sector'),
        'complaint': cell.get('complaint'),
        'baseline': baseline,
        'incident': incident,
        'radio': radio,
    })
    return analysis


def investigate(dataset):
    """Build the full ledger for every cell in a validated dataset."""
    cells = [investigate_cell(cell) for cell in dataset['cells']]
    by_cause = {}
    for cell in cells:
        code = cell['dominant_cause']['code']
        by_cause[code] = by_cause.get(code, 0) + 1
    ledger = {
        'schema_version': LEDGER_SCHEMA_VERSION,
        'method_version': METHOD_VERSION,
        'verification_status': 'UNVERIFIED',
        'dataset': {
            'dataset_id': dataset['dataset_id'],
            'schema_version': dataset['schema_version'],
            'source': dataset.get('source'),
        },
        'summary': {
            'cell_count': len(cells),
            'degraded_count': sum(1 for c in cells if c['degraded']),
            'causes': by_cause,
            'cells': [
                {
                    'cell_id': c['cell_id'],
                    'sector': c.get('sector'),
                    'degraded': c['degraded'],
                    'cause': c['dominant_cause']['code'],
                    'confidence': c['dominant_cause']['confidence'],
                    'throughput_delta_pct': round(c['signals']['throughput_delta_pct'], 2),
                }
                for c in cells
            ],
        },
        'cells': cells,
    }
    ledger['ledger_sha256'] = canonical_sha256(cells)
    return ledger


def load_and_investigate(path):
    return investigate(dl_kpi.load_dataset(path))


def find_cell(ledger, cell_id):
    for cell in ledger['cells']:
        if cell['cell_id'] == cell_id:
            return cell
    raise KeyError(f'unknown cell_id: {cell_id}')


def omit_prb(cell):
    """Return a copy with PRB fields removed (the UI's 'field missing' drill)."""
    import copy

    clone = copy.deepcopy(cell)
    clone['baseline'] = {k: v for k, v in clone['baseline'].items() if 'prb' not in k}
    clone['incident'] = {k: v for k, v in clone['incident'].items() if 'prb' not in k}
    clone['signals'] = {k: v for k, v in clone['signals'].items() if 'prb' not in k}
    for hypothesis in clone['hypotheses']:
        hypothesis['checks'] = [c for c in hypothesis['checks'] if 'prb' not in c['metric']]
        gates = set(hypothesis['gate_checks'])
        dropped = gates - {c['check_id'] for c in hypothesis['checks']}
        if dropped:
            hypothesis.update({
                'verdict': 'INCONCLUSIVE',
                'confidence': 0.5,
                'basis': '必要条件所需字段（PRB 利用率）缺失，无法判定',
                'gate_passed': False,
                'missing_gate_checks': sorted(dropped),
            })
    clone['dominant_cause'] = {
        'code': 'UNDETERMINED',
        'label': '现有证据不足以判定',
        'confidence': 0.4,
        'reason': 'PRB 利用率字段缺失，拥塞假设的必要条件无法验证；按规则不得给出确定结论',
        'evidence_ids': [],
    }
    clone['recommendations'] = []
    clone['missing_evidence'] = sorted(set(clone['missing_evidence']) | {
        'PRB 利用率（当前数据集缺失该字段）',
    })
    return clone