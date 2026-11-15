import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'src'))
from wireless_lab.capacity import calculate
from wireless_lab.routing import route
from wireless_lab.planner import plan

class Core(unittest.TestCase):
    def test_known_capacity(self): self.assertAlmostEqual(calculate(20,15)['capacity_mbps'],100.556153467,places=7)
    def test_0db(self): self.assertAlmostEqual(calculate(10,0)['capacity_mbps'],10)
    def test_negative_db_is_valid(self): self.assertAlmostEqual(calculate(5,-10)['capacity_mbps'],0.687517,places=5)
    def test_invalid_bandwidth(self):
        for bad in [0,-1,'20',True,None,float('nan')]:
            with self.subTest(bad=bad),self.assertRaises(ValueError): calculate(bad,15)
    def test_invalid_snr(self):
        for bad in ['15',float('nan'),float('inf'),5000,-5000]:
            with self.subTest(bad=bad),self.assertRaises(ValueError): calculate(20,bad)
    def test_route_boundaries(self):
        for snr,expect in [(-5,'low'),(-0.01,'low'),(0,'mid'),(19.99,'mid'),(20,'high'),(25,'high')]:
            with self.subTest(snr=snr): self.assertEqual(route(snr)['branch'],expect)
    def test_route_invalid(self):
        with self.assertRaises(ValueError):route(float('nan'))
    def test_plan_not_trace(self):
        p=plan('batch-audit-diagnose')
        self.assertIn('NOT_AN_EXECUTION_TRACE',p['kind'])
        self.assertEqual(p['skill_loads'],['wireless-link-workflow','wireless-capacity-audit','wireless-ops-diagnosis'])
