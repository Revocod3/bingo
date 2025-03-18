# Comprehensive Elastic Beanstalk Deployment Troubleshooting

## Common Deployment Issues & Solutions

### 1. "Environment is not in a Ready state" Error

**Problem:** When running `eb deploy`, you get an error about the environment not being ready.

**Solutions:**
- Check environment status: `eb status bingo-production`
- If status shows "Updating", wait for the update to complete
- If status shows "Error", check logs: `eb logs bingo-production`
- Rebuild environment: `eb rebuild bingo-production`

### 2. Environment Variable Issues

**Problem:** Environment variables not being recognized or showing as `${VARIABLE_NAME}`

**Solutions:**
- Use the script to set variables directly:
  ```bash
  ./setenv.sh bingo-production
  ```
- Verify variables are set: 
  ```bash
  ./verify_env_variables.sh bingo-production
  ```
- Manual setting of individual variables:
  ```bash
  eb setenv KEY_NAME=value
  ```

### 3. Database Connection Errors

**Problem:** Application can't connect to the database

**Solutions:**
- Verify database environment variables are set correctly
- Test connection with the command: 
  ```bash
  eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python manage.py check_db_connection"
  ```
- Check security groups allow traffic from Elastic Beanstalk to RDS
- Verify RDS instance is running and accessible

### 4. Static Files Not Serving

**Problem:** CSS and JS files return 404 errors

**Solutions:**
- Ensure `STATIC_ROOT` is set correctly in Django settings
- Verify `.ebextensions/02_django.config` has correct static file mapping
- Run `python manage.py collectstatic` locally to check for errors
- Check permissions on static files directory

### 5. Email Configuration Issues

**Problem:** Verification emails not being sent

**Solutions:**
- Verify email environment variables are set correctly
- Test email sending with:
  ```bash
  eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python manage.py test_email --email=your@email.com"
  ```
- Check if SMTP server blocks connections from AWS IP addresses
- For Gmail, ensure you're using an App Password if 2FA is enabled

### 6. Deployment Health Check Failures

**Problem:** Application fails health checks after deployment

**Solutions:**
- Check application logs: `eb logs bingo-production`
- SSH into the instance and check post-deployment logs:
  ```bash
  eb ssh bingo-production -c "cat /var/log/app/latest_deploy_summary.log"
  ```
- Examine health check endpoint: `/health/` should return 200 status code
- Manually run the health check script:
  ```bash
  eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python -c \"from bingo.health import health_check; from django.http import HttpRequest; print(health_check(HttpRequest()).content)\""
  ```

### 7. Package Import Errors

**Problem:** Python package import errors in logs

**Solutions:**
- Verify requirements.txt contains all dependencies
- Manually check installed packages:
  ```bash
  eb ssh bingo-production -c "source /var/app/venv/*/bin/activate && pip freeze"
  ```
- Run package check script:
  ```bash
  eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python .ebextensions/check_requirements.py"
  ```

### 8. Migration Errors

**Problem:** Database migrations failing during deployment

**Solutions:**
- Verify database connection works before migrations
- Try running migrations manually:
  ```bash
  eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python manage.py migrate --noinput"
  ```
- Create a custom migration command file if complex migrations are needed

## Advanced Debugging

### SSH into the Instance
```bash
eb ssh bingo-production
```

### Examine Key Log Files
```bash
# Application logs
cat /var/log/app/application.log

# Deployment logs
cat /var/log/eb-activity.log

# Web server logs
cat /var/log/nginx/access.log
cat /var/log/nginx/error.log
```

### Check Running Processes
```bash
ps aux | grep gunicorn
ps aux | grep python
```

### Test Database Connection Directly
```bash
cd /var/app/current
source /var/app/venv/*/bin/activate
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.db import connections
connections['default'].ensure_connection()
print('Database connection successful!')
"
```

## Starting Fresh

If everything else fails, sometimes starting from scratch is the best option:

1. Terminate the environment:
   ```bash
   eb terminate bingo-production
   ```

2. Create a new environment:
   ```bash
   eb create bingo-production
   ```

3. Set all environment variables:
   ```bash
   ./setenv.sh bingo-production
   ```

4. Deploy your application:
   ```bash
   eb deploy bingo-production
   ```

## Getting Help

If you're still stuck after trying these steps, collect the following information:

1. Environment health: `eb health bingo-production`
2. Recent events: `eb events -f bingo-production`
3. Application logs: `eb logs bingo-production`
4. Output from the verify script: `./verify_env_variables.sh bingo-production`
5. Health check response: Access the `/health/` endpoint directly
