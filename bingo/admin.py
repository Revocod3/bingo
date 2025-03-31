from django.contrib import admin
from .models import CardPurchase, Event, BingoCard, Number, TestCoinBalance, Wallet, WinningPattern, DepositRequest

# Register your models here.
admin.site.register(Event)
admin.site.register(BingoCard)
admin.site.register(Number)
admin.site.register(WinningPattern)
admin.site.register(Wallet)
admin.site.register(TestCoinBalance)
admin.site.register(CardPurchase)
admin.site.register(DepositRequest)
