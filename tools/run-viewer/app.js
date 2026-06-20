// Benchmark Run Viewer — Preact + htm (no build step). Schema-adaptive item
// rendering for the four scorer types produced by lab/benchmarks/harness.
import { h, render } from 'https://esm.sh/preact@10.23.2';
import { useState, useEffect, useCallback, useRef } from 'https://esm.sh/preact@10.23.2/hooks';
import htm from 'https://esm.sh/htm@3.1.1';
import { marked } from 'https://esm.sh/marked@14.1.2';

const html = htm.bind(h);

// ---------- helpers ----------
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function passClass(v) {
  const n = parseFloat(v);
  if (Number.isNaN(n)) return 'neutral';
  if (n >= 0.7) return 'pass';
  if (n >= 0.34) return 'partial';
  return 'fail';
}
const fmt = (v, d = 2) => (v === '' || v == null || Number.isNaN(parseFloat(v)) ? '—' : parseFloat(v).toFixed(d));
// tri-state correctness: true → pass, false → fail, missing → unknown.
const okClass = (v) => (v === true ? 'pass' : v === false ? 'fail' : 'neutral');
const okLabel = (v, t = 'correct', f = 'incorrect') => (v === true ? t : v === false ? f : 'n/a');

// Denylist sanitizer for wiki markdown HTML (defense-in-depth alongside the CSP).
function sanitizeHtml(dirty) {
  const tpl = document.createElement('template');
  tpl.innerHTML = dirty;
  const drop = new Set(['script', 'style', 'iframe', 'object', 'embed', 'link', 'meta', 'base', 'form']);
  const nodes = [];
  const walker = document.createTreeWalker(tpl.content, NodeFilter.SHOW_ELEMENT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) nodes.push(n);
  for (const el of nodes) {
    if (drop.has(el.tagName.toLowerCase())) { el.remove(); continue; }
    for (const attr of Array.from(el.attributes)) {
      const name = attr.name.toLowerCase();
      if (name.startsWith('on')) el.removeAttribute(attr.name);
      else if ((name === 'href' || name === 'src') && /^\s*javascript:/i.test(attr.value)) el.removeAttribute(attr.name);
    }
  }
  return tpl.innerHTML;
}

