Administrator Setup Guide
========================

This guide provides comprehensive instructions for school administrators to set up, configure, and maintain the Upton Court Grammar School Maths Society website. It focuses on production deployment using PostgreSQL and covers all necessary administrative tasks.

Prerequisites
------------
Before beginning the setup process, ensure you have:

- A server with Python 3.8+ installed
- PostgreSQL 12+ installed on your server or a separate database server
- Basic understanding of command-line operations
- Administrator access to the server
- Git installed for repository management

PostgreSQL Database Setup
------------------------

Installing PostgreSQL
~~~~~~~~~~~~~~~~~~~~

If PostgreSQL is not already installed on your server:

**For Ubuntu/Debian:**

.. code-block:: bash

   sudo apt update
   sudo apt install postgresql postgresql-contrib

**For CentOS/RHEL:**

.. code-block:: bash

   sudo yum install postgresql-server postgresql-contrib
   sudo postgresql-setup initdb
   sudo systemctl start postgresql
   sudo systemctl enable postgresql

Creating the Database and User
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Log in to PostgreSQL as the postgres user:

   .. code-block:: bash

      sudo -u postgres psql

2. Create a dedicated database user for the application:

   .. code-block:: sql

      CREATE USER mathsoc WITH PASSWORD 'secure_password_here';

3. Create the database:

   .. code-block:: sql

      CREATE DATABASE mathsoc_db OWNER mathsoc;

4. Grant privileges:

   .. code-block:: sql

      GRANT ALL PRIVILEGES ON DATABASE mathsoc_db TO mathsoc;

5. Exit PostgreSQL:

   .. code-block:: sql

        q

