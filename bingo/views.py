from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Event, BingoCard, Number
from .serializers import EventSerializer, BingoCardSerializer, NumberSerializer
import random
import logging
import os
import sys

logger = logging.getLogger(__name__)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
    def perform_create(self, serializer):
        try:
            serializer.save()
            logger.info("Event created successfully")
        except Exception as e:
            logger.error(f"Error creating event: {str(e)}")
            raise

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
        try:
            card = self.get_object()
            number = request.data.get('number')
            
            if not number:
                return Response({'error': 'Number is required'}, status=status.HTTP_400_BAD_REQUEST)
                
            # Logic to mark a number on the bingo card
            logger.info(f"Marking number {number} on card {pk}")
            return Response({'status': 'number marked'})
        except Exception as e:
            logger.error(f"Error marking number: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NumberViewSet(viewsets.ModelViewSet):
    queryset = Number.objects.all()
    serializer_class = NumberSerializer
    
    def perform_create(self, serializer):
        try:
            logger.info("Creating new number")
            serializer.save()
            logger.info("Number created successfully")
        except Exception as e:
            logger.error(f"Error creating number: {str(e)}")
            raise
    
    @action(detail=False, methods=['get'])
    def by_event(self, request):
        """List numbers for a specific event"""
        try:
            event_id = request.query_params.get('event_id')
            if not event_id:
                return Response({"error": "event_id query parameter is required"}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            numbers = Number.objects.filter(event_id=event_id)
            serializer = self.get_serializer(numbers, many=True)
            logger.info(f"Retrieved {len(numbers)} numbers for event {event_id}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching numbers by event: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def draw(self, request):
        """Draw a random number that hasn't been drawn yet"""
        try:
            # Log environment variables to help debug connection issues
            logger.info(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
            logger.info(f"Database host: {os.environ.get('AWS_DB_HOST', 'Not set')}")
            
            # Logic to draw a random number
            numbers = Number.objects.filter(drawn=False)
            logger.info(f"Found {numbers.count()} undrawn numbers")
            if numbers.exists():
                number = random.choice(numbers)
                number.drawn = True
                number.save()
                logger.info(f"Drew number {number.value}")
                return Response(NumberSerializer(number).data)
            logger.warning("No more numbers available to draw")
            return Response({'error': 'No more numbers available'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error drawing number: {str(e)}", exc_info=True)
            return Response({
                'error': f"Failed to draw number: {str(e)}",
                'details': {
                    'python_version': sys.version,
                    'env_settings_module': os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set'),
                    'env_db_host': os.environ.get('AWS_DB_HOST', 'Not set'),
                    'env_db_name': os.environ.get('AWS_DB_NAME', 'Not set'),
                    'env_db_user': os.environ.get('AWS_DB_USER', 'Not set')
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)