function highlightPython(code) {
  const re = /(#[^\n]*)|('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")|\b(\d+\.?\d*)\b|\b(def|return|if|elif|else|for|while|in|not|and|or|None|True|False|import|from|class|with|as|try|except|finally|raise|lambda|yield|pass|break|continue|is|print)\b/g;
  return esc(code).replace(re, (m, c, s, n, k) => {
    if (c) return `<span class="com">${c}</span>`;
    if (s) return `<span class="str">${s}</span>`;
    if (n) return `<span class="num">${n}</span>`;
    if (k) return `<span class="kw">${k}</span>`;
    return m;
  });
}

function parseCompletion(text) {
  if (!text) return { answer: '', think: '' };
  const close = text.indexOf('</think>');
  if (close !== -1) {
    const think = text.slice(0, close).replace(/^\s*<think>/, '').trim();
    return { think, answer: text.slice(close + 8).trim() };
  }
  return { answer: text, think: '' };
}

// Split a completion into prose vs fenced ```code``` segments so only real code
// gets Python highlighting. Line-based: tolerates fence info strings
// (```python title="x"), multiple fences, and unterminated fences (closed at EOF).
function splitFences(text) {
  const parts = [];
  let prose = [], code = [], inCode = false;
  const flushProse = () => { const t = prose.join('\n').trim(); if (t) parts.push({ type: 'prose', text: t }); prose = []; };
  for (const line of String(text).split('\n')) {
    if (/^\s*```/.test(line)) {
      if (!inCode) { flushProse(); inCode = true; code = []; }
      else { parts.push({ type: 'code', text: code.join('\n') }); inCode = false; }
    } else if (inCode) code.push(line);
    else prose.push(line);
  }
  if (inCode) parts.push({ type: 'code', text: code.join('\n') });
  else flushProse();
  return parts;
}

function renderCompletion(text) {
  const parts = splitFences(text);
  if (!parts.some((p) => p.type === 'code')) {
    // no fence -> treat the whole thing as code (matches bare-code completions)
    return html`<pre class="code" dangerouslySetInnerHTML=${{ __html: highlightPython(text) }}></pre>`;
  }
  return parts.filter((p) => p.text).map((p) => (p.type === 'code'
    ? html`<pre class="code" dangerouslySetInnerHTML=${{ __html: highlightPython(p.text) }}></pre>`
    : html`<div class="prose">${p.text}</div>`));
}

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

// ---------- grouped run rail ----------
// base_model (grouping key, = wiki slug) -> variant label (model) -> runs.
function groupRuns(runs) {
  const bases = [];
  const bmap = new Map();
  runs.forEach((r, i) => {
    const idx = r.__i ?? i;
    const base = r.base_model || r.model;
    let b = bmap.get(base);
    if (!b) { b = { base, variants: [], vmap: new Map(), runs: [] }; bmap.set(base, b); bases.push(b); }
    b.runs.push(idx);
    let v = b.vmap.get(r.model);
    if (!v) { v = { label: r.model, runs: [] }; b.vmap.set(r.model, v); b.variants.push(v); }
    v.runs.push(idx);
  });
  return bases;
}

// Runs filter: every whitespace token must appear in base/model/benchmark/scoring
// (separators normalized so "gemma 4" matches "gemma-4-12b").
function matchRun(r, q) {
  if (!q || !q.trim()) return true;
  const hay = `${r.base_model || ''} ${r.model} ${r.benchmark} ${r.scoring} ${r.provider}`
    .toLowerCase().replace(/[-_:.]+/g, ' ');
  return q.toLowerCase().replace(/[-_:.]+/g, ' ').split(/\s+/).filter(Boolean).every((t) => hay.includes(t));
}

function GroupedRail({ runs, sel, expanded, onToggle, onSelectRun, onSelectBase, onLeaderboard, query, onQuery }) {
  const shown = runs.filter((r) => matchRun(r, query));
  const bases = groupRuns(shown);
  return html`
    <div class="rail">
      <button class=${'lbbtn' + (sel === null ? ' sel' : '')} onClick=${onLeaderboard}>▣ leaderboard</button>
      <input class="search" type="search" placeholder="filter model / benchmark…" value=${query}
        onInput=${(e) => onQuery(e.target.value)} />
      <div class="h">${shown.length} runs · ${bases.length} models</div>
      ${bases.length === 0 ? html`<div class="railempty">no matches</div>` : null}
      ${bases.map((b) => {
        const open = expanded[b.base] !== false;
        const baseSel = sel && sel.type === 'base' && sel.base === b.base;
        return html`
          <div class="baseblk">
            <div class=${'baserow' + (baseSel ? ' sel' : '')}>
              <button class="caret" onClick=${() => onToggle(b.base)} title=${open ? 'collapse' : 'expand'}>${open ? '▾' : '▸'}</button>
              <button class="basename" onClick=${() => onSelectBase(b.base)} title="compare variants">
                ${b.base} <span class="cnt">${b.runs.length}</span>
              </button>
            </div>
            ${open ? b.variants.map((v) => html`
              <div class="varblk">
                ${b.variants.length > 1 || v.label !== b.base ? html`<div class="varlabel" title=${v.label}>${v.label}</div>` : null}
                ${v.runs.map((i) => {
                  const r = runs[i];
                  const disabled = !r.raw_exists;
                  const runSel = sel && sel.type === 'run' && sel.i === i;
                  return html`<button class=${'run' + (runSel ? ' sel' : '')} disabled=${disabled}
                      title=${disabled ? 'raw run file not present' : r.raw_file}
                      onClick=${() => !disabled && onSelectRun(i)}>
                      <span class="m">${r.benchmark.split(' ')[0]}</span>
                      ${disabled ? html`<span class="missing">no raw</span>`
                        : html`<span class=${'pill ' + passClass(r.observed_pass_at_k)}>${fmt(r.observed_pass_at_k)}</span>`}
                      <span class="b">${r.scoring}${r.provider === 'openai-compatible' ? ' · api' : ''}</span>
                    </button>`;
                })}
              </div>`) : null}
          </div>`;
      })}
    </div>`;
}

// ---------- item renderers ----------
function ItemMetrics({ it }) {
  const bits = [];
  if (it.prompt_tokens != null) bits.push(['prompt', it.prompt_tokens]);
  if (it.gen_tokens != null) bits.push(['gen', it.gen_tokens]);
  if (it.gen_tok_per_s != null) bits.push(['tok/s', fmt(it.gen_tok_per_s, 1)]);
  if (it.wall_s != null) bits.push(['wall', fmt(it.wall_s, 1) + 's']);
  if (!bits.length) return null;
  return html`<div class="meta">${bits.map(([k, v]) => html`<span>${k} <b>${v}</b></span>`)}</div>`;
}

function CodeItem({ it }) {
  const res = it.result || {};
  return html`
    <div class="card">
      <div class="ch">
        <span class="id">${it.id}</span>
        <span class="t">completion · sandbox ${res.sandbox || '—'}</span>
        <span class=${'pill ' + okClass(res.correct)}>returncode ${res.returncode ?? '—'}</span>
      </div>
      <div class="cb">
        ${renderCompletion(it.completion || '')}
        ${res.stderr
          ? html`<div class="label">stderr</div><pre class="think">${res.stderr}</pre>`
          : html`<div class="label">stderr · empty</div>`}
        <${ItemMetrics} it=${it} />
      </div>
    </div>`;
}

function JudgeItem({ it }) {
  const res = it.result || {};
  const crit = res.per_criterion || {};
  const { think, answer } = parseCompletion(it.completion || '');
  return html`
    <div class="card">
      <div class="ch">
        <span class="id">${it.id}</span>
        <span class="t">judge scorecard</span>
        <span class=${'pill ' + okClass(res.correct)}>${res.score ?? '—'} / 10</span>
      </div>
      <div class="cb">
        ${Object.keys(crit).length
          ? html`<div class="crit">
              ${Object.entries(crit).map(([k, v]) => html`
                <span class="cn">${k.replace(/_/g, ' ')}</span>
                <span class="bar"><i style=${`width:${Math.max(0, Math.min(10, v)) * 10}%`}></i></span>
                <span class="cv">${v}</span>`)}
            </div>`
          : null}
        ${res.rationale ? html`<div class="rationale">${res.rationale}</div>` : null}
        ${answer ? html`<div class="label">completion</div><pre class="code">${answer}</pre>` : null}
        ${think ? html`<details><summary>thinking (${think.length} chars)</summary><pre class="think">${think}</pre></details>` : null}
        <${ItemMetrics} it=${it} />
      </div>
    </div>`;
}

function AgenticItem({ it }) {
  const res = it.result || {};
  const ep = it.episode || {};
  const transcript = ep.transcript || [];
  const calls = ep.tool_calls || [];
  // device diff (home_automation) — the harness nests initial_devices inside
  // final_state; support runs have no devices (diff stays null).
  const finalDevs = (ep.final_state && ep.final_state.devices) || null;
  const initDevs = (ep.final_state && ep.final_state.initial_devices) || ep.initial_devices || null;
  let diff = null;
  if (finalDevs && initDevs) {
    const keys = Array.from(new Set([...Object.keys(initDevs), ...Object.keys(finalDevs)]));
    diff = keys.map((k) => {
      const fv = finalDevs[k] && finalDevs[k].state;
      const iv = initDevs[k] && initDevs[k].state;
      return { k, iv, fv, changed: String(fv) !== String(iv) };
    });
  }
  // any `*_ok` check flag (home: state/unchanged/confirm/required/forbidden;
  // support: terminal/required/forbidden).
  const flags = Object.keys(res).filter((k) => k.endsWith('_ok')).map((k) => [k.slice(0, -3), res[k]]);
  const hasOutcome = res.expected_terminal != null || res.malformed_steps;
  return html`
    <div class="card">
      <div class="ch">
        <span class="id">${it.id}</span>
        <span class="t">${ep.toolset || 'agentic'} · ${ep.protocol || ''} · resolution: ${ep.resolution || res.resolution || '—'}</span>
        <span class=${'pill ' + okClass(res.correct)}>${okLabel(res.correct)}</span>
      </div>
      <div class="cb">
        ${transcript.map((t) => html`<div class=${'bubble ' + (t.speaker === 'user' ? 'u' : 'a')}>${t.text}</div>`)}
        ${calls.length ? html`<div class="label">tool calls</div>` : null}
        ${calls.length ? html`<div class="tools">
          ${calls.map((c) => {
            const r = String(c.result || '');
            const err = /UNKNOWN|ERROR|NOT_|FAIL/i.test(r);
            const args = Object.entries(c.args || {}).map(([k, v]) => `${k}=${v}`).join(' ');
            return html`<div class=${'tool' + (err ? ' err' : '')}>
              <span class="n">${c.name}</span>
              <span class="r">${args}${r ? ' → ' + r : ''}</span>
            </div>`;
          })}
        </div>` : null}
        ${hasOutcome ? html`<div class="label">outcome</div>
          <div class="statekv">
            ${res.expected_terminal != null ? html`<span>expected <b>${res.expected_terminal}</b></span>` : null}
            <span>resolution <b style=${res.terminal_ok === false ? 'color:var(--bad)' : ''}>${res.resolution || ep.resolution || '—'}</b></span>
            ${res.malformed_steps ? html`<span class="changed">malformed <b>${res.malformed_steps}</b></span>` : null}
          </div>` : null}
        ${diff ? html`<div class="label">final state · diff vs initial</div>
          <div class="statekv">
            ${diff.map((d) => html`<span class=${d.changed ? 'changed' : ''}>${d.k} ${d.changed
              ? html`${d.iv} → <b>${d.fv}</b>`
              : html`<b>${d.fv}</b>`}</span>`)}
          </div>` : null}
        ${flags.length ? html`<div class="label">checks</div>
          <div class="statekv">
            ${flags.map(([k, v]) => html`<span><b style=${v ? '' : 'color:var(--bad)'}>${v ? '✓' : '✗'}</b> ${k}</span>`)}
          </div>` : null}
      </div>
    </div>`;
}

function GenericItem({ it }) {
  const r = it.result || {};
  const fields = ['correct', 'score', 'expected', 'extracted', 'match', 'answer']
    .filter((k) => r[k] !== undefined)
    .map((k) => [k, typeof r[k] === 'object' ? JSON.stringify(r[k]) : String(r[k])]);
  return html`
    <div class="card">
      <div class="ch"><span class="id">${it.id}</span><span class="t">raw item</span>
        ${r.correct != null
          ? html`<span class=${'pill ' + okClass(r.correct)}>${okLabel(r.correct)}</span>` : null}
      </div>
      <div class="cb">
        ${fields.length ? html`<div class="statekv">${fields.map(([k, v]) => html`<span>${k} <b>${v}</b></span>`)}</div>` : null}
        ${it.completion ? html`<pre class="code">${it.completion}</pre>` : null}
        <details><summary>result json</summary><pre class="think">${JSON.stringify(it.result, null, 2)}</pre></details>
        <${ItemMetrics} it=${it} />
      </div>
    </div>`;
}

function pickRenderer(scoring) {
  if (scoring === 'code_tests') return CodeItem;
  if (scoring === 'llm_judge') return JudgeItem;
  if (scoring === 'agentic') return AgenticItem;
  return GenericItem;
}

// Render one benchmark item across its k samples. k==1 (and expected k==1) ->
// just the sample card (no chrome, no regression). Otherwise -> a header with the
// n/k pass count + per-sample dots (+ an incomplete flag when fewer samples than
// the run's k landed), a representative sample (a failing one if any), and the
// remaining samples collapsed.
function SampleGroup({ g, Renderer, expectedK }) {
  const ek = expectedK || 1;
  if (g.k <= 1 && ek <= 1) return html`<${Renderer} it=${g.samples[0]} />`;
  const others = g.samples.filter((s) => s !== g.rep);
  const incomplete = ek > 1 && g.k !== ek;
  const repFailed = g.rep.result && g.rep.result.correct === false;
  const dotCh = (s) => (s.result && s.result.correct === true ? '✓'
    : s.result && s.result.correct === false ? '✗' : '·');
  return html`
    <div class="sgroup">
      <div class="sghead">
        <span class="id">${g.id}</span>
        <span class=${'pill ' + sampleBadgeClass(g)}>${g.nCorrect}/${g.k} correct</span>
        ${sampleDots(g)}
        ${incomplete ? html`<span class="warnflag" title=${`run k=${ek}, only ${g.k} sample(s) recorded`}>incomplete</span>` : null}
      </div>
      <div class="slabel">sample ${g.rep.sample_index ?? 0} · representative${repFailed ? ' (failed)' : ''}</div>
      <${Renderer} it=${g.rep} />
      ${others.length ? html`<details><summary>other samples (${others.length})</summary>
        ${others.map((s) => html`<div class="swrap"><div class="slabel">sample ${s.sample_index ?? 0} · ${dotCh(s)}</div><${Renderer} it=${s} /></div>`)}
      </details>` : null}
    </div>`;
}

// ---------- base-model overview (variant x benchmark matrix) ----------
function BaseOverview({ runs, base, wikiHas, onOpenWiki, onSelectRun }) {
  const idxs = runs.map((r, i) => i).filter((i) => (runs[i].base_model || runs[i].model) === base);
  const variants = [], benches = [], vset = new Set(), bset = new Set();
  idxs.forEach((i) => {
    const v = runs[i].model; if (!vset.has(v)) { vset.add(v); variants.push(v); }
    const bn = runs[i].benchmark; if (!bset.has(bn)) { bset.add(bn); benches.push(bn); }
  });
  const cell = (v, bn) => {
    const ms = idxs.filter((i) => runs[i].model === v && runs[i].benchmark === bn
      && Number.isFinite(relK(runs[i])));
    if (!ms.length) return null;
    ms.sort((a, b) => (runK(runs[b]) - runK(runs[a])) || (relK(runs[b]) - relK(runs[a])));
    const i = ms[0];
    return { i, n: ms.length, k: runK(runs[i]), ph: relK(runs[i]), pk: parseFloat(runs[i].observed_pass_at_k), openable: !!runs[i].raw_exists };
  };
  const wp = `models/${base}.md`;
  return html`
    <div class="detail">
      <div class="crumb">model overview</div>
      <div class="dhead">
        <h2>${base}</h2>
        ${wikiHas(wp) ? html`<button class="wikilink" onClick=${() => onOpenWiki(wp)}>model page ↗</button>` : null}
      </div>
      <div class="meta">
        <span><b>${variants.length}</b> variants</span><span><b>${idxs.length}</b> runs</span><span><b>${benches.length}</b> benchmarks</span>
      </div>
      <table class="matrix">
        <thead><tr><th>variant</th>${benches.map((bn) => html`<th>${bn}</th>`)}</tr></thead>
        <tbody>
          ${variants.map((v) => html`<tr>
            <td class="vname">${v}</td>
            ${benches.map((bn) => { const c = cell(v, bn); return html`<td>${c
              ? (c.openable
                  ? html`<button class=${'pill ' + passClass(c.ph)} onClick=${() => onSelectRun(c.i)} title=${`open run · pass^${c.k} ${fmt(c.ph)} · pass@${c.k} ${fmt(c.pk)}`}>${lbCell(c)}</button>`
                  : html`<span class=${'pill ' + passClass(c.ph)} title=${`raw run file not present · pass^${c.k} ${fmt(c.ph)} · pass@${c.k} ${fmt(c.pk)}`}>${lbCell(c)}</span>`)
              : html`<span class="dash">—</span>`}</td>`; })}
          </tr>`)}
        </tbody>
      </table>
      <div class="hint">best pass^k per variant×benchmark (superscript = k; @ = pass@k capability; highest-k run wins the cell) · ×n = runs · click to open (greyed = raw file absent here)</div>
    </div>`;
}

// ---------- cross-model leaderboard (the Runs landing view) ----------
// base_model (rows, = wiki slug) × benchmark (cols), cell = best pass@k.
// Rows ranked by mean pass across the benchmarks they ran.
function Leaderboard({ runs, onSelectBase, onSelectRun }) {
  const benches = [], bset = new Set();
  const bmap = new Map(); const bases = [];
  runs.forEach((r, i) => {
    const bn = r.benchmark;
    if (!bset.has(bn)) { bset.add(bn); benches.push(bn); }
    const base = r.base_model || r.model;
    let b = bmap.get(base);
    if (!b) { b = { base, runs: [] }; bmap.set(base, b); bases.push(b); }
    b.runs.push(i);
  });
  benches.sort();
  const cell = (b, bn) => {
    const ms = b.runs.filter((i) => runs[i].benchmark === bn && Number.isFinite(relK(runs[i])));
    if (!ms.length) return null;
    ms.sort((a, c) => (runK(runs[c]) - runK(runs[a])) || (relK(runs[c]) - relK(runs[a])));
    const i = ms[0];
    return { i, n: ms.length, k: runK(runs[i]), ph: relK(runs[i]), pk: parseFloat(runs[i].observed_pass_at_k), openable: !!runs[i].raw_exists };
  };
  const rows = bases.map((b) => {
    const cells = benches.map((bn) => [bn, cell(b, bn)]);
    const got = cells.filter(([, c]) => c);
    const avg = got.length ? got.reduce((s, [, c]) => s + c.ph, 0) / got.length : NaN;
    return { b, cells, avg, n: got.length };
  });
  rows.sort((a, c) => (Number.isNaN(c.avg) ? -1 : c.avg) - (Number.isNaN(a.avg) ? -1 : a.avg));
  return html`
    <div class="detail">
      <div class="crumb">leaderboard · ${bases.length} models · ${benches.length} benchmarks · ${runs.length} runs</div>
      <div class="dhead"><h2>Cross-model leaderboard</h2></div>
      <div class="meta"><span>ranked by mean <b>pass^k</b> (reliability: items correct on all k; superscript = k, highest-k run wins each cell) · <b>@</b> = pass@k best-of-k capability</span></div>
      <table class="matrix lb">
        <thead><tr><th>#</th><th>model</th>${benches.map((bn) => html`<th>${bn}</th>`)}<th>pass^k</th></tr></thead>
        <tbody>
          ${rows.map((row, ri) => html`<tr>
            <td class="rank">${ri + 1}</td>
            <td class="vname"><button class="lbname" onClick=${() => onSelectBase(row.b.base)} title="compare variants">${row.b.base}</button></td>
            ${row.cells.map(([bn, c]) => html`<td>${c
              ? (c.openable
                  ? html`<button class=${'pill ' + passClass(c.ph)} onClick=${() => onSelectRun(c.i)} title=${`open best ${bn} run · pass^${c.k} ${fmt(c.ph)} · pass@${c.k} ${fmt(c.pk)}`}>${lbCell(c)}</button>`
                  : html`<span class=${'pill ' + passClass(c.ph)} title=${`raw run file not present · pass^${c.k} ${fmt(c.ph)} · pass@${c.k} ${fmt(c.pk)}`}>${lbCell(c)}</span>`)
              : html`<span class="dash">—</span>`}</td>`)}
            <td><span class=${'pill ' + (Number.isNaN(row.avg) ? 'neutral' : passClass(row.avg))}>${Number.isNaN(row.avg) ? '—' : fmt(row.avg)}</span></td>
          </tr>`)}
        </tbody>
      </table>
      <div class="hint">ranked by mean pass^k · @ = pass@k capability · click a model to compare variants · click a cell to open its best run (greyed = raw file absent here)</div>
    </div>`;
}

// Group raw jsonl sample-lines into per-item records. Each raw line is one
// sample: {id, sample_index, result, completion|episode, ...}; at k>1 there are
// k lines per id. Output preserves first-seen id order; samples sorted by index.
function groupSamples(items) {
  const order = [];
  const byId = new Map();
  for (const it of items || []) {
    const id = it.id != null ? it.id : '(no id)';
    let g = byId.get(id);
    if (!g) { g = { id, samples: [] }; byId.set(id, g); order.push(g); }
    g.samples.push(it);
  }
  for (const g of order) {
    g.samples.sort((x, y) => (x.sample_index ?? 0) - (y.sample_index ?? 0));
    g.k = g.samples.length;
    g.nCorrect = g.samples.filter((s) => s.result && s.result.correct === true).length;
    g.hasFail = g.samples.some((s) => s.result && s.result.correct === false);
    g.rep = g.samples.find((s) => s.result && s.result.correct === false) || g.samples[0];
  }
  return order;
}
// item-level reliability colour: all-correct -> pass, mixed -> partial, none -> fail.
const sampleBadgeClass = (g) => (g.nCorrect >= g.k ? 'pass' : g.nCorrect > 0 ? 'partial' : 'fail');
// pass^k for a results.csv row, with a k=1 fallback (pass^1 == pass@1).
function relK(r) {
  const v = parseFloat(r.pass_hat_k);
  if (Number.isFinite(v)) return v;
  return parseInt(r.k, 10) === 1 ? parseFloat(r.observed_pass_at_k) : NaN;
}
// samples per item for a run row (the pass^k exponent), default 1.
function runK(r) { return parseInt(r.k, 10) || 1; }
// per-item-group reliability over a subset of grouped items (for meta slicing).
// k = the run's declared sample count: an item counts toward pass^k only if all k
// declared samples are correct, so an incomplete item can't masquerade as reliable.
function sliceMetrics(gs, expectedK) {
  const n = gs.length;
  if (!n) return { n: 0, obs: NaN, ph: NaN, flaky: 0 };
  const k = expectedK || 1;
  const obs = gs.filter((g) => g.nCorrect >= 1).length / n;
  const ph = gs.filter((g) => g.nCorrect >= k).length / n;
  const flaky = gs.filter((g) => g.nCorrect > 0 && g.nCorrect < k).length;
  return { n, obs, ph, flaky };
}
// per-sample pass/fail dots for a grouped item (shared by run detail + compare).
function sampleDots(g) {
  const cls = (s) => (s.result && s.result.correct === true ? 'ok' : s.result && s.result.correct === false ? 'no' : 'na');
  const ch = (s) => (s.result && s.result.correct === true ? '✓' : s.result && s.result.correct === false ? '✗' : '·');
  return html`<span class="sdots">${g.samples.map((s) => html`<span class=${'sdot ' + cls(s)} title=${'sample ' + (s.sample_index ?? 0)}>${ch(s)}</span>`)}</span>`;
}
// leaderboard/overview cell inner: pass^k (k exponent when k>1) + muted @pass@k + xN.
function lbCell(c) {
  return html`${fmt(c.ph)}${c.k > 1 ? html`<sup class="lbk">${c.k}</sup>` : ''}${c.ph !== c.pk ? html`<span class="lbpk">@${fmt(c.pk)}</span>` : ''}${c.n > 1 ? html` <span class="cnt">×${c.n}</span>` : ''}`;
}

// ---------- side-by-side run compare ----------
function CompareView({ runs, a, b, da, db, onExit }) {
  const [diffOnly, setDiffOnly] = useState(false);
  const ra = runs[a], rb = runs[b];
  if (!da || !db) return html`<div class="detail"><div class="empty">Loading comparison …</div></div>`;
  const RA = pickRenderer(ra.scoring), RB = pickRenderer(rb.scoring);
  const la = groupSamples(da), lb = groupSamples(db);
  const ga = new Map(la.map((g) => [g.id, g])), gb = new Map(lb.map((g) => [g.id, g]));
  const ids = [];
  const seen = new Set();
  for (const g of [...la, ...lb]) { if (!seen.has(g.id)) { seen.add(g.id); ids.push(g.id); } }
  const rate = (g) => (g && g.k ? g.nCorrect / g.k : null);
  // an item differs if its pass rate differs, OR it's present in only one run.
  const differs = (x, y) => {
    if ((x == null) !== (y == null)) return true;
    const rx = rate(x), ry = rate(y);
    return rx != null && ry != null && rx !== ry;
  };
  const shown = diffOnly ? ids.filter((id) => differs(ga.get(id), gb.get(id))) : ids;
  const diffCount = ids.filter((id) => differs(ga.get(id), gb.get(id))).length;
  const side = (g, R) => (g
    ? html`<div>${g.k > 1 ? html`<div class="cmpbadge"><span class=${'pill ' + sampleBadgeClass(g)}>${g.nCorrect}/${g.k}</span>${sampleDots(g)}<span class="slabel">rep: sample ${g.rep.sample_index ?? 0}${g.rep.result && g.rep.result.correct === false ? ' (failed)' : ''}</span></div>` : ''}<${R} it=${g.rep} /></div>`
    : html`<div class="cmpmissing">— not in this run —</div>`);
  const kmismatch = runK(ra) !== runK(rb);
  return html`
    <div class="detail">
      <div class="crumb">compare · ${ra.benchmark} <button class="linkish" onClick=${onExit}>← back to run</button></div>
      <div class="controls">
        <button class=${'toggle' + (diffOnly ? ' on' : '')} onClick=${() => setDiffOnly((v) => !v)}
          title="show only items that differ — different pass rate, or present in just one run">differences ${diffCount}</button>
        <span class="hint">${shown.length} of ${ids.length} items</span>
        ${kmismatch ? html`<span class="hint warnflag" title="one side has more samples than the other — pass^k is not directly comparable across different k">k mismatch: ${runK(ra)} vs ${runK(rb)}</span>` : null}
      </div>
      <div class="cmphead">
        <div class="cmpcol">${ra.model} <span class=${'pill ' + passClass(relK(ra))}>pass^${runK(ra)} ${fmt(relK(ra))}</span></div>
        <div class="cmpcol">${rb.model} <span class=${'pill ' + passClass(relK(rb))}>pass^${runK(rb)} ${fmt(relK(rb))}</span></div>
      </div>
      ${shown.length === 0 ? html`<div class="empty">No ${diffOnly ? 'differing ' : ''}items.</div>` : null}
      ${shown.map((id) => {
        const ia = ga.get(id), ib = gb.get(id);
        const diff = differs(ia, ib);
        return html`<div class=${'cmprow' + (diff ? ' differ' : '')}>
          <div class="cmpidrow"><span class="cmpid">${id}</span>${diff ? html`<span class="diffbadge">differs</span>` : null}</div>
          <div class="cmpcols">
            ${side(ia, RA)}
            ${side(ib, RB)}
          </div>
        </div>`;
      })}
    </div>`;
}

// ---------- run detail ----------
function RunDetail({ runs, runIndex, run, data, wikiHas, onOpenWiki, onCompare }) {
  const [failsOnly, setFailsOnly] = useState(false);
  const [sliceKey, setSliceKey] = useState('');
  const [sliceVal, setSliceVal] = useState(null);
  useEffect(() => { setFailsOnly(false); setSliceKey(''); setSliceVal(null); }, [runIndex]);
  if (!run) return html`<div class="empty">Select a run, a model header to compare variants, or browse the leaderboard.</div>`;
  if (!data) return html`<div class="empty">Loading ${run.raw_file} …</div>`;
  if (data.error) return html`<div class="empty">${data.error}: ${data.file || ''}</div>`;
  const Renderer = pickRenderer(run.scoring);
  const base = run.base_model || run.model;
  const wp = `models/${base}.md`;
  const meta = [
    ['provider', run.provider], ['tok/s', fmt(run.mean_gen_tok_s, 1)],
    ['cost', '$' + fmt(run.cost_usd, 4)], ['ctx', run.num_ctx], ['date', run.date],
  ];
  const sub = (base !== run.model ? base : '') ;
  const groups = groupSamples(data.items);
  const expectedK = runK(run);
  const k = Math.max(expectedK, groups.reduce((m, g) => Math.max(m, g.k), 1));
  // meta slicing (prototype): per-item meta rides on each sample line once the
  // harness emits it. Discover small categorical keys (2..<n distinct values, so
  // unique-per-item keys like persona and object-valued keys are excluded).
  const metaOf = (g) => {
    const m = (g.rep && g.rep.meta) || (g.samples[0] && g.samples[0].meta);
    return (m && typeof m === 'object' && !Array.isArray(m)) ? m : {};
  };
  const keyVals = {}, keyCount = {};
  for (const g of groups) for (const [kk, vv] of Object.entries(metaOf(g))) {
    if (vv == null || (typeof vv !== 'string' && typeof vv !== 'number')) continue;
    (keyVals[kk] = keyVals[kk] || new Set()).add(String(vv));
    keyCount[kk] = (keyCount[kk] || 0) + 1;
  }
  // sliceable: present on EVERY item (full coverage), 2..<n distinct values, <=12 buckets.
  const sliceKeys = Object.keys(keyVals).filter((kk) => {
    const c = keyVals[kk].size;
    return keyCount[kk] === groups.length && c >= 2 && c < groups.length && c <= 12;
  });
  const activeKey = sliceKeys.includes(sliceKey) ? sliceKey : '';
  const sliceBuckets = {};
  if (activeKey) for (const g of groups) { const v = String(metaOf(g)[activeKey] ?? '—'); (sliceBuckets[v] = sliceBuckets[v] || []).push(g); }
  const sliceRows = Object.entries(sliceBuckets).map(([v, gs]) => ({ v, ...sliceMetrics(gs, expectedK) })).sort((a, b) => (b.ph - a.ph));
  const pool = (activeKey && sliceVal != null) ? groups.filter((g) => String(metaOf(g)[activeKey] ?? '—') === sliceVal) : groups;
  const failCount = pool.filter((g) => g.hasFail).length;
  const shown = failsOnly ? pool.filter((g) => g.hasFail) : pool;
  const obs = parseFloat(run.observed_pass_at_k);
  const ph = relK(run);
  const flaky = parseInt(run.flaky_items, 10);
  const sem = parseFloat(run.sem);
  const targets = runs
    .map((r, i) => ({ r, i }))
    .filter(({ r, i }) => i !== runIndex && r.raw_exists && r.benchmark === run.benchmark);
  return html`
    <div class="detail">
      <div class="crumb">${run.benchmark} / ${run.scoring} / ${groups.length} items${k > 1 ? ` × ${k} samples` : ''}${data.parse_errors ? ` · ${data.parse_errors} parse errors` : ''}</div>
      <div class="dhead">
        <h2>${run.model}</h2>
        <span class=${'pill ' + passClass(obs)} title="pass@k: items with >=1 correct sample (best-of-k capability ceiling)">pass@${run.k || 1} ${fmt(obs)}</span>
        ${(k > 1 || (Number.isFinite(ph) && ph !== obs))
          ? html`<span class=${'pill ' + (Number.isFinite(ph) ? passClass(ph) : 'neutral')} title="pass^k: items correct on ALL k samples (tau-bench reliability)">pass^${run.k || 1} ${Number.isFinite(ph) ? fmt(ph) : '—'}</span>` : null}
        ${Number.isFinite(flaky) && flaky > 0 ? html`<span class="pill partial" title="items inconsistent across the k samples">flaky ${flaky}</span>` : null}
        ${Number.isFinite(sem) ? html`<span class="pill neutral" title="standard error of the per-item mean">±${fmt(sem)}</span>` : null}
      </div>
      ${(sub || wikiHas(wp)) ? html`<div class="subhead">${sub ? html`${base} ` : ''}${wikiHas(wp) ? html`<button class="wikilink" onClick=${() => onOpenWiki(wp)}>model page ↗</button>` : ''}</div>` : null}
      <div class="meta">${meta.map(([k, v]) => html`<span>${k} <b>${v || '—'}</b></span>`)}
        <span>sampling <b>${run.sampling || '—'}</b></span>
      </div>
      <div class="controls">
        <button class=${'toggle' + (failsOnly ? ' on' : '')} disabled=${!failsOnly && failCount === 0}
          onClick=${() => setFailsOnly((v) => !v)} title="show only items with at least one incorrect sample (includes flaky items at k>1)">failures ${failCount}</button>
        ${targets.length ? html`<select class="cmpsel" onChange=${(e) => { const v = e.target.value; if (v) onCompare(runIndex, parseInt(v, 10)); e.target.value = ''; }}>
          <option value="">compare vs…</option>
          ${targets.map(({ r, i }) => html`<option value=${i}>${r.model} · ${fmt(r.observed_pass_at_k)}</option>`)}
        </select>` : null}
        ${sliceKeys.length ? html`<select class="cmpsel" onChange=${(e) => { setSliceKey(e.target.value); setSliceVal(null); }}>
          <option value="" selected=${!activeKey}>slice by…</option>
          ${sliceKeys.map((kk) => html`<option value=${kk} selected=${kk === activeKey}>by ${kk}</option>`)}
        </select>` : null}
        ${failsOnly ? html`<span class="hint">${shown.length} of ${pool.length} items</span>` : null}
      </div>
      ${activeKey ? html`<table class="matrix slice">
        <thead><tr><th>${activeKey}</th><th>n</th><th>pass^k</th><th>pass@k</th><th>flaky</th></tr></thead>
        <tbody>
          ${sliceRows.map((s) => html`<tr class=${'slicerow' + (sliceVal === s.v ? ' sel' : '')} role="button" tabindex="0" aria-pressed=${sliceVal === s.v}
            onClick=${() => setSliceVal(sliceVal === s.v ? null : s.v)}
            onKeyDown=${(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSliceVal(sliceVal === s.v ? null : s.v); } }}
            title="filter to this group (Enter/Space)">
            <td class="vname">${s.v}</td><td>${s.n}</td>
            <td><span class=${'pill ' + (Number.isNaN(s.ph) ? 'neutral' : passClass(s.ph))}>${Number.isNaN(s.ph) ? '—' : fmt(s.ph)}</span></td>
            <td><span class=${'pill ' + (Number.isNaN(s.obs) ? 'neutral' : passClass(s.obs))}>${Number.isNaN(s.obs) ? '—' : fmt(s.obs)}</span></td>
            <td>${s.flaky || '—'}</td>
          </tr>`)}
        </tbody>
      </table>
      ${sliceVal != null ? html`<div class="hint">filtered to ${activeKey} = ${sliceVal} · click the row again to clear</div>` : null}` : null}
      <div class="cards">
        ${shown.map((g) => html`<${SampleGroup} g=${g} Renderer=${Renderer} expectedK=${expectedK} key=${g.id} />`)}
      </div>
    </div>`;
}

// ---------- wiki ----------
function preprocessMd(md) {
  md = md.replace(/^---\n[\s\S]*?\n---\n/, ''); // strip YAML frontmatter
  md = md.replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '$2').replace(/\[\[([^\]]+)\]\]/g, '$1');
  return md;
}

// Resolve a relative markdown href against the current page's dir. Returns a
// wiki-relative .md path, or null for external/non-md links. Minimal reader:
// wiki↔wiki links navigate in-app; everything else opens in a new tab.
function resolveWikiHref(href, currentPath) {
  const clean = (href || '').split('#')[0].split('?')[0];
  if (!clean || /^[a-z]+:/i.test(clean) || clean.startsWith('/')) return null;
  const baseDir = (currentPath || '').includes('/') ? (currentPath || '').slice(0, currentPath.lastIndexOf('/')) : '';
  const segs = baseDir ? baseDir.split('/') : [];
  for (const part of clean.split('/')) {
    if (part === '..') { if (!segs.length) return null; segs.pop(); } // climbs above wiki root -> external
    else if (part && part !== '.') segs.push(part);
  }
  const resolved = segs.join('/');
  return resolved.endsWith('.md') ? resolved : null;
}

function WikiPane({ files, sel, onSelect, htmlContent, expanded, onToggle, query, onQuery, results }) {
  // group by top dir
  const groups = {};
  for (const f of files) {
    const top = f.includes('/') ? f.split('/')[0] : '·';
    (groups[top] = groups[top] || []).push(f);
  }
  // Minimal reader: intercept link clicks. wiki↔wiki .md → load in-app;
  // anything else (http, repo `../` paths, unknown) → new tab, app state intact.
  const onMdClick = (e) => {
    const a = e.target.closest('a');
    if (!a) return;
    const href = a.getAttribute('href') || '';
    if (!href || href.startsWith('#')) return;
    e.preventDefault();
    const resolved = resolveWikiHref(href, sel);
    if (resolved && files.includes(resolved)) onSelect(resolved);
    else window.open(href, '_blank', 'noopener');
  };
  return html`
    <div class="body">
      <div class="rail wiki-rail">
        <input class="search" type="search" placeholder="search wiki text…" value=${query}
          onInput=${(e) => onQuery(e.target.value)} />
        ${results !== null
          ? html`<div class="h">${results.length} pages</div>
              ${results.length === 0 ? html`<div class="railempty">no matches</div>` : null}
              ${results.map((res) => html`
                <button class=${'wresult' + (res.path === sel ? ' sel' : '')} onClick=${() => onSelect(res.path)} title=${res.path}>
                  <span class="wrpath">${res.path} <span class="cnt">${res.count}</span></span>
                  ${res.hits.slice(0, 2).map((h) => html`<span class="wrsnip">L${h.line} ${h.text}</span>`)}
                </button>`)}`
          : html`<div class="h">wiki · ${files.length}</div>
              ${Object.entries(groups).map(([dir, fs]) => {
                const open = expanded[dir] !== false;
                return html`<div class="wgroup">
                  <button class="wdir" onClick=${() => onToggle(dir)}>${open ? '▾' : '▸'} ${dir}</button>
                  ${open ? fs.map((f) => html`
                    <button class=${'wfile' + (f === sel ? ' sel' : '')} onClick=${() => onSelect(f)} title=${f}>
                      ${f.includes('/') ? f.split('/').slice(1).join('/') : f}
                    </button>`) : null}
                </div>`;
              })}`}
      </div>
      <div class="detail">
        ${sel
          ? html`<div class="crumb">wiki / ${sel}</div><div class="md" onClick=${onMdClick} dangerouslySetInnerHTML=${{ __html: htmlContent }}></div>`
          : html`<div class="empty">Select a wiki page (read-only).</div>`}
      </div>
    </div>`;
}

// ---------- app ----------
function App() {
  const [tab, setTab] = useState('runs');
  const [runs, setRuns] = useState([]);
  const [sel, setSel] = useState(null); // {type:'run',i} | {type:'base',base} | null
  const [expanded, setExpanded] = useState({});
  const [data, setData] = useState(null);
  const [wikiFiles, setWikiFiles] = useState(null);
  const [wikiSel, setWikiSel] = useState(null);
  const [wikiHtml, setWikiHtml] = useState('');
  const [wikiExpanded, setWikiExpanded] = useState({});
  const [runQuery, setRunQuery] = useState('');
  const [wikiQuery, setWikiQuery] = useState('');
  const [wikiResults, setWikiResults] = useState(null);
  const [cmp, setCmp] = useState(null); // { a, b, da, db } for side-by-side compare
  const cmpReq = useRef(0); // guards against out-of-order compare fetches

  useEffect(() => {
    getJSON('/api/runs').then((d) => setRuns((d.runs || []).map((r, i) => ({ ...r, __i: i })))).catch(() => setRuns([]));
    getJSON('/api/wiki').then((d) => setWikiFiles(d.files || [])).catch(() => setWikiFiles([]));
  }, []);

  const wikiHas = useCallback((p) => (wikiFiles || []).includes(p), [wikiFiles]);

  const fetchRunItems = useCallback((i) =>
    getJSON('/api/run?file=' + encodeURIComponent(runs[i].raw_file)).then((d) => d.items || []), [runs]);

  const selectRun = useCallback((i) => {
    setSel({ type: 'run', i }); setData(null);
    getJSON('/api/run?file=' + encodeURIComponent(runs[i].raw_file))
      .then(setData)
      .catch((e) => setData({ error: String((e && e.message) || e), file: runs[i].raw_file }));
  }, [runs]);

  const selectBase = useCallback((base) => { setSel({ type: 'base', base }); setData(null); }, []);
  const toggleBase = useCallback((base) => setExpanded((m) => ({ ...m, [base]: m[base] === false })), []);
  const showLeaderboard = useCallback(() => { setSel(null); setData(null); }, []);

  const selectCompare = useCallback((a, b) => {
    const req = ++cmpReq.current;
    setSel({ type: 'compare', a, b }); setCmp({ a, b, da: null, db: null });
    Promise.all([fetchRunItems(a), fetchRunItems(b)])
      .then(([da, db]) => { if (req === cmpReq.current) setCmp({ a, b, da, db }); })
      .catch(() => { if (req === cmpReq.current) setCmp({ a, b, da: [], db: [] }); });
  }, [fetchRunItems]);


  const selectWiki = useCallback((f) => {
    setWikiSel(f); setWikiHtml('');
    fetch('/api/wiki?path=' + encodeURIComponent(f))
      .then((r) => { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then((md) => setWikiHtml(sanitizeHtml(marked.parse(preprocessMd(md)))))
      .catch(() => setWikiHtml('<p>Failed to load page.</p>'));
  }, []);

  const openWikiPage = useCallback((p) => { setTab('wiki'); selectWiki(p); }, [selectWiki]);
  const toggleWikiDir = useCallback((d) => setWikiExpanded((m) => ({ ...m, [d]: m[d] === false })), []);
  const searchWiki = useCallback((q) => {
    setWikiQuery(q);
    if (!q.trim()) { setWikiResults(null); return; }
    getJSON('/api/wiki/search?q=' + encodeURIComponent(q)).then((d) => setWikiResults(d.results || [])).catch(() => setWikiResults([]));
  }, []);

  return html`
    <div class="shell">
      <div class="topbar">
        <div class="brand">Benchmark Run Viewer<span class="sub">lab/benchmarks</span></div>
        <div class="tabs">
          <button class=${'tab' + (tab === 'runs' ? ' active' : '')} onClick=${() => setTab('runs')}>runs</button>
          <button class=${'tab' + (tab === 'wiki' ? ' active' : '')} onClick=${() => setTab('wiki')}>wiki</button>
        </div>
      </div>
      ${tab === 'runs'
        ? html`<div class="body">
            <${GroupedRail} runs=${runs} sel=${sel} expanded=${expanded}
              onToggle=${toggleBase} onSelectRun=${selectRun} onSelectBase=${selectBase}
              onLeaderboard=${showLeaderboard} query=${runQuery} onQuery=${setRunQuery} />
            ${sel === null
              ? html`<${Leaderboard} runs=${runs} onSelectBase=${selectBase} onSelectRun=${selectRun} />`
              : sel.type === 'base'
              ? html`<${BaseOverview} runs=${runs} base=${sel.base} wikiHas=${wikiHas} onOpenWiki=${openWikiPage} onSelectRun=${selectRun} />`
              : sel.type === 'compare'
              ? html`<${CompareView} runs=${runs} a=${sel.a} b=${sel.b}
                  da=${cmp && cmp.a === sel.a && cmp.b === sel.b ? cmp.da : null}
                  db=${cmp && cmp.a === sel.a && cmp.b === sel.b ? cmp.db : null}
                  onExit=${() => selectRun(sel.a)} />`
              : html`<${RunDetail} runs=${runs} runIndex=${sel.i} run=${runs[sel.i]} data=${data} wikiHas=${wikiHas} onOpenWiki=${openWikiPage} onCompare=${selectCompare} />`}
          </div>`
        : html`<${WikiPane} files=${wikiFiles || []} sel=${wikiSel} onSelect=${selectWiki} htmlContent=${wikiHtml} expanded=${wikiExpanded} onToggle=${toggleWikiDir} query=${wikiQuery} onQuery=${searchWiki} results=${wikiResults} />`}
    </div>`;
}

render(html`<${App} />`, document.getElementById('app'));
