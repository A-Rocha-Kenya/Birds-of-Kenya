// Shared by the Tree and Explore pages: both read data/taxonomy.json and open the same species sheet.
const page = document.body.dataset.taxonomyPage;
const siteRootPath = document.body.dataset.siteRoot || '';
const loader = document.getElementById('loader');
const errorBox = document.getElementById('error');
const scientificToggle = document.getElementById('showScientific');
const toolbar = document.querySelector('.taxonomy-toolbar-wrap');

const THREATENED = new Set(['VU', 'EN', 'CR']);
const IUCN_LABELS = {
  LC: 'Least Concern', NT: 'Near Threatened', VU: 'Vulnerable', EN: 'Endangered',
  CR: 'Critically Endangered', DD: 'Data Deficient', EW: 'Extinct in the Wild', EX: 'Extinct',
};
const formatNumber = value => Number(value).toLocaleString('en-GB');
const formatDate = value => {
  if (!value) return '';
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('en-GB', {day: 'numeric', month: 'short', year: 'numeric'});
};

const store = {
  get(key) { try { return window.localStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { window.localStorage.setItem(key, value); } catch { /* storage unavailable */ } },
};

let taxonomy;
let speciesList = [];
const speciesIndex = new Map();
const showScientific = () => scientificToggle.checked;
const stickerUrl = species => taxonomy.sticker_cdn + species.sticker;
const tableLink = species => `${siteRootPath}checklist/?q=${encodeURIComponent(species.scientific_name)}`;

// Sticky elements below the toolbar follow its height, which grows when its controls wrap.
if (toolbar) {
  new ResizeObserver(() => document.documentElement.style.setProperty('--toolbar-h', `${toolbar.offsetHeight}px`)).observe(toolbar);
}

function element(tag, attributes = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attributes)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === 'text') node.textContent = value;
    else if (key === 'className') node.className = value;
    else node.setAttribute(key, value === true ? '' : value);
  }
  node.append(...children);
  return node;
}

function sticker(species, size, alt = '') {
  return element('img', {src: stickerUrl(species), alt, width: size, height: size, loading: 'lazy', decoding: 'async'});
}

/* ---------- Status flags ---------- */

const rarityLabel = id => taxonomy.rarity_classes.find(item => item.id === id)?.label || 'Not assessed';
const rarityLevel = id => {
  const index = taxonomy.rarity_classes.findIndex(item => item.id === id);
  return index < 0 ? 0 : index + 1;
};

// Status flags that can be filtered and are shown on cards. Order matters: most important first.
const FLAGS = [
  {id: 'threatened', label: 'Threatened', test: s => THREATENED.has(s.iucn),
    describe: s => `Globally ${IUCN_LABELS[s.iucn]} on the IUCN Red List.`, chip: s => s.iucn},
  {id: 'pending', label: 'Pending EARC', test: s => s.pending_earc,
    describe: () => 'Added since 2019 with no mapped East African Rarities Committee decision.'},
  {id: 'historical', label: 'Historical', test: s => s.historical,
    describe: () => 'Latest Kenyan eBird record is more than 50 years old.'},
  {id: 'naturalized', label: 'Naturalized', test: s => s.naturalized,
    describe: () => 'Established non-native species in Kenya.'},
  {id: 'waterbird', label: 'Waterbird', test: s => s.waterbird, onCard: false,
    describe: () => 'Belongs to a waterbird family (Ramsar Waterbird Population Estimates).'},
];

function rarityMeter(species, size = 'small') {
  const level = rarityLevel(species.rarity);
  const bars = Array.from({length: 5}, (_, index) => element('i', {className: index < level ? 'on' : ''}));
  return element('span', {className: `rarity rarity-${species.rarity} rarity-${size}`, title: rarityLabel(species.rarity)}, [
    element('span', {className: 'rarity-bars', 'aria-hidden': 'true'}, bars),
    element('span', {className: 'rarity-label', text: rarityLabel(species.rarity)}),
  ]);
}

function flagChips(species, {all = false} = {}) {
  return FLAGS.filter(flag => flag.test(species) && (all || flag.onCard !== false)).map(flag =>
    element('span', {className: `flag flag-${flag.id}`, title: flag.describe(species), text: flag.chip ? flag.chip(species) : flag.label}));
}

/* ---------- Species card ---------- */

const overlay = element('div', {className: 'species-overlay', hidden: true});
const card = element('article', {className: 'species-dialog', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'speciesCardTitle', tabindex: '-1'});
overlay.append(card);
document.body.append(overlay);
let sheetSpecies = null;
let lastFocus = null;
const sheetListeners = new Set();

