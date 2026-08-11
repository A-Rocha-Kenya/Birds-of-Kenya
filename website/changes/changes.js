const changeSearch = document.getElementById('changeSearch');
const changeReport = document.getElementById('changeReport');
const changeResultCount = document.getElementById('changeResultCount');
const changeError = document.getElementById('changeError');
const selected = { names: new Set(), concepts: new Set() };
let groups = [];

const filterConfig = {
  names: [['english_name', 'English name'], ['scientific_name', 'Scientific name'], ['classification', 'Family placement']],
  concepts: [['retained', 'Same taxon'], ['replacement', 'One-to-one revision'], ['split', 'Split'], ['lump', 'Lump'], ['many_to_many', 'Complex revision'], ['added', 'Added to current checklist'], ['unresolved', 'Mapping pending']]
};

const dictionary = { english_name: 'English name', scientific_name: 'Scientific name', classification: 'Family placement' };
const escapeHtml = value => {
  const element = document.createElement('span');
  element.textContent = value ?? '';
  return element.innerHTML;
};

const filterButton = ([key, label], kind) => {
  const count = groups.filter(group => kind === 'names' ? group.tags.includes(key) : group.relationship === key).length;
  return `<button class="filter" type="button" data-kind="${kind}" data-key="${key}" aria-pressed="false">${label} <span class="count">${count}</span></button>`;
};

const avibaseLink = id => {
  const shortId = id.replace(/^avibase-/, '');
  return `<a class="source-link" href="https://avibase.bsc-eoc.org/species.jsp?avibaseid=${encodeURIComponent(shortId)}" target="_blank" rel="noopener">Avibase · ${escapeHtml(shortId)}</a>`;
};

const ebirdLinks = row => (row.ebird_codes || []).map(code => `<a class="source-link" href="https://ebird.org/species/${encodeURIComponent(code)}/KE" target="_blank" rel="noopener">eBird · ${escapeHtml(code)}</a>`).join('');
const taxon = row => {
  const note = row.taxonomy_comment ? `<div class="taxonomy-note"><strong>AviList taxonomy decision</strong>${escapeHtml(row.taxonomy_comment)}</div>` : '';
  return `<div class="taxon"><div class="taxon-row"><div class="taxon-names"><span class="english">${escapeHtml(row.english)}</span><span class="scientific">${escapeHtml(row.scientific)}</span></div><div class="source-links">${avibaseLink(row.id)}${ebirdLinks(row)}</div></div>${note}</div>`;
};
const side = (rows, kind) => `<div class="side ${kind}">${rows.length ? rows.map(taxon).join('') : '<div class="empty">None listed</div>'}</div>`;

const card = group => {
  const tags = group.tags.filter(tag => tag !== 'concept').map(tag => `<span class="badge">${escapeHtml(dictionary[tag])}</span>`).join('');
  const unresolved = group.relationship === 'unresolved' ? ' unresolved' : '';
  return `<article class="change-card" id="${escapeHtml(group.id)}"><div class="card-head"><div class="card-title">${escapeHtml(group.title)}</div><div class="badges"><span class="badge relationship${unresolved}">${escapeHtml(group.relationship_label)}</span>${tags}</div></div><div class="concept-grid">${side(group.old, 'old')}<div class="arrow" aria-hidden="true"><span>→</span></div>${side(group.new, 'new')}</div></article>`;
};

const renderChanges = () => {
  const query = changeSearch.value.trim().toLowerCase();
  const visible = groups.filter(group => {
    const namesMatch = !selected.names.size || [...selected.names].every(key => group.tags.includes(key));
    const conceptMatch = !selected.concepts.size || selected.concepts.has(group.relationship);
    return namesMatch && conceptMatch && (!query || JSON.stringify(group).toLowerCase().includes(query));
  });

  changeResultCount.innerHTML = `Showing <b>${visible.length.toLocaleString()}</b> of ${groups.length.toLocaleString()} change groups`;
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
      html += `<h3 class="family-heading">${escapeHtml(family)} <span>${escapeHtml(group.family_english)}</span></h3>`;
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

fetch('../data/taxonomy-changes.json')
  .then(response => {
    if (!response.ok) throw new Error('Comparison data unavailable');
    return response.json();
  })
  .then(data => {
    groups = data.groups;
    document.getElementById('nameFilters').insertAdjacentHTML('beforeend', filterConfig.names.map(item => filterButton(item, 'names')).join(''));
    document.getElementById('conceptFilters').insertAdjacentHTML('beforeend', filterConfig.concepts.map(item => filterButton(item, 'concepts')).join(''));
    bindFilters();
    renderChanges();
  })
  .catch(() => {
    changeResultCount.textContent = 'Comparison unavailable';
    changeError.hidden = false;
    changeError.textContent = 'The taxonomy comparison could not be loaded.';
  });

changeSearch.addEventListener('input', renderChanges);
document.getElementById('clearChangeFilters').addEventListener('click', () => {
  changeSearch.value = '';
  selected.names.clear();
  selected.concepts.clear();
  document.querySelectorAll('.changes-toolbar .filter').forEach(button => button.setAttribute('aria-pressed', 'false'));
  renderChanges();
});
