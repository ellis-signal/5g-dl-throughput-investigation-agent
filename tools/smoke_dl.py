import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from wireless_lab.dl_rca import load_and_investigate  # noqa: E402

ledger = load_and_investigate('data/dl_cells_kpi.json')
print('ledger sha256:', ledger['ledger_sha256'][:16], 'cells:', len(ledger['cells']))
for cell in ledger['cells']:
    print(f"\n{cell['cell_id']} delta={cell['signals']['throughput_delta_pct']:+.2f}% "
          f"ratio={cell['radio']['actual_to_expected_ratio']:.2f} "
          f"-> {cell['dominant_cause']['code']} @ {cell['dominant_cause']['confidence']}")
    for h in cell['hypotheses']:
        print(f"   {h['hypothesis_id']} {h['verdict']:<12} {h['confidence']:<5} {h['basis'][:70]}")
    print('   recs:', [r['recommendation_id'] for r in cell['recommendations']])