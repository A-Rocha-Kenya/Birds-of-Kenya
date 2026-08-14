const siteRoot = document.body.dataset.siteRoot || '';

const resolveSitePath = path => path ? `${siteRoot}${path}` : '';

fetch(resolveSitePath('data/site.json'))
  .then(response => {
    if (!response.ok) throw new Error('Site metadata unavailable');
    return response.json();
  })
  .then(site => {
    if (site.release.status === 'draft') {
      const notice = document.createElement('aside');
      notice.className = 'draft-notice';
      notice.setAttribute('role', 'status');
      notice.textContent = 'Draft preview — this checklist is under review and is not yet a final publication.';
      document.body.prepend(notice);
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
