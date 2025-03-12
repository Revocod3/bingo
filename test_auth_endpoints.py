#!/usr/bin/env python
"""
Script to test authentication endpoints manually.
Run this script from the command line to test the auth flow.
"""
import requests
import argparse

def main():
    parser = argparse.ArgumentParser(description='Test authentication endpoints')
    parser.add_argument('--host', default='http://localhost:8000', help='API host URL')
    parser.add_argument('--email', default='test@example.com', help='Email for registration')
    args = parser.parse_args()
    
    base_url = args.host
    email = args.email
    
    print("\n=== AUTHENTICATION ENDPOINT TEST ===\n")
    
    # 1. Register a new user
    print("1. Testing user registration...")
    register_url = f"{base_url}/api/auth/register/"
    register_data = {
        "email": email,
        "password": "Test@123456",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(register_url, json=register_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}\n")
        
        if response.status_code != 201:
            print("Registration failed. Exiting test.")
            return
    except Exception as e:
        print(f"Request failed: {e}")
        return

    # 2. Ask for verification code (check your console/email)
    verification_code = input("Enter the verification code from your console or email: ")
    
    # 3. Verify email
    print("\n2. Testing email verification...")
    verify_url = f"{base_url}/api/auth/verify-email/"
    verify_data = {
        "email": email,
        "verification_code": verification_code
    }
    
    try:
        response = requests.post(verify_url, json=verify_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}\n")
        
        if response.status_code != 200:
            print("Email verification failed. Exiting test.")
            return
    except Exception as e:
        print(f"Request failed: {e}")
        return
    
    # 4. Get JWT token
    print("3. Testing JWT token acquisition...")
    token_url = f"{base_url}/api/auth/token/"
    token_data = {
        "email": email,
        "password": "Test@123456"
    }
    
    try:
        response = requests.post(token_url, json=token_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access")
            refresh_token = token_data.get("refresh")
            print(f"Access Token: {access_token[:20]}... (truncated)")
            print(f"Refresh Token: {refresh_token[:20]}... (truncated)\n")
        else:
            print(f"Response: {response.text}\n")
            print("Token acquisition failed. Exiting test.")
            return
    except Exception as e:
        print(f"Request failed: {e}")
        return
    
    # 5. Test protected endpoint
    print("4. Testing protected endpoint access...")
    protected_url = f"{base_url}/api/users/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(protected_url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}... (truncated)\n")
    except Exception as e:
        print(f"Request failed: {e}")
    
    print("Authentication flow test completed!")

if __name__ == "__main__":
    main()
