// Benchmark Run Viewer — Preact + htm (no build step). Schema-adaptive item
// rendering for the four scorer types produced by lab/benchmarks/harness.
import { h, render } from 'https://esm.sh/preact@10.23.2';
import { useState, useEffect, useCallback } from 'https://esm.sh/preact@10.23.2/hooks';
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
// gets Python highlighting (prose keywords like "while"/"and" stay plain).
function splitFences(text) {
  const parts = [];
  const re = /```[a-zA-Z0-9]*\n?([\s\S]*?)```/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push({ type: 'prose', text: text.slice(last, m.index).trim() });
    parts.push({ type: 'code', text: m[1].replace(/\n$/, '') });
    last = re.lastIndex;
  }
  if (last < text.length) parts.push({ type: 'prose', text: text.slice(last).trim() });
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
    const base = r.base_model || r.model;
    let b = bmap.get(base);
    if (!b) { b = { base, variants: [], vmap: new Map(), runs: [] }; bmap.set(base, b); bases.push(b); }
    b.runs.push(i);
    let v = b.vmap.get(r.model);
    if (!v) { v = { label: r.model, runs: [] }; b.vmap.set(r.model, v); b.variants.push(v); }
    v.runs.push(i);
  });
  return bases;
}

function GroupedRail({ runs, sel, expanded, onToggle, onSelectRun, onSelectBase }) {
  const bases = groupRuns(runs);
  return html`
    <div class="rail">
      <div class="h">${runs.length} runs · ${bases.length} models</div>
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

// ---------- base-model overview (variant x benchmark matrix) ----------
function BaseOverview({ runs, base, wikiHas, onOpenWiki, onSelectRun }) {
  const idxs = runs.map((r, i) => i).filter((i) => (runs[i].base_model || runs[i].model) === base);
  const variants = [], benches = [], vset = new Set(), bset = new Set();
  idxs.forEach((i) => {
    const v = runs[i].model; if (!vset.has(v)) { vset.add(v); variants.push(v); }
    const bn = runs[i].benchmark.split(' ')[0]; if (!bset.has(bn)) { bset.add(bn); benches.push(bn); }
  });
  const cell = (v, bn) => {
    const ms = idxs.filter((i) => runs[i].model === v && runs[i].benchmark.split(' ')[0] === bn);
    if (!ms.length) return null;
    ms.sort((a, b) => parseFloat(runs[b].observed_pass_at_k) - parseFloat(runs[a].observed_pass_at_k));
    return { i: ms[0], n: ms.length, pk: runs[ms[0]].observed_pass_at_k };
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
              ? html`<button class=${'pill ' + passClass(c.pk)} onClick=${() => onSelectRun(c.i)} title="open run">${fmt(c.pk)}${c.n > 1 ? html` <span class="cnt">×${c.n}</span>` : ''}</button>`
              : html`<span class="dash">—</span>`}</td>`; })}
          </tr>`)}
        </tbody>
      </table>
      <div class="hint">best pass@k per variant×benchmark · ×n = multiple runs · click a cell to open the run</div>
    </div>`;
}

// ---------- run detail ----------
function RunDetail({ run, data, wikiHas, onOpenWiki }) {
  if (!run) return html`<div class="empty">Select a run, or a model header to compare variants.</div>`;
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
  return html`
    <div class="detail">
      <div class="crumb">${run.benchmark} / ${run.scoring} / ${data.n_items} items${data.parse_errors ? ` · ${data.parse_errors} parse errors` : ''}</div>
      <div class="dhead">
        <h2>${run.model}</h2>
        <span class=${'pill ' + passClass(run.observed_pass_at_k)}>pass@${run.k || 1} ${fmt(run.observed_pass_at_k)}</span>
      </div>
      ${(sub || wikiHas(wp)) ? html`<div class="subhead">${sub ? html`${base} ` : ''}${wikiHas(wp) ? html`<button class="wikilink" onClick=${() => onOpenWiki(wp)}>model page ↗</button>` : ''}</div>` : null}
      <div class="meta">${meta.map(([k, v]) => html`<span>${k} <b>${v || '—'}</b></span>`)}
        <span>sampling <b>${run.sampling || '—'}</b></span>
      </div>
      <div class="cards">
        ${data.items.map((it) => html`<${Renderer} it=${it} key=${it.id} />`)}
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
    if (part === '..') segs.pop();
    else if (part && part !== '.') segs.push(part);
  }
  const resolved = segs.join('/');
  return resolved.endsWith('.md') ? resolved : null;
}

function WikiPane({ files, sel, onSelect, htmlContent }) {
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
        <div class="h">wiki · ${files.length}</div>
        ${Object.entries(groups).map(([dir, fs]) => html`
          <div class="wdir">${dir}</div>
          ${fs.map((f) => html`
            <button class=${'wfile' + (f === sel ? ' sel' : '')} onClick=${() => onSelect(f)} title=${f}>
              ${f.includes('/') ? f.split('/').slice(1).join('/') : f}
            </button>`)}
        `)}
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

  useEffect(() => {
    getJSON('/api/runs').then((d) => setRuns(d.runs || [])).catch(() => setRuns([]));
    getJSON('/api/wiki').then((d) => setWikiFiles(d.files || [])).catch(() => setWikiFiles([]));
  }, []);

  const wikiHas = useCallback((p) => (wikiFiles || []).includes(p), [wikiFiles]);

  const selectRun = useCallback((i) => {
    setSel({ type: 'run', i }); setData(null);
    getJSON('/api/run?file=' + encodeURIComponent(runs[i].raw_file))
      .then(setData)
      .catch((e) => setData({ error: String((e && e.message) || e), file: runs[i].raw_file }));
  }, [runs]);

  const selectBase = useCallback((base) => { setSel({ type: 'base', base }); setData(null); }, []);
  const toggleBase = useCallback((base) => setExpanded((m) => ({ ...m, [base]: m[base] === false })), []);

  const selectWiki = useCallback((f) => {
    setWikiSel(f); setWikiHtml('');
    fetch('/api/wiki?path=' + encodeURIComponent(f))
      .then((r) => { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then((md) => setWikiHtml(sanitizeHtml(marked.parse(preprocessMd(md)))))
      .catch(() => setWikiHtml('<p>Failed to load page.</p>'));
  }, []);

  const openWikiPage = useCallback((p) => { setTab('wiki'); selectWiki(p); }, [selectWiki]);

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
              onToggle=${toggleBase} onSelectRun=${selectRun} onSelectBase=${selectBase} />
            ${sel && sel.type === 'base'
              ? html`<${BaseOverview} runs=${runs} base=${sel.base} wikiHas=${wikiHas} onOpenWiki=${openWikiPage} onSelectRun=${selectRun} />`
              : html`<${RunDetail} run=${sel && sel.type === 'run' ? runs[sel.i] : null} data=${data} wikiHas=${wikiHas} onOpenWiki=${openWikiPage} />`}
          </div>`
        : html`<${WikiPane} files=${wikiFiles || []} sel=${wikiSel} onSelect=${selectWiki} htmlContent=${wikiHtml} />`}
    </div>`;
}

render(html`<${App} />`, document.getElementById('app'));
