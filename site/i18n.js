// UI translations (English, Portuguese, Spanish).
// Project summaries come from GitHub and are shown as written.

export const LANGS = ['en', 'pt', 'es'];
const HTML_LANG = { en: 'en', pt: 'pt-BR', es: 'es' };

const projects = { en: ['project', 'projects'], pt: ['projeto', 'projetos'], es: ['proyecto', 'proyectos'] };

const DICT = {
  en: {
    'tab.projects': 'Projects', 'tab.frequency': 'Frequency',
    seeProjects: 'See projects', featured: 'Featured', allProjects: 'All projects',
    all: 'All', allTech: 'All technologies', search: 'Search projects, stacks…',
    'sort.featured': 'Featured first', 'sort.updated': 'Recently updated', 'sort.created': 'Newest',
    'sort.stars': 'Most stars', 'sort.name': 'Name',
    countOf: '{n} of {total}', empty: 'No projects match your filters.',
    loadError: 'Could not load projects.', updated: 'Updated {ago}', live: 'Live ↗',
    auto: 'auto', autoTitle: 'No README yet — summary generated from the detected stack',
    viewCode: 'View code ↗', liveDemo: 'Live demo ↗', createdUpdated: 'Created {c} · Updated {u}',
    readmeLoading: 'Loading README…', readmeError: 'Could not load the README.',
    noReadme: "This repository doesn't have a README yet. The summary above was generated from its detected stack.",
    synced: 'synced from GitHub {ago}', close: 'Close', language: 'Language',
    // Frequency
    frequency: 'Frequency', table: 'Table', chart: 'Chart', showAll: 'Show all {n}', showTop: 'Show top {n}',
    techTitle: 'Technologies',
    techSub: "Share of {scope} that use each technology. A project usually uses several, so the bars don't add up to 100%.",
    langTitle: 'Primary language', langSub: 'Main language of {scope}, by code size in each repo.',
    heatTitle: 'Stack over time', heatSub: 'Projects started each year that use a technology, across {scope}.',
    scopeAll: 'all {projects}', scopeCat: '{projects} in {cat}',
    noTech: 'No technologies detected.', noLang: 'No languages detected.', noProjects: 'No projects.',
    thTech: 'Technology', thProjects: 'Projects', thShare: 'Share', thLang: 'Primary language',
    other: 'Other', otherNote: 'Other: {list}.', fewer: 'Fewer', more: 'More projects',
    nOfTotal: '{tech} · {n} of {total} projects', clickToSee: 'Click to see these projects',
    moreNames: '{names} +{n} more',
    barAria: '{tech}: {share}% of projects ({n} of {total}). Show these projects.',
    heatAria: 'Number of projects per technology and year; full values in the table view.',
    'cat.AI & LLMs': 'AI & LLMs', 'cat.Machine Learning': 'Machine Learning', 'cat.Data Engineering': 'Data Engineering',
    'cat.Data Science': 'Data Science', 'cat.Mobile': 'Mobile', 'cat.Web': 'Web', 'cat.Backend': 'Backend',
    'cat.Algorithms & CS': 'Algorithms & CS', 'cat.Python': 'Python', 'cat.Other': 'Other',
  },
  pt: {
    'tab.projects': 'Projetos', 'tab.frequency': 'Frequência',
    seeProjects: 'Ver projetos', featured: 'Destaques', allProjects: 'Todos os projetos',
    all: 'Todos', allTech: 'Todas as tecnologias', search: 'Buscar projetos, tecnologias…',
    'sort.featured': 'Destaques primeiro', 'sort.updated': 'Atualizados recentemente', 'sort.created': 'Mais novos',
    'sort.stars': 'Mais estrelas', 'sort.name': 'Nome',
    countOf: '{n} de {total}', empty: 'Nenhum projeto corresponde aos filtros.',
    loadError: 'Não foi possível carregar os projetos.', updated: 'Atualizado {ago}', live: 'Ao vivo ↗',
    auto: 'auto', autoTitle: 'Ainda sem README — resumo gerado a partir das tecnologias detectadas',
    viewCode: 'Ver código ↗', liveDemo: 'Ver demo ↗', createdUpdated: 'Criado em {c} · Atualizado em {u}',
    readmeLoading: 'Carregando README…', readmeError: 'Não foi possível carregar o README.',
    noReadme: 'Este repositório ainda não tem README. O resumo acima foi gerado a partir das tecnologias detectadas.',
    synced: 'sincronizado com o GitHub {ago}', close: 'Fechar', language: 'Idioma',
    frequency: 'Frequência', table: 'Tabela', chart: 'Gráfico', showAll: 'Mostrar todas ({n})', showTop: 'Mostrar top {n}',
    techTitle: 'Tecnologias',
    techSub: 'Parcela de {scope} que usa cada tecnologia. Um projeto costuma usar várias, então as barras não somam 100%.',
    langTitle: 'Linguagem principal', langSub: 'Linguagem principal de {scope}, pelo tamanho do código em cada repositório.',
    heatTitle: 'Tecnologias ao longo do tempo', heatSub: 'Projetos iniciados a cada ano que usam uma tecnologia, entre {scope}.',
    scopeAll: 'todos os {projects}', scopeCat: '{projects} em {cat}',
    noTech: 'Nenhuma tecnologia detectada.', noLang: 'Nenhuma linguagem detectada.', noProjects: 'Nenhum projeto.',
    thTech: 'Tecnologia', thProjects: 'Projetos', thShare: 'Parcela', thLang: 'Linguagem principal',
    other: 'Outras', otherNote: 'Outras: {list}.', fewer: 'Menos', more: 'Mais projetos',
    nOfTotal: '{tech} · {n} de {total} projetos', clickToSee: 'Clique para ver esses projetos',
    moreNames: '{names} +{n}',
    barAria: '{tech}: {share}% dos projetos ({n} de {total}). Mostrar esses projetos.',
    heatAria: 'Número de projetos por tecnologia e ano; valores completos na visualização em tabela.',
    'cat.AI & LLMs': 'IA & LLMs', 'cat.Machine Learning': 'Machine Learning', 'cat.Data Engineering': 'Engenharia de Dados',
    'cat.Data Science': 'Ciência de Dados', 'cat.Mobile': 'Mobile', 'cat.Web': 'Web', 'cat.Backend': 'Backend',
    'cat.Algorithms & CS': 'Algoritmos & Computação', 'cat.Python': 'Python', 'cat.Other': 'Outros',
  },
  es: {
    'tab.projects': 'Proyectos', 'tab.frequency': 'Frecuencia',
    seeProjects: 'Ver proyectos', featured: 'Destacados', allProjects: 'Todos los proyectos',
    all: 'Todos', allTech: 'Todas las tecnologías', search: 'Buscar proyectos, tecnologías…',
    'sort.featured': 'Destacados primero', 'sort.updated': 'Actualizados recientemente', 'sort.created': 'Más nuevos',
    'sort.stars': 'Más estrellas', 'sort.name': 'Nombre',
    countOf: '{n} de {total}', empty: 'Ningún proyecto coincide con los filtros.',
    loadError: 'No se pudieron cargar los proyectos.', updated: 'Actualizado {ago}', live: 'En vivo ↗',
    auto: 'auto', autoTitle: 'Aún sin README — resumen generado a partir de las tecnologías detectadas',
    viewCode: 'Ver código ↗', liveDemo: 'Ver demo ↗', createdUpdated: 'Creado en {c} · Actualizado en {u}',
    readmeLoading: 'Cargando README…', readmeError: 'No se pudo cargar el README.',
    noReadme: 'Este repositorio aún no tiene README. El resumen de arriba se generó a partir de las tecnologías detectadas.',
    synced: 'sincronizado con GitHub {ago}', close: 'Cerrar', language: 'Idioma',
    frequency: 'Frecuencia', table: 'Tabla', chart: 'Gráfico', showAll: 'Mostrar todas ({n})', showTop: 'Mostrar top {n}',
    techTitle: 'Tecnologías',
    techSub: 'Proporción de {scope} que usa cada tecnología. Un proyecto suele usar varias, así que las barras no suman 100%.',
    langTitle: 'Lenguaje principal', langSub: 'Lenguaje principal de {scope}, según el tamaño del código de cada repositorio.',
    heatTitle: 'Tecnologías a lo largo del tiempo', heatSub: 'Proyectos iniciados cada año que usan una tecnología, entre {scope}.',
    scopeAll: 'todos los {projects}', scopeCat: '{projects} en {cat}',
    noTech: 'No se detectaron tecnologías.', noLang: 'No se detectaron lenguajes.', noProjects: 'Sin proyectos.',
    thTech: 'Tecnología', thProjects: 'Proyectos', thShare: 'Proporción', thLang: 'Lenguaje principal',
    other: 'Otros', otherNote: 'Otros: {list}.', fewer: 'Menos', more: 'Más proyectos',
    nOfTotal: '{tech} · {n} de {total} proyectos', clickToSee: 'Haz clic para ver estos proyectos',
    moreNames: '{names} +{n}',
    barAria: '{tech}: {share}% de los proyectos ({n} de {total}). Mostrar estos proyectos.',
    heatAria: 'Número de proyectos por tecnología y año; valores completos en la vista de tabla.',
    'cat.AI & LLMs': 'IA y LLMs', 'cat.Machine Learning': 'Machine Learning', 'cat.Data Engineering': 'Ingeniería de Datos',
    'cat.Data Science': 'Ciencia de Datos', 'cat.Mobile': 'Móvil', 'cat.Web': 'Web', 'cat.Backend': 'Backend',
    'cat.Algorithms & CS': 'Algoritmos y Computación', 'cat.Python': 'Python', 'cat.Other': 'Otros',
  },
};

