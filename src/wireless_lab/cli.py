"""Unified CLI: all numeric tools are stdlib-only and deterministic."""
import argparse
import json
import sys
from pathlib import Path

from .capacity import calculate
from .routing import route
from .workflow import json_file, load_source, compute_report, write_json, verify_report
from .audit import audit
from .planner import PLAN_TEMPLATES, plan
from .dl_kpi import load_dataset
from .dl_rca import investigate, find_cell
from .dl_audit import audit as audit_ledger
from .dl_render import render_cell


def parser_for_cli():
    p = argparse.ArgumentParser(prog='wireless', description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('capacity'); a.add_argument('--bandwidth-mhz',type=float,required=True); a.add_argument('--snr-db',type=float,required=True)
    a = sub.add_parser('route'); a.add_argument('--snr-db',type=float,required=True)
    a = sub.add_parser('plan'); a.add_argument('--task', choices=PLAN_TEMPLATES, required=True)
    a = sub.add_parser('validate'); a.add_argument('--input',required=True)
    a = sub.add_parser('compute'); a.add_argument('--input',required=True); a.add_argument('--output',required=True)
    for name in ('verify','audit'):
        a = sub.add_parser(name); a.add_argument('--input',required=True); a.add_argument('--report',required=True); a.add_argument('--receipt')
    a = sub.add_parser('dl-validate'); a.add_argument('--input',required=True)
    a = sub.add_parser('dl-investigate'); a.add_argument('--input',required=True); a.add_argument('--output',required=True)
    a = sub.add_parser('dl-audit'); a.add_argument('--input',required=True); a.add_argument('--ledger',required=True); a.add_argument('--receipt')
    a = sub.add_parser('dl-render'); a.add_argument('--input',required=True); a.add_argument('--cell',required=True); a.add_argument('--output',required=True); a.add_argument('--receipt')
    return p


def main(argv=None):
    args = parser_for_cli().parse_args(argv)
    try:
        if args.cmd == 'capacity': result = calculate(args.bandwidth_mhz, args.snr_db)
        elif args.cmd == 'route': result = route(args.snr_db)
        elif args.cmd == 'plan': result = plan(args.task)
        elif args.cmd == 'validate':
            cases = load_source(args.input)
            result = {'status':'PASS','step':'validate','case_count':len(cases)}
        elif args.cmd == 'compute':
            result = compute_report(args.input)
            path = write_json(args.output, result)
            result = {'status':'UNVERIFIED','step':'compute','output':path,'case_count':result['case_count']}
        elif args.cmd == 'dl-validate':
            dataset = load_dataset(args.input)
            result = {'status':'PASS','step':'dl-validate','dataset_id':dataset['dataset_id'],
                      'cell_count':len(dataset['cells']),'source':dataset['source']}
        elif args.cmd == 'dl-investigate':
            ledger = investigate(load_dataset(args.input))
            path = write_json(args.output, ledger)
            result = {'status':'UNVERIFIED','step':'dl-investigate','output':path,
                      'ledger_sha256':ledger['ledger_sha256'],'summary':ledger['summary']['causes'],
                      'cell_count':ledger['summary']['cell_count']}
        elif args.cmd == 'dl-audit':
            dataset = load_dataset(args.input)
            receipt = audit_ledger(dataset, json_file(args.ledger), dataset_path=args.input)
            if args.receipt: write_json(args.receipt, receipt)
            print(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False))
            return 0 if receipt['status'] == 'PASS' else 1
        elif args.cmd == 'dl-render':
            dataset = load_dataset(args.input)
            cell = find_cell(investigate(dataset), args.cell)
            receipt = json_file(args.receipt) if args.receipt else None
            Path(args.output).write_text(render_cell(cell, dataset=dataset, receipt=receipt), encoding='utf-8')
            result = {'status':'PASS' if receipt and receipt['status'] == 'PASS' else 'UNVERIFIED',
                      'step':'dl-render','output':str(args.output),'cell_id':args.cell}
        elif args.cmd in ('verify','audit'):
            if args.cmd == 'verify': errors = verify_report(args.input, json_file(args.report))
            else: errors = audit(args.input, json_file(args.input), json_file(args.report))
            result = {'status':'PASS' if not errors else 'FAIL', 'step':args.cmd,
                      'source_path':str(args.input), 'report_path':str(args.report), 'errors':errors,
                      'error_count':len(errors)}
            if args.receipt: write_json(args.receipt, result)
            print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
            return 0 if not errors else 1
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, TypeError, OverflowError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
