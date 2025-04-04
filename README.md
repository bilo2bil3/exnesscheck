# Exness Client Validator

A Django web application for checking if clients are registered under your Exness affiliate account.

## Features

- Check client registration by ID or email
- Display detailed client information for registered clients
- Store validation results in a database
- Secure handling of API credentials through environment variables

## Prerequisites

- Python 3.8 or higher
- Django 4.2.7
- Other dependencies as listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd exness_client_validator
```

2. Create a virtual environment and activate it:
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file:
```bash
cp .env.example .env
```

5. Edit the .env file with your Exness Affiliates API credentials:
```
EXNESS_API_EMAIL=your_exness_affiliate_email
EXNESS_API_PASSWORD=your_exness_affiliate_password
```

6. Run migrations:
```bash
python manage.py makemigrations validator_app
python manage.py migrate
```

7. Create a superuser (optional, for admin access):
```bash
python manage.py createsuperuser
```

## Usage

1. Start the development server:
```bash
python manage.py runserver
```

2. Access the application at http://127.0.0.1:8000/

3. To check a client, enter either:
   - Client ID in the "Client ID" field, or
   - Email address in the "Email" field

4. Click "Send" to check if the client is registered under your affiliate account

5. View detailed client information if the client is registered

## Admin Access

You can access the admin panel at http://127.0.0.1:8000/admin/ using the superuser credentials you created earlier. This allows you to view and manage all validation records.

## Security Notes

- Never commit your .env file or any files containing sensitive information
- Keep your API credentials secure
- For production deployment, follow Django's deployment best practices

## Deployment to DigitalOcean

### Option 1: DigitalOcean App Platform (Recommended)

1. **Fork this repository to your GitHub account**

2. **Sign up or log in to DigitalOcean**
   - Go to [DigitalOcean](https://www.digitalocean.com/) and create an account or login

3. **Create a new App**
   - Navigate to the App Platform section
   - Click "Create App"
   - Connect your GitHub account and select your forked repository
   - Choose the branch you want to deploy (usually `main`)

4. **Configure the App**
   - DigitalOcean will automatically detect your Django app
   - Make sure the following environment variables are added:
     - `SECRET_KEY`: Generate a secure random key
     - `DEBUG`: Set to `False`
     - `ALLOWED_HOSTS`: Add your app's domain (will be provided by DigitalOcean)
     - `EXNESS_API_EMAIL`: Your Exness account email
     - `EXNESS_API_PASSWORD`: Your Exness account password
   - Add a PostgreSQL database in the Resources tab

5. **Deploy the App**
   - Click "Create Resources" and wait for the deployment to complete
   - Your app will be available at the provided URL

### Option 2: DigitalOcean Droplet (Manual Setup)

1. **Create a Droplet**
   - Log in to DigitalOcean
   - Create a new Droplet using the Ubuntu 20.04 image
   - Choose an appropriate plan (1GB RAM minimum recommended)
   - Add your SSH key or create a password
   - Click "Create Droplet"

2. **Connect to the Droplet**
   ```bash
   ssh root@your_droplet_ip
   ```

3. **Update System and Install Dependencies**
   ```bash
   apt update && apt upgrade -y
   apt install -y python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl
   ```

4. **Create a PostgreSQL Database**
   ```bash
   sudo -u postgres psql
   ```
   ```sql
   CREATE DATABASE exness_validator;
   CREATE USER exnessuser WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE exness_validator TO exnessuser;
   \q
   ```

5. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/exness-client-validator.git
   cd exness-client-validator
   ```

6. **Set Up Virtual Environment**
   ```bash
   pip3 install virtualenv
   virtualenv venv
   source venv/bin/activate
   ```

7. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

8. **Create .env File**
   ```bash
   cp .env.example .env
   nano .env
   ```
   - Update the variables with your specific configuration

9. **Apply Migrations and Collect Static Files**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

10. **Set Up Gunicorn**
    ```bash
    nano /etc/systemd/system/gunicorn.service
    ```
    Add the following configuration:
    ```
    [Unit]
    Description=gunicorn daemon
    After=network.target

    [Service]
    User=root
    Group=www-data
    WorkingDirectory=/root/exness-client-validator
    ExecStart=/root/exness-client-validator/venv/bin/gunicorn \
              --access-logfile - \
              --workers 3 \
              --bind unix:/root/exness-client-validator/exness_validator.sock \
              exness_client_validator.wsgi:application

    [Install]
    WantedBy=multi-user.target
    ```

11. **Start Gunicorn**
    ```bash
    systemctl start gunicorn
    systemctl enable gunicorn
    ```

12. **Configure Nginx**
    ```bash
    nano /etc/nginx/sites-available/exness_validator
    ```
    Add the following configuration:
    ```
    server {
        listen 80;
        server_name your_domain.com;

        location = /favicon.ico { access_log off; log_not_found off; }
        location /static/ {
            root /root/exness-client-validator;
        }

        location / {
            include proxy_params;
            proxy_pass http://unix:/root/exness-client-validator/exness_validator.sock;
        }
    }
    ```

13. **Enable the Nginx Configuration**
    ```bash
    ln -s /etc/nginx/sites-available/exness_validator /etc/nginx/sites-enabled
    nginx -t
    systemctl restart nginx
    ```

14. **Set Up SSL (Optional but Recommended)**
    ```bash
    apt install certbot python3-certbot-nginx
    certbot --nginx -d your_domain.com
    ```

Your application should now be accessible at your domain or droplet IP address! 