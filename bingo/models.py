from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Event(models.Model):
    name = models.CharField(max_length=100)
    prize = models.DecimalField(max_digits=10, decimal_places=2)
    start = models.DateTimeField()

class BingoCard(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    numbers = models.JSONField()
    is_winner = models.BooleanField(default=False)
    hash = models.CharField(max_length=64, unique=True)

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Number(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='numbers')
    value = models.IntegerField()
    called_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-called_at']
        unique_together = ['event', 'value']

    def __str__(self):
        return f"{self.value} - {self.event}"