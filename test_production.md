# Testing Your Bingo API Production Environment

This guide outlines steps to verify that your production environment is working correctly after deployment to AWS Elastic Beanstalk.

## 1. Verify Deployment Status

First, check if your environment is running:

```bash
eb status bingo-production
```

Look for:
- Status: "Ready"
- Health: "Green"

## 2. Test Environment Variables

Ensure that your environment variables are properly set:

```bash
eb printenv bingo-production
```

This should display all the environment variables set through the `eb setenv` command.

## 3. Test Database Connection

Use the built-in management command to test database connectivity:

```bash
eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python manage.py check_db_connection"
```

This command will:
- SSH into your instance
- Navigate to the application directory
- Activate the virtual environment
- Run the check_db_connection management command

## 4. Test Email Functionality

Test that your email system is configured correctly:

```bash
eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python manage.py test_email --email=your-test-email@example.com"
```

## 5. Test User Registration & Authentication

Test the full user registration flow:

```bash
eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python manage.py test_registration --email=test@example.com --password=TestPass123!"
```

## 6. Test API Endpoints

Use curl or a REST client (Postman, Insomnia) to test your API endpoints:

```bash
# Replace with your actual EB URL
curl https://your-eb-environment-url.elasticbeanstalk.com/swagger/
```

Test specific endpoints:

```bash
# Get JWT token
curl -X POST \
  https://your-eb-environment-url.elasticbeanstalk.com/api/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email": "test@example.com", "password": "TestPass123!"}'

# Use token for authenticated requests
curl -X GET \
  https://your-eb-environment-url.elasticbeanstalk.com/api/users/me/ \
  -H 'Authorization: Bearer your_jwt_token'
```

## 7. Check Application Logs

View logs for troubleshooting:

```bash
eb logs bingo-production
```

## 8. Monitor Server Health

```bash
eb health bingo-production
```

This displays CPU usage, load, and other health metrics.

## 9. Test Static Files

Verify that your static files are being served correctly by visiting:
`https://your-eb-environment-url.elasticbeanstalk.com/static/admin/css/base.css`

## 10. Common Issues and Solutions

### Database Connection Issues
- Check security groups allow traffic from EB to RDS
- Verify RDS instance is running
- Check database credentials in environment variables

### Email Sending Failures
- Verify SMTP settings
- Check if Gmail App Password is valid
- Ensure port 587 is not blocked

### 500 Server Errors
- Check the application logs: `eb logs bingo-production`
- Look for Python tracebacks and error messages

### Slow Performance
- Check if instance size is sufficient
- Look for slow database queries
- Consider adding caching

## 11. Troubleshooting Red Health Status

If your environment shows "Red" health status, it indicates critical issues that need immediate attention:

### Immediate Actions
1. Check detailed health information:
   ```bash
   eb health bingo-production --detailed
   ```

2. View recent events that might explain the issue:
   ```bash
   eb events -f bingo-production
   ```

3. Check application logs for errors:
   ```bash
   eb logs bingo-production
   ```

### Common Causes of Red Health
- **Application Errors**: Your Django application is crashing or failing to start
- **Database Connection Issues**: Unable to connect to the RDS database
- **Configuration Problems**: Missing or incorrect environment variables
- **Deployment Failures**: Failed application deployment or unhealthy instances
- **Resource Constraints**: Insufficient CPU, memory, or disk space

### Specific Troubleshooting Steps
1. For application errors, check the application logs for exceptions:
   ```bash
   eb logs bingo-production --all
   ```

2. If the status shows "Updating" with Red health, wait for the update to complete or abort if it's taking too long:
   ```bash
   eb abort bingo-production
   ```

3. Test the database connection directly:
   ```bash
   eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python manage.py check_db_connection --verbose"
   ```

4. Check if the environment variables are correctly set:
   ```bash
   eb printenv bingo-production
   ```

5. Verify Django's configuration by running a shell:
   ```bash
   eb ssh bingo-production -c "cd /var/app/current && source /var/app/venv/*/bin/activate && python manage.py shell -c 'from django.conf import settings; print(settings.DATABASES)'"
   ```

### Recovery Options
1. **Rebuild the environment**:
   ```bash
   eb rebuild bingo-production
   ```

2. **Deploy a previous working version**:
   ```bash
   eb list-versions
   eb deploy bingo-production --version VERSION_LABEL
   ```

3. **Create a new environment and swap URLs**:
   ```bash
   eb create bingo-production-new
   eb swap bingo-production bingo-production-new
   ```

4. If all else fails, consider creating a clean environment and configuring it from scratch:
   ```bash
   eb terminate bingo-production
   eb create bingo-production
   ```
   Then run the `setenv.sh` script to reconfigure all environment variables.

## 12. Scaling Testing

To test how your application behaves under load, you can temporarily increase the number of instances:

```bash
eb scale 2 bingo-production
```

And then reset back to 1 when testing is complete:

```bash
eb scale 1 bingo-production
```
