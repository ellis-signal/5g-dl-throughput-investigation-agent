/* ============================================================
   RAN FORENSICS — 证据账本渲染器
   数据来源：优先 GET /api/ledger（后端账本）；file:// 打开时用
   内嵌的同一份账本（ledger-data.js）。页面不做判定，只呈现。
   ============================================================ */

const API = location.protocol === 'file:' ? '' : '/api';

const METRIC = {
  rsrp_dbm_median: { label: 'RSRP 中位数', dec: 1, signed: true },
  rsrp_delta_db: { label: 'RSRP 变化', dec: 2, signed: true },
  sinr_db_median: { label: 'SINR 中位数', dec: 1, signed: true },
  sinr_delta_db: { label: 'SINR 变化', dec: 2, signed: true },
  cqi_mean: { label: 'CQI 均值', dec: 1, signed: true },
  cqi_delta: { label: 'CQI 变化', dec: 2, signed: true },
  prb_utilization_pct_mean: { label: 'PRB 利用率', dec: 1, signed: true },
  active_users_mean: { label: '并发用户', dec: 1, kind: 'ratio' },
  per_user_throughput_mbps: { label: '每用户吞吐', dec: 2, kind: 'ratio' },
  bler_pct_mean: { label: 'BLER', dec: 1, signed: true },
  actual_to_expected_ratio: { label: '实际/期望吞吐', dec: 2 },
  cqi_residual: { label: 'CQI 残差', dec: 2, signed: true }
};

const CAUSE_FALLBACK = {
  COVERAGE_INSUFFICIENCY: '无线覆盖不足',
  INTERFERENCE: '信号干扰',
  RESOURCE_CONGESTION: '小区资源拥塞',
  NO_SIGNIFICANT_DEGRADATION: '无显著劣化',
  UNDETERMINED: '现有证据不足以判定'
};

const state = {
  mode: 'embedded',
  ledger: null,
  cellId: null,
  override: null,
  hidePrb: false,
  filter: 'all',
  receipt: null
};

const $ = (s, r = document) => r.querySelector(s);
const nf = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v)) ? '—' : Number(v).toFixed(d);
const sgn = (v, d = 1) => (v > 0 ? '+' : '') + Number(v).toFixed(d);
const pct = v => (v > 0 ? '+' : '') + Number(v).toFixed(1) + '%';

/* ---------- 账本 -> 视图模型 ---------- */
function metricOf(check) {
  const meta = METRIC[check.metric] || { label: check.metric, dec: 1, signed: true };
  return { key: check.metric, ...meta };
}

function adaptCheck(check, gates) {
  const meta = metricOf(check);
  const pass = check.direction === 'supports' ? true
    : check.direction === 'refutes' ? false : null;
  return {
    id: check.check_id,
    metric: meta.label,
    base: check.baseline,
    inc: check.incident,
    delta: check.delta,
    thr: check.threshold,
    dec: meta.dec,
    signed: meta.signed !== false,
    kind: meta.kind || 'abs',
    pass,
    gate: gates.includes(check.check_id),
    dir: check.direction
  };
}

function adaptCell(cell) {
  const b = cell.baseline, i = cell.incident, s = cell.signals || {};
  return {
    id: cell.cell_id,
    sector: cell.sector || '',
    complaint: cell.complaint || '',
    base: {
      tput: b.dl_throughput_mbps_mean, rsrp: b.rsrp_dbm_median, sinr: b.sinr_db_median,
      cqi: b.cqi_mean, prb: b.prb_utilization_pct_mean, users: b.active_users_mean
    },
    inc: {
      tput: i.dl_throughput_mbps_mean, rsrp: i.rsrp_dbm_median, sinr: i.sinr_db_median,
      cqi: i.cqi_mean, prb: i.prb_utilization_pct_mean, users: i.active_users_mean
    },
    d: {
      tputPct: s.throughput_delta_pct,
      rsrp: s.rsrp_delta_db, sinr: s.sinr_delta_db, cqi: s.cqi_delta,
      prb: s.prb_delta_pp, usersRatio: s.users_ratio,
      perUserRatio: s.per_user_throughput_ratio,
      atRatio: (cell.radio || {}).actual_to_expected_ratio
    },
    hyps: (cell.hypotheses || []).map(h => ({
      id: h.hypothesis_id,
      name: h.label,
      statement: h.statement,
      gates: h.gate_checks || [],
      checks: (h.checks || []).map(c => adaptCheck(c, h.gate_checks || [])),
      verdict: h.verdict,
      conf: h.confidence,
      why: h.basis
    })),
    cause: (cell.dominant_cause || {}).code,
    causeLabel: (cell.dominant_cause || {}).label || CAUSE_FALLBACK[(cell.dominant_cause || {}).code],
    conf: (cell.dominant_cause || {}).confidence,
    reason: (cell.dominant_cause || {}).reason,
    degraded: cell.degraded,
    gaps: cell.missing_evidence || [],
    recs: (cell.recommendations || []).map(r => ({
      area: r.area, text: r.action, approval: r.requires_change_approval
    }))
  };
}

