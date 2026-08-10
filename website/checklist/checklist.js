const tableElement = document.getElementById('table');
const loader = document.getElementById('loader');
const errorElement = document.getElementById('error');
const exportButton = document.getElementById('exportFile');
const searchInput = document.getElementById('search');
const clearSearchButton = document.getElementById('clearSearch');
const clearFiltersButton = document.getElementById('clearFilters');
const resultCount = document.getElementById('resultCount');
const statusNotesButton = document.getElementById('statusNotes');
const statusDialog = document.getElementById('statusDialog');
const categoryLegend = document.getElementById('categoryLegend');
const tableTooltip = document.createElement('div');
tableTooltip.className = 'table-tooltip';
tableTooltip.hidden = true;
tableTooltip.setAttribute('role', 'tooltip');
document.body.appendChild(tableTooltip);

let hot;
let exportPlugin;
let allRows = [];
const selectedFilters = new Set();

const statusColumns = ['AM', 'AMR', 'E', 'ES', 'EX', 'HIST', 'IO', 'MM', 'N', 'NR', 'NRR', 'OM', 'PM', 'PMR', 'RAR', 'RS', 'SO', 'VIO', 'VM', 'VN', 'VO', 'VP', 'VSO', 'VSA'];
const migrantColumns = ['AM', 'AMR', 'MM', 'OM', 'PM', 'PMR'];
const vagrantColumns = ['VIO', 'VM', 'VN', 'VO', 'VP', 'VSO', 'VSA'];
const visitorColumns = ['IO', 'RS', 'SO'];
const historicalColumns = ['EX', 'HIST', 'NRR'];
let statusDisplayTokens = { AMR: 'AM+R', NR: 'N+R', PMR: 'PM+R' };
let statusDescriptions = {
  AM: 'Afrotropical migrant', AMR: 'Afrotropical migrant and resident', E: 'Endemic species', ES: 'Endemic subspecies', EX: 'Extinct in Kenya', HIST: 'Historical record',
  IO: 'Northwest Indian Ocean visitor', MM: 'Malagasy migrant', N: 'Nomadic or wanderer', NR: 'Nomadic or wanderer and resident', NRR: 'Not recently recorded',
  OM: 'Oriental migrant', PM: 'Palaearctic migrant', PMR: 'Palaearctic migrant and resident', RAR: 'Fewer than five EARC records at classification',
  RS: 'Red Sea visitor', SO: 'Southern Ocean visitor', VIO: 'Northwest Indian Ocean vagrant', VM: 'Malagasy vagrant', VN: 'Nearctic vagrant',
  VO: 'Oriental vagrant', VP: 'Palaearctic vagrant', VSO: 'Southern Ocean vagrant', VSA: 'Southern African vagrant', W: 'Waterbird'
};
const originDescriptions = { naturalized: 'eBird origin: Naturalized', provisional: 'eBird origin: Provisional' };

const renderCategoryLegend = definitions => {
  const groups = new Map();
  definitions.sort((a, b) => Number(a.display_order) - Number(b.display_order)).forEach(definition => {
    if (!groups.has(definition.display_group)) groups.set(definition.display_group, []);
    groups.get(definition.display_group).push(definition);
  });
  statusDisplayTokens = Object.fromEntries(definitions.map(definition => [definition.code, definition.display_token]));
  statusDescriptions = Object.fromEntries(definitions.flatMap(definition => [[definition.code, definition.label], [definition.display_token, definition.label]]));
  categoryLegend.replaceChildren(...[...groups].map(([group, categories]) => {
    const section = document.createElement('section');
    const heading = document.createElement('h3');
    heading.textContent = group;
    const grid = document.createElement('div');
    grid.className = 'legend-grid';
    categories.forEach(category => {
      const item = document.createElement('p');
      const token = document.createElement('strong');
      token.textContent = category.display_token;
      const label = document.createElement('span');
      label.textContent = category.label;
      item.append(token, label);
      grid.appendChild(item);
    });
    section.append(heading, grid);
    return section;
  }));
};

