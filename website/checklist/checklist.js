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
const columnChooserButton = document.getElementById('columnChooser');
const columnDialog = document.getElementById('columnDialog');
const availableColumnsSelect = document.getElementById('availableColumns');
const visibleColumnsSelect = document.getElementById('visibleColumns');
const tableTooltip = document.createElement('div');
tableTooltip.className = 'table-tooltip';
tableTooltip.hidden = true;
tableTooltip.setAttribute('role', 'tooltip');
document.body.appendChild(tableTooltip);

let hot;
let exportPlugin;
let allRows = [];
const selectedFilters = new Set();

const statusColumns = ['HIST', 'RAR'];
const hiddenCategoryGroups = new Set(['Regular movement', 'Regional visitors', 'Regional vagrants']);
let statusDisplayTokens = {};
let statusDescriptions = {HIST: 'Historical occurrence', RAR: 'Rare'};
const originStatusDefinitions = [
  {
    code: 'naturalized', label: 'Naturalized', definition: 'Established non-native species in Kenya',
    display_group: 'Origin status', display_token: 'Naturalized', display_order: 55
  },
  {
    code: 'provisional', label: 'Provisional', definition: 'eBird provisional origin status',
    display_group: 'Origin status', display_token: 'Provisional', display_order: 56
  }
];
const reviewStatusDefinition = {
  code: 'PE', label: 'Pending EARC', definition: 'Added since 2019 and not represented in the curated EARC decision list',
  display_group: 'Review status', display_token: 'Pending EARC', display_order: 59
};

const renderCategoryLegend = definitions => {
  definitions = [...definitions.filter(definition => !hiddenCategoryGroups.has(definition.display_group)), {
    code: 'S', label: 'Sensitive species', definition: 'Species with observation details withheld for conservation reasons',
    display_group: 'Data handling', display_token: 'S', display_order: 60
  }, ...originStatusDefinitions, reviewStatusDefinition];
  definitions.sort((a, b) => Number(a.display_order) - Number(b.display_order));
  statusDisplayTokens = Object.fromEntries(definitions.map(definition => [definition.code, definition.display_token]));
  statusDescriptions = Object.fromEntries(definitions.flatMap(definition => {
    const description = `${definition.label}: ${definition.definition}`;
    return [[definition.code, description], [definition.display_token, description]];
  }));
  const grid = document.createElement('div');
  grid.className = 'legend-grid';
  definitions.forEach(category => {
    const item = document.createElement('p');
    const token = document.createElement('strong');
    token.textContent = category.display_token;
    const text = document.createElement('span');
    text.textContent = `${category.label}: ${category.definition}`;
    item.append(token, text);
    grid.appendChild(item);
  });
  categoryLegend.replaceChildren(grid);
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
  'iucn_red_list_category',
  'birdlife_datazone_url',
  'birds_of_the_world_url',
  'observations',
  'first_observation_date',
  'last_observation_date',
  'avibase_id',
  'safring_numbers',
  'ebird_species_code'
];

const columnLabels = {
  sequence: 'Sequence',
  english_name: 'English name',
  scientific_name: 'Scientific name',
  order: 'Order',
  family: 'Family',
  family_english_name: 'Family name',
  status: 'Status',
  iucn_red_list_category: 'Conservation',
  birdlife_datazone_url: 'BirdLife Data Zone',
  birds_of_the_world_url: 'Birds of the World',
  observations: 'eBird observations',
  first_observation_date: 'First record',
  last_observation_date: 'Latest record',
  avibase_id: 'Avibase ID',
  safring_numbers: 'KBM',
  ebird_species_code: 'eBird code'
};

const headerDescriptions = {
  sequence: 'Current AviList taxonomic sequence',
  status: 'Kenya checklist status codes; open Codes & notes for definitions',
  iucn_red_list_category: 'Global IUCN Red List category',
  birdlife_datazone_url: 'Open the BirdLife Data Zone species page',
  birds_of_the_world_url: 'Open the Birds of the World species account',
  safring_numbers: 'KBM SAFRING identifier or identifiers linked to this AviList species',
  observations: 'Number of eBird observation clusters within three calendar months and 3 km'
};

const defaultVisibleColumns = [
  'sequence',
  'english_name',
  'scientific_name',
  'status',
  'iucn_red_list_category',
  'avibase_id',
  'ebird_species_code',
  'safring_numbers',
  'birds_of_the_world_url',
  'birdlife_datazone_url',
  'observations',
  'last_observation_date'
];
const savedVisibleColumns = JSON.parse(localStorage.getItem('birds-of-kenya-visible-columns') || '[]');
const restoredVisibleColumns = savedVisibleColumns.filter(field => columns.includes(field));
let visibleColumns = restoredVisibleColumns.length ? restoredVisibleColumns : [...defaultVisibleColumns];
let pendingVisibleColumns = [];
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