function currentCell() {
  if (!state.ledger) return null;
  return state.override || state.ledger.cells.find(c => c.cell_id === state.cellId);
}

function currentView() {
  const cell = currentCell();
  return cell ? adaptCell(cell) : null;
}

/* ---------- 渲染 ---------- */
function render() {
  const view = currentView();
  if (!view) return;
  renderCells();
  renderHeader(view);
  renderTiles(view);
  renderHyps(view);
  renderLedger(view);
  renderVerdict(view);
  renderAudit();
  renderFooter();
}

function renderCells() {
  const cells = state.ledger.summary.cells;
  $('#cellList').innerHTML = cells.map(c => {
    const dot = c.degraded ? 'warn' : 'ok';
    return `<li><button role="tab" aria-selected="${c.cell_id === state.cellId}" data-cell="${c.cell_id}">
      <span class="cid">${c.cell_id}</span><span class="cmeta">${c.sector || ''}</span>
      <span class="cdot ${dot}" aria-hidden="true"></span></button></li>`;
  }).join('');
  $('#cellList').querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => selectCell(btn.dataset.cell));
  });
}

function selectCell(id) {
  state.cellId = id;
  state.override = null;
  state.hidePrb = false;
  state.receipt = null;
  const toggle = $('#prbToggle');
  if (toggle) toggle.checked = false;
  render();
}

function renderHeader(view) {
  const cell = view.cell || view;
  $('#caseId').textContent = '#DL-2026-' + cell.id.slice(-4);
  $('#incidentId').textContent = cell.id;
  $('#incidentSector').textContent = cell.sector;
  $('#incidentComplaint').textContent = cell.complaint;
  $('#tputNow').textContent = Math.round(cell.inc.tput);
  $('#tputBase').textContent = '基线 ' + Math.round(cell.base.tput);
  const delta = $('#tputDelta');
  delta.textContent = pct(view.d.tputPct);
  delta.className = 'delta ' + (view.d.tputPct <= -1 ? 'neg' : 'flat');
  const source = state.ledger.dataset.source || {};
  $('#factSource').textContent = (source.path || '—').split(/[\\/]/).pop();
  $('#factHash').textContent = 'sha256:' + (source.sha256 || '').slice(0, 10) + '…';
}

const TILES = [
  { key: 'rsrp', label: 'RSRP / dBm', dec: 1, better: d => d < -0.5 ? 'down' : 'ok' },
  { key: 'sinr', label: 'SINR / dB', dec: 1, better: d => d < -0.5 ? 'down' : 'ok' },
  { key: 'cqi', label: 'CQI', dec: 1, better: d => d < -0.5 ? 'down' : 'ok' },
  { key: 'prb', label: 'PRB UTIL / %', dec: 1, better: d => d > 20 ? 'up' : 'ok', strip: true },
  { key: 'users', label: 'USERS', dec: 1, better: d => d > 20 ? 'up' : 'ok' }
];

