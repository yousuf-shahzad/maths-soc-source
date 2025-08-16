CSS Guide
=========

Overview
--------

The project uses modular CSS under ``app/static/css``. The main aggregator is ``main.css`` which only imports other files.

Structure
---------

- ``base/``: Foundation and reusable components (``base.css``, ``forms.css``, ``button.css``, ``nav.css``, ``footer.css``, ``pagination.css``, ``section.css``, ``stats.css``, ``cookies.css``, ``alerts.css``, ``mobile.css``)
- ``admin/``: Admin-specific pages (``users.css``, ``challenges.css``, ``dashboard.css``, ``actions.css``)
- ``page/``: Page-level styles (``leaderboard.css``, ``challenge.css``, ``about.css``)
- ``profile/``: Profile page styles
- ``summer/``: Summer competition-specific styles (``nav.css``, ``about.css``)
- ``article-newsletter/``: Articles and PDF presentation (``shared.css``, ``pdf.css``)

Guidelines
----------

- Do not use inline CSS in templates; reuse existing classes or add to a relevant CSS file.
- Prefer updates in ``base/`` for shared components; add page/feature overrides in the closest specific file.
- Keep ``main.css`` free of rules—use it only for ``@import`` statements.
- Check ``app/static/css/order.txt`` for the intended cascade order.

Adding Styles
-------------

1. Identify where the rule belongs (base component vs. page/admin-specific).
2. Add to the existing file when possible; create a new file only if necessary.
3. Ensure the file is imported via ``main.css`` (or linked in the template if it is page-specific and not globally loaded).
4. Verify mobile responsiveness; add media queries to ``base/mobile.css`` for app-wide patterns.