function detect() {
  const fromUrl = new URLSearchParams(location.search).get('lang');
  if (LANGS.includes(fromUrl)) return fromUrl;
  try {
    const saved = localStorage.getItem('lang');
    if (LANGS.includes(saved)) return saved;
  } catch {}
  for (const l of navigator.languages || [navigator.language || 'en']) {
    const code = String(l).slice(0, 2).toLowerCase();
    if (LANGS.includes(code)) return code;
  }
  return 'en';
}

let lang = detect();
document.documentElement.lang = HTML_LANG[lang];

export const getLang = () => lang;

export function setLang(l) {
  if (!LANGS.includes(l)) return;
  lang = l;
  document.documentElement.lang = HTML_LANG[l];
  try { localStorage.setItem('lang', l); } catch {}
}

export function t(key, vars = {}) {
  const s = DICT[lang][key] ?? DICT.en[key] ?? key;
  return s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? `{${k}}`));
}

export const tCat = (c) => (DICT[lang][`cat.${c}`] ?? c);

export const nProjects = (n) => `${n} ${projects[lang][n === 1 ? 0 : 1]}`;

// A config value may be a plain string or {"en": "...", "pt": "...", "es": "..."}.
export const pick = (v) => (v && typeof v === 'object' ? (v[lang] ?? v.en ?? Object.values(v)[0]) : (v ?? ''));

export function ago(iso) {
  const rtf = new Intl.RelativeTimeFormat(HTML_LANG[lang], { numeric: 'auto' });
  const days = (Date.now() - new Date(iso)) / 864e5;
  if (days < 1) return rtf.format(0, 'day');
  if (days < 31) return rtf.format(-Math.round(days), 'day');
  if (days < 365) return rtf.format(-Math.round(days / 30), 'month');
  return rtf.format(-Math.round(days / 365), 'year');
}

export const fmtDate = (iso) => new Date(iso).toLocaleDateString(HTML_LANG[lang], { year: 'numeric', month: 'short' });

// Static text in index.html: data-i18n, data-i18n-placeholder, data-i18n-aria-label.
export function applyStatic(root = document) {
  root.querySelectorAll('[data-i18n]').forEach((el) => { el.textContent = t(el.dataset.i18n); });
  root.querySelectorAll('[data-i18n-placeholder]').forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  root.querySelectorAll('[data-i18n-aria-label]').forEach((el) => el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel)));
}