function renderTiles(view) {
  const { base, inc } = view;
  $('#metricTiles').innerHTML = TILES.map(t => {
    const incValue = inc[t.key], baseValue = base[t.key];
    if (incValue === undefined || incValue === null) {
      return `<div class="tile">
        <div class="tile-top"><dt>${t.label}</dt><span class="flag na">缺失</span></div>
        <dd>—<span class="was">原 ${nf(baseValue, t.dec)}</span></dd></div>`;
    }
    const change = t.key === 'users'
      ? (view.d.usersRatio ? (view.d.usersRatio - 1) * 100 : 0)
      : (t.key === 'prb' ? view.d.prb : view.d[t.key]);
    const cls = change === undefined ? 'ok' : t.better(change);
    const pctChange = baseValue ? ((incValue / baseValue - 1) * 100) : 0;
    const strip = t.strip ? prbStrip(incValue) : '';
    return `<div class="tile">
      <div class="tile-top"><dt>${t.label}</dt><span class="flag ${cls}">${sgn(pctChange)}%</span></div>
      <dd>${nf(incValue, t.dec)}<span class="was">原 ${nf(baseValue, t.dec)}</span></dd>${strip}</div>`;
  }).join('');
}

function prbStrip(v) {
  const cells = 40, on = Math.round((v || 0) / 100 * cells);
  let html = '<div class="prb-strip" aria-hidden="true">';
  for (let i = 0; i < cells; i++) {
    html += `<i class="${i < on ? (v >= 85 ? 'hot' : 'on') : ''}"></i>`;
  }
  return html + '</div>';
}

const VERDICT_CLASS = { SUPPORTED: 'sup', REFUTED: 'ref', INCONCLUSIVE: 'inc' };
const VERDICT_TEXT = { SUPPORTED: '成立', REFUTED: '已否定', INCONCLUSIVE: '不可判定' };

function renderHyps(view) {
  $('#hypGrid').innerHTML = view.hyps.map((h, i) => `
    <article class="hyp ${VERDICT_CLASS[h.verdict] || 'inc'}" style="--d:${i * 50}ms">
      <div class="hyp-top"><span class="hyp-code">${h.id}</span><h3 class="hyp-name">${h.name}</h3>
        <span class="pill ${VERDICT_CLASS[h.verdict] || 'inc'}">${VERDICT_TEXT[h.verdict] || h.verdict}</span></div>
      <p class="hyp-statement">${h.statement}</p>
      <ul class="checks">${h.checks.map(c => checkRow(h, c)).join('')}</ul>
      <div class="hyp-foot"><span>必要条件 ${h.gates.join('·')}</span><span class="seg">${seg(h.conf, h.verdict)}</span><span>${Number(h.conf).toFixed(2)}</span></div>
    </article>`).join('');
}

function checkRow(h, c) {
  const m = c.pass === null ? 'na' : c.pass ? 'ok' : 'no';
  const icon = c.pass === null ? '#i-dash' : c.pass ? '#i-check' : '#i-cross';
  return `<li><span class="mark ${m}" aria-hidden="true"><svg class="ico"><use href="${icon}"/></svg></span>
    <span>${c.metric} <b>${nf(c.inc, c.dec)}</b></span><span class="thr">${c.thr}</span></li>`;
}

function seg(conf, verdict) {
  const n = Math.round((conf || 0) * 10);
  return Array.from({ length: 10 }, (_, i) => `<i class="${i < n ? 'on' : ''}"></i>`).join('');
}

function deltaText(c) {
  if (c.delta === null || c.delta === undefined) return '—';
  if (c.kind === 'ratio') return nf(c.delta, 2) + '×';
  return (c.signed ? sgn(c.delta, c.dec) : nf(c.delta, c.dec));
}

function renderLedger(view) {
  const rows = [];
  view.hyps.forEach(h => h.checks.forEach(c => {
    rows.push({ id: `EV-${view.id}-${h.id}-${c.id}`, c, dir: c.dir });
  }));
  const shown = rows.filter(r => state.filter === 'all' || r.dir === state.filter);
  $('#ledgerCount').textContent = `EVIDENCE LEDGER · ${shown.length}/${rows.length}`;
  $('#ledgerBody').innerHTML = shown.map(({ id, c, dir }) => {
    const tag = dir === 'supports' ? '支持' : dir === 'refutes' ? '否定' : '中性';
    const icon = dir === 'supports' ? '#i-check' : dir === 'refutes' ? '#i-cross' : '#i-dash';
    return `<tr><td class="id">${id}</td><td class="metric">${c.metric}</td>
      <td class="num">${nf(c.base, c.dec)}</td>
      <td class="num">${nf(c.inc, c.dec)}</td>
      <td class="num">${deltaText(c)}</td>
      <td class="thr">${c.thr}</td>
      <td><span class="dir ${dir}"><svg class="ico"><use href="${icon}"/></svg>${tag}</span></td></tr>`;
  }).join('');
  $('#ledgerFoot').textContent = state.hidePrb
    ? 'PRB 字段已隐藏：相关判定为「不可判定」，结论降级为证据不足'
    : '按证据 ID 排序 · 每条可回溯至原始样本';
}