fetch('../data/category-definitions.json')
  .then(response => response.ok ? response.json() : Promise.reject())
  .then(renderCategoryLegend)
  .catch(() => { categoryLegend.textContent = 'Category definitions are unavailable.'; });

const columns = [
  'sequence',
  'english_name',
  'scientific_name',
  'order',
  'family',
  'family_english_name',
  'status',
  'observation_record_count',
  'first_observation_date',
  'last_observation_date',
  'membership_source',
  'sensitive',
  'water_bird',
  'avilist_id',
  'ebird_species_code',
  'source_avibase_ids'
];

const columnLabels = {
  sequence: 'Sequence',
  english_name: 'English name',
  scientific_name: 'Scientific name',
  order: 'Order',
  family: 'Family',
  family_english_name: 'Family name',
  status: 'Status',
  observation_record_count: 'eBird records',
  first_observation_date: 'First record',
  last_observation_date: 'Latest record',
  membership_source: 'Evidence',
  sensitive: 'Sensitive',
  water_bird: 'Waterbird',
  avilist_id: 'AviList ID',
  ebird_species_code: 'eBird code',
  source_avibase_ids: 'Source Avibase IDs'
};

const headerDescriptions = {
  sequence: 'Current AviList taxonomic sequence',
  status: 'Kenya checklist status codes; open Codes & notes for definitions',
  observation_record_count: 'Number of observation records contributing to this release',
  membership_source: 'Observation-based or curated sensitive-species membership',
  sensitive: 'Records may be absent or withheld for conservation reasons',
  source_avibase_ids: 'Avibase concepts mapped to the current AviList species'
};

const hiddenColumns = ['sequence', 'family_english_name', 'first_observation_date', 'membership_source', 'sensitive', 'water_bird', 'source_avibase_ids'];
const truthy = value => value === 'TRUE';
const formatNumber = value => Number(value).toLocaleString('en');

const linkRenderer = urlFor => function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  if (!value) return;
  const link = document.createElement('a');
  link.href = urlFor(value);
  link.target = '_blank';
  link.rel = 'noreferrer';
  link.textContent = value;
  link.title = `Open ${value} in a new tab`;
  td.textContent = '';
  td.appendChild(link);
};

const statusRenderer = function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  td.textContent = '';
  if (!value) return;
  value.split(', ').forEach(code => {
    const pill = document.createElement('span');
    pill.className = 'status-pill';
    pill.textContent = statusDisplayTokens[code] || code;
    pill.dataset.tooltip = statusDescriptions[code];
    pill.tabIndex = 0;
    pill.setAttribute('aria-label', `${code}: ${statusDescriptions[code]}`);
    td.appendChild(pill);
  });
};

const englishNameRenderer = function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  const source = instance.getSourceDataAtRow(row);
  const origin = source.exotic_status;
  td.textContent = '';
  td.append(document.createTextNode(value));
  if (origin !== 'native') {
    const badge = document.createElement('span');
    badge.className = `ebird-origin ${origin}`;
    badge.textContent = origin === 'naturalized' ? 'N' : 'P';
    badge.dataset.tooltip = originDescriptions[origin];
    badge.tabIndex = 0;
    badge.setAttribute('aria-label', originDescriptions[origin]);
    td.appendChild(badge);
  }
  if (truthy(source.sensitive)) {
    const sensitive = document.createElement('span');
    sensitive.className = 'ebird-origin sensitive';
    sensitive.textContent = 'S';
    sensitive.dataset.tooltip = 'Sensitive species: observation details are withheld for conservation reasons';
    sensitive.tabIndex = 0;
    sensitive.setAttribute('aria-label', sensitive.dataset.tooltip);
    td.appendChild(sensitive);
  }
};

const sourceRenderer = function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  const pill = document.createElement('span');
  pill.className = 'source-pill';
  pill.textContent = value === 'curated_sensitive_species' ? 'Curated sensitive list' : 'eBird observations';
  td.textContent = '';
  td.appendChild(pill);
};

