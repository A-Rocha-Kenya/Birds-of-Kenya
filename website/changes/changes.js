const changeSearch = document.getElementById('changeSearch');
const changeReport = document.getElementById('changeReport');
const changeError = document.getElementById('changeError');
const selected = { names: new Set(), concepts: new Set() };
let groups = [];

const filterConfig = {
  names: [['concept', 'Taxon concept'], ['english', 'English name'], ['scientific', 'Scientific name'], ['order', 'Order'], ['family', 'Family']],
  concepts: [['1:1', '1:1'], ['n:1', 'n:1'], ['1:n', '1:n'], ['n:n', 'n:n']]
};

const dictionary = {english: 'English name', scientific: 'Scientific name', order: 'Order', family: 'Family', family_english: 'Family name'};
const escapeHtml = value => {
  const element = document.createElement('span');
  element.textContent = value ?? '';
  return element.innerHTML;
};

const matchesField = (group, key) => key === 'concept' ? group.concept_changed : group.tags.includes(key);

const filterButton = ([key, label], kind) => {
  const count = groups.filter(group => kind === 'names' ? matchesField(group, key) : group.cardinality === key).length;
  return `<button class="filter" type="button" data-kind="${kind}" data-key="${key}" aria-pressed="false">${label} <span class="count">${count}</span></button>`;
};

const avibaseLink = id => {
  const shortId = id.replace(/^avibase-/, '');
  return `<a class="source-link" href="https://avibase.bsc-eoc.org/species.jsp?avibaseid=${encodeURIComponent(shortId)}" target="_blank" rel="noopener">Avibase · ${escapeHtml(shortId)}</a>`;
};

const taxon = row => `<div class="taxon"><div class="taxon-row"><div class="taxon-names"><span class="english">${escapeHtml(row.english)}</span><span class="scientific">${escapeHtml(row.scientific)}</span><small>${escapeHtml([row.order, `${row.family_english} (${row.family})`.trim()].filter(Boolean).join(" · "))}</small></div><div class="source-links">${avibaseLink(row.id)}</div></div></div>`;
const side = (rows, kind) => `<div class="side ${kind}"><strong>${escapeHtml(kind === 'old' ? fromVersion.value : toVersion.value)}</strong>${rows.map(taxon).join('')}</div>`;
const card = group => {
  const tags = group.tags.map(tag => `<span class="badge">${escapeHtml(dictionary[tag])}</span>`).join('');
  const concept = group.concept_changed ? '<span class="badge">Taxon concept</span>' : '';
  return `<article class="change-card" id="${escapeHtml(group.id)}"><div class="card-head"><div class="card-title">${escapeHtml(group.title)}</div><div class="badges"><span class="badge relationship">${escapeHtml(group.relationship_label)}</span>${concept}${tags}</div></div><div class="concept-grid">${side(group.old, 'old')}<div class="arrow" aria-hidden="true">→</div>${side(group.new, 'new')}</div></article>`;
};

const renderChanges = () => {
  const query = changeSearch.value.trim().toLowerCase();
  const visible = groups.filter(group => {
    const namesMatch = !selected.names.size || [...selected.names].every(key => matchesField(group, key));
    const conceptMatch = !selected.concepts.size || selected.concepts.has(group.cardinality);
    return namesMatch && conceptMatch && (!query || JSON.stringify(group).toLowerCase().includes(query));
  });

  let html = '';
  let order = '';
  let family = '';
  visible.forEach(group => {
    if (group.order !== order) {
      order = group.order;
      family = '';
      html += `<h2 class="order-heading">${escapeHtml(order)}</h2>`;
    }
    if (group.family !== family) {
      family = group.family;
      html += `<h3 class="family-heading">${escapeHtml(group.family_english)} <span>${escapeHtml(family)}</span></h3>`;
    }
    html += card(group);
  });
  changeReport.innerHTML = html || '<div class="no-results">No changes match these filters.</div>';
};