function renderVerdict(view) {
  $('#causeLabel').textContent = view.causeLabel || CAUSE_FALLBACK[view.cause] || view.cause;
  $('#causeCode').textContent = view.cause;
  $('#confValue').textContent = Number(view.conf).toFixed(2);

  const meterClass = view.cause === 'UNDETERMINED' ? 'warn'
    : view.cause === 'NO_SIGNIFICANT_DEGRADATION' ? 'bad' : '';
  const on = Math.round(view.conf * 10);
  $('#confMeter').innerHTML = Array.from({ length: 10 }, (_, i) =>
    `<i class="${i < on ? 'on ' + meterClass : ''}"></i>`).join('');
  $('#confMeter').setAttribute('aria-label', `置信度 ${view.conf.toFixed(2)}`);

  const ratioText = view.d.atRatio === undefined ? '' : ` 香农标尺：实际/期望 = ${nf(view.d.atRatio, 2)}。`;
  $('#reason').textContent = `${view.reason || ''}${ratioText}`;

  const ruled = view.hyps.filter(h => h.verdict === 'REFUTED');
  $('#ruleOut').innerHTML = ruled.map(h =>
    `<li>${h.name}<span class="why">${h.why}</span></li>`).join('') || '<li>无（当前证据不足以否定任何假设）</li>';

  $('#gaps').innerHTML = (view.gaps.length ? view.gaps : ['无关键缺口'])
    .map(g => `<li>${g}</li>`).join('');

  $('#actions').innerHTML = (view.recs.length ? view.recs : [{ area: '维持观察', text: '当前结论下不做任何网络变更。' }])
    .map(x => `<li><b>${x.area}</b> · ${x.text}</li>`).join('');
}

function renderAudit() {
  const chip = $('#auditChip'), text = $('#auditText'), btn = $('#auditBtn');
  const receipt = $('#receipt'), status = $('#receiptStatus'), hash = $('#receiptHash');
  const link = $('#reportLink');

  const lis = document.querySelectorAll('.timeline li');
  lis.forEach(li => li.classList.remove('done', 'active'));
  const audited = state.receipt && state.receipt.status === 'PASS';
  lis.forEach((li, i) => {
    if (audited) { li.classList.add('done'); return; }
    if (i < 3) li.classList.add('done');
    if (i === 3) li.classList.add('active');
  });

  if (audited) {
    const demo = !!state.receipt.note;
    chip.className = 'chip chip-pass';
    text.textContent = demo ? '演示回执 PASS' : '已审计 PASS';
    receipt.classList.add('is-pass');
    status.textContent = demo
      ? `PASS（演示）· ${state.receipt.note}`
      : `PASS · ${state.receipt.checks.length} 项检查通过（独立复算）`;
    hash.textContent = 'ledger sha256:' + (state.receipt.ledger_sha256 || '').slice(0, 16) + '…';
  } else if (state.receipt && state.receipt.status !== 'PASS') {
    chip.className = 'chip chip-pending';
    text.textContent = '审计 FAIL';
    receipt.classList.remove('is-pass');
    status.textContent = `FAIL · ${state.receipt.error_count} 项不一致，报告不可交付`;
    hash.textContent = (state.receipt.errors || []).slice(0, 2).join(' / ').slice(0, 90);
  } else {
    chip.className = 'chip chip-pending';
    text.textContent = '未审计 UNVERIFIED';
    receipt.classList.remove('is-pass');
    status.textContent = state.hidePrb
      ? '证据不完整（PRB 缺失），审计不可执行'
      : '尚无回执 · 报告不可交付';
    hash.textContent = '';
  }

  btn.disabled = state.hidePrb;
  if (state.mode === 'api' && !state.hidePrb) {
    link.innerHTML = `<a class="report-link-a" href="${API}/report/${state.cellId}" target="_blank" rel="noopener">导出 Markdown 报告 ↗</a>`;
  } else {
    link.innerHTML = '';
  }
}

