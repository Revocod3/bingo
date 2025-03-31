from rest_framework import serializers
from .models import DepositRequest, Event, BingoCard, Number, SystemConfig, TestCoinBalance, CardPurchase, WinningPattern

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class BingoCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BingoCard
        fields = ['id', 'event', 'numbers', 'is_winner', 'created_at']
        read_only_fields = ['hash']  # Mark hash as read-only to prevent validation issues

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
    card_id = serializers.UUIDField()  # Changed from IntegerField to UUIDField to match BingoCard.id
    pattern_name = serializers.CharField(required=False, default='bingo')

class WinningPatternDetailSerializer(serializers.Serializer):
    pattern_name = serializers.CharField()
    display_name = serializers.CharField(required=False)
    positions = serializers.ListField(child=serializers.IntegerField())
    matched_numbers = serializers.ListField(child=serializers.CharField(), required=False)

class BingoClaimResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    card = serializers.DictField(required=False)  # Change to DictField to avoid validation
    winning_pattern = WinningPatternDetailSerializer(required=False)
    event_id = serializers.UUIDField(required=False)
    called_numbers = serializers.ListField(child=serializers.IntegerField(), required=False)

class WinningPatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = WinningPattern
        fields = ['id', 'name', 'display_name', 'positions', 'is_active', 'created_at', 'updated_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def validate_positions(self, positions):
        """Validate that positions are in the correct format and within range"""
        if not isinstance(positions, list):
            raise serializers.ValidationError("Positions must be an array")
        
        if len(positions) == 0:
            raise serializers.ValidationError("Positions cannot be empty")
            
        for pos in positions:
            if not isinstance(pos, int):
                raise serializers.ValidationError("Each position must be an integer")
            if pos < 0 or pos > 24:
                raise serializers.ValidationError("Positions must be between 0 and 24")
                
        return positions

class WinningPatternCreateSerializer(WinningPatternSerializer):
    class Meta(WinningPatternSerializer.Meta):
        read_only_fields = ['id', 'created_at', 'updated_at']

class DepositRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DepositRequest
        fields = ['id', 'user', 'amount', 'unique_code', 'reference', 
                  'status', 'status_display', 'created_at', 'updated_at', 
                  'approved_by', 'admin_notes']
        read_only_fields = ['id', 'unique_code', 'status', 'created_at', 
                           'updated_at', 'approved_by']

class DepositRequestCreateSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1, max_value=1000)

class DepositConfirmSerializer(serializers.Serializer):
    unique_code = serializers.CharField(max_length=6)
    reference = serializers.CharField(max_length=50)

class DepositAdminActionSerializer(serializers.Serializer):
    admin_notes = serializers.CharField(required=False, allow_blank=True)

class SystemConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfig
        fields = ['card_price', 'last_updated']
        read_only_fields = ['last_updated']

class CardPriceUpdateSerializer(serializers.Serializer):
    card_price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)