function fact(label, value) {
  return value ? element('div', {className: 'card-fact'}, [element('dt', {text: label}), element('dd', {}, [value])]) : null;
}

function openSheet(species) {
  const {order, family} = speciesIndex.get(species.id);
  const position = speciesList.indexOf(species);
  if (overlay.hidden) lastFocus = document.activeElement;
  sheetSpecies = species;

  const close = element('button', {type: 'button', className: 'card-button card-close', 'aria-label': 'Close', text: '×'});
  const previous = element('button', {type: 'button', className: 'card-button', 'aria-label': 'Previous species', text: '←', disabled: position === 0});
  const next = element('button', {type: 'button', className: 'card-button', 'aria-label': 'Next species', text: '→', disabled: position === speciesList.length - 1});
  close.addEventListener('click', closeSheet);
  previous.addEventListener('click', () => openSheet(speciesList[position - 1]));
  next.addEventListener('click', () => openSheet(speciesList[position + 1]));

  const evidence = species.sensitive
    ? 'Evidence is not published for this sensitive species.'
    : species.rarity === 'not-assessed'
      ? 'Included from curated records; no eBird observations to assess.'
      : `${formatNumber(species.observations)} clustered eBird ${species.observations === 1 ? 'observation' : 'observations'}`;
  const range = species.first_observation && species.last_observation
    ? (species.first_observation === species.last_observation ? formatDate(species.first_observation)
      : `${formatDate(species.first_observation)} – ${formatDate(species.last_observation)}`)
    : '';
  const flags = FLAGS.filter(flag => flag.test(species));
  const iucn = species.iucn && IUCN_LABELS[species.iucn] && !THREATENED.has(species.iucn) ? `${IUCN_LABELS[species.iucn]} (${species.iucn})` : '';

  card.replaceChildren(
    element('header', {className: 'card-bar'}, [
      element('p', {className: 'card-lineage'}, [
        element('span', {text: order.english_name}), element('span', {'aria-hidden': 'true', text: ' › '}),
        element('span', {text: family.english_name}),
        element('i', {className: 'card-lineage-sci', text: ` · ${order.order} › ${family.family}`}),
      ]),
      element('div', {className: 'card-nav'}, [
        element('span', {className: 'card-position', text: `${position + 1} / ${formatNumber(speciesList.length)}`}),
        previous, next, close,
      ]),
    ]),
    element('div', {className: 'card-layout'}, [
      element('div', {className: 'card-art'}, [sticker(species, 320, `Illustration of ${species.english_name}`)]),
      element('div', {className: 'card-main'}, [
        element('h2', {id: 'speciesCardTitle', text: species.english_name}),
        element('p', {className: 'card-scientific', text: species.scientific_name}),
        element('section', {className: `card-rarity rarity-${species.rarity}`, 'aria-label': 'Rarity'}, [
          rarityMeter(species, 'large'),
          element('p', {text: evidence}),
          range ? element('p', {className: 'card-range', text: `Recorded ${range}`}) : '',
        ]),
        flags.length ? element('ul', {className: 'card-flags', 'aria-label': 'Status'}, flags.map(flag =>
          element('li', {}, [
            element('span', {className: `flag flag-${flag.id}`, text: flag.chip ? flag.chip(species) : flag.label}),
            element('span', {text: flag.describe(species)}),
          ]))) : '',
        element('dl', {className: 'card-facts'}, [
          fact('IUCN Red List', iucn),
          fact('EARC decision', species.earc_decision),
          fact('Taxonomy note', species.taxonomy_comment),
        ].filter(Boolean)),
        element('div', {className: 'card-links'}, [
          species.birds_of_the_world_url && element('a', {href: species.birds_of_the_world_url, target: '_blank', rel: 'noreferrer', text: 'Birds of the World ↗'}),
          species.birdlife_datazone_url && element('a', {href: species.birdlife_datazone_url, target: '_blank', rel: 'noreferrer', text: 'BirdLife DataZone ↗'}),
          element('a', {href: tableLink(species), text: 'View in the table →'}),
        ].filter(Boolean)),
        element('p', {className: 'card-credit', text: `Illustration: ${taxonomy.sticker_credit.name}, ${taxonomy.sticker_credit.licence}. ${taxonomy.sticker_credit.note}`}),
      ]),
    ]),
  );
  overlay.hidden = false;
  document.body.classList.add('has-species-card');
  card.scrollTop = 0;
  card.focus({preventScroll: true});
  sheetListeners.forEach(listener => listener(species));
}

