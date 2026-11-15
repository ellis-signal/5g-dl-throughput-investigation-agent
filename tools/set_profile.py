#!/usr/bin/env python3
"""Switch frontmatter gating between classroom and integrated profiles."""
import argparse
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'.dsh'/'skills'
ALL={p.parent.name:p for p in DIR.glob('*/SKILL.md')}


def profile_flags(profile, name):
    if profile == 'teaching':
        return True, False
    if name in {'wireless-capacity','wireless-capacity-examples'}:
        return True, True
    if name == 'wireless-link-orchestrator':
        return True, False
    return False, False


def replace_key(text, key, value):
    value='true' if value else 'false'
    pattern=rf'(?m)^{re.escape(key)}:\s*(?:true|false)\s*$'
    replaced,n=re.subn(pattern,f'{key}: {value}',text)
    if n!=1: raise ValueError(f'expected exactly one {key} field; got {n}')
    return replaced


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--set',choices=['teaching','integrated'], required=True)
    args=parser.parse_args()
    if len(ALL)!=8: raise RuntimeError(f'Expected 8 skills, found {len(ALL)}')
    for name,path in sorted(ALL.items()):
        inv,disabled=profile_flags(args.set,name)
        text=path.read_text(encoding='utf8')
        text=replace_key(text,'user-invocable',inv)
        text=replace_key(text,'disable-model-invocation',disabled)
        path.write_text(text,encoding='utf8')
        print(f'{name:32} user-invocable={str(inv).lower():5} disable-model-invocation={str(disabled).lower()}')
    print(f'ACTIVE_PROFILE={args.set} (actual Harness behavior must be tested in a session)')

if __name__=='__main__':main()
