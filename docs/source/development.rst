Development Guide
==================================

Purpose of this Guide
--------------------

This guide provides detailed instructions for developers and administrators to set up, develop, and maintain the Maths Society website for Upton Court Grammar School.

Prerequisites
-------------

Operating Systems
~~~~~~~~~~~~~~~~~

- Windows 10/11
- macOS (10.15+)
- Linux (Ubuntu 20.04+, CentOS 8+)

Software Requirements
~~~~~~~~~~~~~~~~~~~~

- **Python**: Version 3.8 or higher
  - Recommended: Python 3.9 or 3.10
- **Package Manager**: 
  - pip (comes with Python)
  - Optional: poetry or conda for advanced dependency management

Recommended Development Tools
----------------------------

Integrated Development Environment (IDE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Visual Studio Code
- PyCharm Community Edition
- Sublime Text
- Atom

Version Control
~~~~~~~~~~~~~~~

- Git (latest version)
- GitHub Desktop (optional, for less technical users)

Repository Setup
----------------

Cloning the Repository
~~~~~~~~~~~~~~~~~~~~~

Clone using HTTPS:

.. code-block:: bash

   git clone https://github.com/yousuf-shahzad/math-soc-source.git
   cd math-soc-source

Or using SSH (recommended for developers):

.. code-block:: bash

   git clone git@github.com:yousuf-shahzad/math-soc-source.git
   cd math-soc-source

Virtual Environment Setup
------------------------

Windows
~~~~~~~

Using Python's built-in venv:

.. code-block:: powershell

   python -m venv venv
   .\venv\Scripts\activate

Using Anaconda/Miniconda:

.. code-block:: powershell

   conda create -n mathsoc python=3.9
   conda activate mathsoc

macOS/Linux
~~~~~~~~~~~

Using Python's built-in venv:

.. code-block:: bash

   python3 -m venv venv
   source venv/bin/activate

Using Anaconda/Miniconda:

.. code-block:: bash

   conda create -n mathsoc python=3.9
   conda activate mathsoc

Dependency Installation
----------------------

.. code-block:: bash

   # Ensure you're in the virtual environment
   pip install -r requirements.txt

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~

Create a ``.env`` file in the project root:

.. code-block:: env

   # Application Configuration
   SECRET_KEY=your_secure_random_key_here
   FLASK_ENV=development
   APP_ENVIRONMENT=development

   # Database Configuration
   DATABASE_TYPE=sqlite  # Default for development
   # For PostgreSQL, use:
   # DATABASE_TYPE=postgresql
   # DB_USERNAME=your_username
   # DB_PASSWORD=your_password
   # DB_HOST=localhost
   # DB_NAME=mathsoc_db

   # Optional Logging
   LOG_TO_STDOUT=false

Generating a Secure Secret Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Windows:

.. code-block:: powershell

   python -c "import secrets; print(secrets.token_hex(24))"

macOS/Linux:

.. code-block:: bash

   python3 -c "import secrets; print(secrets.token_hex(24))"

Development Workflow
-------------------

Running the Application
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Development Server
   python run.py

   # Alternative with Flask CLI
   flask run

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Ensure pytest is installed
   pytest tests/

Common Development Tasks
-----------------------

Database Migrations
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create a new migration
   flask db migrate -m "Description of changes"

   # Apply migrations
   flask db upgrade

Adding New Dependencies
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Activate virtual environment first
   pip install new-package-name
   pip freeze > requirements.txt

Best Practices
--------------

1. Always work in a virtual environment
2. Use type hints in your code
3. Write comprehensive unit tests
4. Follow PEP 8 style guidelines
5. Use meaningful commit messages
6. Review dependencies regularly for security updates

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

Dependency Conflicts
^^^^^^^^^^^^^^^^^^^

- Delete ``venv`` folder
- Recreate virtual environment
- Reinstall dependencies

Database Connection
^^^^^^^^^^^^^^^^^^

- Check ``.env`` file
- Verify database credentials
- Ensure database service is running

Logging and Debugging
~~~~~~~~~~~~~~~~~~~~

- Use ``print()`` statements sparingly
- Leverage Flask's debug mode
- Consider using logging module for more robust debugging

Contributing
------------

1. Create a feature branch:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. Make your changes
3. Run tests
4. Commit with a clear message
5. Push to your fork
6. Create a Pull Request

Contact
-------

For technical support or collaboration:

- Yousuf Shahzad
- Sudhakara Ambati

Upton Court Grammar School


Architecture Overview
----------------------

High-Level Components
~~~~~~~~~~~~~~~~~~~~~

- **Application Factory**: ``app.create_app`` builds the Flask app with the requested configuration (development, testing, production).
- **Blueprints**: Modular structure with ``auth``, ``main``, ``profile``, and ``admin`` blueprints.
- **Database**: SQLAlchemy models in ``app/models.py``; database initialization via Flask-Migrate (Alembic).
- **Forms**: WTForms under each blueprint's ``forms.py``.
- **Templates**: Jinja templates organized per blueprint in ``app/templates/<blueprint>/``; shared base template ``base.html``.
- **Static Assets**: Modular CSS in ``app/static/css``; images under ``app/static/images``; user uploads under ``app/static/uploads``.
- **Rich Text**: CKEditor is integrated for content fields in admin.

App Factory and Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The application uses an app factory pattern (``app/__init__.py``):

- Loads configuration via ``config.get_config``
- Initializes extensions: SQLAlchemy, Flask-Login, Flask-Migrate, CKEditor
- Registers blueprints
- Configurable via environment variables (see ``installation``)

Database and Migrations
~~~~~~~~~~~~~~~~~~~~~~~

- Create migrations: ``flask db migrate -m "message"``
- Apply migrations: ``flask db upgrade``
- For development seeding, ``init_db.py`` can create default schools and an admin user (non-production only)

CSS and Frontend Scheme
-----------------------

We use a modular CSS approach. Key points:

- ``app/static/css/main.css`` is an import hub (no direct styles)
- Base components live under ``app/static/css/base`` (e.g., ``base.css``, ``forms.css``, ``button.css``)
- Feature/page-specific styles live under folders like ``admin/``, ``page/``, ``profile/``, ``summer/``, ``article-newsletter/``
- The file ``app/static/css/order.txt`` lists suggested cascade order
- Avoid inline CSS in templates; use classes from base/feature CSS files

Blueprint Conventions
---------------------

- ``routes.py`` defines endpoints; ``forms.py`` defines WTForms; ``__init__.py`` registers the blueprint
- Templates: route naming aligns with subfolders under ``app/templates/<blueprint>/``
- Admin pages follow consistent form and layout classes (see ``base/forms.css``, ``base/button.css``)

Developer Onboarding (Quick)
----------------------------

1. Set up environment (see :doc:`installation`).
2. Run ``flask db upgrade`` (or ``python init_db.py`` in dev).
3. Start the dev server with ``python run.py``.
4. Explore blueprints: ``app/admin``, ``app/auth``, ``app/main``, ``app/profile``.
5. Run tests with ``pytest``; add new tests in ``tests/`` mirroring module layout.
6. For UI work, reuse classes from ``base`` CSS and mirror existing admin templates.

Code Style and Quality
----------------------

- PEP 8, type hints encouraged
- Keep functions small and focused
- Prefer blueprint modularity; avoid monolithic files
- Update or add tests for new features and bug fixes
- Keep migrations atomic and named clearly

Security Notes
--------------

- Never commit real secrets; use ``.env``
- Set a strong ``SECRET_KEY`` in production
- Validate file uploads; review upload folders and allowed types
- Regularly update dependencies