function closeSheet() {
  if (overlay.hidden) return;
  overlay.hidden = true;
  document.body.classList.remove('has-species-card');
  sheetSpecies = null;
  sheetListeners.forEach(listener => listener(null));
  lastFocus?.focus?.({preventScroll: true});
}

overlay.addEventListener('click', event => { if (event.target === overlay) closeSheet(); });
document.addEventListener('keydown', event => {
  if (!sheetSpecies) return;
  if (event.key === 'Escape') closeSheet();
  if (event.target.closest?.('input, select, textarea')) return;
  const position = speciesList.indexOf(sheetSpecies);
  if (event.key === 'ArrowRight' && position < speciesList.length - 1) openSheet(speciesList[position + 1]);
  if (event.key === 'ArrowLeft' && position > 0) openSheet(speciesList[position - 1]);
});

/* ---------- Explore: search, filters and family plates ---------- */

const normalise = text => text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

function buildExplore() {
  const plates = document.getElementById('plates');
  const searchInput = document.getElementById('speciesSearch');
  const clearSearch = document.getElementById('clearSpeciesSearch');
  const clearAll = document.getElementById('clearExploreFilters');
  const countLine = document.getElementById('exploreCount');
  const empty = document.getElementById('exploreEmpty');
  const selectedRarity = new Set();
  const selectedFlags = new Set();
  const entries = [];
  const families = [];
  const orders = [];

  for (const order of taxonomy.orders) {
    const section = element('section', {className: 'order-section', id: `order-${order.order}`, 'aria-labelledby': `order-title-${order.order}`});
    const orderCount = element('span');
    section.append(element('header', {className: 'order-header'}, [
      element('h2', {id: `order-title-${order.order}`, text: order.english_name}),
      element('p', {}, [element('i', {className: 'sci', text: order.order}), orderCount]),
    ]));
    const orderEntry = {section, count: orderCount, families: []};

    for (const family of order.families) {
      const grid = element('div', {className: 'plate-grid'});
      const familyCount = element('span', {className: 'plate-count'});
      const familyEntry = {plate: null, count: familyCount, total: family.species.length, entries: []};
      for (const species of family.species) {
        const button = element('button', {type: 'button', className: 'plate-species', 'aria-haspopup': 'dialog', 'aria-label': `${species.english_name}, ${rarityLabel(species.rarity)}`}, [
          element('span', {className: 'plate-sticker'}, [sticker(species, 104, '')]),
          element('span', {className: 'plate-name', text: species.english_name}),
          element('i', {className: 'sci', text: species.scientific_name}),
          rarityMeter(species),
          element('span', {className: 'plate-flags'}, flagChips(species)),
        ]);
        button.addEventListener('click', () => openSheet(species));
        // Search matches the most specific level first: species, then family, then order names.
        const entry = {
          species, button,
          levels: [
            normalise(`${species.english_name} ${species.scientific_name}`),
            normalise(`${family.english_name} ${family.family}`),
            normalise(`${order.english_name} ${order.order}`),
          ],
        };
        entries.push(entry);
        familyEntry.entries.push(entry);
        grid.append(button);
      }
      familyEntry.plate = element('article', {className: 'family-plate', id: `family-${family.family}`, 'aria-labelledby': `family-title-${family.family}`}, [
        element('header', {className: 'plate-header'}, [
          element('h3', {id: `family-title-${family.family}`, text: family.english_name}),
          element('i', {className: 'sci', text: family.family}),
          familyCount,
        ]),
        grid,
      ]);
      section.append(familyEntry.plate);
      orderEntry.families.push(familyEntry);
      families.push(familyEntry);
    }
    orders.push(orderEntry);
    plates.append(section);
  }

  const chip = (group, id, label, count, selected) => {
    const button = element('button', {type: 'button', className: `filter filter-${group}-${id}`, 'aria-pressed': 'false'}, [
      element('span', {text: label}), element('span', {className: 'count', text: formatNumber(count)}),
    ]);
    button.addEventListener('click', () => {
      selected.has(id) ? selected.delete(id) : selected.add(id);
      button.setAttribute('aria-pressed', String(selected.has(id)));
      apply();
    });
    return button;
  };
  const rarityRow = document.getElementById('rarityFilters');
  [...taxonomy.rarity_classes].reverse().forEach(item => {
    const count = speciesList.filter(species => species.rarity === item.id).length;
    rarityRow.append(chip('rarity', item.id, item.label, count, selectedRarity));
  });
  const flagRow = document.getElementById('flagFilters');
  FLAGS.forEach(flag => flagRow.append(chip('flag', flag.id, flag.label, speciesList.filter(flag.test).length, selectedFlags)));

  const infoButton = document.getElementById('rarityInfoButton');
  const info = document.getElementById('rarityInfo');
  const range = item => (item.max === null ? `${formatNumber(item.min)} or more` : item.min === 0 ? `fewer than ${item.max + 1}` : `${formatNumber(item.min)}–${formatNumber(item.max)}`);
  info.append(
    element('p', {text: 'Rarity shows how often a species is recorded in Kenya, from the clustered eBird observations used for this checklist release: reports within three months and 3 km of each other count once. It is not a population estimate or a conservation assessment, and well-watched areas and conspicuous birds are recorded more often.'}),
    element('ul', {}, taxonomy.rarity_classes.map(item => element('li', {}, [
      rarityMeter({rarity: item.id}), element('span', {text: `${range(item)} observations`}),
    ]))),
    element('p', {text: '“Very rare” matches the checklist’s Rare (RAR) category. Sensitive species and species included only from curated records are not assessed.'}),
  );
  infoButton.addEventListener('click', () => {
    info.hidden = !info.hidden;
    infoButton.setAttribute('aria-expanded', String(!info.hidden));
  });

  function apply() {
    const query = normalise(searchInput.value.trim());
    const terms = query.split(/\s+/).filter(Boolean);
    let shown = 0;
    const matchesAt = (entry, level) => terms.every(term => entry.levels[level].includes(term));
    const level = terms.length ? [0, 1, 2].find(index => entries.some(entry => matchesAt(entry, index))) : null;
    for (const entry of entries) {
      const visible = (level === null || (level !== undefined && matchesAt(entry, level)))
        && (!selectedRarity.size || selectedRarity.has(entry.species.rarity))
        && (!selectedFlags.size || FLAGS.some(flag => selectedFlags.has(flag.id) && flag.test(entry.species)));
      entry.button.hidden = !visible;
      entry.visible = visible;
      if (visible) shown += 1;
    }
    const filtered = Boolean(terms.length || selectedRarity.size || selectedFlags.size);
    for (const family of families) {
      const visible = family.entries.filter(entry => entry.visible).length;
      family.plate.hidden = visible === 0;
      family.count.textContent = filtered ? `${visible} of ${family.total} species` : `${family.total} species`;
    }
    for (const order of orders) {
      const familyCount = order.families.filter(family => !family.plate.hidden).length;
      const visible = order.families.reduce((sum, family) => sum + family.entries.filter(entry => entry.visible).length, 0);
      order.section.hidden = visible === 0;
      order.count.textContent = `${familyCount} ${familyCount === 1 ? 'family' : 'families'} · ${formatNumber(visible)} species`;
    }
    countLine.innerHTML = filtered
      ? `<b>${formatNumber(shown)}</b> of ${formatNumber(entries.length)} species`
      : `<b>${formatNumber(entries.length)}</b> species`;
    empty.hidden = shown > 0;
    clearSearch.hidden = !terms.length;
    clearAll.hidden = !filtered;
    const url = new URL(window.location.href);
    if (searchInput.value.trim()) url.searchParams.set('q', searchInput.value.trim()); else url.searchParams.delete('q');
    history.replaceState(null, '', url);
  }

  searchInput.value = new URLSearchParams(window.location.search).get('q') || '';
  searchInput.addEventListener('input', apply);
  searchInput.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      const first = entries.find(entry => entry.visible);
      if (first) openSheet(first.species);
    }
  });
  clearSearch.addEventListener('click', () => { searchInput.value = ''; searchInput.focus(); apply(); });
  clearAll.addEventListener('click', () => {
    searchInput.value = '';
    selectedRarity.clear();
    selectedFlags.clear();
    document.querySelectorAll('.explore-filters .filter').forEach(button => button.setAttribute('aria-pressed', 'false'));
    apply();
  });
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !sheetSpecies && !event.target.closest?.('input, select, textarea')) {
      event.preventDefault();
      searchInput.focus();
    }
  });
  sheetListeners.add(species => {
    entries.forEach(entry => entry.button.classList.toggle('is-active', entry.species === species));
  });
  apply();
}

