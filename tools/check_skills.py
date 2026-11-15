#!/usr/bin/env python3
"""Static checker for eight skills: no hidden L1->L2 dependency, valid one-hop references."""
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parent.parent
NAMES={'wireless-capacity','wireless-capacity-examples','wireless-capacity-code','wireless-link-branch','wireless-link-workflow','wireless-ops-diagnosis','wireless-capacity-audit','wireless-link-orchestrator'}

def check():
    errors=[]
    skills={p.parent.name:p for p in (ROOT/'.dsh'/'skills').glob('*/SKILL.md')}
    if set(skills)!=NAMES: errors.append(f'skill set mismatch {set(skills)^NAMES}')
    for name,p in skills.items():
        data=p.read_text(encoding='utf8')
        if not data.startswith('---\n') or '\n---\n' not in data[4:]:
            errors.append(f'{name}: bad frontmatter');continue
        head,body=data[4:].split('\n---\n',1)
        props=dict(re.findall(r'(?m)^([a-z-]+):\s*(.+)$',head))
        if props.get('name')!=name:errors.append(f'{name}: frontmatter name mismatch')
        if not props.get('description'):errors.append(f'{name}: description missing')
        for key in ('user-invocable','disable-model-invocation'):
            if props.get(key) not in ('true','false'): errors.append(f'{name}: invalid {key}')
        if len(body.splitlines())>500:errors.append(f'{name}: body > 500 lines')
        if re.search(r'沿用\s*L[1-8]|参照\s*L[1-8]',body):errors.append(f'{name}: lesson-dependent instructions')
        if name!='wireless-link-orchestrator' and re.search(r'\bskill\s*\(',body): errors.append(f'{name}: unexpected cross skill loader')
        for link in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)',body):
            if link.startswith('http'): continue
            pth=(p.parent/link).resolve()
            if not pth.is_file():errors.append(f'{name}: broken link {link}')
            if not pth.is_relative_to(ROOT.resolve()):errors.append(f'{name}: link outside repository {link}')
        if name!='wireless-link-orchestrator' and 'wireless-link-orchestrator' in body:errors.append('reverse orchestrator dependency')
    return errors

if __name__=='__main__':
    issues=check()
    print('PASS: 8 skills, valid frontmatter + references' if not issues else 'FAIL:\n'+'\n'.join(issues))
    sys.exit(1 if issues else 0)
