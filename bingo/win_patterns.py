import logging
from django.db import models
import importlib

logger = logging.getLogger(__name__)

# Default patterns to fallback on if database access fails
DEFAULT_PATTERNS = {
    # Horizontal lines
    'row_1': [0, 1, 2, 3, 4],
    'row_2': [5, 6, 7, 8, 9],
    'row_3': [10, 11, 12, 13, 14],
    'row_4': [15, 16, 17, 18, 19],
    'row_5': [20, 21, 22, 23, 24],
    
    # Vertical lines
    'col_1': [0, 5, 10, 15, 20],
    'col_2': [1, 6, 11, 16, 21],
    'col_3': [2, 7, 12, 17, 22],
    'col_4': [3, 8, 13, 18, 23],
    'col_5': [4, 9, 14, 19, 24],
    
    # Diagonals
    'diag_1': [0, 6, 12, 18, 24],
    'diag_2': [4, 8, 12, 16, 20],
    
    # Special patterns
    'corners': [0, 4, 20, 24],
    'center': [6, 7, 8, 11, 12, 13, 16, 17, 18],
    
    # Full card
    'blackout': list(range(25)),
    
    # Standard bingo (default) - any row, column, or diagonal
    'bingo': None,  # This will be checked separately
}

def get_patterns_from_db():
    """
    Get patterns from the database.
    Returns a dictionary of pattern_name: positions
    """
    try:
        # Import here to avoid circular imports
        from .models import WinningPattern
        
        patterns = {}
        for pattern in WinningPattern.objects.filter(is_active=True):
            patterns[pattern.name] = pattern.positions
        
        if patterns:
            return patterns
        return DEFAULT_PATTERNS
    except Exception as e:
        logger.error(f"Error fetching patterns from database: {e}", exc_info=True)
        return DEFAULT_PATTERNS

def get_patterns_for_event(event_id):
    """
    Get patterns allowed for a specific event.
    If the event has no specific patterns, return all active patterns.
    
    Args:
        event_id: UUID of the event
        
    Returns:
        dict: Dictionary of pattern_name: positions
    """
    try:
        # Import here to avoid circular imports
        from .models import WinningPattern, Event
        
        # Try to get the event
        try:
            event = Event.objects.get(id=event_id)
            
            # If the event has specific patterns, use those
            if event.allowed_patterns.exists():
                patterns = {}
                for pattern in event.allowed_patterns.filter(is_active=True):
                    patterns[pattern.name] = pattern.positions
                
                if patterns:
                    return patterns
            
            # Otherwise fall back to all active patterns
            return get_patterns_from_db()
            
        except Event.DoesNotExist:
            # If event doesn't exist, fall back to all active patterns
            return get_patterns_from_db()
            
    except Exception as e:
        logger.error(f"Error fetching patterns for event: {e}", exc_info=True)
        return DEFAULT_PATTERNS

