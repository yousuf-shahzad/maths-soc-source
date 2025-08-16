Installation
============

Outlined is the most basic setup for installing the project locally.

Prerequisites
-------------
- Python 3.8+
- pip

Getting the Code and Dependencies
---------------------------------

Windows (PowerShell / cmd):

.. code-block:: powershell

   git clone https://github.com/yousuf-shahzad/maths-soc-source.git
   cd maths-soc-source
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt

macOS/Linux (bash/zsh):

.. code-block:: bash

   git clone https://github.com/yousuf-shahzad/maths-soc-source.git
   cd maths-soc-source
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

Environment Configuration
-------------------------

Create a ``.env`` file in the project root. If ``DATABASE_URL`` is set, it takes precedence over individual DB settings.

.. code-block:: ini

   # Secret key (required in production)
   SECRET_KEY=change_me

   # Database (PostgreSQL default; sqlite supported)
   # If DATABASE_URL is present, it overrides these
   DATABASE_TYPE=postgresql  # or sqlite
   DB_USERNAME=postgres
   DB_PASSWORD=
   DB_HOST=localhost
   DB_NAME=mathsoc

   # Environment flags
   FLASK_ENV=development      # development|testing|production
   APP_ENVIRONMENT=development
   ENV=dev

   # Logging
   LOG_TO_STDOUT=false

Database Initialization
-----------------------

Option A: Apply migrations (recommended):

.. code-block:: powershell

   set FLASK_APP=run:app
   flask db upgrade

Option B: Seed defaults for development:

.. code-block:: powershell

   python init_db.py

Running the App
---------------

.. code-block:: powershell

   python run.py