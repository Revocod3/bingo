from rest_framework import viewsets
from .models import Event, BingoCard
from .serializers import EventSerializer, BingoCardSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class BingoCardViewSet(viewsets.ModelViewSet):
    queryset = BingoCard.objects.all()
    serializer_class = BingoCardSerializer