def parse_card_numbers(card_numbers):
    """
    Parse card numbers into a flat list regardless of format.
    Standardized format is a list of 25 strings like ["B1", "I16", "N0", etc.] 
    where N0 represents the free space in the middle.
    
    Returns a list of 25 integers where:
    - Regular numbers are parsed from their string representation
    - Free space is represented as 0
    """
    numbers_list = [0] * 25  # Initialize with zeros
    
    # Log the input format for debugging
    logger.debug(f"Parsing card numbers format: {type(card_numbers)}")
    
    # Handle list of strings format (standard format: ["B1", "B2", ...])
    if isinstance(card_numbers, list) and len(card_numbers) == 25 and all(isinstance(item, str) for item in card_numbers):
        # Extract the BINGO column information
        bingo_columns = {
            'B': [],
            'I': [],
            'N': [],
            'G': [],
            'O': []
        }
        
        # First pass: categorize by column
        for idx, item in enumerate(card_numbers):
            if item == "N0" or item == "0":
                # Free space
                bingo_columns['N'].append(0)
            elif len(item) >= 2:
                # Get the letter and number parts
                letter = item[0]
                if letter in bingo_columns:
                    try:
                        num_part = ''.join(c for c in item[1:] if c.isdigit())
                        if num_part:
                            bingo_columns[letter].append(int(num_part))
                    except ValueError:
                        bingo_columns[letter].append(0)
        
        # Second pass: remap to proper positions (row-major order)
        for col_idx, letter in enumerate("BINGO"):
            col_values = bingo_columns[letter]
            for row_idx, value in enumerate(col_values[:5]):
                pos = row_idx * 5 + col_idx  # Convert to row-major index
                if pos < 25:
                    numbers_list[pos] = value
        
        return numbers_list
    
    # Fall back to other formats...
    if isinstance(card_numbers, dict):
        # Check for BINGO column format (B: [1,2,3...], I: [16,17,18...], etc.)
        if "B" in card_numbers and isinstance(card_numbers["B"], list):
            col_index = 0
            for col in "BINGO":
                col_numbers = card_numbers.get(col, [])
                for row_index, num in enumerate(col_numbers[:5]):  # Limit to 5 numbers per column
                    position = row_index * 5 + col_index
                    if position < 25:  # Make sure we don't go out of bounds
                        numbers_list[position] = num
                col_index += 1
                
        # Check for letter-prefixed format (B1, I16, etc.)
        elif any(isinstance(k, str) and k.startswith(('B', 'I', 'N', 'G', 'O')) for k in card_numbers.keys()):
            # Convert from format like {"B1": position, "I16": position} to a 5x5 grid
            for key, position in card_numbers.items():
                if isinstance(position, int) and 0 <= position < 25:
                    # Extract the number from the key (e.g., "B1" -> 1)
                    try:
                        letter = key[0]
                        number = int(key[1:])
                        numbers_list[position] = number
                    except (IndexError, ValueError):
                        pass
                        
        # Check for position-based format ({0: 1, 1: 16, ...})
        else:
            for pos, value in card_numbers.items():
                try:
                    pos_int = int(pos) if isinstance(pos, str) else pos
                    if 0 <= pos_int < 25:
                        numbers_list[pos_int] = value
                except (ValueError, TypeError):
                    pass
                    
    elif isinstance(card_numbers, list):
        # Check if this is already a flat list
        if len(card_numbers) <= 25:
            # Pad with zeros if needed
            numbers_list[:len(card_numbers)] = card_numbers
        else:
            # If it's too long, just take the first 25
            numbers_list = card_numbers[:25]
            
    # Handle format where the card has a list of strings like ["B1", "I16", ...]
    elif all(isinstance(item, str) for item in card_numbers):
        # Similar processing as the first case but for a non-25 length list
        bingo_columns = {
            'B': [],
            'I': [],
            'N': [],
            'G': [],
            'O': []
        }
        
        for item in card_numbers[:25]:
            if item.startswith('N0') or item == '0':
                bingo_columns['N'].append(0)
            elif len(item) >= 2:
                letter = item[0]
                if letter in bingo_columns:
                    try:
                        num_part = ''.join(c for c in item[1:] if c.isdigit())
                        if num_part:
                            bingo_columns[letter].append(int(num_part))
                    except ValueError:
                        bingo_columns[letter].append(0)
        
        # Map to proper positions
        for col_idx, letter in enumerate("BINGO"):
            col_values = bingo_columns[letter]
            for row_idx, value in enumerate(col_values[:5]):
                pos = row_idx * 5 + col_idx
                if pos < 25:
                    numbers_list[pos] = value
    
    # Log the parsed result for debugging
    logger.debug(f"Parsed card numbers: {numbers_list}")        
    return numbers_list