/* ---------- Tree: dated, foldable evolutionary tree ---------- */

const ORDER_PALETTE = ['#1f6848', '#b5752a', '#3f7fa6', '#8c5a9e', '#6f8f2f', '#c0563f', '#2f8f87', '#a68a2a', '#5a6fb5', '#9e4f6f'];

function buildTree(phylogeny) {
  const host = document.getElementById('timeTree');
  const axis = document.getElementById('timeAxis');
  const searchInput = document.getElementById('treeSearch');
  const foldButtons = document.querySelectorAll('[data-fold]');
  const orderColor = new Map(taxonomy.orders.map((order, index) => [order.order, ORDER_PALETTE[index % ORDER_PALETTE.length]]));
  const familiesPerOrder = new Map(taxonomy.orders.map(order => [order.order, order.families.length]));
  const orderInfo = new Map(taxonomy.orders.map(order => [order.order, order]));
  const familyInfo = new Map(taxonomy.orders.flatMap(order => order.families.map(family => [family.family, family])));

  const toNode = ([length, content]) => (Array.isArray(content) ? {length, children: content.map(toNode)} : {length, id: content});
  const root = d3.hierarchy(toNode(phylogeny.tree));
  root.each(node => {
    node.dist = node.parent ? node.parent.dist + node.data.length : 0;
    if (node.data.id) node.entry = speciesIndex.get(node.data.id);
  });
  const rootAge = d3.max(root.leaves(), leaf => leaf.dist);
  root.eachAfter(node => {
    node.age = Math.max(0, rootAge - node.dist);
    const leaves = node.leaves();
    node.count = leaves.length;
    node.orders = new Set(leaves.map(leaf => leaf.entry.order.order));
    node.families = new Set(leaves.map(leaf => leaf.entry.family.family));
  });
  const leafById = new Map(root.leaves().map(leaf => [leaf.data.id, leaf]));
  const only = set => (set.size === 1 ? set.values().next().value : null);

  const openOrders = new Set();
  const openFamilies = new Set();
  let highlighted = null;

  // Which rows are visible: a folded order, a folded family, or a species.
  function visible(node) {
    if (!node.children) return {node, kind: 'species'};
    const order = only(node.orders);
    const family = only(node.families);
    if (order && !openOrders.has(order) && node.count > 1) return {node, kind: 'order', key: order};
    if (family && !openFamilies.has(family) && node.count > 1) return {node, kind: 'family', key: family};
    return {node, kind: 'clade', children: node.children.map(visible)};
  }

  function rowContent(row) {
    const node = row.node;
    if (row.kind === 'species') {
      const species = node.entry.species;
      const button = element('button', {type: 'button', className: 'tt-species', 'aria-haspopup': 'dialog', 'aria-label': `${species.english_name}, ${rarityLabel(species.rarity)}, open species card`}, [
        sticker(species, 44, ''),
        element('span', {className: 'tt-text'}, [
          element('span', {className: 'tt-name', text: species.english_name}),
          element('i', {className: 'sci tt-meta', text: species.scientific_name}),
        ]),
        element('span', {className: 'tt-status'}, [rarityMeter(species), ...flagChips(species)]),
      ]);
      button.addEventListener('click', () => openSheet(species));
      return button;
    }
    const info = row.kind === 'order' ? orderInfo.get(row.key) : familyInfo.get(row.key);
    const leaves = node.leaves();
    const preview = [speciesIndex.get(info.representative).species, ...leaves.map(leaf => leaf.entry.species)]
      .filter((species, index, list) => list.indexOf(species) === index).slice(0, 3);
    const label = row.kind === 'order' ? 'order' : 'family';
    const button = element('button', {type: 'button', className: `tt-group tt-${row.kind}`, 'aria-expanded': 'false', 'aria-label': `Open ${info.english_name}, ${node.count} species`}, [
      element('span', {className: 'tt-chevron', 'aria-hidden': 'true', text: '▸'}),
      element('span', {className: 'tt-preview', 'aria-hidden': 'true'}, preview.map(species => sticker(species, 40, ''))),
      element('span', {className: 'tt-text'}, [
        element('span', {className: 'tt-name', text: info.english_name}),
        element('span', {className: 'tt-meta'}, [
          element('i', {className: 'sci', text: row.key}),
          element('span', {text: `${node.count} species${node.count < info.species?.length ? ` of ${info.species.length}` : ''} · ${label}`}),
        ]),
      ]),
    ]);
    button.addEventListener('click', event => {
      if (row.kind === 'order') {
        openOrders.add(row.key);
        const order = orderInfo.get(row.key);
        if (order.families.length === 1 || event.shiftKey) order.families.forEach(family => openFamilies.add(family.family));
      } else {
        openFamilies.add(row.key);
      }
      render({keep: button});
    });
    if (row.kind === 'order') {
      const all = element('button', {type: 'button', className: 'tt-open-all', text: 'All species', 'aria-label': `Open every species in ${info.english_name}`});
      all.addEventListener('click', () => {
        openOrders.add(row.key);
        orderInfo.get(row.key).families.forEach(family => openFamilies.add(family.family));
        render({keep: all});
      });
      return element('div', {className: 'tt-group-wrap'}, [button, all]);
    }
    return button;
  }

  function render({keep = null, reveal = null} = {}) {
    // Keep the clicked row in place on screen while rows above it open or close.
    const anchor = keep?.closest('.tt-row');
    const anchorKey = anchor?.dataset.key;
    const anchorTop = anchor ? anchor.getBoundingClientRect().top : 0;

    const tree = d3.hierarchy(visible(root), item => item.children);
    const rows = tree.leaves();
    const width = host.clientWidth || 1000;
    // On phones the names need the room: the tree keeps about a quarter of the width.
    const narrow = width < 600;
    const gutter = narrow ? 34 : 40;
    const treeWidth = narrow ? Math.max(72, Math.round(width * 0.24)) : Math.max(90, width - Math.min(600, Math.max(235, width * 0.52)) - gutter);
    const x = d3.scaleLinear().domain([rootAge, 0]).range([10, treeWidth - 4]);
    const heightOf = row => (row.data.kind === 'species' ? 58 : 54);
    let y = 8;
    rows.forEach(row => { row.top = y; row.y = y + heightOf(row) / 2; y += heightOf(row); });
    tree.eachAfter(item => { if (item.children) item.y = (item.children[0].y + item.children[item.children.length - 1].y) / 2; });
    const height = y + 8;
    const ageOf = item => item.data.node.age;
    const keyOf = item => (item.data.kind === 'species' ? item.data.node.data.id : `${item.data.kind}:${item.data.key}:${item.data.node.count}:${item.data.node.age}`);

    host.style.height = `${height}px`;
    host.style.setProperty('--tree-width', `${treeWidth}px`);
    host.style.setProperty('--gutter', `${gutter}px`);

    // Branches.
    const links = tree.links().map(link => `M${x(ageOf(link.source))},${link.source.y}V${link.target.y}H${x(ageOf(link.target))}`).join('');
    const tails = rows.map(row => `M${x(ageOf(row))},${row.y}H${x(0)}`).join('');
    const wedges = rows.filter(row => row.data.kind !== 'species').map(row => {
      const spread = Math.min(15, 5 + Math.sqrt(row.data.node.count) * 1.4);
      return `<path class="tt-wedge" d="M${x(ageOf(row))},${row.y}L${x(0)},${row.y - spread}V${row.y + spread}Z" fill="${orderColor.get(only(row.data.node.orders))}"/>`;
    }).join('');
    const splits = tree.descendants().filter(item => item.children).map(item =>
      `<circle class="tt-split-node" cx="${x(ageOf(item))}" cy="${item.y}" r="3.2"><title>Split ${ageOf(item).toFixed(1)} million years ago</title></circle>`).join('');
    const ticks = x.ticks(Math.max(3, Math.floor(treeWidth / 90)));
    const grid = ticks.map(tick => `<line class="tt-grid" x1="${x(tick)}" x2="${x(tick)}" y1="0" y2="${height}"/>`).join('');
    let svg = host.querySelector('svg.tt-branches');
    if (!svg) {
      svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.classList.add('tt-branches');
      svg.setAttribute('aria-hidden', 'true');
      host.append(svg);
    }
    svg.setAttribute('width', treeWidth);
    svg.setAttribute('height', height);
    svg.innerHTML = `${grid}${wedges}<path class="tt-link" d="${links}"/><path class="tt-tail" d="${tails}"/>${splits}`;

    axis.innerHTML = `<div class="tt-axis-track" style="width:${treeWidth}px">${ticks.map(tick =>
      `<span style="left:${x(tick)}px">${tick === 0 ? 'Today' : tick}</span>`).join('')}</div><span class="tt-axis-unit">million years ago</span>`;

    // Rows: reuse elements so focus and images survive re-rendering.
    const existing = new Map([...host.querySelectorAll('.tt-row')].map(element => [element.dataset.key, element]));
    const next = new Set();
    for (const row of rows) {
      const key = keyOf(row);
      next.add(key);
      let item = existing.get(key);
      if (!item) {
        item = element('div', {className: `tt-row tt-row-${row.data.kind}`, 'data-key': key}, [rowContent(row.data)]);
        if (row.data.kind === 'species') item.dataset.species = row.data.node.data.id;
        host.append(item);
      }
      item.style.top = `${row.top}px`;
      item.style.height = `${heightOf(row)}px`;
    }
    existing.forEach((element, key) => { if (!next.has(key)) element.remove(); });

    // Brackets for open orders and families, each with a fold button.
    host.querySelectorAll('.tt-bracket').forEach(element => element.remove());
    const runs = (keyFn, include) => {
      const result = [];
      rows.forEach(row => {
        const key = keyFn(row);
        if (!key || !include(row, key)) return;
        const last = result[result.length - 1];
        if (last && last.key === key && last.end === rows.indexOf(row) - 1) { last.end += 1; last.bottom = row.top + heightOf(row); }
        else result.push({key, start: rows.indexOf(row), end: rows.indexOf(row), top: row.top, bottom: row.top + heightOf(row)});
      });
      return result;
    };
    const rowOrder = row => only(row.data.node.orders);
    const rowFamily = row => only(row.data.node.families);
    const brackets = [
      ...runs(rowOrder, (row, order) => openOrders.has(order) && orderInfo.get(order).families.reduce((sum, family) => sum + family.species.length, 0) > 1)
        .map(run => ({...run, level: 'order', info: orderInfo.get(run.key)})),
      ...runs(rowFamily, (row, family) => row.data.kind === 'species' && openFamilies.has(family) && familiesPerOrder.get(rowOrder(row)) > 1 && familyInfo.get(family).species.length > 1)
        .map(run => ({...run, level: 'family', info: familyInfo.get(run.key)})),
    ];
    for (const bracket of brackets) {
      const order = bracket.level === 'order' ? bracket.key : [...familyInfo.keys()].includes(bracket.key) && taxonomy.orders.find(o => o.families.some(f => f.family === bracket.key)).order;
      const fold = element('button', {type: 'button', className: 'tt-fold', 'aria-label': `Fold ${bracket.info.english_name}`, title: `Fold ${bracket.info.english_name}`, text: '−'});
      fold.addEventListener('click', () => {
        if (bracket.level === 'order') {
          openOrders.delete(bracket.key);
          orderInfo.get(bracket.key).families.forEach(family => openFamilies.delete(family.family));
        } else {
          openFamilies.delete(bracket.key);
        }
        render({keep: fold});
      });
      const tall = bracket.bottom - bracket.top > 110;
      host.append(element('div', {
        className: `tt-bracket tt-bracket-${bracket.level}`,
        style: `top:${bracket.top + 4}px;height:${bracket.bottom - bracket.top - 8}px;--clade:${orderColor.get(order)}`,
        title: bracket.info.english_name,
      }, [fold, tall ? element('span', {className: 'tt-bracket-label', text: bracket.info.english_name}) : '']));
    }

    // Toolbar state.
    const allOrders = taxonomy.orders.length;
    foldButtons.forEach(button => {
      const state = button.dataset.fold;
      const active = state === 'orders' ? openOrders.size === 0
        : state === 'families' ? openOrders.size === allOrders && openFamilies.size === 0
          : openOrders.size === allOrders && openFamilies.size === familyInfo.size;
      button.setAttribute('aria-pressed', String(active));
    });
    host.querySelectorAll('.tt-row-species').forEach(item => item.classList.toggle('is-highlighted', item.dataset.species === highlighted));

    const hash = [openOrders.size && `o=${[...openOrders].join(',')}`, openFamilies.size && `f=${[...openFamilies].join(',')}`].filter(Boolean).join('&');
    history.replaceState(null, '', hash ? `#${hash}` : window.location.pathname + window.location.search);

    if (anchorKey) {
      const moved = host.querySelector(`.tt-row[data-key="${CSS.escape(anchorKey)}"]`) || keep?.closest('.tt-bracket');
      if (moved) window.scrollBy(0, moved.getBoundingClientRect().top - anchorTop);
    }
    if (reveal) {
      const target = host.querySelector(`.tt-row[data-species="${reveal}"]`);
      target?.scrollIntoView({block: 'center', behavior: 'smooth'});
    }
  }

  function revealSpecies(id) {
    const {order, family} = speciesIndex.get(id);
    openOrders.add(order.order);
    openFamilies.add(family.family);
    highlighted = id;
    render({reveal: id});
  }

  foldButtons.forEach(button => button.addEventListener('click', () => {
    openOrders.clear();
    openFamilies.clear();
    if (button.dataset.fold !== 'orders') taxonomy.orders.forEach(order => openOrders.add(order.order));
    if (button.dataset.fold === 'species') familyInfo.forEach((family, key) => openFamilies.add(key));
    render();
  }));

  const datalist = document.getElementById('treeSpecies');
  const byName = new Map();
  speciesList.forEach(species => {
    byName.set(normalise(species.english_name), species.id);
    byName.set(normalise(species.scientific_name), species.id);
    datalist.append(element('option', {value: species.english_name}));
  });
  const find = () => {
    const id = byName.get(normalise(searchInput.value.trim()));
    if (id) revealSpecies(id);
  };
  searchInput.addEventListener('change', find);
  searchInput.addEventListener('keydown', event => { if (event.key === 'Enter') find(); });

  // Opening a species card highlights it here, and stepping through the card follows along in the tree.
  sheetListeners.add(species => {
    if (!species) return;
    if (!host.querySelector(`.tt-row[data-species="${species.id}"]`)) revealSpecies(species.id);
    else { highlighted = species.id; render(); }
  });

  const source = document.getElementById('treeSource');
  source.replaceChildren(
    `Tree: clootl, Aves tree v${phylogeny.tree_version} (eBird taxonomy ${phylogeny.taxonomy_year}), pruned to the ${formatNumber(phylogeny.species)} species on this checklist and built from `,
    element('a', {href: `${siteRootPath}data/phylogeny-citations.csv`, text: `${phylogeny.studies} published studies`}),
    `. ${phylogeny.citations.join(' ')}`,
  );

  const params = new URLSearchParams(window.location.hash.slice(1));
  (params.get('o') || '').split(',').filter(order => orderInfo.has(order)).forEach(order => {
    openOrders.add(order);
    const families = orderInfo.get(order).families;
    if (families.length === 1) openFamilies.add(families[0].family);
  });
  (params.get('f') || '').split(',').filter(family => familyInfo.has(family)).forEach(family => openFamilies.add(family));
  render();
  let lastWidth = host.clientWidth;
  new ResizeObserver(() => {
    if (host.clientWidth === lastWidth) return;
    lastWidth = host.clientWidth;
    host.querySelectorAll('.tt-row').forEach(item => item.remove());
    render();
  }).observe(host);
  return {refresh: () => {}};
}