const resourceLinkRenderer = label => function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  td.textContent = '';
  if (!value) return;
  const link = document.createElement('a');
  link.href = value;
  link.target = '_blank';
  link.rel = 'noreferrer';
  link.className = 'resource-link';
  link.textContent = label;
  link.title = `Open ${label} in a new tab`;
  td.appendChild(link);
};

const conservationColors = {
  LC: 'least-concern', NT: 'near-threatened', VU: 'vulnerable', EN: 'endangered',
  CR: 'critically-endangered', EW: 'extinct-in-wild', EX: 'extinct', DD: 'data-deficient', NE: 'not-evaluated'
};
const conservationLabels = {
  LC: 'Least Concern', NT: 'Near Threatened', VU: 'Vulnerable', EN: 'Endangered',
  CR: 'Critically Endangered', EW: 'Extinct in the Wild', EX: 'Extinct',
  DD: 'Data Deficient', NE: 'Not Evaluated'
};

const conservationRenderer = function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  td.textContent = '';
  if (!value) return;
  const icon = document.createElement('span');
  icon.className = `conservation-status ${conservationColors[value] || 'not-evaluated'}`;
  icon.textContent = value;
  icon.dataset.tooltip = `IUCN Red List: ${conservationLabels[value] || value}`;
  icon.tabIndex = 0;
  icon.setAttribute('aria-label', icon.dataset.tooltip);
  td.appendChild(icon);
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

const numberRenderer = function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  td.textContent = value ? formatNumber(value) : 'Withheld';
  if (!value) td.title = 'Observation evidence is not published for this sensitive species';
};

const avibaseIdRenderer = function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  const code = value.replace(/^avibase-/, '');
  const link = document.createElement('a');
  link.href = `https://avibase.bsc-eoc.org/species.jsp?avibaseid=${encodeURIComponent(code)}`;
  link.target = '_blank';
  link.rel = 'noreferrer';
  link.textContent = code;
  link.title = `Open ${value} in a new tab`;
  td.textContent = '';
  td.appendChild(link);
};

const safringNumbersRenderer = function(instance, td, row, col, prop, value) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  td.textContent = '';
  if (!value) return;
  value.split(';').forEach((number, index) => {
    if (index) td.appendChild(document.createTextNode('; '));
    const link = document.createElement('a');
    link.href = `https://kenya.birdmap.africa/species/${encodeURIComponent(number)}`;
    link.target = '_blank';
    link.rel = 'noreferrer';
    link.textContent = number;
    link.title = `Open KBM SAFRING number ${number} in a new tab`;
    td.appendChild(link);
  });
};

const columnDefinitions = columns.map(field => {
  const definition = { data: field, renderer: 'text' };
  if (field === 'english_name') {
    definition.className = 'english-name';
  }
  if (field === 'scientific_name') definition.className = 'scientific-name';
  if (field === 'status') definition.renderer = statusRenderer;
  if (field === 'iucn_red_list_category') definition.renderer = conservationRenderer;
  if (field === 'birdlife_datazone_url') definition.renderer = resourceLinkRenderer('Data Zone');
  if (field === 'birds_of_the_world_url') definition.renderer = resourceLinkRenderer('Birds of the World');
  if (field === 'avibase_id') definition.renderer = avibaseIdRenderer;
  if (field === 'safring_numbers') definition.renderer = safringNumbersRenderer;
  if (field === 'observations') {
    definition.renderer = numberRenderer;
    definition.className = 'number';
  }
  if (field === 'ebird_species_code') definition.renderer = linkRenderer(value => `https://ebird.org/species/${encodeURIComponent(value)}/KE`);
  return definition;
});
const columnDefinitionsByField = Object.fromEntries(columns.map((field, index) => [field, columnDefinitions[index]]));

const enrichRow = row => ({
  ...row,
  status: [
    ...statusColumns.filter(code => truthy(row[code])),
    ...(truthy(row.pending_earc) ? ['PE'] : []),
    ...(truthy(row.sensitive) ? ['S'] : []),
    ...(truthy(row.water_bird) ? ['W'] : []),
    ...(row.exotic_status !== 'native' ? [row.exotic_status] : [])
  ].join(', ')
});

const applyColumnSettings = () => {
  hot.updateSettings({
    columns: visibleColumns.map(field => columnDefinitionsByField[field]),
    colHeaders: visibleColumns.map(field => columnLabels[field])
  });
};

const renderColumnPicker = () => {
  const makeOption = field => {
    const option = document.createElement('option');
    option.value = field;
    option.textContent = columnLabels[field];
    return option;
  };
  availableColumnsSelect.replaceChildren(...columns.filter(field => !pendingVisibleColumns.includes(field)).map(makeOption));
  visibleColumnsSelect.replaceChildren(...pendingVisibleColumns.map(makeOption));
};

