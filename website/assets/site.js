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
  })
  .catch(() => {
    document.querySelectorAll('[data-site-status]').forEach(element => {
      element.textContent = 'Release metadata could not be loaded.';
    });
  });
