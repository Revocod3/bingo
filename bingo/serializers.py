from rest_framework import serializers
from .models import Event, BingoCard, Number

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