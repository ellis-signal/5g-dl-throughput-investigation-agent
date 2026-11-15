import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'src'))

from wireless_lab.dl_audit import audit
from wireless_lab.dl_kpi import load_dataset, validate_dataset
from wireless_lab.dl_rca import find_cell, investigate, omit_prb
from wireless_lab.dl_render import render_cell

DATA = ROOT / 'data' / 'dl_cells_kpi.json'
EXPECTED = {
    'NR-CELL-1001': 'COVERAGE_INSUFFICIENCY',
    'NR-CELL-1002': 'INTERFERENCE',
    'NR-CELL-1003': 'RESOURCE_CONGESTION',
    'NR-CELL-1004': 'NO_SIGNIFICANT_DEGRADATION',
}


class Investigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_dataset(str(DATA))
        cls.ledger = investigate(cls.dataset)

    def test_cells_and_verdicts(self):
        self.assertEqual(len(self.ledger['cells']), 4)
        for cell in self.ledger['cells']:
            self.assertEqual(cell['dominant_cause']['code'], EXPECTED[cell['cell_id']])
        self.assertEqual(self.ledger['summary']['degraded_count'], 3)

    def test_each_cell_has_one_supported_hypothesis(self):
        for cell in self.ledger['cells']:
            supported = [h['hypothesis_id'] for h in cell['hypotheses'] if h['verdict'] == 'SUPPORTED']
            expected = {
                'COVERAGE_INSUFFICIENCY': ['H1'],
                'INTERFERENCE': ['H2'],
                'RESOURCE_CONGESTION': ['H3'],
                'NO_SIGNIFICANT_DEGRADATION': [],
            }[cell['dominant_cause']['code']]
            self.assertEqual(supported, expected, cell['cell_id'])

    def test_evidence_ids_are_addressable(self):
        cell = find_cell(self.ledger, 'NR-CELL-1002')
        ids = [c['evidence_id'] for h in cell['hypotheses'] for c in h['checks']]
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.startswith('EV-NR-CELL-1002-H') for i in ids))

    def test_deterministic(self):
        again = investigate(load_dataset(str(DATA)))
        self.assertEqual(again['ledger_sha256'], self.ledger['ledger_sha256'])
        self.assertEqual(json.dumps(again, sort_keys=True), json.dumps(self.ledger, sort_keys=True))

    def test_serialisable_without_nan(self):
        text = json.dumps(self.ledger, allow_nan=False)
        self.assertNotIn('NaN', text)

    def test_omit_prb_degrades_to_undetermined(self):
        cell = find_cell(self.ledger, 'NR-CELL-1003')
        degraded = omit_prb(cell)
        self.assertEqual(degraded['dominant_cause']['code'], 'UNDETERMINED')
        h3 = next(h for h in degraded['hypotheses'] if h['hypothesis_id'] == 'H3')
        self.assertEqual(h3['verdict'], 'INCONCLUSIVE')
        self.assertEqual(h3['missing_gate_checks'], ['C1'])
        self.assertTrue(any('PRB' in g for g in degraded['missing_evidence']))


class Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_dataset(str(DATA))
        cls.ledger = investigate(cls.dataset)

    def test_passes_on_generated_ledger(self):
        receipt = audit(self.dataset, self.ledger, dataset_path=str(DATA))
        self.assertEqual(receipt['status'], 'PASS', receipt['errors'][:3])
        self.assertEqual(receipt['error_count'], 0)
        self.assertGreater(len(receipt['checks']), 100)
        self.assertEqual(receipt['ledger_sha256'], self.ledger['ledger_sha256'])

    def test_survives_json_round_trip(self):
        """The browser posts back parsed JSON: ints become floats, hash must hold."""
        posted = json.loads(json.dumps(self.ledger))
        receipt = audit(self.dataset, posted, dataset_path=str(DATA))
        self.assertEqual(receipt['status'], 'PASS', receipt['errors'][:3])
        self.assertEqual(receipt['ledger_sha256'], self.ledger['ledger_sha256'])

    def test_fails_on_flipped_verdict(self):
        tampered = copy.deepcopy(self.ledger)
        cell = find_cell(tampered, 'NR-CELL-1002')
        for hypothesis in cell['hypotheses']:
            if hypothesis['hypothesis_id'] == 'H1':
                hypothesis['verdict'] = 'SUPPORTED'
                hypothesis['confidence'] = 0.95
        receipt = audit(self.dataset, tampered, dataset_path=str(DATA))
        self.assertEqual(receipt['status'], 'FAIL')
        self.assertTrue(any('NR-CELL-1002.H1.verdict' in e for e in receipt['errors']))

    def test_fails_on_tampered_throughput(self):
        tampered = copy.deepcopy(self.ledger)
        cell = find_cell(tampered, 'NR-CELL-1001')
        cell['incident']['dl_throughput_mbps_mean'] = 900.0
        receipt = audit(self.dataset, tampered, dataset_path=str(DATA))
        self.assertEqual(receipt['status'], 'FAIL')

    def test_fails_on_wrong_source_hash(self):
        tampered = copy.deepcopy(self.ledger)
        tampered['dataset']['source']['sha256'] = '0' * 64
        receipt = audit(self.dataset, tampered, dataset_path=str(DATA))
        self.assertEqual(receipt['status'], 'FAIL')
        self.assertTrue(any('dataset.sha256' in e for e in receipt['errors']))


class Contracts(unittest.TestCase):
    def test_rejects_unknown_window(self):
        raw = json.loads(DATA.read_text(encoding='utf-8'))
        raw['cells'][0]['samples'][0]['window'] = 'unknown'
        with self.assertRaises(ValueError):
            validate_dataset(raw)

    def test_rejects_missing_window_samples(self):
        raw = json.loads(DATA.read_text(encoding='utf-8'))
        raw['cells'][0]['samples'] = [s for s in raw['cells'][0]['samples'] if s['window'] == 'baseline']
        with self.assertRaises(ValueError):
            validate_dataset(raw)

    def test_rejects_out_of_range_metric(self):
        raw = json.loads(DATA.read_text(encoding='utf-8'))
        raw['cells'][0]['samples'][0]['prb_utilization_pct'] = 140
        with self.assertRaises(ValueError):
            validate_dataset(raw)

    def test_rejects_duplicate_sample(self):
        raw = json.loads(DATA.read_text(encoding='utf-8'))
        samples = raw['cells'][0]['samples']
        samples.append(copy.deepcopy(samples[0]))
        with self.assertRaises(ValueError):
            validate_dataset(raw)


class Render(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_dataset(str(DATA))
        cls.ledger = investigate(cls.dataset)

    def test_report_sections(self):
        cell = find_cell(self.ledger, 'NR-CELL-1002')
        text = render_cell(cell, dataset=self.dataset)
        for heading in ('## 1. 数据来源', '## 2. 指标对比', '## 3. 假设判定',
                        '## 4. 证据明细', '## 5. 缺失证据', '## 6. 处置建议'):
            self.assertIn(heading, text)
        self.assertIn('EV-NR-CELL-1002-H2-C1', text)
        self.assertIn('UNVERIFIED', text)

    def test_report_marks_audited(self):
        cell = find_cell(self.ledger, 'NR-CELL-1002')
        receipt = audit(self.dataset, self.ledger, dataset_path=str(DATA))
        text = render_cell(cell, dataset=self.dataset, receipt=receipt)
        self.assertIn('已审计 PASS', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)