const bindFilters = () => {
  document.querySelectorAll('.changes-toolbar .filter').forEach(button => button.addEventListener('click', () => {
    const set = selected[button.dataset.kind];
    set.has(button.dataset.key) ? set.delete(button.dataset.key) : set.add(button.dataset.key);
    button.setAttribute('aria-pressed', set.has(button.dataset.key));
    renderChanges();
  }));
};

const fromVersion = document.getElementById('fromVersion');
const toVersion = document.getElementById('toVersion');
let catalog;
let requestNumber = 0;

const loadComparison = async () => {
  const request = ++requestNumber;
  changeError.hidden = true;
  groups = [];
  changeReport.replaceChildren();
  selected.names.clear();
  selected.concepts.clear();
  changeSearch.value = '';
  const pair = catalog.pairs.find(p => p.from_release === fromVersion.value && p.to_release === toVersion.value);
  document.getElementById('comparisonHeading').textContent = `From ${fromVersion.value} to ${toVersion.value}`;
  document.getElementById('comparisonCsv').href = `../${pair.files.csv}?v=${pair.revision}`;
  document.getElementById('comparisonSummary').textContent = 'Loading comparison…';
  const params = new URLSearchParams({from: fromVersion.value, to: toVersion.value});
  history.replaceState(null, '', `?${params}`);
  try {
    const response = await fetch(`../${pair.files.json}?v=${pair.revision}`);
    if (!response.ok) throw new Error('Comparison unavailable');
    const data = await response.json();
    if (request !== requestNumber) return;
    groups = data.groups;
    const excluded = catalog.releases.filter(r => [fromVersion.value, toVersion.value].includes(r.id)).reduce((n, r) => n + r.taxonomy_excluded_rows, 0);
    document.getElementById('comparisonSummary').textContent = `${groups.length} taxonomic changes. List additions/removals without reviewed taxonomic links are excluded.${excluded ? ` ${excluded} historical rows lack unique concept IDs and cannot be compared.` : ''}`;
    document.getElementById('nameFilters').innerHTML = '<span class="filter-label">Changed field</span>' + filterConfig.names.map(item => filterButton(item, 'names')).join('');
    document.getElementById('conceptFilters').innerHTML = '<span class="filter-label">Concept relationship</span>' + filterConfig.concepts.map(item => filterButton(item, 'concepts')).join('');
    bindFilters();
    renderChanges();
  } catch (error) {
    if (request !== requestNumber) return;
    changeError.hidden = false;
    changeError.textContent = 'The selected taxonomy comparison could not be loaded.';
    document.getElementById('comparisonSummary').textContent = '';
  }
};

fetch('../data/releases.json', {cache: 'no-cache'}).then(response => {
  if (!response.ok) throw new Error('Archive unavailable');
  return response.json();
}).then(data => {
  catalog = data;
  for (const select of [fromVersion, toVersion]) {
    data.releases.forEach(release => select.add(new Option(`${release.id}${release.status === 'draft' ? ' (preview)' : ''}`, release.id)));
  }
  const params = new URLSearchParams(location.search);
  const ids = data.releases.map(r => r.id);
  toVersion.value = ids.includes(params.get('to')) ? params.get('to') : data.active_release;
  fromVersion.value = ids.includes(params.get('from')) ? params.get('from') : ids[Math.max(0, ids.indexOf(toVersion.value) - 1)];
  fromVersion.addEventListener('change', loadComparison);
  toVersion.addEventListener('change', loadComparison);
  return loadComparison();
}).catch(() => {
  changeError.hidden = false;
  changeError.textContent = 'The checklist version archive could not be loaded.';
});

changeSearch.addEventListener('input', renderChanges);
document.getElementById('clearChangeFilters').addEventListener('click', () => {
  changeSearch.value = '';
  selected.names.clear();
  selected.concepts.clear();
  document.querySelectorAll('.changes-toolbar .filter').forEach(button => button.setAttribute('aria-pressed', 'false'));
  renderChanges();
});
