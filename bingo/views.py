from jsonschema import ValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from .models import Event, BingoCard, Number, PaymentMethod, TestCoinBalance, CardPurchase, WinningPattern, DepositRequest, SystemConfig, RatesConfig
from .serializers import (
    EventSerializer, BingoCardSerializer, NumberSerializer, PaymentMethodCreateUpdateSerializer, PaymentMethodSerializer,
    TestCoinBalanceSerializer, CardPurchaseSerializer,
    CardPurchaseRequestSerializer, BingoClaimRequestSerializer, BingoClaimResponseSerializer,
    WinningPatternSerializer, DepositRequestSerializer, DepositRequestCreateSerializer,
    DepositConfirmSerializer, DepositAdminActionSerializer, CardPriceUpdateSerializer, SystemConfigSerializer,
    EmailCardsSerializer, RatesConfigSerializer, RatesUpdateSerializer
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
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .permissions import IsSellerPermission

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
    
    @action(detail=True, methods=['get'])
    def patterns(self, request, pk=None):
        """Get all winning patterns allowed for this event"""
        event = self.get_object()
        
        # If the event has specific patterns allowed, return those
        if event.allowed_patterns.exists():
            patterns = event.allowed_patterns.filter(is_active=True)
        else:
            # Otherwise return all active patterns
            patterns = WinningPattern.objects.filter(is_active=True)
        
        serializer = WinningPatternSerializer(patterns, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_patterns(self, request, pk=None):
        """Set the allowed patterns for this event"""
        event = self.get_object()
        pattern_ids = request.data.get('pattern_ids', [])
        
        if not isinstance(pattern_ids, list):
            return Response({"error": "pattern_ids must be an array"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the patterns
            patterns = WinningPattern.objects.filter(id__in=pattern_ids)
            
            # Clear existing patterns and set the new ones
            event.allowed_patterns.clear()
            event.allowed_patterns.add(*patterns)
            
            return Response({
                "success": True,
                "patterns": WinningPatternSerializer(patterns, many=True).data
            })
        except Exception as e:
            logger.error(f"Error setting patterns for event: {str(e)}")
            return Response({"error": f"Failed to set patterns: {str(e)}"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def add_pattern(self, request, pk=None):
        """Add a pattern to the allowed patterns for this event"""
        event = self.get_object()
        pattern_id = request.data.get('pattern_id')
        
        if not pattern_id:
            return Response({"error": "pattern_id is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            pattern = WinningPattern.objects.get(id=pattern_id)
            event.allowed_patterns.add(pattern)
            
            return Response({
                "success": True,
                "message": f"Pattern '{pattern.display_name}' added to event '{event.name}'"
            })
        except WinningPattern.DoesNotExist:
            return Response({"error": "Pattern not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error adding pattern to event: {str(e)}")
            return Response({"error": f"Failed to add pattern: {str(e)}"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def remove_pattern(self, request, pk=None):
        """Remove a pattern from the allowed patterns for this event"""
        event = self.get_object()
        pattern_id = request.data.get('pattern_id')
        
        if not pattern_id:
            return Response({"error": "pattern_id is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            pattern = WinningPattern.objects.get(id=pattern_id)
            event.allowed_patterns.remove(pattern)
            
            return Response({
                "success": True,
                "message": f"Pattern '{pattern.display_name}' removed from event '{event.name}'"
            })
        except WinningPattern.DoesNotExist:
            return Response({"error": "Pattern not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error removing pattern from event: {str(e)}")
            return Response({"error": f"Failed to remove pattern: {str(e)}"}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BingoCardViewSet(viewsets.ModelViewSet):
    serializer_class = BingoCardSerializer
    permission_classes = [IsAuthenticated]
    queryset = BingoCard.objects.all()  # Add this line for router registration
    
    def get_queryset(self):
        """Ensure users can only see their own cards"""
        return BingoCard.objects.filter(user=self.request.user)
    
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
        
        # Get cost per card from system configuration
        cost_per_card = float(SystemConfig.get_card_price())
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
        """
        Generate a valid bingo card with numbers in the correct range for each column.
        Card format: ["B1", "B3", "I16", "N31", "N0", ...] (25 elements)
        
        Numbers are arranged in column-first order to match the standard 5x5 grid:
        0  5  10 15 20 (B column)
        1  6  11 16 21 (I column)
        2  7  12 17 22 (N column with free space at 12)
        3  8  13 18 23 (G column)
        4  9  14 19 24 (O column)
        """
        # B: 1-15, I: 16-30, N: 31-45, G: 46-60, O: 61-75
        columns = {
            'B': list(range(1, 16)),    # 1-15
            'I': list(range(16, 31)),   # 16-30
            'N': list(range(31, 46)),   # 31-45
            'G': list(range(46, 61)),   # 46-60
            'O': list(range(61, 76))    # 61-75
        }
        
        # Shuffle each column's numbers
        for col in columns.keys():
            random.shuffle(columns[col])
        
        # Initialize empty card
        card_numbers = [""] * 25
        
        # Populate card by column
        for col_idx, letter in enumerate("BINGO"):
            col_values = columns[letter][:5]  # Get 5 numbers for this column
            
            # Place numbers in the grid
            for row_idx in range(5):
                position = row_idx * 5 + col_idx
                
                # Handle the free space in the middle (position 12)
                if position == 12:  # Center cell
                    card_numbers[position] = "N0"  # Free space
                else:
                    card_numbers[position] = f"{letter}{col_values[row_idx]}"
        
        return card_numbers

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def claim(self, request):
        """Claim a bingo win for a card"""
        serializer = BingoClaimRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        card_id = serializer.validated_data['card_id']
        # Make pattern optional - if not provided, we'll check all patterns
        pattern_name = serializer.validated_data.get('pattern', 'bingo')
        user = request.user
        
        try:
            # Get the card and ensure it belongs to the user
            try:
                card = BingoCard.objects.get(id=card_id, user=user)
            except BingoCard.DoesNotExist:
                response_data = {
                    "success": False,
                    "message": "Card not found or doesn't belong to you"
                }
                response_serializer = BingoClaimResponseSerializer(data=response_data)
                response_serializer.is_valid(raise_exception=True)
                return Response(response_serializer.data, status=status.HTTP_404_NOT_FOUND)
            
            # Get all called numbers for this event
            called_numbers = set(Number.objects.filter(
                event_id=card.event_id
            ).values_list('value', flat=True))
            
            # Check if the pattern is completed with called numbers
            from .win_patterns import check_win_pattern
            # Check the specified pattern or 'bingo' if none provided
            is_winner, win_details = check_win_pattern(card.numbers, called_numbers, pattern_name)
            
            if is_winner:
                # Mark the card as a winner if not already marked
                if not card.is_winner:
                    card.is_winner = True
                    card.save()
                
                # Serialize card separately first
                card_data = BingoCardSerializer(card).data
                
                response_data = {
                    "success": True,
                    "message": f"Congratulations! Valid bingo claim with pattern {win_details['pattern_name']}!",
                    "card": card_data,  # Use pre-serialized data
                    "winning_pattern": win_details
                }
                response_serializer = BingoClaimResponseSerializer(data=response_data)
                response_serializer.is_valid(raise_exception=True)
                return Response(response_serializer.data)
            else:
                response_data = {
                    "success": False,
                    "message": "Invalid winning pattern or not all numbers have been called"
                }
                response_serializer = BingoClaimResponseSerializer(data=response_data)
                response_serializer.is_valid(raise_exception=True)
                return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error verifying win: {str(e)}", exc_info=True)
            response_data = {
                "success": False,
                "message": f"Error verifying win: {str(e)}"
            }
            response_serializer = BingoClaimResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def verify_pattern(self, request, pk=None):
        """Verify if a specific pattern is completed on a card"""
        try:
            card = self.get_object()
            pattern_name = request.query_params.get('pattern', 'bingo')
            
            # Get all called numbers for this event
            called_numbers = list(Number.objects.filter(
                event_id=card.event_id
            ).values_list('value', flat=True))
            
            # Check if the pattern is completed with called numbers
            from .win_patterns import check_win_pattern
            is_winner, win_details = check_win_pattern(card.numbers, set(called_numbers), pattern_name)
            
            # Get the pattern display name from the database
            pattern_display_name = None
            if win_details and 'pattern_name' in win_details:
                try:
                    pattern = WinningPattern.objects.get(name=win_details['pattern_name'])
                    pattern_display_name = pattern.display_name
                except WinningPattern.DoesNotExist:
                    pattern_display_name = win_details['pattern_name'].replace('_', ' ').title()
                    
            if win_details and pattern_display_name:
                win_details['display_name'] = pattern_display_name
            
            return Response({
                "success": is_winner,
                "card_id": card.id,
                "event_id": card.event_id,
                "called_numbers": called_numbers,
                "winning_pattern": win_details if is_winner else None,
                "message": "Pattern completed!" if is_winner else "Pattern not completed yet"
            })
            
        except Exception as e:
            logger.error(f"Error verifying pattern: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": f"Error verifying pattern: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def status(self, request, pk=None):
        """Get comprehensive status of a card, including all pattern progress"""
        try:
            card = self.get_object()
            
            # Get all called numbers for this event
            called_numbers = list(Number.objects.filter(
                event_id=card.event_id
            ).values_list('value', flat=True))
            
            # Get all patterns that apply to this event
            event = card.event
            if (event.allowed_patterns.exists()):
                patterns = event.allowed_patterns.filter(is_active=True)
            else:
                patterns = WinningPattern.objects.filter(is_active=True)
            
            # Check progress for each pattern
            pattern_status = []
            from .win_patterns import parse_card_numbers
            
            # Parse the card for pattern checking
            card_flat = parse_card_numbers(card.numbers)
            
            for pattern in patterns:
                # Count how many positions are matched
                matched_positions = []
                missing_positions = []
                
                for pos in pattern.positions:
                    if 0 <= pos < len(card_flat):
                        card_value = card_flat[pos]
                        if card_value == 0 or card_value in called_numbers:  # Free space or called number
                            matched_positions.append(pos)
                        else:
                            missing_positions.append(pos)
                
                # Calculate completion percentage
                total_positions = len(pattern.positions)
                matched_count = len(matched_positions)
                completion_pct = (matched_count / total_positions) * 100 if total_positions > 0 else 0
                
                # Get missing numbers
                missing_numbers = []
                for pos in missing_positions:
                    if 0 <= pos < len(card_flat) and card_flat[pos] > 0:
                        missing_numbers.append(card_flat[pos])
                
                pattern_status.append({
                    'pattern_id': pattern.id,
                    'pattern_name': pattern.name,
                    'display_name': pattern.display_name,
                    'matched': matched_count,
                    'total': total_positions,
                    'completion_percentage': round(completion_pct, 1),
                    'is_complete': matched_count == total_positions,
                    'missing_numbers': sorted(missing_numbers)
                })
            
            # Format results in descending order of completion
            pattern_status.sort(key=lambda x: x['completion_percentage'], reverse=True)
            
            # Format the card for display
            from .templates import format_card_for_display
            card_display = format_card_for_display(card.numbers)
            
            return Response({
                'card_id': card.id,
                'event_id': card.event_id,
                'event_name': card.event.name,
                'is_winner': card.is_winner,
                'called_numbers_count': len(called_numbers),
                'called_numbers': sorted(called_numbers),
                'card_display': card_display,
                'patterns': pattern_status
            })
            
        except Exception as e:
            logger.error(f"Error getting card status: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f"Error getting card status: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get', 'post'], permission_classes=[IsAuthenticated])
    def card_price(self, request):
        """Get or update the price of bingo cards (staff only for updates)"""
        if request.method == 'GET':
            # Anyone can get the current price
            price = SystemConfig.get_card_price()
            return Response({"card_price": price})
        
        # For POST, only staff can update the price
        if not request.user.is_staff:
            return Response({"error": "Staff permissions required"}, 
                            status=status.HTTP_403_FORBIDDEN)
        
        serializer = CardPriceUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            price = serializer.validated_data['card_price']
            config = SystemConfig.update_card_price(price, request.user)
            return Response({
                "success": True,
                "message": f"Card price updated to {price}",
                "card_price": config.card_price
            })
        except Exception as e:
            logger.error(f"Error updating card price: {str(e)}")
            return Response({
                "success": False,
                "message": f"Failed to update price: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsSellerPermission])
    def generate_bulk(self, request):
        """Generate multiple bingo cards for sellers"""
        quantity = request.data.get('quantity', 1)
        event_id = request.data.get('event_id')
        
        # Validate input
        if not event_id:
            return Response({"error": "event_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
            return Response({"error": "quantity must be a number between 1 and 100"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate multiple cards
        cards = []
        for _ in range(quantity):
            card_numbers = self._generate_bingo_card_numbers()
            cards.append({
                'numbers': card_numbers,
                'event_id': event_id
            })
        
        # Return the generated cards
        return Response({
            "success": True,
            "cards": cards,
            "message": f"Successfully generated {quantity} cards"
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsSellerPermission])
    def download_pdf(self, request):
        """Download generated cards as PDF"""
        cards = request.data.get('cards', [])
        event_id = request.data.get('event_id')
        
        if not cards or not event_id:
            return Response({"error": "cards and event_id are required"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate PDF with cards
        pdf = self._generate_cards_pdf(cards, event)
        
        # Create response with PDF
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bingo_cards_{event.name}.pdf"'
        
        return response
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsSellerPermission])
    def email_cards(self, request):
        """Send generated cards to an email"""
        serializer = EmailCardsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        event_id = serializer.validated_data['event_id']
        cards = serializer.validated_data['cards']
        subject = serializer.validated_data['subject']
        message = serializer.validated_data['message']
        
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Generate PDF with cards
        pdf = self._generate_cards_pdf(cards, event)
        
        # Create HTML content
        html_message = render_to_string(
            'email/bingo_cards_email.html',
            {
                'event_name': event.name,
                'event_date': event.start_date.strftime('%Y-%m-%d %H:%M'),
                'event_description': event.description,
                'message': message,
                'cards_count': len(cards)
            }
        )
        
        # Send email with PDF attached
        try:
            email_message = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            
            # Set HTML content type
            email_message.content_subtype = "html"
            
            # Attach the PDF
            email_message.attach(f'bingo_cards_{event.name}.pdf', pdf, 'application/pdf')
            email_message.send()
            
            return Response({
                "success": True,
                "message": f"Bingo cards sent to {email} successfully"
            })
            
        except Exception as e:
            logger.error(f"Error sending bingo cards email: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "message": f"Failed to send email: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_cards_pdf(self, cards, event):
        """Generate a PDF with the given cards"""
        buffer = BytesIO()
        
        # Create the PDF object
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # For each card, create a table representation
        for i, card in enumerate(cards):
            elements.append(self._create_card_table(card['numbers'], i+1))
            
            # Add some space between cards
            if i < len(cards) - 1:
                elements.append(Spacer(1, 0.5*inch))
        
        # Build the PDF
        doc.build(elements)
        
        # Get the value of the BytesIO buffer
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf
    
    def _create_card_table(self, card_numbers, card_number):
        """Create a table representation of a bingo card for PDF"""
        styles = getSampleStyleSheet()
        
        # Create header for the card
        header = Paragraph(f"BINGO CARD #{card_number}", styles['Heading1'])
        
        # Create the data for the table
        table_data = [['B', 'I', 'N', 'G', 'O']]
        
        # Parse the card in standard format
        from .win_patterns import parse_card_numbers
        flat_card = parse_card_numbers(card_numbers)
        
        # Organize the flat card into a 5x5 grid
        for row in range(5):
            table_row = []
            for col in range(5):
                pos = row * 5 + col
                if pos < len(flat_card):
                    value = flat_card[pos]
                    # For the free space in the middle
                    if value == 0 and row == 2 and col == 2:
                        table_row.append("FREE")
                    else:
                        table_row.append(str(value))
                else:
                    table_row.append("")
            table_data.append(table_row)
        
        # Create the table
        table = Table(table_data, colWidths=[0.8*inch]*5, rowHeights=[0.4*inch] + [0.8*inch]*5)
        
        # Style the table
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (4, 0), colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('FONTSIZE', (0, 0), (4, 0), 16),
            ('FONTNAME', (0, 0), (4, 0), 'Helvetica-Bold'),
        ]))
        
        # Return both the header and the table
        return [header, Spacer(1, 0.2*inch), table]

class NumberViewSet(viewsets.ModelViewSet):
    queryset = Number.objects.all()
    serializer_class = NumberSerializer
    
    def perform_create(self, serializer):
        try:
            event_id = self.request.data.get('event_id')
            if not event_id:
                raise ValidationError("event_id is required")
                
            # Verify event exists
            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                raise ValidationError("Event not found")
                
            # Check if number already exists for this event
            value = self.request.data.get('value')
            if Number.objects.filter(event_id=event_id, value=value).exists():
                raise ValidationError("This number has already been called for this event")
                
            logger.info(f"Creating number {value} for event {event_id}")
            serializer.save(event=event)
            logger.info("Number created successfully")
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
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
    
    @action(detail=False, methods=['delete'])
    def delete_last(self, request):
        """Delete the last called number for a specific event"""
        try:
            event_id = request.query_params.get('event_id')
            if not event_id:
                return Response({"error": "event_id query parameter is required"}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Get the latest number for this event
                latest_number = Number.objects.filter(event_id=event_id).order_by('-called_at').first()
                
                if not latest_number:
                    return Response({"error": "No numbers found for this event"}, 
                                    status=status.HTTP_404_NOT_FOUND)
                
                # Delete the number
                latest_number.delete()
                logger.info(f"Deleted latest number for event {event_id}")
                
                return Response({"success": True, "message": "Latest number deleted successfully"})
        except Exception as e:
            logger.error(f"Error deleting latest number: {str(e)}", exc_info=True)
            return Response({"error": f"Failed to delete latest number: {str(e)}"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['delete'])
    def reset_event(self, request):
        """Reset all called numbers for a specific event"""
        try:
            event_id = request.query_params.get('event_id')
            if not event_id:
                return Response({"error": "event_id query parameter is required"}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Delete all numbers for this event
                deleted_count, _ = Number.objects.filter(event_id=event_id).delete()
                logger.info(f"Reset {deleted_count} numbers for event {event_id}")
                
                return Response({
                    "success": True, 
                    "message": f"Successfully reset {deleted_count} numbers for this event"
                })
        except Exception as e:
            logger.error(f"Error resetting event numbers: {str(e)}")
            return Response({"error": f"Failed to reset event numbers: {str(e)}"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

class WinningPatternViewSet(viewsets.ModelViewSet):
    queryset = WinningPattern.objects.all()
    serializer_class = WinningPatternSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Allow users to see all active patterns but only their own inactive patterns"""
        user = self.request.user
        if self.request.user.is_staff:
            return WinningPattern.objects.all()
        return WinningPattern.objects.filter(
            Q(is_active=True) | Q(created_by=user)
        )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active winning patterns"""
        active_patterns = WinningPattern.objects.filter(is_active=True)
        serializer = self.get_serializer(active_patterns, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def validate(self, request):
        """Validate if the given positions form a valid pattern"""
        positions = request.data.get('positions', [])
        
        if not isinstance(positions, list):
            return Response({"error": "Positions must be an array"}, status=status.HTTP_400_BAD_REQUEST)
            
        if not all(isinstance(pos, int) and 0 <= pos <= 24 for pos in positions):
            return Response({"error": "Each position must be an integer between 0 and 24"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check that the pattern includes at least 4 positions
        if len(positions) < 4:
            return Response({"error": "Pattern must include at least 4 positions"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check the pattern doesn't overlap with existing patterns
        existing_patterns = WinningPattern.objects.filter(is_active=True)
        for pattern in existing_patterns:
            if set(pattern.positions) == set(positions):
                return Response({
                    "valid": False,
                    "message": f"Pattern matches existing pattern: {pattern.display_name}"
                })
        
        return Response({
            "valid": True,
            "message": "Valid pattern positions"
        })

    @action(detail=False, methods=['get'])
    def with_positions_map(self, request):
        """Get active patterns with a positions map for frontend visualization"""
        # Get all active patterns
        active_patterns = WinningPattern.objects.filter(is_active=True)
        
        # Prepare response with additional position maps
        result = []
        for pattern in active_patterns:
            # Create a 5x5 grid of booleans representing the pattern
            position_map = [[False for _ in range(5)] for _ in range(5)]
            for pos in pattern.positions:
                if 0 <= pos < 25:
                    row = pos // 5
                    col = pos % 5
                    position_map[row][col] = True
            
            # Add the pattern with position map to results
            pattern_data = WinningPatternSerializer(pattern).data
            pattern_data['position_map'] = position_map
            result.append(pattern_data)
            
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def visualize(self, request, pk=None):
        """Generate an ASCII visualization of the pattern"""
        try:
            pattern = self.get_object()
            positions = pattern.positions
            
            # Create a 5x5 grid representation
            grid = [['·' for _ in range(5)] for _ in range(5)]
            
            # Fill in the pattern positions
            for pos in positions:
                if 0 <= pos < 25:
                    row = pos // 5
                    col = pos % 5
                    grid[row][col] = 'X'
            
            # Generate ASCII representation
            ascii_grid = "  B I N G O\n"
            for i, row in enumerate(grid):
                ascii_grid += f"{i+1} {' '.join(row)}\n"
            
            return Response({
                'pattern': WinningPatternSerializer(pattern).data,
                'visualization': ascii_grid
            })
            
        except Exception as e:
            logger.error(f"Error visualizing pattern: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Could not visualize pattern: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DepositRequestViewSet(viewsets.ModelViewSet):
    queryset = DepositRequest.objects.all()
    serializer_class = DepositRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Staff can see all requests, users only see their own
        if user.is_staff:
            return DepositRequest.objects.all()
        return DepositRequest.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'request_deposit':
            return DepositRequestCreateSerializer
        if self.action == 'confirm_deposit':
            return DepositConfirmSerializer
        if self.action in ['approve', 'reject']:
            return DepositAdminActionSerializer
        return DepositRequestSerializer
    
    @action(detail=False, methods=['post'])
    def request_deposit(self, request):
        """Initiate a deposit request and get a unique code"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        amount = serializer.validated_data['amount']
        
        # Generate unique code
        unique_code = DepositRequest.generate_unique_code()
        
        # Create deposit request
        deposit = DepositRequest.objects.create(
            user=request.user,
            amount=amount,
            unique_code=unique_code,
            status='pending'
        )
        
        # Return bank details and unique code
        return Response({
            'success': True,
            'deposit_id': deposit.id,
            'amount': amount,
            'unique_code': unique_code,
            'bank_details': {
                'bank_name': 'Banco Nacional de Costa Rica',
                'account_number': 'CR123456789',
                'account_holder': 'BINGO App',
                'instructions': 'Incluya el código único en el asunto o descripción de la transferencia.'
            },
            'message': 'Por favor realice la transferencia y luego confirme con el número de referencia.'
        })
    
    @action(detail=False, methods=['post'])
    def confirm_deposit(self, request):
        """Confirm deposit with transaction reference"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        unique_code = serializer.validated_data['unique_code']
        reference = serializer.validated_data['reference']
        payment_method_id = serializer.validated_data.get('payment_method')
        
        try:
            deposit = DepositRequest.objects.get(
                unique_code=unique_code,
                user=request.user,
                status='pending'
            )
            
            # Update reference and payment method if provided
            deposit.reference = reference
            
            # Validate payment method exists if provided
            if payment_method_id:
                try:
                    payment_method = PaymentMethod.objects.get(id=payment_method_id)
                    deposit.payment_method = str(payment_method_id)
                except PaymentMethod.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'El método de pago especificado no existe.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            deposit.save()
            
            return Response({
                'success': True,
                'deposit_id': deposit.id,
                'status': 'pending',
                'payment_method': payment_method_id,
                'message': 'Su solicitud de recarga está siendo procesada. Le notificaremos cuando sea aprobada.'
            })
            
        except DepositRequest.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No se encontró una solicitud de depósito pendiente con ese código.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve a deposit request (staff only)"""
        if not request.user.is_staff:
            return Response({
                'success': False,
                'message': 'Solo el personal administrativo puede aprobar depósitos.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            deposit = self.get_object()
            
            if deposit.status != 'pending':
                return Response({
                    'success': False,
                    'message': f'Esta solicitud ya ha sido {deposit.get_status_display().lower()}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Update admin notes if provided
            if 'admin_notes' in serializer.validated_data:
                deposit.admin_notes = serializer.validated_data['admin_notes']
            
            # Process approval
            deposit, balance = DepositRequest.approve(deposit.id, request.user)
            
            return Response({
                'success': True,
                'deposit_id': deposit.id,
                'amount': deposit.amount,
                'new_balance': balance.balance,
                'message': f'Depósito de {deposit.amount} monedas aprobado exitosamente.'
            })
            
        except Exception as e:
            logger.error(f"Error approving deposit: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Error al aprobar el depósito: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject a deposit request (staff only)"""
        if not request.user.is_staff:
            return Response({
                'success': False,
                'message': 'Solo el personal administrativo puede rechazar depósitos.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            deposit = self.get_object()
            
            if deposit.status != 'pending':
                return Response({
                    'success': False,
                    'message': f'Esta solicitud ya ha sido {deposit.get_status_display().lower()}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Update admin notes if provided
            if 'admin_notes' in serializer.validated_data:
                deposit.admin_notes = serializer.validated_data['admin_notes']
            
            # Reject the deposit
            deposit.status = 'rejected'
            deposit.approved_by = request.user
            deposit.save()
            
            return Response({
                'success': True,
                'deposit_id': deposit.id,
                'message': 'Depósito rechazado.'
            })
            
        except Exception as e:
            logger.error(f"Error rejecting deposit: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Error al rechazar el depósito: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def my_deposits(self, request):
        """Get all deposit requests for the current user"""
        deposits = DepositRequest.objects.filter(user=request.user)
        serializer = DepositRequestSerializer(deposits, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending(self, request):
        """Get all pending deposit requests (staff only)"""
        if not request.user.is_staff:
            return Response({
                'success': False,
                'message': 'Solo el personal administrativo puede ver depósitos pendientes.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        deposits = DepositRequest.objects.filter(status='pending')
        serializer = DepositRequestSerializer(deposits, many=True)
        return Response(serializer.data)

class PaymentMethodViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PaymentMethodCreateUpdateSerializer
        return PaymentMethodSerializer
    
    def get_permissions(self):
        # Only staff members can create, update or delete payment methods
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active payment methods"""
        payment_methods = PaymentMethod.objects.filter(is_active=True)
        serializer = self.get_serializer(payment_methods, many=True)
        return Response(serializer.data)

class RatesConfigViewSet(viewsets.ModelViewSet):
    queryset = RatesConfig.objects.all()
    serializer_class = RatesConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'update_rates':
            return RatesUpdateSerializer
        return RatesConfigSerializer
    
    def get_permissions(self):
        # Solo administradores pueden modificar las tasas
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'update_rates']:
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Obtener la configuración de tasas actual"""
        rates_config = RatesConfig.get_current()
        serializer = self.get_serializer(rates_config)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def update_rates(self, request):
        """Actualizar la configuración de tasas"""
        serializer = RatesUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        rates_config = RatesConfig.get_current()
        rates_config.rates = serializer.validated_data['rates']
        
        if 'description' in serializer.validated_data:
            rates_config.description = serializer.validated_data['description']
            
        rates_config.save()
        
        return Response({
            'success': True,
            'message': 'Tasas actualizadas correctamente',
            'rates': rates_config.rates,
            'last_updated': rates_config.last_updated
        })