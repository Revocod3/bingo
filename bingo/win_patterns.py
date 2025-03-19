import logging

logger = logging.getLogger(__name__)

# Common bingo patterns
PATTERNS = {
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

def check_win_pattern(card_numbers, called_numbers, pattern_name='bingo'):
    """
    Check if a card has won with the specified pattern.
    
    Args:
        card_numbers: Dictionary of card numbers (or can be a list of 25 numbers)
        called_numbers: Set of called numbers
        pattern_name: Name of the pattern to check (default is 'bingo' - any line)
    
    Returns:
        bool: True if the pattern is completed, False otherwise
    """
    try:
        # Convert card numbers to a list if it's a dictionary
        numbers_list = []
        if isinstance(card_numbers, dict):
            # Sort by position or key to ensure correct order
            for i in range(25):
                pos = str(i)
                if pos in card_numbers:
                    numbers_list.append(card_numbers[pos])
                elif i in card_numbers:
                    numbers_list.append(card_numbers[i])
        elif isinstance(card_numbers, list):
            numbers_list = card_numbers
        else:
            logger.error(f"Unsupported card_numbers format: {type(card_numbers)}")
            return False
        
        # Get the pattern definition
        pattern = PATTERNS.get(pattern_name.lower())
        
        # Special case for "bingo" which can be any row, column, or diagonal
        if pattern_name.lower() == 'bingo' or pattern is None:
            # Check each row, column and diagonal
            for p_name, p_positions in PATTERNS.items():
                if p_name.startswith('row_') or p_name.startswith('col_') or p_name.startswith('diag_'):
                    if all(numbers_list[pos] in called_numbers for pos in p_positions):
                        logger.info(f"Win detected with pattern {p_name}")
                        return True
            return False
        
        # Check if all numbers in the pattern are called
        return all(numbers_list[pos] in called_numbers for pos in pattern)
    except Exception as e:
        logger.error(f"Error checking win pattern: {str(e)}")
        return False