const numberRenderer = function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  td.textContent = value ? formatNumber(value) : 'Withheld';
  if (!value) td.title = 'Observation evidence is not published for this sensitive species';
};

const columnDefinitions = columns.map(field => {
  const definition = { data: field, renderer: 'text' };
  if (field === 'english_name') {
    definition.className = 'english-name';
    definition.renderer = englishNameRenderer;
  }
  if (field === 'scientific_name') definition.className = 'scientific-name';
  if (field === 'status') definition.renderer = statusRenderer;
  if (field === 'observation_record_count') {
    definition.renderer = numberRenderer;
    definition.className = 'number';
  }
  if (field === 'membership_source') definition.renderer = sourceRenderer;
  if (field === 'avilist_id') definition.renderer = linkRenderer(value => `https://avibase.bsc-eoc.org/species.jsp?avibaseid=${encodeURIComponent(value.replace(/^avibase-/, ''))}`);
  if (field === 'ebird_species_code') definition.renderer = linkRenderer(value => `https://ebird.org/species/${encodeURIComponent(value)}/KE`);
  return definition;
});

const enrichRow = row => ({
  ...row,
  status: [...statusColumns.filter(code => truthy(row[code])), ...(truthy(row.water_bird) ? ['W'] : [])].join(', ')
});

const matchesFilter = (row, filter) => {
  if (filter === 'endemic') return truthy(row.E) || truthy(row.ES);
  if (filter === 'migrant') return migrantColumns.some(code => truthy(row[code]));
  if (filter === 'vagrant') return vagrantColumns.some(code => truthy(row[code]));
  if (filter === 'visitor') return visitorColumns.some(code => truthy(row[code]));
  if (filter === 'historical') return historicalColumns.some(code => truthy(row[code]));
  if (filter === 'rare') return truthy(row.RAR);
  if (filter === 'waterbird') return truthy(row.water_bird);
  return true;
};

const searchableText = row => [
  row.english_name,
  row.scientific_name,
  row.order,
  row.family,
  row.family_english_name,
  row.status,
  row.avilist_id,
  row.ebird_species_code,
  row.exotic_status
].join(' ').toLowerCase();

const renderView = () => {
  const query = searchInput.value.trim().toLowerCase();
  const rows = allRows.filter(row => {
    const filtersMatch = [...selectedFilters].every(filter => matchesFilter(row, filter));
    return filtersMatch && (!query || searchableText(row).includes(query));
  });

  hot.loadData(rows);
  resultCount.innerHTML = `Showing <b>${rows.length.toLocaleString()}</b> of ${allRows.length.toLocaleString()} species`;
  clearSearchButton.hidden = !query;
  clearFiltersButton.hidden = selectedFilters.size === 0;
};

const setFilterCounts = rows => {
  const setText = (id, value) => { document.getElementById(id).textContent = value.toLocaleString(); };
  setText('endemicCount', rows.filter(row => truthy(row.E) || truthy(row.ES)).length);
  setText('migrantCount', rows.filter(row => migrantColumns.some(code => truthy(row[code]))).length);
  setText('vagrantCount', rows.filter(row => vagrantColumns.some(code => truthy(row[code]))).length);
  setText('visitorCount', rows.filter(row => visitorColumns.some(code => truthy(row[code]))).length);
  setText('historicalCount', rows.filter(row => historicalColumns.some(code => truthy(row[code]))).length);
  setText('rareCount', rows.filter(row => truthy(row.RAR)).length);
  setText('waterbirdFilterCount', rows.filter(row => truthy(row.water_bird)).length);
};

const showError = message => {
  loader.hidden = true;
  errorElement.hidden = false;
  resultCount.textContent = 'Checklist unavailable';
  errorElement.textContent = message;
};

const tableHeight = () => Math.max(560, window.innerHeight - 150);

const showTooltip = element => {
  const bounds = element.getBoundingClientRect();
  tableTooltip.textContent = element.dataset.tooltip;
  tableTooltip.style.left = `${bounds.left + bounds.width / 2}px`;
  tableTooltip.style.top = `${bounds.top - 8}px`;
  tableTooltip.hidden = false;
};

