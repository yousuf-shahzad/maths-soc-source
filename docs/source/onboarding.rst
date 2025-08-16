New Developer Onboarding
========================

Goal
----

Get productive in under an hour.

Checklist
---------

1. Read :doc:`installation` and run the app locally
2. Skim :doc:`development` (architecture, blueprints, CSS scheme)
3. Explore code: ``app/admin``, ``app/auth``, ``app/main``, ``app/profile``
4. Run tests: ``pytest``
5. Pick a small task (UI tweak or a simple route) and submit a PR

Local Setup Quick Commands (Windows)
------------------------------------

.. code-block:: powershell

   git clone https://github.com/yousuf-shahzad/maths-soc-source.git
   cd maths-soc-source
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   # Create .env (see installation)
   set FLASK_APP=run:app
   flask db upgrade
   python run.py

Conventions
-----------

- Blueprints: keep routes, forms, and templates organized per module
- CSS: no inline styles; reuse ``base`` classes; import via ``main.css``
- Commit messages: short and descriptive (imperative mood)
- PRs: include a brief description, screenshots for UI

Where to Add Things
-------------------

- New admin page: ``app/admin/routes.py``, template under ``app/templates/admin/``
- New form: ``<blueprint>/forms.py`` with WTForms
- New model: ``app/models.py`` (add migration)
- New CSS for a page: ``app/static/css/page/`` (or appropriate section)

Common Gotchas
--------------

- Forgot to activate venv → packages not found
- Migrations out of date → run ``flask db upgrade``
- SECRET_KEY missing in production → set in ``.env`` or environment
