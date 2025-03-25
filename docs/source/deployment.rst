Maths Society Website Deployment Guide
======================================

Overview
--------

This guide provides comprehensive instructions for deploying the Upton Court Grammar School Maths Society website, with support for both Linux (Ubuntu/Debian) and Windows environments.

Prerequisites
-------------

Before beginning, ensure you have:

- Python 3.8 or higher
- Git
- PostgreSQL 12+ (recommended)
- Administrator access to the server
- Basic understanding of command-line operations

Deployment Options
------------------

Option 1.1: Local Server Deployment (Linux)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

PostgreSQL Setup (Ubuntu/Debian)
'''''''''''''''''''''''''''''''''

1. Install PostgreSQL:

.. code-block:: bash

    sudo apt update
    sudo apt install postgresql postgresql-contrib

2. Create Database and User:

.. code-block:: bash

    # Switch to postgres user
    sudo -u postgres psql

    # Create database user and database
    CREATE USER mathsoc WITH PASSWORD 'your_secure_password';
    CREATE DATABASE mathsoc_db OWNER mathsoc;
    GRANT ALL PRIVILEGES ON DATABASE mathsoc_db TO mathsoc;

    # Exit PostgreSQL
    \q

Option 1.2: Local Server Deployment (Windows)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Install PostgreSQL:
   - Download from official PostgreSQL website
   - During installation, set a strong password for the postgres user
   - Use pgAdmin to create the database:
     - Create user: ``mathsoc``
     - Create database: ``mathsoc_db``
     - Assign user as owner

Environment Setup (Both Linux and Windows)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Clone the Repository:

.. code-block:: bash

    git clone https://github.com/yousuf-shahzad/math-soc-source.git
    cd math-soc-source

2. Create Virtual Environment:

.. code-block:: bash

    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    venv\Scripts\activate

3. Install Dependencies:

.. code-block:: bash

    pip install -r requirements.txt

4. Configure Environment Variables:
Create a ``.env`` file in the project root:

.. code-block:: ini

    SECRET_KEY=generate_a_long_random_string_here
    FLASK_ENV=production
    APP_ENVIRONMENT=production

    DATABASE_TYPE=postgresql
    DB_USERNAME=mathsoc
    DB_PASSWORD=your_secure_password
    DB_HOST=localhost
    DB_NAME=mathsoc_db

5. Initialize Database:

.. code-block:: bash

    flask db upgrade

6. Create Admin User:

.. code-block:: bash

    flask shell

    # In the shell
    from app.models import User
    from app.database import db

    admin = User(
        full_name='Admin User', 
        year=13,
        maths_class='Staff',
        key_stage='KS5',
        is_admin=True
    )
    admin.set_password('your_admin_password')
    db.session.add(admin)
    db.session.commit()
    exit()

Option 2: External Hosting Providers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Recommended Providers
^^^^^^^^^^^^^^^^^^^^^

- Heroku
- DigitalOcean
- AWS Elastic Beanstalk
- PythonAnywhere

General Deployment Checklist for External Providers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Prepare Application**
   - Ensure ``requirements.txt`` is up to date
   - Create a ``Procfile`` for Heroku or similar:

     .. code-block:: bash

         web: gunicorn run:app

   - Add ``runtime.txt`` specifying Python version:

     .. code-block:: bash

         python-3.8.10

2. **Database Configuration**
   - Use provider's managed PostgreSQL service
   - Set environment variables in provider's dashboard
   - Ensure ``DATABASE_URL`` is correctly configured in ``.env``

3. **Static Files**
   - Configure static file hosting
   - Use cloud storage like AWS S3 for user uploads

4. **Security Considerations**
   - Use provider's SSL/TLS encryption
   - Enable two-factor authentication
   - Regularly update dependencies
   - Use strong, unique passwords
   - Limit administrative access

Provider-Specific Notes
^^^^^^^^^^^^^^^^^^^^^^^

- **Heroku**:

  .. code-block:: bash

      heroku create your-app-name
      heroku addons:create heroku-postgresql
      heroku config:set SECRET_KEY=your_secret_key
      git push heroku main

- **DigitalOcean App Platform**:
  - Connect GitHub repository
  - Auto-deploy on push
  - Use managed databases

- **AWS Elastic Beanstalk**:
  - Use Elastic Beanstalk CLI
  - Configure ``.ebextensions`` for environment setup

Maintenance and Updates
----------------------

1. Regular Updates:

.. code-block:: bash

    git pull
    pip install -U -r requirements.txt
    flask db upgrade
    sudo systemctl restart mathsoc  # For Linux systemd

2. Backup Database:

.. code-block:: bash

    # Linux PostgreSQL backup
    pg_dump -U mathsoc mathsoc_db > backup.sql

Backup Strategy
---------------

Backup Intervals and Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Local Server Deployments
'''''''''''''''''''''''''''

