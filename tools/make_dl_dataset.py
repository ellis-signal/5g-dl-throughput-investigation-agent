#!/usr/bin/env python3
"""Generate the deterministic synthetic KPI dataset used by the MVP.

Injection rules are fixed here, BEFORE the data exists, and are documented in
docs/MVP.md: one fault class per cell, noise on every other metric.
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'dl_cells_kpi.json'
SEED = 20261008
N = 24

CELLS = [
    {
        'cell_id': 'NR-CELL-1001', 'sector': 'Sector 1 · 城区',
        'complaint': '用户反馈网页与视频明显变慢，室内尤其明显。',
        'fault': 'coverage',
        'base': {'tput': 380, 'rsrp': -92.0, 'sinr': 14.0, 'cqi': 10.0, 'prb': 45.0, 'users': 38, 'bler': 4.0},
        'inc': {'tput': 205, 'rsrp': -108.0, 'sinr': 8.5, 'cqi': 7.0, 'prb': 40.0, 'users': 36, 'bler': 6.0},
    },
    {
        'cell_id': 'NR-CELL-1002', 'sector': 'Sector 2 · 城区',
        'complaint': '投诉集中在同一时段：网页打开慢、视频持续缓冲。',
        'fault': 'interference',
        'base': {'tput': 470, 'rsrp': -95.0, 'sinr': 18.0, 'cqi': 12.0, 'prb': 52.0, 'users': 42, 'bler': 4.0},
        'inc': {'tput': 96, 'rsrp': -94.6, 'sinr': 1.5, 'cqi': 5.0, 'prb': 54.0, 'users': 43, 'bler': 19.0},
    },
    {
        'cell_id': 'NR-CELL-1003', 'sector': 'Sector 3 · 商圈',
        'complaint': '晚高峰用户抱怨卡顿，白天正常。',
        'fault': 'congestion',
        'base': {'tput': 540, 'rsrp': -90.0, 'sinr': 20.0, 'cqi': 13.0, 'prb': 42.0, 'users': 30, 'bler': 3.0},
        'inc': {'tput': 430, 'rsrp': -90.3, 'sinr': 19.0, 'cqi': 12.0, 'prb': 97.0, 'users': 130, 'bler': 5.0},
    },
    {
        'cell_id': 'NR-CELL-1004', 'sector': 'Sector 1 · 郊区',
        'complaint': '无投诉，纳入同批数据作为对照。',
        'fault': 'none',
        'base': {'tput': 455, 'rsrp': -91.0, 'sinr': 17.5, 'cqi': 12.0, 'prb': 48.0, 'users': 40, 'bler': 3.0},
        'inc': {'tput': 448, 'rsrp': -91.2, 'sinr': 17.6, 'cqi': 12.0, 'prb': 49.0, 'users': 41, 'bler': 3.0},
    },
]


def clip(value, low, high):
    return max(low, min(high, value))


def samples(window, day, mean, rng):
    rows = []
    for hour in range(N):
        rows.append({
            'window': window,
            'timestamp': f'2026-10-{day:02d}T{hour:02d}:00:00Z',
            'rsrp_dbm': round(mean['rsrp'] + rng.gauss(0, 0.6), 2),
            'sinr_db': round(mean['sinr'] + rng.gauss(0, 0.5), 2),
            'cqi': round(clip(mean['cqi'] + rng.gauss(0, 0.45), 0, 15), 2),
            'prb_utilization_pct': round(clip(mean['prb'] + rng.gauss(0, 2.5), 0, 100), 2),
            'active_users': round(max(1.0, mean['users'] + rng.gauss(0, 1.2)), 2),
            'dl_throughput_mbps': round(max(0.1, mean['tput'] + rng.gauss(0, 0.03 * mean['tput'])), 2),
            'bler_pct': round(clip(mean['bler'] + rng.gauss(0, 0.8), 0, 100), 2),
        })
    return rows


def main():
    rng = random.Random(SEED)
    cells = []
    for cell in CELLS:
        cells.append({
            'cell_id': cell['cell_id'],
            'sector': cell['sector'],
            'complaint': cell['complaint'],
            'bandwidth_mhz': 100,
            'samples': samples('baseline', 1, cell['base'], rng) + samples('incident', 8, cell['inc'], rng),
        })
    payload = {
        'schema_version': 1,
        'dataset_id': 'dl-throughput-investigation-2026-10',
        'description': '合成数据：4 小区 × 2 窗口 × 24 小时；每小区注入一类故障，其余指标仅加噪声。',
        'cells': cells,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'wrote {OUT} ({len(cells)} cells)')


if __name__ == '__main__':
    main()