def check_win_pattern(card_numbers, called_numbers, pattern_name='bingo', event_id=None):
    """
    Check if a card has won with the specified pattern.
    
    Args:
        card_numbers: Card numbers in any supported format
        called_numbers: Set of called numbers
        pattern_name: Name of the pattern to check (default is 'bingo' - any line)
        event_id: Optional event ID to check patterns allowed for that event
    
    Returns:
        bool: True if the pattern is completed, False otherwise
        dict: Details about the winning pattern and matched numbers, or None if not a winner
    """
    try:
        # Parse card numbers to a standard format
        numbers_list = parse_card_numbers(card_numbers)
        
        # Get patterns based on event_id if provided
        if event_id:
            patterns = get_patterns_for_event(event_id)
        else:
            patterns = get_patterns_from_db()
        
        # Handle custom pattern name mapping - map Spanish names to English pattern names
        pattern_name_mapping = {
            'linea horizontal 1': 'row_1',
            'linea horizontal 2': 'row_2',
            'linea horizontal 3': 'row_3',
            'linea horizontal 4': 'row_4',
            'linea horizontal 5': 'row_5',
            'linea vertical 1': 'col_1',
            'linea vertical 2': 'col_2',
            'linea vertical 3': 'col_3',
            'linea vertical 4': 'col_4',
            'linea vertical 5': 'col_5',
        }
        
        # Try to map the pattern name if it's in Spanish
        normalized_pattern_name = pattern_name.lower()
        if normalized_pattern_name in pattern_name_mapping:
            pattern_name = pattern_name_mapping[normalized_pattern_name]
            
        pattern = patterns.get(pattern_name.lower())
        
        # Log debugging information about the pattern check
        logger.debug(f"Checking pattern: {pattern_name} with positions: {pattern}")
        logger.debug(f"Card numbers: {numbers_list}")
        logger.debug(f"Called numbers: {called_numbers}")
            
        # Special case for "bingo" which can be any row, column, or diagonal
        if pattern_name.lower() == 'bingo' or pattern is None:
            # Check each pattern in the database
            for p_name, p_positions in patterns.items():
                # Only check default patterns if no specific pattern name was provided
                if pattern_name.lower() == 'bingo' or p_name == pattern_name.lower():
                    # Check if all numbers in this pattern are called
                    matched_positions = []
                    for pos in p_positions:
                        if 0 <= pos < len(numbers_list):
                            value = numbers_list[pos]
                            if value in called_numbers or value == 0:  # 0 is free space
                                matched_positions.append(pos)
                    
                    if len(matched_positions) == len(p_positions):
                        # This pattern is a winner!
                        matched_numbers = [str(numbers_list[pos]) for pos in matched_positions]
                        
                        # Get display name from system default
                        pattern_display_name = p_name.replace('_', ' ').title()
                        
                        # If this came from a database pattern, try to get its display name
                        try:
                            from .models import WinningPattern
                            db_pattern = WinningPattern.objects.filter(name=p_name).first()
                            if db_pattern:
                                pattern_display_name = db_pattern.display_name
                        except Exception:
                            # If we can't retrieve from DB, use the formatted name
                            pass
                        
                        logger.debug(f"Winner with pattern: {p_name}, positions: {p_positions}, numbers: {matched_numbers}")
                        
                        return True, {
                            'pattern_name': p_name,
                            'positions': p_positions,
                            'matched_numbers': matched_numbers,
                            'display_name': pattern_display_name
                        }
            return False, None
        
        # Check if all numbers in the specific pattern are called
        matched_positions = []
        for pos in pattern:
            if 0 <= pos < len(numbers_list):
                value = numbers_list[pos]
                if value in called_numbers or value == 0:  # 0 is free space
                    matched_positions.append(pos)
        
        if len(matched_positions) == len(pattern):
            # Winner with the specified pattern!
            matched_numbers = [str(numbers_list[pos]) for pos in matched_positions]
            
            # Get display name if possible
            pattern_display_name = pattern_name.replace('_', ' ').title()
            try:
                from .models import WinningPattern
                db_pattern = WinningPattern.objects.filter(name=pattern_name.lower()).first()
                if db_pattern:
                    pattern_display_name = db_pattern.display_name
            except Exception:
                # If we can't retrieve from DB, use the formatted name
                pass
            
            logger.debug(f"Winner with pattern: {pattern_name}, positions: {pattern}, numbers: {matched_numbers}")
            
            return True, {
                'pattern_name': pattern_name,
                'positions': pattern,
                'matched_numbers': matched_numbers,
                'display_name': pattern_display_name
            }
        
        return False, None
        
    except Exception as e:
        logger.error(f"Error checking win pattern: {str(e)}", exc_info=True)
        return False, None