const selectedColumns = select => [...select.selectedOptions].map(option => option.value);

const matchesFilter = (row, filter) => {
  if (filter === 'historical') return truthy(row.HIST);
  if (filter === 'rare') return truthy(row.RAR);
  if (filter === 'waterbird') return truthy(row.water_bird);
  if (filter === 'naturalized') return row.exotic_status === 'naturalized';
  if (filter === 'pending-earc') return truthy(row.pending_earc);
  if (filter === 'sensitive') return truthy(row.sensitive);
  return true;
};

const searchableText = row => [
  row.english_name,
  row.scientific_name,
  row.order,
  row.family,
  row.family_english_name,
  row.status,
  row.avibase_id,
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
  setText('historicalCount', rows.filter(row => truthy(row.HIST)).length);
  setText('rareCount', rows.filter(row => truthy(row.RAR)).length);
  setText('waterbirdFilterCount', rows.filter(row => truthy(row.water_bird)).length);
  setText('naturalizedCount', rows.filter(row => row.exotic_status === 'naturalized').length);
  setText('pendingEarcCount', rows.filter(row => truthy(row.pending_earc)).length);
  setText('sensitiveCount', rows.filter(row => truthy(row.sensitive)).length);
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

Papa.parse('../data/checklist.csv?v=20260813-1', {
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
      colHeaders: visibleColumns.map(field => columnLabels[field]),
      columns: visibleColumns.map(field => columnDefinitionsByField[field]),
      readOnly: true,
      multiColumnSorting: true,
      filters: true,
      dropdownMenu: ['filter_by_condition', 'filter_by_value', 'filter_action_bar'],
      manualColumnResize: true,
      manualColumnFreeze: true,
      contextMenu: ['freeze_column', 'unfreeze_column', '---------', 'filter_by_value', 'filter_action_bar'],
      licenseKey: 'non-commercial-and-evaluation',
      modifyColWidth: width => Math.min(width, 300),
      afterGetColHeader: (col, th) => {
        const field = visibleColumns[col];
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

document.querySelectorAll('.filter[data-filter]').forEach(button => button.addEventListener('click', () => {
  const filter = button.dataset.filter;
  selectedFilters.has(filter) ? selectedFilters.delete(filter) : selectedFilters.add(filter);
  button.setAttribute('aria-pressed', selectedFilters.has(filter));
  renderView();
}));

clearFiltersButton.addEventListener('click', () => {
  selectedFilters.clear();
  document.querySelectorAll('.filter[data-filter]').forEach(button => button.setAttribute('aria-pressed', 'false'));
  renderView();
});

exportButton.addEventListener('click', () => {
  if (!exportPlugin) return;
  exportPlugin.downloadFile('csv', {
    columnDelimiter: ',',
    columnHeaders: true,
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

columnChooserButton.addEventListener('click', () => {
  pendingVisibleColumns = [...visibleColumns];
  renderColumnPicker();
  columnDialog.showModal();
});

document.getElementById('addColumn').addEventListener('click', () => {
  pendingVisibleColumns.push(...selectedColumns(availableColumnsSelect));
  renderColumnPicker();
});

document.getElementById('removeColumn').addEventListener('click', () => {
  const selected = selectedColumns(visibleColumnsSelect);
  if (pendingVisibleColumns.length === selected.length) return;
  pendingVisibleColumns = pendingVisibleColumns.filter(field => !selected.includes(field));
  renderColumnPicker();
});

const moveSelectedColumn = direction => {
  const [field] = selectedColumns(visibleColumnsSelect);
  const index = pendingVisibleColumns.indexOf(field);
  const target = index + direction;
  if (index < 0 || target < 0 || target >= pendingVisibleColumns.length) return;
  [pendingVisibleColumns[index], pendingVisibleColumns[target]] = [pendingVisibleColumns[target], pendingVisibleColumns[index]];
  renderColumnPicker();
  visibleColumnsSelect.value = field;
};

document.getElementById('moveColumnUp').addEventListener('click', () => moveSelectedColumn(-1));
document.getElementById('moveColumnDown').addEventListener('click', () => moveSelectedColumn(1));
document.getElementById('resetColumns').addEventListener('click', () => {
  pendingVisibleColumns = [...defaultVisibleColumns];
  renderColumnPicker();
});
document.getElementById('cancelColumns').addEventListener('click', () => columnDialog.close());
columnDialog.querySelector('.dialog-close').addEventListener('click', () => columnDialog.close());
columnDialog.addEventListener('click', event => {
  if (event.target === columnDialog) columnDialog.close();
});
document.getElementById('applyColumns').addEventListener('click', () => {
  visibleColumns = [...pendingVisibleColumns];
  localStorage.setItem('birds-of-kenya-visible-columns', JSON.stringify(visibleColumns));
  applyColumnSettings();
  columnDialog.close();
});
