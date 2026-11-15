"""Run A/B/C comparisons and reuse C's recorded tool results to score D."""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wireless_lab.agent import CASES, run, with_review


def score(result, expected):
    match = re.search(r'\{[\s\S]*\}', result['answer'])
    try:
        parsed = json.loads(match.group()) if match else {}
    except ValueError:
        parsed = {}
    label = str(parsed.get('label', '')).upper()
    called = [event['name'] for event in result['trace']
              if event['kind'] == 'tool' and 'error' not in event['result']]
    return dict(mode=result['mode'], case_id=result['case_id'], expected=expected,
                label=label, correct=int(label == expected),
                required_tools=int({'get_kpi', 'compare_windows'} <= set(called)),
                tool_calls=len(called), seconds=result['seconds'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results' / 'reproduction')
    args = parser.parse_args()
    traces = args.output / 'traces'
    traces.mkdir(parents=True, exist_ok=True)
    cases = json.loads(CASES.read_text(encoding='utf-8'))
    rows = []
    for mode in 'ABC':
        for case in cases:
            result = run(case['id'], mode)
            outputs = [result, with_review(result)] if mode == 'C' else [result]
            for item in outputs:
                row = score(item, case['expected'])
                rows.append(row)
                (traces / f"{row['mode']}-{row['case_id']}.json").write_text(
                    json.dumps(item, ensure_ascii=False, indent=2), encoding='utf-8')
                print(json.dumps(row, ensure_ascii=False), flush=True)
    with (args.output / 'evaluation.csv').open('w', newline='', encoding='utf-8-sig') as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    main()