**Daily Backups**
- Recommended for small to medium-sized deployments
- Best practice: Automated daily database and file backups

PostgreSQL Daily Backup Script (Linux):

.. code-block:: bash

    #!/bin/bash
    
    # Create backup directory
    BACKUP_DIR="/var/backups/mathsoc"
    mkdir -p $BACKUP_DIR
    
    # Database backup
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    DB_BACKUP_FILE="$BACKUP_DIR/mathsoc_db_backup_$TIMESTAMP.sql"
    
    # Perform PostgreSQL backup
    pg_dump -U mathsoc -d mathsoc_db -F c -f $DB_BACKUP_FILE
    
    # File system backup (excluding temporary and cache files)
    tar -czvf "$BACKUP_DIR/mathsoc_files_$TIMESTAMP.tar.gz" \
        /path/to/math-soc-source \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='venv'
    
    # Optional: Rotate and remove old backups (keep last 7 days)
    find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
    find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

PostgreSQL Daily Backup Script (Windows):

.. code-block:: batch

    @echo off
    
    REM Create backup directory
    set BACKUP_DIR=C:\Backups\MathSoc
    if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
    
    REM Generate timestamp
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
    set TIMESTAMP=%datetime:~0,4%%datetime:~4,2%%datetime:~6,2%_%datetime:~8,2%%datetime:~10,2%%datetime:~12,2%
    
    REM Backup database
    "C:\Program Files\PostgreSQL\12\bin\pg_dump.exe" -U mathsoc -d mathsoc_db -F c -f "%BACKUP_DIR%\mathsoc_db_backup_%TIMESTAMP%.sql"
    
    REM File system backup
    powershell Compress-Archive -Path "C:\path\to\math-soc-source" -DestinationPath "%BACKUP_DIR%\mathsoc_files_%TIMESTAMP%.zip" -Force

2. Cloud Deployment Backup Strategies
''''''''''''''''''''''''''''''''''''

**Provider-Specific Backup Methods**

Heroku:
- Automated Database Backups:

.. code-block:: bash

    # Manual database backup
    heroku pg:backups capture

    # Schedule automated backups
    heroku pg:backups schedule DATABASE_URL --at '02:00 UTC'

    # List backups
    heroku pg:backups

DigitalOcean Managed Databases:
- Enable automated backups in dashboard
- Configure backup window and retention
- Backup frequency options:
  - Daily
  - Weekly
  - Custom intervals

AWS RDS Backup Configuration:
- Enable automated backups
- Set backup retention period (1-35 days)
- Configure backup window in AWS Management Console

3. Backup Verification and Testing
''''''''''''''''''''''''''''''''''

Backup Verification Script:

.. code-block:: bash

    #!/bin/bash
    
    # Restore test database
    TEST_DB="mathsoc_backup_test"
    
    # Latest backup file
    LATEST_BACKUP=$(ls -t /var/backups/mathsoc/*.sql | head -n1)
    
    # Create test database
    createdb $TEST_DB
    
    # Restore backup to test database
    pg_restore -d $TEST_DB $LATEST_BACKUP
    
    # Run basic validation queries
    psql -d $TEST_DB -c "SELECT COUNT(*) FROM users;"
    
    # Drop test database
    dropdb $TEST_DB

1. Offsite and Cloud Storage Backup
'''''''''''''''''''''''''''''''''''

Additional Backup Strategies:
- Use cloud storage services
- Implement multi-location backups

Example AWS S3 Backup Script:

.. code-block:: bash

    #!/bin/bash
    
    BACKUP_FILE="/var/backups/mathsoc/latest_backup.tar.gz"
    S3_BUCKET="s3://mathsoc-backups"
    
    # Compress and upload to S3
    tar -czvf $BACKUP_FILE /path/to/math-soc-source
    aws s3 cp $BACKUP_FILE $S3_BUCKET/

5. Backup Retention Policy
'''''''''''''''''''''''''

Recommended Retention Intervals:
- Daily backups: Retain for 7 days
- Weekly backups: Retain for 4 weeks
- Monthly backups: Retain for 3-6 months
- Annual backups: Retain for 1-2 years

**Considerations:**
- Storage costs
- Compliance requirements
- Disk space limitations

Troubleshooting
---------------

- Check application logs
- Verify database connections
- Ensure all environment variables are set
- Validate dependencies

Contact Support
---------------

For technical issues:
- Yousuf Shahzad (Developer)
- Sudhakara Ambati (Developer)

**Note**: Always test deployment in a staging environment first.