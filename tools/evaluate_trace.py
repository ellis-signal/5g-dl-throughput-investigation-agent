#!/usr/bin/env python3
"""Rubric for manually NORMALIZED DSH traces. Synthetic fixtures are not proof of live DSH execution."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'src'))
from wireless_lab.planner import plan


def assess(obj):
    errors=[]
    if not isinstance(obj,dict) or 'task_type' not in obj or 'events' not in obj:
        return {'status':'FAIL','errors':['expected task_type and events']}
    try: expected=plan(obj['task_type'])
    except KeyError: return {'status':'FAIL','errors':['unknown task_type']}
    events=obj['events']
    if not isinstance(events,list):return {'status':'FAIL','errors':['events must be a list']}
    load_events=[(i,e.get('name')) for i,e in enumerate(events) if isinstance(e,dict) and e.get('kind')=='skill_load']
    if [name for _,name in load_events]!=expected['skill_loads']:
        errors.append(f'skill loads expected {expected["skill_loads"]}, got {[n for _,n in load_events]}')
    executed=[]
    for i,e in enumerate(events):
        if not isinstance(e,dict): errors.append(f'events[{i}]: not an object');continue
        if e.get('kind') not in ('skill_load','tool','file_read','final'):
            errors.append(f'events[{i}]: invalid kind');continue
        if e.get('kind')=='tool':
            if not isinstance(e.get('exit_code'),int) or isinstance(e.get('exit_code'),bool):
                errors.append(f'events[{i}]: missing real exit_code')
            executed.append((i,e.get('action'),e.get('status')))
        if e.get('kind')=='file_read':
            if not isinstance(e.get('path'),str) or not e.get('path'):
                errors.append(f'events[{i}]: missing read path')
            executed.append((i,e.get('action'),None))
    actions=[action for _,action,_ in executed]
    target=[s['action'] for s in expected['steps']]
    if actions!=target:errors.append(f'action coverage/order expected {target}, got {actions}')
    loaded={}
    for i,name in load_events:
        loaded.setdefault(name,i)
    for index, action, _ in executed:
        step=next((s for s in expected['steps'] if s['action']==action),None)
        if step and (step['skill'] not in loaded or loaded[step['skill']]>index):
            errors.append(f'{action}: missing prior real skill_load for {step["skill"]}')
    for i,action,status in executed:
        if events[i].get('kind')=='tool' and events[i].get('exit_code')!=0:
            errors.append(f'{action}: CLI exit code not zero')
        if action in ('validate','verify','audit') and (status!='PASS' or events[i].get('exit_code')!=0):
            errors.append(f'{action}: not successful')
        if action=='compute' and (status!='UNVERIFIED' or events[i].get('exit_code')!=0):
            errors.append('compute: missing UNVERIFIED success')
    final=[e for e in events if isinstance(e,dict) and e.get('kind')=='final']
    if len(final)!=1 or final[0].get('status')!='PASS': errors.append('final PASS not supported by one explicit final event')
    for i,e in enumerate(events):
        if not isinstance(e,dict) or e.get('kind')!='final': continue
        if i!=len(events)-1:errors.append('final before end of trajectory')
    return {
        'status':'PASS' if not errors else 'FAIL','task_type':obj['task_type'],
        'expected_skill_loads':len(expected['skill_loads']), 'observed_skill_loads':len(load_events),
        'expected_actions':len(target),'observed_actions':len(actions),'errors':errors,
        'warning':'This rubric checks a normalized record, not the authenticity of the underlying Harness trace.'
    }


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True)
    args=parser.parse_args()
    try:
        obj=json.loads(Path(args.input).read_text(encoding='utf8'))
        verdict=assess(obj)
        print(json.dumps(verdict,indent=2,ensure_ascii=False))
        return 0 if verdict['status']=='PASS' else 1
    except (OSError,ValueError) as exc:
        print(f'ERROR {exc}',file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
