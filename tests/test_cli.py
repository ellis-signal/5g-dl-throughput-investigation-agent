import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
CMD=[sys.executable,str(ROOT/'tools/wireless.py')]

def call(*args): return subprocess.run(CMD+list(map(str,args)),cwd=ROOT,text=True,capture_output=True)

class CLI(unittest.TestCase):
    def test_capacity_cli_success(self):
        p=call('capacity','--bandwidth-mhz','20','--snr-db','15')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertAlmostEqual(json.loads(p.stdout)['capacity_mbps'],100.556153467,places=5)
    def test_bad_input_exit_two(self):
        p=call('capacity','--bandwidth-mhz','0','--snr-db','15')
        self.assertEqual(p.returncode,2)
        self.assertIn('bandwidth_mhz',p.stderr)
    def test_validate_real_input(self):
        p=call('validate','--input','data/links.json')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)['case_count'],4)
    def test_full_workflow(self):
        with tempfile.TemporaryDirectory() as t:
            output=str(Path(t)/'result.json'); ver=str(Path(t)/'verify.json'); aud=str(Path(t)/'audit.json')
            for params,expected in [
                (('compute','--input','data/links.json','--output',output),'UNVERIFIED'),
                (('verify','--input','data/links.json','--report',output,'--receipt',ver),'PASS'),
                (('audit','--input','data/links.json','--report',output,'--receipt',aud),'PASS'),
            ]:
                p=call(*params);self.assertEqual(p.returncode,0,p.stderr+p.stdout)
                self.assertEqual(json.loads(p.stdout)['status'],expected)
            doc=json.loads(Path(output).read_text())
            self.assertEqual(doc['verification_status'],'UNVERIFIED') # report cannot self certify
            self.assertEqual(len(doc['cases']),4)
            self.assertEqual(json.loads(Path(aud).read_text())['status'],'PASS')
    def test_bad_report_audit_fails(self):
        p=call('audit','--input','data/links.json','--report','fixtures/bad_report.json')
        self.assertEqual(p.returncode,1,p.stderr)
        d=json.loads(p.stdout)
        self.assertEqual(d['status'],'FAIL')
        self.assertTrue(any('link-a.capacity_mbps' in e for e in d['errors']))
    def test_source_sha_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'source.json';source.write_text((ROOT/'data/links.json').read_text())
            output=Path(t)/'result.json'
            self.assertEqual(call('compute','--input',source,'--output',output).returncode,0)
            altered=json.loads(source.read_text());altered[0]['actual_throughput_mbps']=75
            source.write_text(json.dumps(altered))
            for sub in ('verify','audit'):
                p=call(sub,'--input',source,'--report',output)
                self.assertEqual(p.returncode,1,p.stderr)
                self.assertIn('source',p.stdout)
    def test_reject_duplicate_id(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'bad.json';d=json.loads((ROOT/'data/links.json').read_text())
            d[1]['case_id']=d[0]['case_id'];source.write_text(json.dumps(d))
            p=call('validate','--input',source)
            self.assertEqual(p.returncode,2)
            self.assertIn('unique',p.stderr)
    def test_audit_fails_capacity_tamper(self):
        with tempfile.TemporaryDirectory() as t:
            report=Path(t)/'result.json';call('compute','--input','data/links.json','--output',report)
            d=json.loads(report.read_text());d['cases'][0]['capacity_mbps']=999
            report.write_text(json.dumps(d))
            self.assertEqual(call('verify','--input','data/links.json','--report',report).returncode,1)
            self.assertEqual(call('audit','--input','data/links.json','--report',report).returncode,1)
    def test_plan_cli_no_skill_load_claim(self):
        p=call('plan','--task','batch-audit')
        self.assertEqual(p.returncode,0)
        self.assertIn('NOT_AN_EXECUTION_TRACE',json.loads(p.stdout)['kind'])

class MoreCLI(unittest.TestCase):
    def test_extra_source_fields_rejected_consistent_with_schema(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'bad.json'
            obj=json.loads((ROOT/'data/links.json').read_text())
            obj[0]['unknown']='oops';source.write_text(json.dumps(obj))
            p=call('validate','--input',source)
            self.assertEqual(p.returncode,2)
            self.assertIn('unexpected fields',p.stderr)
    def test_actual_over_model_bound_flagged(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'s.json';report=Path(t)/'r.json'
            obj=json.loads((ROOT/'data/links.json').read_text())
            obj[0]['actual_throughput_mbps']=9999
            source.write_text(json.dumps(obj))
            self.assertEqual(call('compute','--input',source,'--output',report).returncode,0)
            p=call('audit','--input',source,'--report',report)
            self.assertEqual(p.returncode,1)
            self.assertIn('theoretical bound',p.stdout)
