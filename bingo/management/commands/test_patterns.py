import logging
import random
import json
from django.core.management.base import BaseCommand
from bingo.models import WinningPattern, BingoCard, Event, Number
from bingo.win_patterns import check_win_pattern, parse_card_numbers

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test winning pattern detection with different card formats'

    def add_arguments(self, parser):
        parser.add_argument('--pattern', type=str, help='Specific pattern name to test')
        parser.add_argument('--card-id', type=str, help='Test with a specific card ID')
        parser.add_argument('--event-id', type=str, help='Test with cards from a specific event')
        parser.add_argument('--format', choices=['column', 'position', 'list', 'all'], 
                           default='all', help='Card format to test')

    def _generate_column_format_card(self):
        """Generate a card in column format (B: [1,2,3...], I: [16,17,18...])"""
        card = {
            'B': random.sample(range(1, 16), 5),
            'I': random.sample(range(16, 31), 5),
            'N': random.sample(range(31, 46), 5),
            'G': random.sample(range(46, 61), 5),
            'O': random.sample(range(61, 76), 5),
        }
        # Set middle space as free
        card['free_space'] = {'column': 'N', 'row': 2}
        
        return card

    def _generate_position_format_card(self):
        """Generate a card in position format {0: 1, 1: 16, ...}"""
        numbers = []
        for col_idx, col_range in enumerate([
            range(1, 16),    # B: 1-15
            range(16, 31),   # I: 16-30
            range(31, 46),   # N: 31-45
            range(46, 61),   # G: 46-60
            range(61, 76)    # O: 61-75
        ]):
            numbers.extend(random.sample(list(col_range), 5))
        
        # Set middle position as free space
        middle_pos = 12  # Row 2, Column 2 (0-indexed)
        numbers[middle_pos] = 0
        
        # Create position-based dictionary
        return {str(i): num for i, num in enumerate(numbers)}

    def _generate_list_format_card(self):
        """Generate a card as a list of strings in format B1, I16, etc."""
        card = []
        for col_letter, col_range in [
            ('B', range(1, 16)),    # B: 1-15
            ('I', range(16, 31)),   # I: 16-30
            ('N', range(31, 46)),   # N: 31-45
            ('G', range(46, 61)),   # G: 46-60
            ('O', range(61, 76))    # O: 61-75
        ]:
            card.extend([f"{col_letter}{num}" for num in random.sample(list(col_range), 5)])
        
        # Set middle position as free space
        middle_pos = 12  # Row 2, Column 2 (0-indexed)
        card[middle_pos] = "N0"
        
        return card

    def test_pattern_with_card(self, pattern, card_format):
        """Test if a pattern can be detected in various card formats"""
        positions = pattern.positions
        
        # Generate a card in the requested format
        if card_format == 'column':
            card = self._generate_column_format_card()
        elif card_format == 'position':
            card = self._generate_position_format_card()
        elif card_format == 'list':
            card = self._generate_list_format_card()
        else:
            self.stdout.write(self.style.ERROR(f"Unsupported format: {card_format}"))
            return False
            
        # Parse the card to get the flat list representation
        flat_card = parse_card_numbers(card)
        
        # Create "called numbers" that include all numbers in the pattern positions
        # plus some random other numbers
        called_numbers = set()
        for pos in positions:
            if pos < len(flat_card) and flat_card[pos] > 0:  # Skip free space (0)
                called_numbers.add(flat_card[pos])
        
        # Add some random numbers to called_numbers
        all_possible = set(range(1, 76))
        random_count = min(10, 75 - len(called_numbers))
        called_numbers.update(random.sample(
            list(all_possible - called_numbers), random_count))
        
        # Check if the pattern is detected
        is_winner, win_details = check_win_pattern(card, called_numbers, pattern.name)
        
        if is_winner:
            self.stdout.write(self.style.SUCCESS(
                f"Pattern '{pattern.display_name}' detected with {card_format} format"))
            self.stdout.write(f"Called numbers: {sorted(called_numbers)}")
            self.stdout.write(f"Win details: {json.dumps(win_details, indent=2)}")
            return True
        else:
            self.stdout.write(self.style.ERROR(
                f"Pattern '{pattern.display_name}' NOT detected with {card_format} format"))
            
            # Debug output
            self.stdout.write(f"Pattern positions: {positions}")
            self.stdout.write(f"Card: {json.dumps(card, indent=2) if isinstance(card, dict) else card}")
            self.stdout.write(f"Parsed card: {flat_card}")
            self.stdout.write(f"Called numbers: {sorted(called_numbers)}")
            return False

    def test_with_real_card(self, card_id):
        """Test all patterns with a real card from the database"""
        try:
            card = BingoCard.objects.get(id=card_id)
            self.stdout.write(f"Testing patterns with card #{card.id}")
            
            # Get all active patterns
            patterns = WinningPattern.objects.filter(is_active=True)
            
            # Create a set of all numbers in the card
            card_nums = parse_card_numbers(card.numbers)
            self.stdout.write(f"Card numbers: {card_nums}")
            
            # Test each pattern
            for pattern in patterns:
                is_winner, win_details = check_win_pattern(card.numbers, set(card_nums), pattern.name)
                if is_winner:
                    self.stdout.write(self.style.SUCCESS(
                        f"Pattern '{pattern.display_name}' would be detected if all numbers called"))
                else:
                    self.stdout.write(
                        f"Pattern '{pattern.display_name}' would NOT be detected")
            
            # Get called numbers for this card's event
            event_numbers = set(Number.objects.filter(
                event_id=card.event_id
            ).values_list('value', flat=True))
            
            self.stdout.write(f"Called numbers in event: {sorted(event_numbers)}")
            
            # Check which patterns are completed with current event numbers
            completed_patterns = []
            for pattern in patterns:
                is_winner, win_details = check_win_pattern(card.numbers, event_numbers, pattern.name)
                if is_winner:
                    completed_patterns.append(pattern.display_name)
            
            if completed_patterns:
                self.stdout.write(self.style.SUCCESS(
                    f"Card #{card.id} has completed the following patterns with current called numbers: "
                    f"{', '.join(completed_patterns)}"))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Card #{card.id} has not completed any patterns with current called numbers"))
                
        except BingoCard.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Card with ID {card_id} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error testing card: {str(e)}"))

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting pattern testing..."))
        
        # Test with specific card if provided
        if options['card_id']:
            self.test_with_real_card(options['card_id'])
            return
        
        # Test patterns with specific event's cards
        if options['event_id']:
            try:
                event = Event.objects.get(id=options['event_id'])
                cards = BingoCard.objects.filter(event=event)[:5]  # Test with first 5 cards
                for card in cards:
                    self.test_with_real_card(card.id)
                return
            except Event.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Event with ID {options['event_id']} not found"))
                return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error testing event cards: {str(e)}"))
                return
        
        # Get all active patterns or a specific one
        if options['pattern']:
            try:
                patterns = [WinningPattern.objects.get(name=options['pattern'])]
            except WinningPattern.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Pattern '{options['pattern']}' not found"))
                return
        else:
            patterns = WinningPattern.objects.filter(is_active=True)
        
        if not patterns:
            self.stdout.write(self.style.WARNING("No active patterns found. Please create some patterns first."))
            return
            
        # Test each pattern with the requested format(s)
        formats_to_test = ['column', 'position', 'list'] if options['format'] == 'all' else [options['format']]
        
        for pattern in patterns:
            self.stdout.write("=" * 80)
            self.stdout.write(f"Testing pattern: {pattern.display_name}")
            self.stdout.write(f"  Positions: {pattern.positions}")
            self.stdout.write("-" * 80)
            
            for card_format in formats_to_test:
                result = self.test_pattern_with_card(pattern, card_format)
                if not result:
                    # Try again with a new random card
                    self.stdout.write("Trying again with a different card...")
                    result = self.test_pattern_with_card(pattern, card_format)
                self.stdout.write("-" * 40)
            
            self.stdout.write("=" * 80)
            self.stdout.write("")
            
        self.stdout.write(self.style.SUCCESS("Pattern testing completed!"))