tableElement.addEventListener('mouseover', event => {
  const element = event.target.closest('[data-tooltip]');
  if (element) showTooltip(element);
});
tableElement.addEventListener('mouseout', event => {
  const element = event.target.closest('[data-tooltip]');
  if (element && !element.contains(event.relatedTarget)) tableTooltip.hidden = true;
});
tableElement.addEventListener('focusin', event => {
  const element = event.target.closest('[data-tooltip]');
  if (element) showTooltip(element);
});
tableElement.addEventListener('focusout', () => { tableTooltip.hidden = true; });

Papa.parse('../data/checklist.csv', {
  encoding: 'UTF-8',
  download: true,
  header: true,
  skipEmptyLines: true,
  complete: results => {
    if (results.errors.length) {
      showError('The checklist could not be read. Please check the CSV file and reload the page.');
      return;
    }

    allRows = results.data.map(enrichRow);
    setFilterCounts(allRows);
    hot = new Handsontable(tableElement, {
      data: allRows,
      width: '100%',
      height: tableHeight(),
      stretchH: 'all',
      colHeaders: columns.map(field => columnLabels[field]),
      columns: columnDefinitions,
      readOnly: true,
      multiColumnSorting: true,
      filters: true,
      dropdownMenu: ['filter_by_condition', 'filter_by_value', 'filter_action_bar'],
      manualColumnResize: true,
      manualColumnFreeze: true,
      hiddenColumns: { columns: hiddenColumns.map(field => columns.indexOf(field)), indicators: true },
      contextMenu: ['freeze_column', 'unfreeze_column', '---------', 'hidden_columns_hide', 'hidden_columns_show', '---------', 'filter_by_value', 'filter_action_bar'],
      licenseKey: 'non-commercial-and-evaluation',
      modifyColWidth: width => Math.min(width, 300),
      afterGetColHeader: (col, th) => {
        const field = columns[col];
        const label = th.querySelector('.colHeader');
        if (label && headerDescriptions[field]) {
          label.title = headerDescriptions[field];
          label.setAttribute('aria-label', `${columnLabels[field]}: ${headerDescriptions[field]}`);
        }
      }
    });

    exportPlugin = hot.getPlugin('exportFile');
    exportButton.disabled = false;
    loader.hidden = true;
    renderView();
    window.addEventListener('resize', () => hot.updateSettings({ height: tableHeight() }));
  },
  error: () => showError('The checklist could not be loaded. Check your connection and reload the page.')
});

searchInput.addEventListener('input', renderView);
clearSearchButton.addEventListener('click', () => {
  searchInput.value = '';
  searchInput.focus();
  renderView();
});

document.querySelectorAll('.filter').forEach(button => button.addEventListener('click', () => {
  const filter = button.dataset.filter;
  selectedFilters.has(filter) ? selectedFilters.delete(filter) : selectedFilters.add(filter);
  button.setAttribute('aria-pressed', selectedFilters.has(filter));
  renderView();
}));

clearFiltersButton.addEventListener('click', () => {
  selectedFilters.clear();
  document.querySelectorAll('.filter').forEach(button => button.setAttribute('aria-pressed', 'false'));
  renderView();
});

exportButton.addEventListener('click', () => {
  if (!exportPlugin) return;
  exportPlugin.downloadFile('csv', {
    columnDelimiter: ',',
    exportHiddenColumns: false,
    exportHiddenRows: false,
    fileExtension: 'csv',
    filename: 'Birds_of_Kenya_2026-06.0',
    mimeType: 'text/csv',
    rowDelimiter: '\r\n'
  });
});

statusNotesButton.addEventListener('click', () => statusDialog.showModal());
statusDialog.querySelector('.dialog-close').addEventListener('click', () => statusDialog.close());
statusDialog.addEventListener('click', event => {
  if (event.target === statusDialog) statusDialog.close();
});
