#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo '== Phase A: skill / knowledge references =='
python3 tools/check_skills.py
echo '== Phase B: code =='
python3 tools/wireless.py capacity --bandwidth-mhz 20 --snr-db 15
for snr in -5 10 25; do python3 tools/wireless.py route --snr-db "$snr"; done
python3 tools/wireless.py validate --input data/links.json
python3 tools/wireless.py compute --input data/links.json --output outputs/link_report.json
python3 tools/wireless.py verify --input data/links.json --report outputs/link_report.json --receipt outputs/verify_receipt.json
python3 tools/wireless.py audit --input data/links.json --report outputs/link_report.json --receipt outputs/audit_receipt.json
echo '== Expected failure: deliberately malformed report =='
if python3 tools/wireless.py audit --input data/links.json --report fixtures/bad_report.json; then
    echo 'ERROR: malformed report unexpectedly passed' >&2; exit 1
else
    code=$?
    if [ "$code" -ne 1 ]; then echo "ERROR: expected audit exit 1, got $code" >&2; exit 1; fi
    echo 'EXPECTED FAIL: malformed report rejected (exit=1)'
fi
echo '== Phase C: synthetic fixture validation (not DSH execution) =='
python3 tools/evaluate_trace.py --input eval/synthetic-trace-pass.json
if python3 tools/evaluate_trace.py --input eval/synthetic-trace-missing-audit.json; then
    echo 'ERROR: missing-audit trace unexpectedly passed' >&2; exit 1
else
    code=$?
    if [ "$code" -ne 1 ]; then echo "ERROR: expected evaluator exit 1, got $code" >&2; exit 1; fi
    echo 'EXPECTED FAIL: missing audit action rejected (exit=1)'
fi
echo '== Phase D: regression tests =='
python3 -m unittest discover -s tests -v
echo 'ALL LOCAL TESTS PASSED — DSH live integration is not covered.'
