import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def load_script(script):
    spec=importlib.util.spec_from_file_location(script,ROOT/'tools'/f'{script}.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class Skills(unittest.TestCase):
    def test_skill_links_and_count(self):
        self.assertEqual(load_script('check_skills').check(),[])
    def test_l2_no_implicit_l1(self):
        body=(ROOT/'.dsh/skills/wireless-capacity-examples/SKILL.md').read_text(encoding='utf-8')
        self.assertNotIn('沿用 L1',body)
        self.assertIn('../../../knowledge/wireless/shannon.md',body)
    def test_only_l8_uses_skill_loader_instruction(self):
        for p in (ROOT/'.dsh/skills').glob('*/SKILL.md'):
            body=p.read_text(encoding='utf-8')
            if p.parent.name=='wireless-link-orchestrator':self.assertIn('`skill`',body)
            else:self.assertNotIn('调用另一个 Skill',body)
    def test_all_contracts_json_valid(self):
        for p in (ROOT/'contracts').glob('*.json'):
            self.assertTrue(json.loads(p.read_text(encoding='utf-8')))
    def test_profile_flags(self):
        module=load_script('set_profile')
        u,m=module.profile_flags('integrated','wireless-capacity')
        self.assertEqual((u,m),(True,True))
        self.assertEqual(module.profile_flags('integrated','wireless-capacity-code'),(False,False))
        self.assertEqual(module.profile_flags('integrated','wireless-link-orchestrator'),(True,False))
    def test_trace_evaluator_positive_negative(self):
        m=load_script('evaluate_trace')
        passed=json.loads((ROOT/'eval/synthetic-trace-pass.json').read_text(encoding='utf-8'))
        failed=json.loads((ROOT/'eval/synthetic-trace-missing-audit.json').read_text(encoding='utf-8'))
        self.assertEqual(m.assess(passed)['status'],'PASS')
        self.assertEqual(m.assess(failed)['status'],'FAIL')
    def test_trace_evaluator_fails_on_premature_load(self):
        m=load_script('evaluate_trace')
        obj=json.loads((ROOT/'eval/synthetic-trace-pass.json').read_text(encoding='utf-8'))
        obj['events'].pop(0)
        self.assertEqual(m.assess(obj)['status'],'FAIL')
