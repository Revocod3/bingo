import logging
import json
from django.core.management.base import BaseCommand
from bingo.models import BingoCard, Number, WinningPattern
from bingo.win_patterns import check_win_pattern, parse_card_numbers

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verify if a bingo card has a winning pattern'

    def add_arguments(self, parser):
        parser.add_argument('card_id', type=str, help='UUID of the card to verify')
        parser.add_argument('--pattern', type=str, help='Specific pattern to check (default: check all)')
        parser.add_argument('--force-call', type=str, nargs='+', help='Force specific numbers to be "called"')
        parser.add_argument('--debug', action='store_true', help='Show detailed debug information')

    def handle(self, *args, **options):
        card_id = options['card_id']
        pattern_name = options['pattern'] or 'bingo'
        force_call = options['force_call']
        debug = options['debug']

        try:
            # Get the card
            try:
                card = BingoCard.objects.get(id=card_id)
            except BingoCard.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Card not found: {card_id}"))
                return

            # Get the pattern if specified
            if pattern_name != 'bingo':
                try:
                    pattern = WinningPattern.objects.get(name=pattern_name)
                    self.stdout.write(f"Checking pattern: {pattern.display_name}")
                except WinningPattern.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Pattern not found: {pattern_name}"))
                    return
            else:
                self.stdout.write("Checking all available patterns...")

            # Get called numbers from the event
            called_numbers = set(Number.objects.filter(
                event_id=card.event_id
            ).values_list('value', flat=True))
            
            # Add forced numbers if provided
            if force_call:
                forced_numbers = set(int(n) for n in force_call if n.isdigit())
                called_numbers.update(forced_numbers)
                self.stdout.write(f"Forced numbers added to called numbers: {forced_numbers}")
            
            self.stdout.write(f"Total called numbers: {sorted(called_numbers)}")
            
            # Parse the card numbers
            if debug:
                card_flat = parse_card_numbers(card.numbers)
                self.stdout.write(f"Card in raw format: {card.numbers}")
                self.stdout.write(f"Card parsed to flat list: {card_flat}")
                
                # Print the card in a visual 5x5 format
                self.stdout.write("\nCard visualization:")
                self.stdout.write("  B   I   N   G   O ")
                for row in range(5):
                    row_values = []
                    for col in range(5):
                        pos = row * 5 + col
                        value = card_flat[pos] if pos < len(card_flat) else "??"
                        value_str = str(value).rjust(3, " ")
                        row_values.append(value_str)
                    self.stdout.write(" ".join(row_values))
                self.stdout.write("")
            
            # Check if the pattern is complete
            is_winner, win_details = check_win_pattern(
                card.numbers, 
                called_numbers, 
                pattern_name,
                event_id=card.event_id
            )
            
            if is_winner:
                self.stdout.write(self.style.SUCCESS("WINNER!"))
                self.stdout.write(f"Winning pattern: {win_details['pattern_name']}")
                self.stdout.write(f"Matched positions: {win_details['positions']}")
                self.stdout.write(f"Matched numbers: {win_details['matched_numbers']}")
                
                # Mark the card as a winner if not already
                if not card.is_winner:
                    if input("Mark this card as a winner in the database? (y/n) ").lower() == 'y':
                        card.is_winner = True
                        card.save()
                        self.stdout.write(self.style.SUCCESS("Card marked as winner in database"))
            else:
                self.stdout.write(self.style.ERROR("Not a winner"))
                
                # If debugging, try to determine what numbers are missing
                if debug and pattern_name != 'bingo':
                    try:
                        pattern = WinningPattern.objects.get(name=pattern_name)
                        flat_card = parse_card_numbers(card.numbers)
                        
                        # Check each position in the pattern
                        missing = []
                        for pos in pattern.positions:
                            if pos < len(flat_card):
                                num_value = flat_card[pos]
                                if num_value not in called_numbers and num_value != 0:  # 0 is free space
                                    missing.append((pos, num_value))
                        
                        if missing:
                            self.stdout.write("Missing numbers for this pattern:")
                            for pos, value in missing:
                                self.stdout.write(f"  Position {pos}: {value}")
                    except Exception as e:
                        self.stdout.write(f"Error during debug: {str(e)}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
