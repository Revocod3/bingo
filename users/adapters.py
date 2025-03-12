from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from bingo.models import User, Wallet

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        Override the save_user method to set custom attributes
        and perform actions on user save
        """
        user = super().save_user(request, user, form, commit=False)
        user.is_email_verified = True  # Auto verify email for standard signup if desired
        
        if commit:
            user.save()
            # Create a wallet for the user
            Wallet.objects.get_or_create(user=user)
            
        return user

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Called after successful authentication but before login and redirect
        """
        # Get or create user from social account details
        if sociallogin.is_existing:
            return
        
        # Auto connect to an existing account with the same email address
        if sociallogin.account.provider in ['facebook', 'google'] and sociallogin.account.extra_data.get('email'):
            try:
                user_email = sociallogin.account.extra_data.get('email').lower()
                existing_user = User.objects.get(email=user_email)
                sociallogin.connect(request, existing_user)
            except self.get_model('CustomUser').DoesNotExist:
                pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        Override the save_user method to set custom attributes
        """
        user = super().save_user(request, sociallogin, form)
        
        # Set email as verified for social login
        user.is_email_verified = True
        user.save()
        
        # Create a wallet for the user
        Wallet.objects.get_or_create(user=user)
        
        return user