/* ---------- Start ---------- */

let tree;
fetch(`${siteRootPath}data/taxonomy.json`, {cache: 'no-cache'})
  .then(response => {
    if (!response.ok) throw new Error('Taxonomy unavailable');
    return response.json();
  })
  .then(data => {
    taxonomy = data;
    for (const order of data.orders) {
      for (const family of order.families) {
        for (const species of family.species) {
          speciesList.push(species);
          speciesIndex.set(species.id, {order, family, species});
        }
      }
    }
    const credit = data.sticker_credit;
    document.getElementById('illustrationCredit')?.replaceChildren(
      'Illustrations: ',
      element('a', {href: credit.url, target: '_blank', rel: 'noreferrer', text: credit.name}),
      ', ',
      element('a', {href: credit.licence_url, target: '_blank', rel: 'noreferrer', text: credit.licence}),
      `. ${credit.note}`,
    );
    scientificToggle.checked = store.get('taxonomy-scientific') === 'true';
    document.body.classList.toggle('show-scientific', scientificToggle.checked);
    loader.hidden = true;
    document.getElementById(page === 'tree' ? 'treeView' : 'exploreView').hidden = false;
    if (page === 'tree') {
      return fetch(`${siteRootPath}data/phylogeny.json`, {cache: 'no-cache'})
        .then(response => { if (!response.ok) throw new Error('Phylogeny unavailable'); return response.json(); })
        .then(phylogeny => { tree = buildTree(phylogeny); });
    }
    buildExplore();
  })
  .catch(error => {
    console.error(error);
    loader.hidden = true;
    errorBox.textContent = 'The taxonomy could not be loaded. Check your connection and reload the page.';
    errorBox.hidden = false;
  });

scientificToggle.addEventListener('change', () => {
  document.body.classList.toggle('show-scientific', scientificToggle.checked);
  store.set('taxonomy-scientific', String(scientificToggle.checked));
  tree?.refresh();
});
