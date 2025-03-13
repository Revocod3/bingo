from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Event, BingoCard, Number
from .serializers import EventSerializer, BingoCardSerializer, NumberSerializer
import random

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
    def perform_create(self, serializer):
        serializer.save()

class BingoCardViewSet(viewsets.ModelViewSet):
    queryset = BingoCard.objects.all()
    serializer_class = BingoCardSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a unique bingo card"""
        # Extract event_id from request data
        event_id = request.data.get('event_id')
        if not event_id:
            return Response({"error": "event_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Here you would implement your card generation logic
        # For now, creating a basic card
        card = BingoCard.objects.create(event=event)
        
        return Response(BingoCardSerializer(card).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_number(self, request, pk=None):
        card = self.get_object()
        number = request.data.get('number')
        
        # Logic to mark a number on the bingo card
        return Response({'status': 'number marked'})

class NumberViewSet(viewsets.ModelViewSet):
    queryset = Number.objects.all()
    serializer_class = NumberSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_event(self, request):
        """List numbers for a specific event"""
        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response({"error": "event_id query parameter is required"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        numbers = Number.objects.filter(event_id=event_id)
        serializer = self.get_serializer(numbers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def draw(self, request):
        # Logic to draw a random number
        numbers = Number.objects.filter(drawn=False)
        if numbers.exists():
            number = random.choice(numbers)
            number.drawn = True
            number.save()
            return Response(NumberSerializer(number).data)
        return Response({'error': 'No more numbers available'}, status=status.HTTP_404_NOT_FOUND)