from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Event, BingoCard, Number, TestCoinBalance, CardPurchase
from .serializers import (
    EventSerializer, BingoCardSerializer, NumberSerializer,
    TestCoinBalanceSerializer, CardPurchaseSerializer,
    CardPurchaseRequestSerializer,
)
import random
import logging
import os
import sys
import hashlib
import json
from django.db import transaction
from django.core.cache import cache
import uuid

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
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def purchase(self, request):
        """Purchase bingo cards for an event using test coins"""
        serializer = CardPurchaseRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        event_id = serializer.validated_data['event_id']
        quantity = serializer.validated_data['quantity']
        user = request.user
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Cost per card - could be dynamic based on event
        cost_per_card = 10
        total_cost = cost_per_card * quantity
        
        # Use a Redis lock to prevent race conditions
        lock_id = f"purchase_lock:{user.id}"
        lock_timeout = 60  # 1 minute timeout
        
        # Try to acquire the lock
        lock_acquired = cache.add(lock_id, "locked", lock_timeout)
        if not lock_acquired:
            return Response({"error": "Another purchase is in progress"}, 
                           status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        try:
            # Transaction to ensure atomicity
            with transaction.atomic():
                # Get or create test coin balance
                balance, created = TestCoinBalance.objects.get_or_create(user=user)
                
                if balance.balance < total_cost:
                    return Response({
                        "success": False,
                        "message": f"Insufficient test coins. Need {total_cost}, have {balance.balance}."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Deduct coins with F() to prevent race conditions
                success, result = TestCoinBalance.deduct_coins(user.id, total_cost)
                if not success:
                    return Response({
                        "success": False,
                        "message": result
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get or create card purchase record
                card_purchase, created = CardPurchase.objects.get_or_create(
                    user=user,
                    event=event,
                    defaults={"cards_owned": 0}
                )
                
                # Update cards owned
                card_purchase.cards_owned += quantity
                card_purchase.save()
                
                # Generate unique bingo cards
                cards = []
                for _ in range(quantity):
                    # Generate a unique card
                    card_numbers = self._generate_bingo_card_numbers()
                    
                    # Create a unique hash for the card
                    card_hash = hashlib.sha256(
                        f"{user.id}-{event.id}-{json.dumps(card_numbers)}-{uuid.uuid4()}".encode()
                    ).hexdigest()
                    
                    # Create the card
                    card = BingoCard.objects.create(
                        event=event,
                        user=user,
                        numbers=card_numbers,
                        is_winner=False,
                        hash=card_hash
                    )
                    cards.append(card)
                
                # Return the response
                return Response({
                    "success": True,
                    "new_balance": result.balance,
                    "cards": BingoCardSerializer(cards, many=True).data,
                    "message": f"Successfully purchased {quantity} cards"
                })
                
        except Exception as e:
            logger.error(f"Error during card purchase: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": f"Purchase failed: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Release the lock
            cache.delete(lock_id)
    
    def _generate_bingo_card_numbers(self):
        """Generate a random set of numbers for a bingo card"""
        # Standard 5x5 bingo card with free space in center
        card = {
            "B": sorted(random.sample(range(1, 16), 5)),
            "I": sorted(random.sample(range(16, 31), 5)),
            "N": sorted(random.sample(range(31, 46), 5)),
            "G": sorted(random.sample(range(46, 61), 5)),
            "O": sorted(random.sample(range(61, 76), 5)),
            "free_space": {"column": "N", "row": 2}  # Center position
        }
        return card

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

class TestCoinBalanceViewSet(viewsets.ModelViewSet):
    queryset = TestCoinBalance.objects.all()
    serializer_class = TestCoinBalanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users should only see their own balance
        return TestCoinBalance.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_balance(self, request):
        """Get the current user's test coin balance"""
        balance, created = TestCoinBalance.objects.get_or_create(
            user=request.user,
            defaults={"balance": 100}
        )
        return Response({
            "balance": balance.balance,
            "last_updated": balance.last_updated
        })

class CardPurchaseViewSet(viewsets.ModelViewSet):
    queryset = CardPurchase.objects.all()
    serializer_class = CardPurchaseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users should only see their own purchases
        return CardPurchase.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_purchases(self, request):
        """Get the current user's card purchases"""
        event_id = request.query_params.get('event_id')
        
        queryset = self.get_queryset()
        if event_id:
            queryset = queryset.filter(event_id=event_id)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)