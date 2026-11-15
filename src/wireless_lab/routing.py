"""Illustrative SNR router, not a standards-defined wireless threshold."""
from .capacity import finite_number

BRANCH_FILES = {
    'low': 'knowledge/wireless/low-snr.md',
    'mid': 'knowledge/wireless/mid-snr.md',
    'high': 'knowledge/wireless/high-snr.md',
}


def route(snr_db):
    snr_db = finite_number(snr_db, 'snr_db')
    branch = 'low' if snr_db < 0 else ('mid' if snr_db < 20 else 'high')
    return {
        'snr_db': snr_db,
        'branch': branch,
        'reference': BRANCH_FILES[branch],
        'threshold_source': 'classroom-only heuristic; not a 3GPP/IEEE threshold',
    }
