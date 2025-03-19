from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db import transaction
import uuid

User = get_user_model()

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    prize = models.DecimalField(max_digits=10, decimal_places=2)
    start = models.DateTimeField()
    end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class BingoCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    numbers = models.JSONField()
    is_winner = models.BooleanField(default=False)
    hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Number(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='numbers')
    value = models.IntegerField()
    called_at = models.DateTimeField(auto_now_add=True)
    drawn = models.BooleanField(default=True)  # Track if this number has been drawn

    class Meta:
        ordering = ['-called_at']
        unique_together = ['event', 'value']

    def __str__(self):
        return f"{self.value} - {self.event}"

class TestCoinBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='test_coins')
    balance = models.PositiveIntegerField(default=100)  # Start with 100 test coins
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'test_coin_balance'
        indexes = [
            models.Index(fields=['user']),  # Index for quick user lookups
        ]
    
    def __str__(self):
        return f"{self.user.email}: {self.balance} coins"
    
    @classmethod
    @transaction.atomic
    def deduct_coins(cls, user_id, amount):
        """Safely deduct coins with optimistic concurrency control"""
        # Select for update to prevent race conditions
        balance = cls.objects.select_for_update().get(user_id=user_id)
        if balance.balance < amount:
            return False, "Insufficient coins"
        
        balance.balance = F('balance') - amount
        balance.save()
        balance.refresh_from_db()
        return True, balance

class CardPurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='card_purchases')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='card_purchases')
    cards_owned = models.PositiveIntegerField(default=0)
    purchase_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'card_purchases'
        unique_together = ['user', 'event']  # Each user can have one purchase record per event
        indexes = [
            models.Index(fields=['user', 'event']),  # Composite index for fast lookups
        ]
    
    def __str__(self):
        return f"{self.user.email}: {self.cards_owned} cards for {self.event.name}"