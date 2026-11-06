const changeSearch = document.getElementById('changeSearch');
const changeReport = document.getElementById('changeReport');
const changeError = document.getElementById('changeError');
const selected = { names: new Set(), concepts: new Set() };
let groups = [];

const filterConfig = {
  names: [['concept', 'Taxon concept'], ['english', 'Common name'], ['scientific', 'Scientific name'], ['order', 'Order'], ['family', 'Family']],
  concepts: [['1:1', '1:1'], ['n:1', 'n:1'], ['1:n', '1:n'], ['n:n', 'n:n'], ['0:1', '0:1'], ['1:0', '1:0']]
};

const dictionary = {english: 'Common name', scientific: 'Scientific name', order: 'Order', family: 'Family', family_english: 'Family name'};
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
const side = (rows, kind, note = '') => `<div class="side ${kind}">${rows.length ? rows.map(taxon).join('') : '<p class="empty">No linked entry in this version</p>'}${note}</div>`;
const card = group => {
  const tags = group.tags.map(tag => `<span class="badge">${escapeHtml(dictionary[tag])}</span>`).join('');
  const concept = group.concept_changed ? '<span class="badge">Taxon concept</span>' : '';
  const reviewed = group.membershipReview;
  const fromYear = fromVersion.value.slice(1, 5);
  const toYear = toVersion.value.slice(1, 5);
  const reviewedLabel = {listed: `Already covered in ${fromYear}`, possible: `Possible ${fromYear} counterpart`, addition: `Added to the ${toYear} checklist`, removal: `Omitted from the ${toYear} checklist`};
  const label = reviewed ? reviewedLabel[reviewed.status] : {added: 'Unlinked in source edition', removed: 'Unlinked in target edition'}[group.relationship] || group.relationship_label;
  const earc = reviewed?.earc_status === 'accepted'
    ? `<a class="badge earc-decision" href="${escapeHtml(reviewed.earc_url)}" target="_blank" rel="noopener">Accepted by EARC</a>`
    : reviewed?.earc_status === 'review' ? '<span class="badge pending-earc">EARC review</span>' : '';
  const sightings = (reviewed?.sighting_urls ?? []).map((url, i, urls) =>
    `<a href="${escapeHtml(url)}" target="_blank" rel="noopener">eBird sighting${urls.length > 1 ? ` ${i + 1}` : ''}</a>`).join(' ');
  const older = reviewed && reviewed.status !== 'removal'
    ? `<div class="side old"><p class="empty">${reviewed.entry_previous ? escapeHtml(reviewed.entry_previous) : `No checklist entry in ${fromYear}`}</p></div>`
    : side(group.old, 'old');
  const newer = reviewed?.status === 'removal'
    ? `<div class="side new"><p class="empty">No checklist entry in ${toYear}<small>${escapeHtml(reviewed.reason)}</small></p></div>`
    : side(group.new, 'new', reviewed ? `<p class="review-note">${escapeHtml(reviewed.reason)}${sightings ? ` ${sightings}` : ''}</p>` : '');
  return `<article class="change-card" id="${escapeHtml(group.id)}"><div class="card-head"><div class="badges"><span class="badge relationship">${escapeHtml(label)}</span>${earc}${concept}${tags}</div></div><div class="concept-grid">${older}<div class="arrow" aria-hidden="true">→</div>${newer}</div></article>`;
};

const renderChanges = () => {
  const searchKey = value => value.toLowerCase().replace(/[‘’]/g, "'");
  const query = searchKey(changeSearch.value.trim());
  const visible = groups.filter(group => {
    const namesMatch = !selected.names.size || [...selected.names].every(key => matchesField(group, key));
    const conceptMatch = !selected.concepts.size || selected.concepts.has(group.cardinality);
    return namesMatch && conceptMatch && (!query || searchKey(JSON.stringify(group)).includes(query));
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
  document.getElementById('comparisonCsv').href = `../${pair.files.csv}?v=${pair.revision}`;
  changeReport.setAttribute('aria-busy', 'true');
  const params = new URLSearchParams({from: fromVersion.value.slice(1, 5), to: toVersion.value.slice(1, 5)});
  history.replaceState(null, '', `?${params}`);
  try {
    const response = await fetch(`../${pair.files.json}?v=${pair.revision}`);
    if (!response.ok) throw new Error('Comparison unavailable');
    const data = await response.json();
    if (request !== requestNumber) return;
    groups = data.groups;
    const review = catalog.membership_reviews[`${data.from_release}/${data.to_release}`];
    if (review) {
      for (const group of groups) {
        if (group.relationship === 'added') group.membershipReview = review[group.new[0].id];
        if (group.relationship === 'removed') group.membershipReview = review[group.old[0].id];
      }
    }
    document.getElementById('nameFilters').innerHTML = '<span class="filter-label">Changed field</span>' + filterConfig.names.map(item => filterButton(item, 'names')).join('');
    document.getElementById('conceptFilters').innerHTML = '<span class="filter-label">Concept relationship</span>' + filterConfig.concepts.map(item => filterButton(item, 'concepts')).join('');
    bindFilters();
    renderChanges();
  } catch (error) {
    if (request !== requestNumber) return;
    changeError.hidden = false;
    changeError.textContent = 'The selected taxonomy comparison could not be loaded.';
  } finally {
    if (request === requestNumber) changeReport.removeAttribute('aria-busy');
  }
};

fetch('../data/releases.json', {cache: 'no-cache'}).then(response => {
  if (!response.ok) throw new Error('Archive unavailable');
  return response.json();
}).then(data => {
  catalog = data;
  const ids = Object.values(data.latest_by_year);
  for (const select of [fromVersion, toVersion]) {
    for (const [year, id] of Object.entries(data.latest_by_year)) select.add(new Option(year, id));
  }
  const params = new URLSearchParams(location.search);
  const latestFor = id => data.latest_by_year[id] ??
    (data.releases.some(release => release.id === id) ? data.latest_by_year[id.slice(1, 5)] : undefined);
  toVersion.value = latestFor(params.get('to')) ?? latestFor(data.active_release) ?? ids.at(-1);
  fromVersion.value = latestFor(params.get('from')) ?? ids[Math.max(0, ids.indexOf(toVersion.value) - 1)];
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
