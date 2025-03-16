from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta

User = get_user_model()

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.verify_email_url = reverse('verify_email')
        self.resend_verification_url = reverse('resend_verification')
        self.token_url = reverse('token_obtain_pair')
        
        # Test user data
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'strongpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        # Create a verified user for token tests
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            password='verifiedpass123',
            first_name='Verified',
            last_name='User',
            is_email_verified=True
        )

    def test_user_registration(self):
        """Test user registration endpoint"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Confirm user creation in the database
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
        
        # Verify a verification code has been generated
        user = User.objects.get(email=self.user_data['email'])
        self.assertIsNotNone(user.verification_code)
        self.assertIsNotNone(user.verification_code_created_at)
        self.assertFalse(user.is_email_verified)

    def test_email_verification(self):
        """Test email verification endpoint"""
        # Create an unverified user with a verification code
        verification_code = '123456'
        user = User.objects.create_user(
            email='unverified@example.com',
            password='testpass123',
            verification_code=verification_code,
            verification_code_created_at=timezone.now()
        )
        
        verification_data = {
            'email': 'unverified@example.com',
            'verification_code': verification_code
        }
        response = self.client.post(self.verify_email_url, verification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Confirm the user is now verified and the verification code is cleared
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertIsNone(user.verification_code)

    def test_expired_verification_code(self):
        """Test expired verification code rejection"""
        verification_code = '123456'
        expired_time = timezone.now() - timedelta(hours=25)
        user = User.objects.create_user(
            email='expired@example.com',
            password='testpass123',
            verification_code=verification_code,
            verification_code_created_at=expired_time
        )
        
        verification_data = {
            'email': 'expired@example.com',
            'verification_code': verification_code
        }
        response = self.client.post(self.verify_email_url, verification_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Ensure the user remains unverified
        user.refresh_from_db()
        self.assertFalse(user.is_email_verified)

    def test_resend_verification(self):
        """Test resend verification endpoint"""
        old_code = '111111'
        user = User.objects.create_user(
            email='resend@example.com',
            password='testpass123',
            verification_code=old_code,
            verification_code_created_at=timezone.now() - timedelta(hours=5)
        )
        
        resend_data = {'email': 'resend@example.com'}
        response = self.client.post(self.resend_verification_url, resend_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify that the verification code has been updated
        user.refresh_from_db()
        self.assertNotEqual(user.verification_code, old_code)
        self.assertIsNotNone(user.verification_code_created_at)

    def test_token_authentication(self):
        """Test JWT token generation for verified users"""
        token_data = {
            'email': 'verified@example.com',
            'password': 'verifiedpass123'
        }
        response = self.client.post(self.token_url, token_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_invalid_login(self):
        """Test invalid login credentials"""
        invalid_data = {
            'email': 'verified@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.token_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_unverified_login_blocked(self):
        """Test that unverified users cannot login"""
        # Create an unverified user
        unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='testpass123',
            verification_code='123456',
            verification_code_created_at=timezone.now(),
            is_email_verified=False
        )
        
        token_data = {
            'email': 'unverified@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.token_url, token_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('verification', str(response.content).lower())
        
    def test_bypass_email_verification_disabled(self):
        """Test that the BYPASS_EMAIL_VERIFICATION setting actually prevents auto-verification"""
        # This test depends on the BYPASS_EMAIL_VERIFICATION setting being False
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to login with the newly registered user (should fail as email isn't verified)
        token_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.token_url, token_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
