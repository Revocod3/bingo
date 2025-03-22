from rest_framework import serializers
from .models import Event, BingoCard, Number, TestCoinBalance, CardPurchase

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class BingoCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BingoCard
        fields = '__all__'

class NumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Number
        fields = '__all__'

class TestCoinBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCoinBalance
        fields = ['id', 'user', 'balance', 'last_updated']
        read_only_fields = ['last_updated']

class CardPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardPurchase
        fields = ['id', 'user', 'event', 'cards_owned', 'purchase_date', 'last_modified']
        read_only_fields = ['purchase_date', 'last_modified']

class CardPurchaseRequestSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=20)  # Limit purchases to 20 cards at once

class CardPurchaseResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    new_balance = serializers.IntegerField()
    cards = BingoCardSerializer(many=True, required=False)
    message = serializers.CharField(required=False)

class BingoClaimRequestSerializer(serializers.Serializer):
    card_id = serializers.IntegerField()
    pattern = serializers.CharField(required=False, default='bingo')

class BingoClaimResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)
    card = BingoCardSerializer(required=False)