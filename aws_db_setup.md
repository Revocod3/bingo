# AWS Setup for Bingo App

This guide outlines the steps to set up AWS services for the Bingo application.

## Part I: AWS RDS Setup

This guide outlines the steps to set up an AWS RDS PostgreSQL database for the Bingo application.

## 1. Create an RDS Instance

1. Log in to the AWS Management Console
2. Navigate to RDS service
3. Click "Create database"
4. Select "Standard create" and choose PostgreSQL
5. Choose the appropriate version (compatible with Django 5.1)
6. Select the appropriate instance class:
   - Development/testing: db.t3.micro
   - Production: db.t3.small or larger based on load
7. Configure storage:
   - Allocate at least 20GB
   - Enable storage autoscaling
   - Set maximum storage threshold as needed

## 2. Network & Security Configuration

1. VPC: Use your application VPC
2. Public accessibility: 
   - Development: Yes (for easy access)
   - Production: No (use private subnet with VPC peering)
3. Create a security group allowing PostgreSQL (port 5432) from your application servers only
4. Configure the database subnet group with appropriate subnets

## 3. Database Authentication

1. Set a secure master username and password
2. Store these credentials in a secure location (e.g., AWS Secrets Manager)

## 4. Database Options

1. Initial database name: `bingo`
2. Parameter group: Create a custom parameter group with:
   - `max_connections`: 100 (or higher based on needs)
   - `shared_buffers`: 25% of instance memory
   - `work_mem`: 4MB
   - `maintenance_work_mem`: 64MB
   - `effective_cache_size`: 75% of instance memory

## 5. Backup & Maintenance

1. Enable automated backups
2. Set a retention period (7-35 days)
3. Schedule maintenance window during low-traffic periods

## 6. Update Environment Variables

After creating your RDS instance, update the following environment variables in your deployment:

```
AWS_DB_NAME=bingo
AWS_DB_USER=your_master_username
AWS_DB_PASSWORD=your_secure_password
AWS_DB_HOST=your-db-instance.xxxxx.region.rds.amazonaws.com
AWS_DB_PORT=5432
AWS_DB_SSL_MODE=require
ENVIRONMENT=production
```

## 7. Database Migration

1. Run the database migration:
   ```bash
   python manage.py check_db_connection
   python manage.py migrate
   ```

## Part II: AWS Elastic Beanstalk Setup

Now that your RDS database is configured, let's deploy the web application to AWS Elastic Beanstalk.

### 1. Install EB CLI

```bash
pip install awsebcli
```

### 2. Prepare Your Django Project

1. Create an `.ebignore` file to exclude files from deployment:
   ```
   venv/
   *.pyc
   __pycache__/
   .env.local
   .git/
   .gitignore
   ```

2. Create the `requirements.txt` file (already in your project)

3. Create a Procfile in your project root:
   ```
   web: gunicorn core.wsgi:application --workers 3 --timeout 60
   ```

### 3. Initialize Elastic Beanstalk

```bash
# Navigate to your project root
cd /home/kevin/Bingo/bingo-api

# Initialize EB project
eb init -p python-3.12 bingo-app

# When prompted:
# - Select your AWS region
# - Create or select an existing key pair for SSH access
```

### 4. Configure Environment Variables

Create a `.ebextensions` directory in your project root with a file named `01_environment.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    DJANGO_SETTINGS_MODULE: core.settings
    ENVIRONMENT: production
    SECRET_KEY: YOUR_SECRET_KEY
    AWS_DB_NAME: bingo
    AWS_DB_USER: your_master_username
    AWS_DB_PASSWORD: your_secure_password
    AWS_DB_HOST: your-db-instance.xxxxx.region.rds.amazonaws.com
    AWS_DB_PORT: 5432
    AWS_DB_SSL_MODE: require
    EMAIL_HOST: smtp.gmail.com
    EMAIL_PORT: 587
    EMAIL_HOST_USER: your_email@gmail.com
    EMAIL_HOST_PASSWORD: your_app_password
    EMAIL_USE_TLS: True
    DEFAULT_FROM_EMAIL: your_email@gmail.com
    BYPASS_EMAIL_VERIFICATION: False
    EMAIL_BACKEND: django.core.mail.backends.smtp.EmailBackend
    FRONTEND_URL: https://your-frontend-domain.com
```

### 5. Configure Django Static Files

Create another file in `.ebextensions` named `02_django.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: core.wsgi:application
  aws:elasticbeanstalk:environment:proxy:staticfiles:
    /static: staticfiles

container_commands:
  01_collectstatic:
    command: "python manage.py collectstatic --noinput"
  02_migrate:
    command: "python manage.py migrate --noinput"
    leader_only: true
  03_createsu:
    command: "python manage.py check_db_connection"
    leader_only: true
```

### 6. Create Elastic Beanstalk Environment and Deploy

```bash
# Create environment and deploy
eb create bingo-production

# For future deployments
eb deploy
```

### 7. Configure HTTPS with Certificate Manager

1. Request a certificate in AWS Certificate Manager
2. Configure the Elastic Beanstalk environment to use the certificate
3. Set up a custom domain with your DNS provider pointing to the EB environment URL

### 8. Monitoring

1. Use CloudWatch for monitoring your application
2. Set up alarms for:
   - High CPU utilization
   - High memory usage
   - Error rates

### 9. Performance Considerations

- Enable environment caching
- Scale your environment horizontally for increased traffic
- Optimize static file delivery with CloudFront
- Consider using AWS ElastiCache for caching

### 10. Security Best Practices

- Use IAM roles for Elastic Beanstalk with least privilege
- Regularly update your application and dependencies
- Use security groups to restrict access
- Implement AWS WAF for additional protection
- Consider AWS Shield for DDoS protection
