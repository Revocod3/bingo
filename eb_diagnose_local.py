#!/usr/bin/env python3
import json
import subprocess
import argparse
import requests
from datetime import datetime

def run_command(command):
    """Run a command and return its output"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        print(f"Error: {result.stderr}")
    return result.stdout.strip()

def main():
    parser = argparse.ArgumentParser(description="Diagnose Elastic Beanstalk Environment")
    parser.add_argument("--env", required=True, help="Elastic Beanstalk environment name")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    args = parser.parse_args()
    
    env_name = args.env
    region = args.region
    
    print(f"=== Elastic Beanstalk Environment Diagnostic Tool ===")
    print(f"Environment: {env_name}")
    print(f"Region: {region}")
    print(f"Time: {datetime.now()}")
    print("\n=== Environment Health ===")
    
    # Check environment health
    health_data = run_command(f"aws elasticbeanstalk describe-environment-health --environment-name {env_name} --attribute-names All --region {region}")
    print(health_data)
    
    # Get recent events
    print("\n=== Recent Events ===")
    events = run_command(f"aws elasticbeanstalk describe-events --environment-name {env_name} --region {region} --max-items 10")
    print(events)
    
    # Get instance health
    print("\n=== Instance Health ===")
    instances = run_command(f"aws elasticbeanstalk describe-instances-health --environment-name {env_name} --attribute-names All --region {region}")
    print(instances)
    
    # Get environment variables (without secrets)
    print("\n=== Environment Configuration ===")
    config = run_command(f"aws elasticbeanstalk describe-configuration-settings --environment-name {env_name} --application-name $(aws elasticbeanstalk describe-environments --environment-names {env_name} --region {region} --query 'Environments[0].ApplicationName' --output text) --region {region}")
    
    # Parse and print environment variables (excluding sensitive ones)
    try:
        config_data = json.loads(config)
        env_vars = None
        for setting in config_data.get('ConfigurationSettings', []):
            for option in setting.get('OptionSettings', []):
                if option.get('Namespace') == 'aws:elasticbeanstalk:application:environment':
                    env_vars = option.get('Value', '{}')
                    break
            if env_vars:
                break
                
        if env_vars:
            print("\n=== Environment Variables ===")
            for key, value in json.loads(env_vars).items():
                if any(secret in key.lower() for secret in ['password', 'secret', 'key', 'token']):
                    print(f"{key}: ******")
                else:
                    print(f"{key}: {value}")
    except Exception as e:
        print(f"Error parsing configuration: {e}")
    
    # Check endpoint health
    try:
        print("\n=== Endpoint Health Check ===")
        env_url = run_command(f"aws elasticbeanstalk describe-environments --environment-names {env_name} --region {region} --query 'Environments[0].CNAME' --output text")
        
        if env_url:
            # Try to access the health endpoint
            health_url = f"https://{env_url}/health/"
            print(f"Checking health endpoint: {health_url}")
            
            try:
                response = requests.get(health_url, timeout=10)
                print(f"Status code: {response.status_code}")
                print("Response:")
                try:
                    print(json.dumps(response.json(), indent=2))
                except:
                    print(response.text[:500])  # Print first 500 chars if not JSON
            except requests.exceptions.RequestException as e:
                print(f"Error connecting to health endpoint: {e}")
    except Exception as e:
        print(f"Error checking endpoint health: {e}")
    
    print("\n=== Logs ===")
    print("To fetch the latest logs, run:")
    print(f"eb logs {env_name}")
    
    print("\n=== Next Steps ===")
    print("1. Check the logs for application errors")
    print("2. Verify that all required environment variables are set correctly")
    print("3. Check that the database connection is working")
    print("4. Consider deploying with --debug option: eb deploy --debug")

if __name__ == "__main__":
    main()
