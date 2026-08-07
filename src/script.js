const tableElement = document.getElementById('table');
const loader = document.getElementById('loader');
const errorElement = document.getElementById('error');
const exportButton = document.getElementById('exportFile');
let hot;
let exportPlugin;

const headerDescriptions = {
  sort: 'Sorting key according to the 2019 checklist',
  family_scientific: 'Scientific family name',
  family_english: 'Family in common name',
  common_name: 'Common name',
  scientific_name: 'Scientific name',
  red_list: 'IUCN Red List category',
  status_birdlife: 'BirdLife designation',
  water_bird: 'Waterbird classification',
  strict_water_bird: 'Strict waterbird classification',
  ADU: 'Animal Demographic Unit / Kenya Bird Map Atlas identifier',
  avibaseid: 'Avibase identifier',
  wikiDataID: 'Wikidata identifier',
  iNaturalisttaxonID: 'iNaturalist taxon identifier',
  ITIS: 'Integrated Taxonomic Information System identifier',
  IUCNtaxonID: 'IUCN identifier',
  ObservationorgID: 'Observation.org identifier',
  GBIFID: 'GBIF identifier',
  'Clements--code': 'eBird/Clements species code',
  'HBW&BL--SISRecID': 'BirdLife species factsheet identifier',
  entry_checklist_of_kenya: 'Original name in the 2019 checklist',
  note_2009: 'Notes associated with the 2009 checklist',
  note_2019: 'Notes associated with the 2019 checklist'
};

const statusColumns = ['AM', 'AMR', 'E', 'EX', 'HIST', 'IO', 'MM', 'N', 'NR', 'NRR', 'OM', 'PM', 'PMR', 'RAR', 'RS', 'SO', 'VIO', 'VM', 'VN', 'VO', 'VP', 'VSO', 'VSA'];
const hiddenColumns = ['water_bird', 'strict_water_bird', 'status_birdlife', 'family_scientific', 'family_english'];

const linkRenderer = urlFor => function(instance, td, row, col, prop, value, cellProperties) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  if (!value) return;
  const link = document.createElement('a');
  link.href = urlFor(value);
  link.target = '_blank';
  link.rel = 'noreferrer';
  link.textContent = value;
  link.title = 'Open external record';
  td.textContent = '';
  td.appendChild(link);
};

const redListRenderer = function(instance, td, row, col, prop, value, cellProperties) {
  Handsontable.renderers.TextRenderer.apply(this, arguments);
  if (!value) return;
  td.textContent = value.match(/\b(\w)/g)?.join('') || value;
  td.title = value;
};

const setSummary = rows => {
  const count = (id, value) => { document.getElementById(id).textContent = value.toLocaleString(); };
  count('recordCount', rows.length);
  count('familyCount', new Set(rows.map(row => row.family_scientific).filter(Boolean)).size);
  count('threatenedCount', rows.filter(row => ['Vulnerable', 'Endangered', 'Critically Endangered'].includes(row.red_list)).length);
  count('waterbirdCount', rows.filter(row => row.water_bird === 'TRUE').length);
  count('endemicCount', rows.filter(row => row.E === 'TRUE' || row.status_birdlife === 'Endemic').length);
};

const showError = message => {
  loader.hidden = true;
  errorElement.hidden = false;
  errorElement.textContent = message;
};

const dataUrl = window.location.pathname.includes('/src/') ? '../data/main.csv' : 'data/main.csv';
Papa.parse(dataUrl, {
  encoding: 'UTF-8',
  download: true,
  header: true,
  skipEmptyLines: true,
  complete: results => {
    if (results.errors.length) {
      showError('The checklist could not be read. Please check the CSV file and reload the page.');
      return;
    }
    const rows = results.data;
    setSummary(rows);
    const columns = results.meta.fields.filter(field => !statusColumns.includes(field));
    const statusIndex = columns.indexOf('sort') + 1;
    columns.splice(statusIndex, 0, 'status');
    const tableRows = rows.map(row => {
      const output = { ...row, status: statusColumns.filter(code => row[code]).join(', ') };
      statusColumns.forEach(code => delete output[code]);
      return output;
    });
    const columnDefinitions = columns.map(field => ({
      data: field,
      renderer: field === 'red_list' ? redListRenderer : 'text'
    }));
    const linkFields = {
      avibaseid: value => `https://avibase.bsc-eoc.org/species.jsp?avibaseid=${encodeURIComponent(value)}`,
      'HBW&BL--SISRecID': value => `https://datazone.birdlife.org/species/factsheet/${encodeURIComponent(value)}`,
      'Clements--code': value => `https://ebird.org/species/${encodeURIComponent(value)}/KE`,
      GBIFID: value => `https://www.gbif.org/species/${encodeURIComponent(value)}`,
      iNaturalisttaxonID: value => `https://www.inaturalist.org/observations?place_id=7042&taxon_id=${encodeURIComponent(value)}`,
      ITIS: value => `https://www.itis.gov/servlet/SingleRpt/SingleRpt?search_topic=TSN&search_value=${encodeURIComponent(value)}`,
      IUCNtaxonID: value => `https://apiv3.iucnredlist.org/api/v3/taxonredirect/${encodeURIComponent(value)}`,
      wikiDataID: value => `https://www.wikidata.org/wiki/${encodeURIComponent(value)}`,
      ADU: value => `https://kenyabirdmap.adu.org.za/species_info.php?spp=${encodeURIComponent(value)}`,
      ObservationorgID: value => `https://observation.org/species/${encodeURIComponent(value)}`
    };
    columnDefinitions.forEach(definition => {
      if (linkFields[definition.data]) definition.renderer = linkRenderer(linkFields[definition.data]);
    });
    hot = new Handsontable(tableElement, {
      data: tableRows,
      colHeaders: columns,
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
      modifyColWidth: width => Math.min(width, 320),
      afterGetColHeader: (col, th) => {
        const field = columns[col];
        const label = th.querySelector('.colHeader');
        if (label && headerDescriptions[field]) {
          label.title = headerDescriptions[field];
          label.setAttribute('aria-label', `${field}: ${headerDescriptions[field]}`);
        }
      }
    });
    exportPlugin = hot.getPlugin('exportFile');
    exportButton.disabled = false;
    loader.hidden = true;
  },
  error: () => showError('The checklist could not be loaded. Check your connection and reload the page.')
});

exportButton.addEventListener('click', () => {
  if (!exportPlugin) return;
  exportPlugin.downloadFile('csv', {
    columnDelimiter: ',',
    exportHiddenColumns: false,
    exportHiddenRows: false,
    fileExtension: 'csv',
    filename: 'Birds_of_Kenya_2019',
    mimeType: 'text/csv',
    rowDelimiter: '\r\n'
  });
});
