# Maths Society Web Platform

## Overview

An interactive Flask web application for Upton Court Grammar School’s Maths Society. Students can attempt challenges (including Summer Competition challenges), track progress on leaderboards, and read articles/newsletters. Admins manage users, content, and competitions through a dedicated admin area.

Tech highlights: Flask, SQLAlchemy, Flask-Login, WTForms, Flask-Migrate (Alembic), CKEditor, Jinja2, PyTest, and Sphinx docs.

## Features

- Authentication and profiles (students and admins)
- Challenges with answer boxes (MathLive input) and scheduled release times
- Summer Competition mode with timed/locked challenges
- Leaderboards and stats
- Articles/Newsletters with file uploads (PDF-friendly)
- Admin panel: manage users, challenges, articles

## Quick Start (Windows)

Prerequisites: Python 3.8+ and pip

1. Clone and enter the project

```bash
git clone https://github.com/yousuf-shahzad/maths-soc-source.git
cd maths-soc-source
```

1. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

1. Install dependencies

```bash
pip install -r requirements.txt
```

1. Configure environment (create a .env file)

```env
# If DATABASE_URL is set, it overrides the settings below
SECRET_KEY=change_me

# Database (defaults to PostgreSQL if not provided)
DATABASE_TYPE=postgresql   # or sqlite
DB_USERNAME=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_NAME=mathsoc

# Environment flags (any of these can mark production)
FLASK_ENV=development      # development|testing|production
APP_ENVIRONMENT=development
ENV=dev

# Logging
LOG_TO_STDOUT=false
```

1. Initialize the database

Option A: Use Flask-Migrate (recommended)

```cmd
set FLASK_APP=run:app
flask db upgrade
```

Option B: Seed defaults via helper script (dev only)

```bash
python init_db.py
```

This creates tables and a default admin user (non‑production) with password “admin123” — change it immediately.

1. Run the app

```bash
python run.py
```

## Configuration

Configuration lives in `config.py` and supports:

- SECRET_KEY (required in production)
- DATABASE_URL (takes precedence if set)
- DATABASE_TYPE (postgresql|sqlite) + DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME
- FLASK_ENV / APP_ENVIRONMENT / ENV (any can indicate production)
- LOG_TO_STDOUT (true|false)

The app uses an application factory (`create_app`) and initializes: SQLAlchemy, Flask‑Migrate, Flask‑Login, and CKEditor.

## Running Tests

```bash
pytest
```

## Project Structure (top-level)

```text
app/
	admin/        # Admin routes, forms, templates
	auth/         # Auth routes & forms
	main/         # Public routes
	profile/      # Profile routes & forms
	static/
		css/        # Modular CSS (see below)
		images/
		uploads/    # User uploads
	templates/    # Jinja templates
docs/           # Sphinx documentation
migrations/     # Alembic migrations (Flask-Migrate)
tests/          # PyTest suite
config.py
run.py          # App entrypoint
init_db.py      # Dev helper to seed data
```

## CSS Organization

Modular CSS under `app/static/css`:

- `base/` foundation and components (base.css, forms.css, button.css, nav.css, etc.)
- `admin/` admin pages (users, challenges, dashboard)
- `page/` page-specific styles (leaderboard, challenge, about)
- `profile/`, `summer/`, `article-newsletter/`
- `main.css` is an import hub only; no inline styles
- `order.txt` lists load order for predictable cascade

## Documentation

Sphinx docs are in `docs/`. To build:

```bash
cd docs
pip install -r requirements.txt
make html
```

## Deployment Notes

- Set a strong `SECRET_KEY` and appropriate DB settings (prefer managed PostgreSQL)
- Ensure `FLASK_ENV`, `APP_ENVIRONMENT`, or `ENV` indicate production
- Run migrations: `flask db upgrade`
- Enable logging to stdout if required by your platform (`LOG_TO_STDOUT=true`)

## License

MIT — see `LICENSE`.

## Contact

Upton Court Grammar School — Maths Society

## Useful Links

- [Flask](https://flask.palletsprojects.com/)
- [Jinja](https://jinja.palletsprojects.com/)
