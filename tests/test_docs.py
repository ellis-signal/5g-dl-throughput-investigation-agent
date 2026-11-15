import json
import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

class Documents(unittest.TestCase):
    def test_eight_lectures(self):
        docs=list((ROOT/'lessons').glob('L*.md'))
        self.assertEqual(len(docs),8)
    def test_all_markdown_links_valid(self):
        files=[ROOT/'LECTURES-INDEX.md',ROOT/'LECTURES-COMPLETE.md',ROOT/'README.md',ROOT/'docs/ARCHITECTURE.md'] + list((ROOT/'lessons').glob('*.md'))
        for p in files:
            text=p.read_text(encoding='utf8')
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith(('http:','https:','#')):continue
                with self.subTest(file=p.name,link=link):
                    self.assertTrue((p.parent/link).exists())
    def test_no_old_script_paths(self):
        for p in list((ROOT/'lessons').glob('*.md'))+[ROOT/'LECTURES-COMPLETE.md']:
            text=p.read_text(encoding='utf8')
            for disallowed in ('/scripts/capacity.py','/scripts/route.py','/scripts/workflow.py'):
                with self.subTest(file=p.name,disallowed=disallowed):
                    self.assertNotIn(disallowed,text)
    def test_schema_contract_names(self):
        source=json.loads((ROOT/'contracts/links-v1.schema.json').read_text())
        report=json.loads((ROOT/'contracts/report-v1.schema.json').read_text())
        self.assertIn('case_id',source['items']['required'])
        self.assertIn('verification_status',report['required'])