function renderFooter() {
  const note = $('#sourceNote');
  if (!note) return;
  note.textContent = state.mode === 'api'
    ? '数据源：后端账本 /api/ledger · 方法 dl-rca-v1 · 审计为独立复算，非模型判断'
    : '内置账本（离线回退）· 启动后端后自动切换为 /api/ledger · 内容由同一生成器产出';
}

/* ---------- 交互 ---------- */
document.addEventListener('click', e => {
  const f = e.target.closest('.filter');
  if (!f) return;
  state.filter = f.dataset.filter;
  document.querySelectorAll('.filter').forEach(b => b.classList.toggle('is-on', b === f));
  const view = currentView();
  if (view) renderLedger(view);
});

$('#prbToggle').addEventListener('change', async e => {
  state.hidePrb = e.target.checked;
  state.receipt = null;
  if (!state.hidePrb) {
    state.override = null;
    render();
    return;
  }
  if (state.mode !== 'api') {
    state.override = omitPrbLocal(currentCell());
    render();
    return;
  }
  try {
    const res = await fetch(`${API}/cell/${state.cellId}?omit=prb`);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    state.override = data.cell;
  } catch (err) {
    state.override = omitPrbLocal(currentCell());
  }
  render();
});

function omitPrbLocal(cell) {
  const clone = JSON.parse(JSON.stringify(cell));
  for (const key of ['baseline', 'incident', 'signals']) {
    Object.keys(clone[key] || {}).forEach(k => { if (k.includes('prb')) delete clone[key][k]; });
  }
  clone.hypotheses.forEach(h => {
    h.checks = h.checks.filter(c => !String(c.metric).includes('prb'));
    if (h.checks.some(c => h.gate_checks.includes(c.check_id)) === false) {
      h.verdict = 'INCONCLUSIVE';
      h.confidence = 0.5;
      h.basis = '必要条件所需字段（PRB 利用率）缺失，无法判定';
    }
  });
  clone.dominant_cause = {
    code: 'UNDETERMINED', label: CAUSE_FALLBACK.UNDETERMINED, confidence: 0.4,
    reason: 'PRB 利用率字段缺失，拥塞假设的必要条件无法验证；按规则不得给出确定结论'
  };
  clone.recommendations = [];
  clone.missing_evidence = [...new Set([...(clone.missing_evidence || []), 'PRB 利用率（当前数据集缺失该字段）'])];
  return clone;
}

$('#auditBtn').addEventListener('click', async () => {
  const btn = $('#auditBtn');
  btn.disabled = true;
  $('#auditText').textContent = '审计中…';
  if (state.mode !== 'api') {
    state.receipt = {
      status: 'PASS',
      checks: new Array(294).fill(0).map((_, i) => ({ check_id: 'local.' + i, ok: true, detail: '' })),
      errors: [], error_count: 0,
      ledger_sha256: state.ledger.ledger_sha256,
      note: '离线演示：回执为本地占位，不代表真实审计'
    };
    render();
    return;
  }
  try {
    const res = await fetch(`${API}/audit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ledger: state.ledger, cell_id: state.cellId })
    });
    state.receipt = await res.json();
  } catch (err) {
    state.receipt = { status: 'FAIL', checks: [], errors: [String(err)], error_count: 1, ledger_sha256: '' };
  }
  render();
});

/* ---------- 启动 ---------- */
async function boot() {
  if (API) {
    try {
      const res = await fetch(`${API}/ledger`, { cache: 'no-store' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      state.ledger = await res.json();
      state.mode = 'api';
    } catch (err) {
      console.warn('[ran-forensics] API unavailable, using embedded ledger:', err.message);
    }
  }
  if (!state.ledger && window.EMBEDDED_LEDGER) {
    state.ledger = window.EMBEDDED_LEDGER;
    state.mode = 'embedded';
  }
  if (!state.ledger) {
    document.querySelector('#main').innerHTML =
      '<p class="noscript">没有可用的账本：请启动后端（python -m uvicorn backend.app:app --port 8765），或确认 ledger-data.js 已生成。</p>';
    return;
  }
  const preferred = state.ledger.summary.cells.find(c => c.cause === 'INTERFERENCE');
  state.cellId = preferred ? preferred.cell_id : state.ledger.summary.cells[0].cell_id;
  render();
}

boot();