"""Canonical JSON + hash shared by the ledger writer and the auditor.

Numbers are normalized to float before hashing so an int/float round-trip
through a JavaScript client (JSON.stringify drops the trailing ".0") cannot
change the digest. This module contains no thresholds or verdicts.
"""
import hashlib
import json


def _normalize(value):
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    return value


def canonical_json(value):
    return json.dumps(_normalize(value), ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def canonical_sha256(value):
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()