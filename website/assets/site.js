const siteRoot = document.body.dataset.siteRoot || '';

const resolveSitePath = path => path ? `${siteRoot}${path}` : '';

fetch(resolveSitePath('data/site.json'), {cache: 'no-cache'})
  .then(response => {
    if (!response.ok) throw new Error('Site metadata unavailable');
    return response.json();
  })
  .then(site => {
    if (site.release.status === 'draft') {
      const notice = document.createElement('aside');
      notice.className = 'draft-notice';
      notice.setAttribute('role', 'status');
      notice.textContent = `Draft preview — ${site.sources.avilist} and ${site.sources.ebird_taxonomy}, using EBD ${site.sources.ebd} with documented taxonomic reconciliation. Evidence counts and dates are provisional pending an updated EBD. This preview may change before release.`;
      document.body.prepend(notice);
      document.querySelector('.citation-panel')?.setAttribute('hidden', '');
    }

    document.querySelectorAll('[data-site]').forEach(element => {
      const value = element.dataset.site.split('.').reduce((current, key) => current?.[key], site);
      if (value !== undefined && value !== '') element.textContent = value;
    });

    document.querySelectorAll('[data-download]').forEach(link => {
      const path = site.downloads[link.dataset.download];
      if (path) {
        link.href = resolveSitePath(path);
      } else {
        link.hidden = true;
      }
    });

    document.querySelectorAll('[data-gbif-link]').forEach(link => {
      const url = site.gbif[link.dataset.gbifLink];
      if (url) {
        link.href = url;
        link.hidden = false;
      }
    });

    document.querySelectorAll('[data-gbif-pending]').forEach(element => {
      element.hidden = Boolean(site.gbif.dataset_url || site.gbif.doi_url);
    });

    document.querySelectorAll('[data-contributors]').forEach(list => {
      list.replaceChildren();
      site.contributors.forEach(contributor => {
        const item = document.createElement('li');
        const details = [`Role: ${contributor.roles.join(', ')}`];
        if (contributor.affiliations.length) details.push(`Affiliation: ${contributor.affiliations.join('; ')}`);
        item.dataset.tooltip = details.join('\n');
        const name = document.createElement('span');
        name.textContent = contributor.name;
        item.append(name);

        if (contributor.orcid) {
          const link = document.createElement('a');
          link.className = 'orcid-link';
          link.href = contributor.orcid;
          link.target = '_blank';
          link.rel = 'noreferrer';
          link.setAttribute('aria-label', `Open ${contributor.name}'s ORCID record`);
          const icon = document.createElement('img');
          icon.src = `${siteRoot}assets/images/orcid-id.svg`;
          icon.alt = 'ORCID iD';
          link.append(icon);
          item.append(link);
        }

        list.append(item);
      });
    });
  })
  .catch(() => {
    document.querySelectorAll('[data-site-status]').forEach(element => {
      element.textContent = 'Release metadata could not be loaded.';
    });
  });

const pdfArchive = document.querySelector('[data-release-downloads]');
if (pdfArchive) {
  fetch(resolveSitePath('data/releases.json'), {cache: 'no-cache'}).then(response => {
    if (!response.ok) throw new Error('Archive unavailable');
    return response.json();
  }).then(archive => {
    const latest = new Set(Object.values(archive.latest_by_year));
    const previous = archive.releases.filter(release =>
      latest.has(release.id) && release.status === 'released' && release.id !== archive.active_release && release.pdf);
    for (const release of previous.reverse()) {
      const item = document.createElement('li');
      const details = document.createElement('div');
      const version = document.createElement('strong');
      const description = document.createElement('small');
      version.textContent = release.id.slice(1, 5);
      description.textContent = release.pdf_label.replace(/; CSV includes v\d{4}\.\d+ corrections| and revised digital IDs/g, "");
      details.append(version, description);
      const link = document.createElement('a');
      link.href = resolveSitePath(release.pdf);
      link.download = '';
      link.textContent = 'PDF ↓';
      link.setAttribute('aria-label', `Download ${version.textContent} checklist PDF`);
      item.append(details, link);
      pdfArchive.append(item);
    }
  }).catch(() => {
    const item = document.createElement('li');
    item.textContent = 'Previous checklist PDFs could not be loaded.';
    pdfArchive.append(item);
  });
}
