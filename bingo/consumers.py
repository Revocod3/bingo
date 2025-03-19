import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from .models import Event, BingoCard, Number
from .win_patterns import check_win_pattern
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

User = get_user_model()
logger = logging.getLogger(__name__)

class BingoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.room_group_name = f"bingo_event_{self.event_id}"
        
        # Authenticate the user from the token
        token = self.scope['query_string'].decode().split('=')[1] if 'query_string' in self.scope else None
        
        if token:
            try:
                # Verify the token and get the user
                token_obj = AccessToken(token)
                user_id = token_obj['user_id']
                self.user = await self.get_user_from_id(user_id)
                self.scope['user'] = self.user
            except (InvalidTokenError, ExpiredSignatureError) as e:
                logger.error(f"Invalid token: {str(e)}")
                self.user = None
                await self.close(code=4001)  # Unauthorized
                return
        else:
            self.user = None
            # Allow anonymous connections for viewing only
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send event info when they connect
        event_info = await self._get_event_info(self.event_id)
        if event_info:
            await self.send(text_data=json.dumps({
                'type': 'event_info',
                'event': event_info
            }))
        
        # If the user is authenticated, send their cards
        if self.user and self.user.is_authenticated:
            cards = await self._get_user_cards()
            await self.send(text_data=json.dumps({
                'type': 'user_cards',
                'cards': cards
            }))
            
            # Log connection
            logger.info(f"User {self.user.email} connected to event {self.event_id}")
        else:
            logger.info(f"Anonymous user connected to event {self.event_id}")

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"User disconnected from event {self.event_id} with code {close_code}")

    async def receive(self, text_data):
        """
        Handle messages received from WebSocket client
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            # Handler for calling numbers (admin only)
            if message_type == 'call_number':
                await self._handle_call_number(text_data_json)
                
            # Handler for claiming a win
            elif message_type == 'claim_win':
                await self._handle_claim_win(text_data_json)
                
            # Handler for player joining the game
            elif message_type == 'join_game':
                await self._handle_join_game()
                
            # Handler for player chat messages
            elif message_type == 'chat_message':
                await self._handle_chat_message(text_data_json)
                
            else:
                logger.warning(f"Unknown message type: {message_type}")
        except json.JSONDecodeError:
            logger.error("Received invalid JSON")
        except Exception as e:
            logger.exception(f"Error handling WebSocket message: {str(e)}")

    async def _handle_call_number(self, data):
        """Handle number calling from admin"""
        # Check if user is admin/host
        if not self.user.is_authenticated or not await self._is_event_admin(self.event_id, self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'You do not have permission to call numbers'
            }))
            return
        
        # Process the number call
        number_value = data.get('number')
        if not number_value or not isinstance(number_value, int) or number_value < 1 or number_value > 75:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid number. Must be an integer between 1 and 75.'
            }))
            return
            
        success, result = await self._call_number(self.event_id, number_value)
        
        if success:
            # Broadcast to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_number',
                    'number': result
                }
            )
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': result
            }))

    async def _handle_claim_win(self, data):
        """Handle win claims from players"""
        if not self.user.is_authenticated:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'You must be logged in to claim a win'
            }))
            return
        
        card_id = data.get('card_id')
        winning_pattern = data.get('pattern', 'bingo')  # Default to full bingo
        
        if not card_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Missing card_id'
            }))
            return
            
        # Verify win
        is_valid_win, result = await self._verify_win(card_id, self.user.id, winning_pattern)
        
        if is_valid_win:
            # Broadcast the win to all users
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_win',
                    'user_id': self.user.id,
                    'username': self.user.email,  # Or use a display name field if available
                    'card_id': card_id,
                    'card': result,
                    'pattern': winning_pattern
                }
            )
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': result
            }))

    async def _handle_join_game(self):
        """Handle player joining the game"""
        if self.user.is_authenticated:
            # Broadcast to the group that a player has joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_player_joined',
                    'user_id': self.user.id,
                    'username': self.user.email
                }
            )

    async def _handle_chat_message(self, data):
        """Handle chat messages between players"""
        if not self.user.is_authenticated:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'You must be logged in to send messages'
            }))
            return
            
        message = data.get('message', '').strip()
        if not message:
            return
            
        # Limit message length
        message = message[:200]
        
        # Broadcast to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_chat_message',
                'user_id': self.user.id,
                'username': self.user.email,
                'message': message
            }
        )

    # Broadcast handlers - these methods are called by the channel layer

    async def broadcast_number(self, event):
        """Broadcast a called number to all clients"""
        await self.send(text_data=json.dumps({
            'type': 'number_called',
            'number': event['number']
        }))

    async def broadcast_win(self, event):
        """Broadcast a win to all clients"""
        await self.send(text_data=json.dumps({
            'type': 'winner_announcement',
            'user_id': event['user_id'],
            'username': event['username'],
            'card_id': event['card_id'],
            'card': event['card'],
            'pattern': event['pattern']
        }))

    async def broadcast_player_joined(self, event):
        """Broadcast when a player joins the game"""
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def broadcast_chat_message(self, event):
        """Broadcast chat messages to all clients"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'user_id': event['user_id'],
            'username': event['username'],
            'message': event['message']
        }))

    # Database helper methods using database_sync_to_async

    @database_sync_to_async
    def _get_event_info(self, event_id):
        """Get event information and called numbers"""
        try:
            event = Event.objects.get(id=event_id)
            
            # Get all called numbers for this event
            called_numbers = Number.objects.filter(event_id=event_id).order_by('called_at')
            
            return {
                'id': event.id,
                'name': event.name,
                'prize': str(event.prize),
                'start_date': event.start.isoformat(),  # Changed from start to start_date
                'called_numbers': list(called_numbers.values('id', 'value', 'called_at'))
            }
        except Event.DoesNotExist:
            logger.error(f"Event {event_id} does not exist")
            return None
        except Exception as e:
            logger.error(f"Error getting event info: {str(e)}")
            return None
    
    @database_sync_to_async
    def _get_user_cards(self):
        """Get all cards owned by the current user for this event"""
        if not self.user.is_authenticated:
            return []
        
        try:
            cards = BingoCard.objects.filter(
                user=self.user,
                event_id=self.event_id
            ).values('id', 'numbers', 'is_winner', 'hash')
            return list(cards)
        except Exception as e:
            logger.error(f"Error getting user cards: {str(e)}")
            return []
    
    @database_sync_to_async
    def _is_event_admin(self, event_id, user_id):
        """Check if user is event admin (owner or staff)"""
        return self.user.is_staff
    
    @database_sync_to_async
    def _call_number(self, event_id, number_value):
        """Call a number for the event"""
        try:
            with transaction.atomic():
                # Check if the number has already been called for this event
                if Number.objects.filter(event_id=event_id, value=number_value).exists():
                    return False, "This number has already been called"
                
                # Create the number
                number = Number.objects.create(
                    event_id=event_id,
                    value=number_value
                )
                
                # Return the number details
                return True, {
                    'id': number.id,
                    'value': number.value,
                    'called_at': number.called_at.isoformat()
                }
        except Exception as e:
            logger.error(f"Error calling number: {str(e)}")
            return False, str(e)
    
    @database_sync_to_async
    def _verify_win(self, card_id, user_id, pattern):
        """Verify if a card has won with the given pattern"""
        try:
            # Get the card and ensure it belongs to the user
            card = BingoCard.objects.get(id=card_id, user_id=user_id)
            
            # Get all called numbers for this event
            called_numbers = set(Number.objects.filter(
                event_id=card.event_id
            ).values_list('value', flat=True))
            
            # Check if the pattern is completed with called numbers
            is_winner = check_win_pattern(card.numbers, called_numbers, pattern)
            
            if is_winner:
                # Mark the card as a winner if not already marked
                if not card.is_winner:
                    card.is_winner = True
                    card.save()
                
                return True, {
                    'id': card.id,
                    'numbers': card.numbers,
                    'hash': card.hash
                }
            else:
                return False, "Invalid winning pattern or not all numbers have been called"
        except BingoCard.DoesNotExist:
            return False, "Card not found or doesn't belong to you"
        except Exception as e:
            logger.error(f"Error verifying win: {str(e)}")
            return False, str(e)

    @database_sync_to_async
    def get_user_from_id(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
