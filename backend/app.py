"""FastAPI backend for the 5G DL root-cause investigation.

Serves the static frontend and exposes the evidence ledger, single-cell views,
Markdown reports and the independent audit receipt. All analysis lives in
`wireless_lab.*` and is stdlib-only; this module is a thin HTTP adapter.

Run:
    python -m uvicorn backend.app:app --port 8765
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / 'src'))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, PlainTextResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from wireless_lab.dl_audit import audit  # noqa: E402
from wireless_lab.dl_kpi import load_dataset  # noqa: E402
from wireless_lab.dl_rca import find_cell, investigate, omit_prb  # noqa: E402
from wireless_lab.dl_render import render_cell  # noqa: E402

FRONTEND_DIR = BASE_DIR / 'frontend'
DATA_PATH = BASE_DIR / 'data' / 'dl_cells_kpi.json'

app = FastAPI(
    title='5G DL RCA Backend',
    description='Evidence ledger, independent audit and Markdown report for one downlink degradation case.',
    version='1.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

_cache = {}


def _dataset():
    if 'dataset' not in _cache:
        _cache['dataset'] = load_dataset(str(DATA_PATH))
    return _cache['dataset']


def _ledger():
    if 'ledger' not in _cache:
        _cache['ledger'] = investigate(_dataset())
    return _cache['ledger']


class AuditRequest(BaseModel):
    ledger: dict
    cell_id: str | None = None


app.mount('/static', StaticFiles(directory=str(FRONTEND_DIR)), name='static')  # legacy path


@app.get('/')
def index():
    return FileResponse(FRONTEND_DIR / 'index.html')


@app.get('/health')
def health():
    ledger = _ledger()
    return {
        'status': 'ok',
        'method_version': ledger['method_version'],
        'dataset_id': ledger['dataset']['dataset_id'],
        'cell_count': ledger['summary']['cell_count'],
        'ledger_sha256': ledger['ledger_sha256'],
        'verification_status': ledger['verification_status'],
    }


@app.get('/api/cells')
def cells():
    ledger = _ledger()
    return {
        'dataset': ledger['dataset'],
        'method_version': ledger['method_version'],
        'summary': ledger['summary'],
    }


@app.get('/api/ledger')
def get_ledger():
    return _ledger()


@app.get('/api/cell/{cell_id}')
def get_cell(cell_id: str, omit: str | None = None):
    try:
        cell = find_cell(_ledger(), cell_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if omit:
        if omit != 'prb':
            raise HTTPException(status_code=400, detail='unsupported omit field; only "prb" is simulated')
        cell = omit_prb(cell)
    return {
        'schema_version': _ledger()['schema_version'],
        'method_version': _ledger()['method_version'],
        'verification_status': 'UNVERIFIED',
        'cell': cell,
    }


@app.get('/api/report/{cell_id}', response_class=PlainTextResponse)
def get_report(cell_id: str):
    try:
        cell = find_cell(_ledger(), cell_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PlainTextResponse(render_cell(cell, dataset=_dataset()), media_type='text/markdown; charset=utf-8')


@app.post('/api/audit')
def post_audit(payload: AuditRequest):
    receipt = audit(_dataset(), payload.ledger, dataset_path=str(DATA_PATH))
    return receipt


class AgentRequest(BaseModel):
    case_id: str
    question: str = ''


@app.post('/api/agent')
def investigate_agent(payload: AgentRequest):
    from wireless_lab.agent import run
    try:
        return run(payload.case_id, 'D', payload.question.strip() or None)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'模型服务或调查工具不可用: {exc}') from exc


# Mounted last so the /api/* routes above win over the static catch-all.
app.mount('/', StaticFiles(directory=str(FRONTEND_DIR), html=True), name='site')