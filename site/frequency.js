// "Frequency" tab: how often each technology / language shows up across projects.
// Charts are plain HTML (no library). Every chart has a table-view twin.

const CATEGORY_ORDER = ['AI & LLMs', 'Machine Learning', 'Data Engineering', 'Data Science',
  'Mobile', 'Web', 'Backend', 'Algorithms & CS', 'Python', 'Other'];
const LANG_SLOTS = 5;          // top languages get a categorical slot; the rest fold into "Other"
const TOP_TECHS = 15;          // bars shown before "Show all"
const HEAT_ROWS = 16;          // technologies in the stack-over-time heatmap
const HEAT_BINS = [1, 2, 3, 5, 8, 12]; // lower bounds of the 6 sequential steps

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pct = (n, d) => (d ? Math.round((n / d) * 100) : 0);
const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
const $ = (id) => document.getElementById(id);

// --- tooltip ---------------------------------------------------------------
let tip;
function showTip(target, value, lines, evt) {
  tip ??= Object.assign(document.body.appendChild(document.createElement('div')), { className: 'viz-tip', role: 'tooltip' });
  tip.replaceChildren();
  const strong = document.createElement('strong');
  strong.textContent = value;
  tip.append(strong);
  for (const l of lines) {
    const row = document.createElement('span');
    row.textContent = l;
    tip.append(row);
  }
  tip.hidden = false;
  const r = target.getBoundingClientRect();
  const x = evt?.clientX ?? r.left + r.width / 2;
  const y = evt?.clientY ?? r.top;
  const w = tip.offsetWidth;
  const h = tip.offsetHeight;
  tip.style.left = `${Math.min(Math.max(8, x - w / 2), innerWidth - w - 8)}px`;
  tip.style.top = `${y - h - 12 < 8 ? y + 18 : y - h - 12}px`;
}
const hideTip = () => { if (tip) tip.hidden = true; };

function bindTips(root, describe) {
  const on = (e) => {
    const el = e.target.closest('[data-tip]');
    if (!el || !root.contains(el)) return hideTip();
    const [value, ...lines] = describe(el);
    showTip(el, value, lines, e.type === 'pointermove' ? e : null);
  };
  root.addEventListener('pointermove', on);
  root.addEventListener('focusin', on);
  root.addEventListener('pointerleave', hideTip);
  root.addEventListener('focusout', hideTip);
}

// --- data ------------------------------------------------------------------
const primaryLang = (p) => p.languages?.[0]?.name || 'Unknown';

