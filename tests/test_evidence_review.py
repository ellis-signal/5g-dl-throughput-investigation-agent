import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wireless_lab.agent import load_case, compare_windows, with_review
from wireless_lab.review import review


class EvidenceReviewTests(unittest.TestCase):
    def evaluate(self, case_id):
        return review(load_case(case_id), compare_windows(case_id))

    def test_interference_uses_support_and_counterevidence(self):
        result = self.evaluate('NR-CELL-1002')
        self.assertEqual(result['label'], 'INTERFERENCE')
        self.assertEqual(result['hypotheses']['COVERAGE'][0]['status'], '削弱')
        self.assertEqual(result['hypotheses']['INTERFERENCE'][1]['status'], '支持')

    def test_missing_measurements_are_preserved(self):
        result = self.evaluate('NR-CELL-1010')
        self.assertEqual(result['label'], 'INSUFFICIENT')
        self.assertIn('E3', result['missing'])

    def test_competing_directions_remain_unresolved(self):
        result = self.evaluate('NR-CELL-1007')
        self.assertEqual(result['label'], 'INSUFFICIENT')
        self.assertCountEqual(result['candidates'], ['COVERAGE', 'CONGESTION'])

    def test_failed_tool_does_not_yield_definitive_label(self):
        result = with_review({'answer': 'COVERAGE', 'trace': [
            {'kind': 'tool', 'name': 'compare_windows', 'result': {'error': '失败'}}
        ]})
        self.assertEqual(result['model_answer'], 'COVERAGE')
        self.assertEqual(result['review']['label'], 'INSUFFICIENT')
