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

async function getJSON(url) {
  const r = await fetch(url);
  return r.json();
}

// ---------- run list ----------
function RunList({ runs, sel, onSelect }) {
  return html`
    <div class="rail">
      <div class="h">runs · ${runs.length}</div>
      ${runs.map((r, i) => {
        const pk = r.observed_pass_at_k;
        const disabled = !r.raw_exists;
        return html`
          <button
            class=${'run' + (i === sel ? ' sel' : '')}
            disabled=${disabled}
            title=${disabled ? 'raw run file not present on this machine' : r.raw_file}
            onClick=${() => !disabled && onSelect(i)}>
            <span class="m">${r.model}</span>
            ${disabled
              ? html`<span class="missing">no raw</span>`
              : html`<span class=${'pill ' + passClass(pk)}>${fmt(pk)}</span>`}
            <span class="b">${r.benchmark} · ${r.scoring}</span>
          </button>`;
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
  const ok = res.correct;
  return html`
    <div class="card">
      <div class="ch">
        <span class="id">${it.id}</span>
        <span class="t">completion · sandbox ${res.sandbox || '—'}</span>
        <span class=${'pill ' + (ok ? 'pass' : 'fail')}>returncode ${res.returncode ?? '—'}</span>
      </div>
      <div class="cb">
        <pre class="code" dangerouslySetInnerHTML=${{ __html: highlightPython(it.completion || '') }}></pre>
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
  const ok = res.correct;
  return html`
    <div class="card">
      <div class="ch">
        <span class="id">${it.id}</span>
        <span class="t">judge scorecard</span>
        <span class=${'pill ' + (ok ? 'pass' : 'fail')}>${res.score ?? '—'} / 10</span>
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
  // device diff (home_automation) — compare final vs initial. The harness nests
  // initial_devices inside final_state; fall back to an episode-level field.
  const finalDevs = (ep.final_state && ep.final_state.devices) || null;
  const initDevs = (ep.final_state && ep.final_state.initial_devices) || ep.initial_devices || null;
  let diff = null;
  if (finalDevs && initDevs) {
    diff = Object.keys(finalDevs).map((k) => {
      const fv = finalDevs[k] && finalDevs[k].state;
      const iv = initDevs[k] && initDevs[k].state;
      return { k, v: fv, changed: String(fv) !== String(iv) };
    });
  }
  const flags = [];
  for (const f of ['state_ok', 'unchanged_ok', 'confirm_ok', 'required_ok', 'forbidden_ok']) {
    if (res[f] != null) flags.push([f.replace('_ok', ''), res[f]]);
  }
  return html`
    <div class="card">
      <div class="ch">
        <span class="id">${it.id}</span>
        <span class="t">${ep.toolset || 'agentic'} · ${ep.protocol || ''} · resolution: ${ep.resolution || res.resolution || '—'}</span>
        <span class=${'pill ' + (res.correct ? 'pass' : 'fail')}>${res.correct ? 'correct' : 'incorrect'}</span>
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
        ${diff ? html`<div class="label">final state · diff vs initial</div>
          <div class="statekv">
            ${diff.map((d) => html`<span class=${d.changed ? 'changed' : ''}>${d.k} <b>${d.v}</b></span>`)}
          </div>` : null}
        ${flags.length ? html`<div class="label">checks</div>
          <div class="statekv">
            ${flags.map(([k, v]) => html`<span><b style=${v ? '' : 'color:var(--bad)'}>${v ? '✓' : '✗'}</b> ${k}</span>`)}
          </div>` : null}
      </div>
    </div>`;
}

function GenericItem({ it }) {
  return html`
    <div class="card">
      <div class="ch"><span class="id">${it.id}</span><span class="t">raw item</span>
        ${it.result && it.result.correct != null
          ? html`<span class=${'pill ' + (it.result.correct ? 'pass' : 'fail')}>${it.result.correct ? 'correct' : 'incorrect'}</span>` : null}
      </div>
      <div class="cb">
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

// ---------- run detail ----------
function RunDetail({ run, data }) {
  if (!run) return html`<div class="empty">Select a run from the left.</div>`;
  if (!data) return html`<div class="empty">Loading ${run.raw_file} …</div>`;
  if (data.error) return html`<div class="empty">${data.error}: ${data.file || ''}</div>`;
  const Renderer = pickRenderer(run.scoring);
  const meta = [
    ['provider', run.provider], ['tok/s', fmt(run.mean_gen_tok_s, 1)],
    ['cost', '$' + fmt(run.cost_usd, 4)], ['ctx', run.num_ctx], ['date', run.date],
  ];
  return html`
    <div class="detail">
      <div class="crumb">${run.benchmark} / ${run.scoring} / ${data.n_items} items${data.parse_errors ? ` · ${data.parse_errors} parse errors` : ''}</div>
      <div class="dhead">
        <h2>${run.model}</h2>
        <span class=${'pill ' + passClass(run.observed_pass_at_k)}>pass@${run.k || 1} ${fmt(run.observed_pass_at_k)}</span>
      </div>
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

function WikiPane({ files, sel, onSelect, htmlContent }) {
  // group by top dir
  const groups = {};
  for (const f of files) {
    const top = f.includes('/') ? f.split('/')[0] : '·';
    (groups[top] = groups[top] || []).push(f);
  }
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
          ? html`<div class="crumb">wiki / ${sel}</div><div class="md" dangerouslySetInnerHTML=${{ __html: htmlContent }}></div>`
          : html`<div class="empty">Select a wiki page (read-only).</div>`}
      </div>
    </div>`;
}

// ---------- app ----------
function App() {
  const [tab, setTab] = useState('runs');
  const [runs, setRuns] = useState([]);
  const [sel, setSel] = useState(-1);
  const [data, setData] = useState(null);
  const [wikiFiles, setWikiFiles] = useState(null);
  const [wikiSel, setWikiSel] = useState(null);
  const [wikiHtml, setWikiHtml] = useState('');

  useEffect(() => { getJSON('/api/runs').then((d) => setRuns(d.runs || [])); }, []);

  const selectRun = useCallback((i) => {
    setSel(i); setData(null);
    getJSON('/api/run?file=' + encodeURIComponent(runs[i].raw_file)).then(setData);
  }, [runs]);

  const openWiki = useCallback(() => {
    setTab('wiki');
    if (wikiFiles == null) getJSON('/api/wiki').then((d) => setWikiFiles(d.files || []));
  }, [wikiFiles]);

  const selectWiki = useCallback((f) => {
    setWikiSel(f);
    fetch('/api/wiki?path=' + encodeURIComponent(f)).then((r) => r.text())
      .then((md) => setWikiHtml(marked.parse(preprocessMd(md))));
  }, []);

  return html`
    <div class="shell">
      <div class="topbar">
        <div class="brand">Benchmark Run Viewer<span class="sub">lab/benchmarks</span></div>
        <div class="tabs">
          <button class=${'tab' + (tab === 'runs' ? ' active' : '')} onClick=${() => setTab('runs')}>runs</button>
          <button class=${'tab' + (tab === 'wiki' ? ' active' : '')} onClick=${openWiki}>wiki</button>
        </div>
      </div>
      ${tab === 'runs'
        ? html`<div class="body">
            <${RunList} runs=${runs} sel=${sel} onSelect=${selectRun} />
            <${RunDetail} run=${sel >= 0 ? runs[sel] : null} data=${data} />
          </div>`
        : html`<${WikiPane} files=${wikiFiles || []} sel=${wikiSel} onSelect=${selectWiki} htmlContent=${wikiHtml} />`}
    </div>`;
}

render(html`<${App} />`, document.getElementById('app'));