function techCounts(projects) {
  const m = new Map();
  projects.forEach((p) => p.stack.forEach((s) => m.set(s, (m.get(s) || 0) + 1)));
  return [...m].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

// --- charts ----------------------------------------------------------------
function techChart(projects, showAll) {
  const counts = techCounts(projects);
  const rows = showAll ? counts : counts.slice(0, TOP_TECHS);
  if (!rows.length) return { html: '<p class="viz-empty">No technologies detected.</p>', table: '' };
  const max = pct(rows[0][1], projects.length);
  const domain = Math.max(10, Math.ceil(max / 10) * 10);
  const step = domain > 50 ? 20 : 10;
  const ticks = [];
  for (let t = 0; t <= domain; t += step) ticks.push(t);

  const html = `<div class="hbar" style="--n:${rows.length}">
    <div class="hbar-axis" aria-hidden="true">${ticks.map((t) => `<span style="left:${(t / domain) * 100}%">${t}%</span>`).join('')}</div>
    <div class="hbar-grid" aria-hidden="true">${ticks.map((t) => `<i style="left:${(t / domain) * 100}%"></i>`).join('')}</div>
    ${rows.map(([name, n]) => {
      const share = pct(n, projects.length);
      return `<button type="button" class="hbar-row" data-tip data-tech="${esc(name)}" data-n="${n}"
        aria-label="${esc(name)}: ${share}% of projects (${n} of ${projects.length}). Show these projects.">
        <span class="hbar-label">${esc(name)}</span>
        <span class="hbar-plot"><span class="hbar-bar" style="--f:${share / domain}"></span><span class="hbar-val" style="--f:${share / domain}">${share}%</span></span>
      </button>`;
    }).join('')}
  </div>`;
  const table = `<table class="viz-table"><thead><tr><th>Technology</th><th>Projects</th><th>Share</th></tr></thead><tbody>${
    counts.map(([name, n]) => `<tr><td>${esc(name)}</td><td>${n}</td><td>${pct(n, projects.length)}%</td></tr>`).join('')}</tbody></table>`;
  return { html, table, total: counts.length };
}

function langChart(projects, slots) {
  const m = new Map();
  projects.forEach((p) => {
    const l = slots.includes(primaryLang(p)) ? primaryLang(p) : 'Other';
    m.set(l, (m.get(l) || 0) + 1);
  });
  const parts = [...slots, 'Other'].filter((l) => m.get(l)).map((l) => ({ l, n: m.get(l), slot: slots.indexOf(l) + 1 || 'other' }));
  if (!parts.length) return { html: '<p class="viz-empty">No languages detected.</p>', table: '' };
  const total = projects.length;
  const html = `<div class="segbar" role="img" aria-label="${esc(parts.map((p) => `${p.l} ${pct(p.n, total)}%`).join(', '))}">
    ${parts.map((p) => `<span class="seg" tabindex="0" data-tip data-lang="${esc(p.l)}" data-n="${p.n}"
      style="flex:${p.n};--fill:var(--series-${p.slot})" data-slot="${p.slot}"><b>${pct(p.n, total)}%</b></span>`).join('')}
  </div>
  <div class="viz-legend">${parts.map((p) => `<span><i style="--fill:var(--series-${p.slot})"></i>${esc(p.l)}</span>`).join('')}</div>`;
  const other = projects.filter((p) => !slots.includes(primaryLang(p))).map(primaryLang);
  const otherNote = other.length ? `<p class="viz-note">Other: ${esc([...new Set(other)].join(', '))}.</p>` : '';
  const table = `<table class="viz-table"><thead><tr><th>Primary language</th><th>Projects</th><th>Share</th></tr></thead><tbody>${
    parts.map((p) => `<tr><td>${esc(p.l)}</td><td>${p.n}</td><td>${pct(p.n, total)}%</td></tr>`).join('')}</tbody></table>${otherNote}`;
  return { html: html + otherNote, table };
}

function heatChart(projects) {
  if (!projects.length) return { html: '<p class="viz-empty">No projects.</p>', table: '' };
  const yearOf = (p) => Number(p.created.slice(0, 4));
  const years = [];
  const lo = Math.min(...projects.map(yearOf));
  const hi = Math.max(...projects.map(yearOf));
  for (let y = lo; y <= hi; y++) years.push(y);

  // count[tech][year]
  const count = new Map();
  projects.forEach((p) => p.stack.forEach((s) => {
    if (!count.has(s)) count.set(s, new Map());
    const row = count.get(s);
    row.set(yearOf(p), (row.get(yearOf(p)) || 0) + 1);
  }));
  // Rows: the top technologies of each year (so every era is represented), then overall top.
  const picked = new Set();
  const perYear = Math.max(2, Math.ceil(HEAT_ROWS / years.length));
  years.forEach((y) => {
    [...count].filter(([, r]) => r.get(y)).sort((a, b) => b[1].get(y) - a[1].get(y))
      .slice(0, perYear).forEach(([s]) => picked.add(s));
  });
  techCounts(projects).forEach(([s]) => { if (picked.size < HEAT_ROWS) picked.add(s); });
  const total = (s) => [...count.get(s).values()].reduce((a, b) => a + b, 0);
  const meanYear = (s) => [...count.get(s)].reduce((a, [y, n]) => a + y * n, 0) / total(s);
  const rows = [...picked].slice(0, HEAT_ROWS).sort((a, b) => meanYear(a) - meanYear(b));

  const bin = (n) => HEAT_BINS.reduce((b, lb, i) => (n >= lb ? i + 1 : b), 0);
  const html = `<div class="heat" style="--cols:${years.length}" role="img"
      aria-label="Number of projects per technology and year; full values in the table view.">
    <span></span>${years.map((y) => `<span class="heat-year">${y}</span>`).join('')}
    ${rows.map((s) => `<span class="heat-label">${esc(s)}</span>${years.map((y) => {
      const n = count.get(s).get(y) || 0;
      return `<span class="heat-cell" data-bin="${bin(n)}" ${n ? `data-tip data-tech="${esc(s)}" data-year="${y}" data-n="${n}"` : ''}></span>`;
    }).join('')}`).join('')}
  </div>
  <div class="heat-scale" aria-hidden="true"><span>Fewer</span>${HEAT_BINS.map((_, i) => `<i data-bin="${i + 1}"></i>`).join('')}<span>More projects</span></div>`;
  const table = `<table class="viz-table"><thead><tr><th>Technology</th>${years.map((y) => `<th>${y}</th>`).join('')}</tr></thead><tbody>${
    rows.map((s) => `<tr><td>${esc(s)}</td>${years.map((y) => `<td>${count.get(s).get(y) || '–'}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  return { html, table };
}

// Hide in-segment labels that don't fit their block (never clip them).
function fitSegLabels(root) {
  root.querySelectorAll('.seg b').forEach((b) => {
    b.style.visibility = '';
    if (b.offsetWidth + 12 > b.parentElement.clientWidth) b.style.visibility = 'hidden';
  });
}

// --- tab -------------------------------------------------------------------
export function initFrequency(data, { onPickTech }) {
  const all = data.projects;
  const state = { cat: '', showAll: false, table: {} };

  // Language colour slots are fixed on the full dataset so they never repaint on filter.
  const langTotals = new Map();
  all.forEach((p) => langTotals.set(primaryLang(p), (langTotals.get(primaryLang(p)) || 0) + 1));
  const slots = [...langTotals].sort((a, b) => b[1] - a[1]).map(([l]) => l)
    .filter((l) => l !== 'Unknown').slice(0, LANG_SLOTS);

  const counts = {};
  all.forEach((p) => { counts[p.category] = (counts[p.category] || 0) + 1; });
  const cats = Object.keys(counts).sort((a, b) => CATEGORY_ORDER.indexOf(a) - CATEGORY_ORDER.indexOf(b));
  $('freqCats').innerHTML = [['', 'All', all.length], ...cats.map((c) => [c, c, counts[c]])]
    .map(([val, label, n]) => `<button class="chip" role="tab" type="button" data-val="${esc(val)}" data-cat="${esc(val)}"
      aria-selected="${val === ''}">${esc(label)} <small>${n}</small></button>`).join('');

  const render = () => {
    const projects = state.cat ? all.filter((p) => p.category === state.cat) : all;
    const scope = state.cat ? `${plural(projects.length, 'project')} in ${state.cat}` : `all ${plural(projects.length, 'project')}`;
    document.querySelectorAll('.freq-scope').forEach((el) => { el.textContent = scope; });

    const t = techChart(projects, state.showAll);
    $('techChart').innerHTML = state.table.tech ? t.table : t.html;
    $('techMore').hidden = state.table.tech || (t.total ?? 0) <= TOP_TECHS;
    $('techMore').textContent = state.showAll ? `Show top ${TOP_TECHS}` : `Show all ${t.total}`;

    const l = langChart(projects, slots);
    $('langChart').innerHTML = state.table.lang ? l.table : l.html;
    fitSegLabels($('langChart'));

    const h = heatChart(projects);
    $('heatChart').innerHTML = state.table.heat ? h.table : h.html;

    document.querySelectorAll('[data-table-toggle]').forEach((b) => {
      const on = !!state.table[b.dataset.tableToggle];
      b.setAttribute('aria-pressed', String(on));
      b.textContent = on ? 'Chart' : 'Table';
    });
    document.querySelectorAll('#freqCats .chip').forEach((c) => c.setAttribute('aria-selected', String(c.dataset.val === state.cat)));
    state.projects = projects;
  };

  $('freqCats').addEventListener('click', (e) => {
    const chip = e.target.closest('.chip');
    if (chip) { state.cat = chip.dataset.val; render(); }
  });
  $('techMore').addEventListener('click', () => { state.showAll = !state.showAll; render(); });
  document.querySelectorAll('[data-table-toggle]').forEach((b) => b.addEventListener('click', () => {
    state.table[b.dataset.tableToggle] = !state.table[b.dataset.tableToggle];
    render();
  }));
  $('techChart').addEventListener('click', (e) => {
    const row = e.target.closest('.hbar-row');
    if (row) { hideTip(); onPickTech(row.dataset.tech); }
  });

  const names = (filter) => {
    const list = state.projects.filter(filter).map((p) => p.title);
    return list.length > 3 ? `${list.slice(0, 3).join(', ')} +${list.length - 3} more` : list.join(', ');
  };
  bindTips($('techChart'), (el) => {
    const n = Number(el.dataset.n);
    return [`${pct(n, state.projects.length)}%`, `${el.dataset.tech} · ${n} of ${state.projects.length} projects`,
      names((p) => p.stack.includes(el.dataset.tech)), 'Click to see these projects'];
  });
  bindTips($('langChart'), (el) => {
    const n = Number(el.dataset.n);
    const l = el.dataset.lang;
    return [`${pct(n, state.projects.length)}%`, `${l} · ${plural(n, 'project')}`,
      names((p) => (l === 'Other' ? !slots.includes(primaryLang(p)) : primaryLang(p) === l))];
  });
  bindTips($('heatChart'), (el) => {
    const y = Number(el.dataset.year);
    return [plural(Number(el.dataset.n), 'project'), `${el.dataset.tech} · ${y}`,
      names((p) => p.stack.includes(el.dataset.tech) && Number(p.created.slice(0, 4)) === y)];
  });

  new ResizeObserver(() => fitSegLabels($('langChart'))).observe($('langChart'));
  render();
  return { refit: () => fitSegLabels($('langChart')) };
}