Setting PostgreSQL for Remote Access (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your database is on a separate server:

1. Edit PostgreSQL configuration:

   .. code-block:: bash

      sudo nano /etc/postgresql/12/main/postgresql.conf

2. Update the listen address:

   .. code-block:: text

      listen_addresses = '*'

3. Configure client authentication:

   .. code-block:: bash

      sudo nano /etc/postgresql/12/main/pg_hba.conf

4. Add the following line (adjust as needed for security):

   .. code-block:: text

      host    mathsoc_db    mathsoc    <app_server_ip>/32    md5

5. Restart PostgreSQL:

   .. code-block:: bash

      sudo systemctl restart postgresql

Environment Configuration
------------------------

Setting Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a ``.env`` file in the application root directory:

.. code-block:: bash

   # Create and edit .env file
   nano .env

Add the following variables:

.. code-block:: text

   # Application configuration
   SECRET_KEY=generate_a_secure_random_key_here
   FLASK_ENV=production
   APP_ENVIRONMENT=production

   # Database configuration
   DATABASE_TYPE=postgresql
   DB_USERNAME=mathsoc
   DB_PASSWORD=secure_password_here
   DB_HOST=localhost
   DB_NAME=mathsoc_db

   # Logging
   LOG_TO_STDOUT=true

To generate a secure random key:

.. code-block:: bash

   python -c "import os; print(os.urandom(24).hex())"

Setting Up Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment
   source venv/bin/activate

   # On Windows: venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

Initial Deployment
-----------------

Cloning the Repository
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/yousuf-shahzad/math-soc-source.git
   cd math-soc-source

Database Initialization
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # With virtual environment activated
   flask db upgrade

Creating an Admin User
~~~~~~~~~~~~~~~~~~~~~

Access the Flask shell:

.. code-block:: bash

   flask shell

In the shell, create an admin user:

.. code-block:: python

   from app.models import User
   from app.database import db

   # Create admin user
   admin = User(
        full_name='Admin User', 
        year=13,  # Can be any valid year
        maths_class='Staff',
        key_stage='KS5',
        is_admin=True
   )
   admin.set_password('secure_admin_password')
   db.session.add(admin)
   db.session.commit()

   # Confirm creation
   admin_check = User.query.filter_by(is_admin=True).first()
   print(f"Admin created: {admin_check.full_name}")

   # Exit shell
   exit()

Setting Up with Gunicorn and Nginx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install Gunicorn (should already be in requirements.txt)

2. Create a systemd service file:

   .. code-block:: bash

      sudo nano /etc/systemd/system/mathsoc.service

3. Add the following configuration:

   .. code-block:: text

      [Unit]
      Description=Maths Society Website
      After=network.target
      
      [Service]
      User=your_server_username
      WorkingDirectory=/path/to/math-soc-source
      Environment="PATH=/path/to/math-soc-source/venv/bin"
      EnvironmentFile=/path/to/math-soc-source/.env
      ExecStart=/path/to/math-soc-source/venv/bin/gunicorn -w 4 -k gevent -b 127.0.0.1:8000 "run:app"
      Restart=always
      
      [Install]
      WantedBy=multi-user.target

4. Start and enable the service:

   .. code-block:: bash

      sudo systemctl start mathsoc
      sudo systemctl enable mathsoc

5. Install and configure Nginx:

   .. code-block:: bash

      sudo apt install nginx

6. Create Nginx site configuration:

   .. code-block:: bash

      sudo nano /etc/nginx/sites-available/mathsoc

7. Add the following configuration:

   .. code-block:: text

      server {
          listen 80;
          server_name your_domain.com;
          
          location / {
              proxy_pass http://127.0.0.1:8000;
              proxy_set_header Host $host;
              proxy_set_header X-Real-IP $remote_addr;
          }
          
          location /static {
              alias /path/to/math-soc-source/app/static;
          }
      }

8. Enable the site:

   .. code-block:: bash

      sudo ln -s /etc/nginx/sites-available/mathsoc /etc/nginx/sites-enabled
      sudo nginx -t  # Test configuration
      sudo systemctl restart nginx

9. Set up SSL with Let's Encrypt (recommended):

   .. code-block:: bash

      sudo apt install certbot python3-certbot-nginx
      sudo certbot --nginx -d your_domain.com

User Management
--------------

Managing Admin Users
~~~~~~~~~~~~~~~~~~

To create additional admin users, use the Flask shell method shown in the Initial Deployment section.

To remove admin privileges:

.. code-block:: python

   from app.models import User
   from app.database import db

   user = User.query.filter_by(full_name='Admin Name').first()
   if user:
        user.is_admin = False
        db.session.commit()
        print(f"Admin privileges removed from {user.full_name}")

User Moderation
~~~~~~~~~~~~~

The website includes profanity checking for user registration. Admin users can further manage users through the admin panel:

1. Log in with an admin account
2. Navigate to the admin section
3. Use the user management interface to:
   - View all users
   - Reset passwords if needed
   - Delete problematic accounts

Backup and Recovery
------------------

Database Backup
~~~~~~~~~~~~~

Set up regular PostgreSQL backups:

1. Create a backup script:

   .. code-block:: bash

      nano /path/to/backup_script.sh

2. Add the following content:

   .. code-block:: bash

      #!/bin/bash
      BACKUP_DIR="/path/to/backups"
      TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
      BACKUP_FILE="$BACKUP_DIR/mathsoc_db_$TIMESTAMP.sql"
      
      # Create backup directory if it doesn't exist
      mkdir -p $BACKUP_DIR
      
      # Create backup
      PGPASSWORD="secure_password_here" pg_dump -h localhost -U mathsoc -d mathsoc_db > $BACKUP_FILE
      
      # Compress backup
      gzip $BACKUP_FILE
      
      # Delete backups older than 30 days
      find $BACKUP_DIR -name "mathsoc_db_*.sql.gz" -mtime +30 -delete

3. Make the script executable:

   .. code-block:: bash

      chmod +x /path/to/backup_script.sh

4. Set up a cron job to run daily:

   .. code-block:: bash

      crontab -e

   Add:

   .. code-block:: text

      0 2 * * * /path/to/backup_script.sh

Recovery Procedure
~~~~~~~~~~~~~~~~

To restore from a backup:

.. code-block:: bash

   # Uncompress backup if needed
   gunzip /path/to/backup_file.sql.gz

   # Restore database
   PGPASSWORD="secure_password_here" psql -h localhost -U mathsoc -d mathsoc_db < /path/to/backup_file.sql

Security Considerations
----------------------

Application Security
~~~~~~~~~~~~~~~~~

1. **Keep dependencies updated**:

   .. code-block:: bash

      pip install -U -r requirements.txt

2. **Set secure passwords** for database and admin users

3. **Use HTTPS** with Let's Encrypt as configured earlier

4. **Restrict .env file permissions**:

   .. code-block:: bash

      chmod 600 .env

Server Security
~~~~~~~~~~~~~

1. **Enable firewall**:

   .. code-block:: bash

      sudo ufw allow 22
      sudo ufw allow 80
      sudo ufw allow 443
      sudo ufw enable

2. **Configure automatic security updates**:

   .. code-block:: bash

      sudo apt install unattended-upgrades
      sudo dpkg-reconfigure unattended-upgrades

3. **Set up fail2ban** to protect against brute force attacks:

   .. code-block:: bash

      sudo apt install fail2ban
      sudo systemctl enable fail2ban
      sudo systemctl start fail2ban

Maintenance Procedures
---------------------

Regular Updates
~~~~~~~~~~~~~

1. **Update the application**:

   .. code-block:: bash

      cd /path/to/math-soc-source
      git pull
      source venv/bin/activate
      pip install -U -r requirements.txt
      flask db upgrade  # If there are database migrations
      sudo systemctl restart mathsoc

2. **System updates**:

   .. code-block:: bash

      sudo apt update
      sudo apt upgrade

Monitoring
~~~~~~~~

1. **Check application logs**:

   .. code-block:: bash

      sudo journalctl -u mathsoc

2. **Monitor database performance**:

   .. code-block:: sql

      -- In psql
      SELECT * FROM pg_stat_activity;

3. **Check disk usage**:

   .. code-block:: bash

      df -h

Newsletter Management
~~~~~~~~~~~~~~~~~~~

The application includes a newsletter system. To manage subscribers:

1. Log in as an admin
2. Navigate to the newsletter admin section
3. Create and send newsletters
4. Export subscriber lists if needed

Troubleshooting
--------------

Common Issues and Solutions
~~~~~~~~~~~~~~~~~~~~~~~~~

Application Won't Start
^^^^^^^^^^^^^^^^^^^^^^^

1. Check the logs:

   .. code-block:: bash

      sudo journalctl -u mathsoc -n 50

2. Verify environment variables:

   .. code-block:: bash

      cat .env

3. Confirm the database is running:

   .. code-block:: bash

      sudo systemctl status postgresql

Database Connection Issues
^^^^^^^^^^^^^^^^^^^^^^^^

1. Check database credentials in ``.env``

2. Verify PostgreSQL is running:

   .. code-block:: bash

      sudo pg_isready

3. Test connection:

   .. code-block:: bash

      PGPASSWORD="secure_password_here" psql -h localhost -U mathsoc -d mathsoc_db

Slow Performance
^^^^^^^^^^^^^

1. Check server resources:

   .. code-block:: bash

      top

2. Consider increasing gunicorn workers (in mathsoc.service)

3. Analyze database performance:

   .. code-block:: sql

      -- In psql
      EXPLAIN ANALYZE SELECT * FROM your_problematic_query;

Contact Information
-----------------

For additional assistance, please contact:

- Yousuf Shahzad (Developer)
- Sudhakara Ambati (Developer)

Upton Court Grammar School