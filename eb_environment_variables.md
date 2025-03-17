# Managing AWS Elastic Beanstalk Environment Variables

## Understanding the Issue

When you see environment variables showing as `${VARIABLE_NAME}` in the EB environment, it means:
- The variable references aren't being substituted with actual values
- EB doesn't support variable substitution in the same way as other systems

## Option 1: Set Variables Directly via EB CLI

The most straightforward solution is to set your environment variables using the EB CLI:

```bash
eb setenv SECRET_KEY="your-secret-key" \
         AWS_DB_NAME="your-db-name" \
         AWS_DB_USER="your-db-username" \
         AWS_DB_PASSWORD="your-db-password" \
         AWS_DB_HOST="your-db-hostname.region.rds.amazonaws.com" \
         AWS_DB_PORT="5432" \
         EMAIL_HOST="smtp.gmail.com" \
         EMAIL_PORT="587" \
         EMAIL_HOST_USER="your-email@gmail.com" \
         EMAIL_HOST_PASSWORD="your-email-password" \
         DEFAULT_FROM_EMAIL="your-email@gmail.com" \
         FRONTEND_URL="https://your-frontend-domain.com"
```

## Option 2: Use AWS Console

1. Go to the AWS Elastic Beanstalk Console
2. Select your application and environment
3. Navigate to "Configuration" > "Software"
4. Find the "Environment properties" section
5. Add each key-value pair:
   - SECRET_KEY: your-secret-key
   - AWS_DB_NAME: your-db-name
   - AWS_DB_USER: your-db-username
   - And so on...
6. Click "Apply" to update the environment

## Option 3: Store Sensitive Values in AWS Systems Manager Parameter Store

For sensitive information like passwords and keys:

1. Go to AWS Systems Manager > Parameter Store
2. Create parameters with secure values
3. Then reference them in your code using boto3

```python
import boto3

ssm = boto3.client('ssm')
parameter = ssm.get_parameter(Name='/bingo/production/db_password', WithDecryption=True)
db_password = parameter['Parameter']['Value']
```

## Where to Find Your Values

1. **Database Credentials (AWS_DB_*)**: 
   - Found in the RDS Console > Databases > Your DB instance > Connectivity & Security
   - The password is only available when you first create the database

2. **SECRET_KEY**:
   - Should be a strong random string that you generate
   - Can use Django's built-in secret key generator:
     ```python
     from django.core.management.utils import get_random_secret_key
     print(get_random_secret_key())
     ```

3. **Email Settings (EMAIL_*)**: 
   - These are your SMTP server details
   - For Gmail, you need an "App Password" from your Google Account

4. **FRONTEND_URL**: 
   - The URL where your frontend application is hosted

## Security Best Practices

1. Never commit sensitive values to version control
2. Use AWS Secrets Manager for highly sensitive values
3. Consider using separate parameter stores for different environments
4. Rotate credentials regularly
5. Use IAM roles to restrict which services can access your variables
