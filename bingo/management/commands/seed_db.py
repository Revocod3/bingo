import logging
import random
import hashlib
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import CustomUser
from bingo.models import Event, BingoCard, Number, WinningPattern
import datetime

# Try to import wallet-related models, but handle gracefully if they don't exist
try:
    from bingo.models import Wallet, TestCoin
    HAS_WALLET_MODELS = True
except ImportError:
    HAS_WALLET_MODELS = False

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Seeds the database with initial data for testing'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Number of regular users to create')
        parser.add_argument('--events', type=int, default=3, help='Number of events to create')
        parser.add_argument('--cards-per-user', type=int, default=2, help='Number of cards per user per event')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def clear_existing_data(self):
        """Clear existing data to allow clean reseeding"""
        self.stdout.write('Clearing existing data...')
        
        # Clear in order to avoid foreign key constraint issues
        # First, delete Numbers which reference Events
        number_count = Number.objects.all().count()
        Number.objects.all().delete()
        self.stdout.write(f'Deleted {number_count} called numbers')
        
        # Delete BingoCards which reference Users and Events
        card_count = BingoCard.objects.all().count()
        BingoCard.objects.all().delete()
        self.stdout.write(f'Deleted {card_count} bingo cards')
        
        # Delete Events
        event_count = Event.objects.all().count()
        Event.objects.all().delete()
        self.stdout.write(f'Deleted {event_count} events')
        
        # Delete test coins and wallets if models exist
        if HAS_WALLET_MODELS:
            coin_count = TestCoin.objects.all().count()
            TestCoin.objects.all().delete()
            self.stdout.write(f'Deleted {coin_count} test coins')
            
            wallet_count = Wallet.objects.all().count()
            Wallet.objects.all().delete()
            self.stdout.write(f'Deleted {wallet_count} wallets')
        
        # Note: We're not deleting users by default to preserve user accounts
        self.stdout.write(self.style.SUCCESS('Data clearing completed'))

    def generate_bingo_card(self):
        """
        Generate a proper Bingo card with numbers in the format:
        ["B1", "B3", "I16", "N31", "N0", ...] where:
        - B column: 1-15
        - I column: 16-30
        - N column: 31-45 (with free space in center)
        - G column: 46-60
        - O column: 61-75
        
        Numbers are arranged in column-first order to match the standard 5x5 grid:
        0  5  10 15 20 (B column)
        1  6  11 16 21 (I column)
        2  7  12 17 22 (N column with free space at 12)
        3  8  13 18 23 (G column)
        4  9  14 19 24 (O column)
        """
        # Define column letters and ranges
        columns = [
            ('B', range(1, 16)),    # 1-15
            ('I', range(16, 31)),   # 16-30
            ('N', range(31, 46)),   # 31-45
            ('G', range(46, 61)),   # 46-60
            ('O', range(61, 76))    # 61-75
        ]
        
        # Initialize empty list for card numbers (25 positions)
        card_numbers = [""] * 25
        
        # Generate numbers for each column
        for col_idx, (letter, number_range) in enumerate(columns):
            # Select 5 random unique numbers from the column range
            col_numbers = random.sample(list(number_range), 5)
            
            # Place numbers in the appropriate positions
            for row_idx in range(5):
                # Calculate position in the flat card array (col-first layout)
                position = row_idx * 5 + col_idx
                
                # Handle free space in the middle (position 12)
                if position == 12:  # Center position
                    card_numbers[position] = "N0"  # Free space
                else:
                    card_numbers[position] = f"{letter}{col_numbers[row_idx]}"
        
        return card_numbers

    def create_default_patterns(self):
        """Create default winning patterns if they don't exist"""
        self.stdout.write('Creating default winning patterns...')
        
        # Define default patterns
        default_patterns = [
            # Horizontal lines
            {'name': 'row_1', 'display_name': 'Top Row', 'positions': [0, 1, 2, 3, 4]},
            {'name': 'row_2', 'display_name': 'Second Row', 'positions': [5, 6, 7, 8, 9]},
            {'name': 'row_3', 'display_name': 'Middle Row', 'positions': [10, 11, 12, 13, 14]},
            {'name': 'row_4', 'display_name': 'Fourth Row', 'positions': [15, 16, 17, 18, 19]},
            {'name': 'row_5', 'display_name': 'Bottom Row', 'positions': [20, 21, 22, 23, 24]},
            
            # Vertical lines
            {'name': 'col_1', 'display_name': 'First Column', 'positions': [0, 5, 10, 15, 20]},
            {'name': 'col_2', 'display_name': 'Second Column', 'positions': [1, 6, 11, 16, 21]},
            {'name': 'col_3', 'display_name': 'Middle Column', 'positions': [2, 7, 12, 17, 22]},
            {'name': 'col_4', 'display_name': 'Fourth Column', 'positions': [3, 8, 13, 18, 23]},
            {'name': 'col_5', 'display_name': 'Last Column', 'positions': [4, 9, 14, 19, 24]},
            
            # Diagonals
            {'name': 'diag_1', 'display_name': 'Diagonal (Top Left to Bottom Right)', 'positions': [0, 6, 12, 18, 24]},
            {'name': 'diag_2', 'display_name': 'Diagonal (Top Right to Bottom Left)', 'positions': [4, 8, 12, 16, 20]},
            
            # Special patterns
            {'name': 'corners', 'display_name': 'Four Corners', 'positions': [0, 4, 20, 24]},
            {'name': 'center', 'display_name': 'Center Square (3x3)', 'positions': [6, 7, 8, 11, 12, 13, 16, 17, 18]},
            
            # Full card
            {'name': 'blackout', 'display_name': 'Blackout (Full Card)', 'positions': list(range(25))},
            
            # Shapes
            {'name': 'x_shape', 'display_name': 'X Shape', 'positions': [0, 4, 6, 8, 12, 16, 18, 20, 24]},
            {'name': 'plus_sign', 'display_name': 'Plus Sign', 'positions': [2, 7, 10, 11, 12, 13, 14, 17, 22]},
        ]
        
        created_count = 0
        existing_count = 0
        
        # Try to find an admin user to use as creator
        try:
            admin_user = CustomUser.objects.filter(is_superuser=True).first()
        except:
            admin_user = None
            self.stdout.write(self.style.WARNING('No admin user found for pattern creation. Using system.'))
        
        # Create patterns
        for pattern_data in default_patterns:
            try:
                # Skip if pattern already exists
                if WinningPattern.objects.filter(name=pattern_data['name']).exists():
                    existing_count += 1
                    continue
                    
                WinningPattern.objects.create(
                    name=pattern_data['name'],
                    display_name=pattern_data['display_name'],
                    positions=pattern_data['positions'],
                    is_active=True,
                    created_by=admin_user
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating pattern {pattern_data['name']}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new patterns, {existing_count} already existed.'))

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))
        
        # Clear existing data if requested
        if options['clear']:
            self.clear_existing_data()
        
        num_users = options['users']
        num_events = options['events']
        cards_per_user = options['cards_per_user']
        
        # Create admin user if doesn't exist
        admin_email = 'admin@example.com'
        admin_password = 'admin1234'
        
        try:
            admin = CustomUser.objects.get(email=admin_email)
            self.stdout.write(f'Admin user already exists: {admin_email}')
        except CustomUser.DoesNotExist:
            admin = CustomUser.objects.create_user(
                email=admin_email,
                password=admin_password,
                is_staff=True,
                is_superuser=True,
                is_email_verified=True,
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_email} / {admin_password}'))
        
        # Create default winning patterns
        self.create_default_patterns()
        
        # Create regular users
        users = [admin]  # Start with the admin user
        for i in range(1, num_users + 1):
            email = f'user{i}@example.com'
            try:
                user = CustomUser.objects.get(email=email)
                self.stdout.write(f'User already exists: {email}')
            except CustomUser.DoesNotExist:
                user = CustomUser.objects.create_user(
                    email=email,
                    password='pass1234',
                    is_email_verified=True,
                    first_name=f'User{i}',
                    last_name='Test'
                )
                self.stdout.write(self.style.SUCCESS(f'Created user: {email} / pass1234'))
            users.append(user)
            
            # Create wallet and test coins for each user if those models exist
            if HAS_WALLET_MODELS:
                wallet, created = Wallet.objects.get_or_create(user=user)
                if created:
                    self.stdout.write(f'Created wallet for user: {email}')
                
                # Add test coins for regular users to purchase cards
                TestCoin.objects.get_or_create(
                    wallet=wallet,
                    defaults={'balance': 1000}
                )
                self.stdout.write(f'Ensured test coins for user: {email}')
            else:
                self.stdout.write(f'Skipping wallet creation (models not available)')
        
        # Create events
        events = []
        # Inspect the Event model to determine available fields
        event_fields = [f.name for f in Event._meta.fields]
        self.stdout.write(f"Available Event model fields: {event_fields}")
        
        for i in range(1, num_events + 1):
            name = f'Bingo Event {i}'
            
            # Start date is today + i days at 20:00
            start_date = timezone.now() + datetime.timedelta(days=i)
            start_date = start_date.replace(hour=20, minute=0, second=0, microsecond=0)
            
            # End date is 3 hours after start date
            end_date = start_date + datetime.timedelta(hours=3)
            
            # Create event with basic properties, adaptable to model structure
            event_data = {
                'name': name,
                'prize': i * 1000,  # Prize increases with each event
                'start': start_date,
                'end': end_date,     # Add the end date that's required
            }
            
            # Try to create the event
            try:
                event, created = Event.objects.get_or_create(
                    name=name,
                    defaults=event_data
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created event: {name} starting at {start_date}, ending at {end_date}'))
                else:
                    self.stdout.write(f'Event already exists: {name}')
                
                events.append(event)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating event: {str(e)}"))
        
        # Create bingo cards for each user and event
        for user in users:
            for event in events:
                existing_cards = BingoCard.objects.filter(user=user, event=event).count()
                cards_to_create = cards_per_user - existing_cards
                
                if cards_to_create <= 0:
                    self.stdout.write(f'User {user.email} already has enough cards for event {event.name}')
                    continue
                
                for _ in range(cards_to_create):
                    # Generate card numbers using the new method
                    numbers = self.generate_bingo_card()
                    
                    # Generate a unique hash for this card based on the numbers
                    card_hash = hashlib.md5(
                        json.dumps(numbers, sort_keys=True).encode() + 
                        f"{user.id}{event.id}{random.randint(1, 10000)}".encode()
                    ).hexdigest()
                    
                    try:
                        card = BingoCard.objects.create(
                            user=user,
                            event=event,
                            numbers=numbers,
                            hash=card_hash,  # Set the hash explicitly
                        )
                        self.stdout.write(f'Created card #{card.id} for user {user.email} in event {event.name}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error creating card: {str(e)}'))
        
        # For the first event, add some called numbers to simulate an in-progress game
        if events:
            event = events[0]
            existing_numbers = Number.objects.filter(event=event).count()
            
            if existing_numbers == 0:
                # Call 10 random numbers
                called_nums = random.sample(range(1, 76), 10)
                for num in called_nums:
                    Number.objects.create(
                        event=event,
                        value=num
                    )
                self.stdout.write(self.style.SUCCESS(f'Added {len(called_nums)} called numbers to event {event.name}'))
            else:
                self.stdout.write(f'Event {event.name} already has {existing_numbers} called numbers')
        
        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
