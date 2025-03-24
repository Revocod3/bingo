import logging
from .win_patterns import parse_card_numbers

logger = logging.getLogger(__name__)

def format_card_for_display(card_numbers):
    """
    Format a card as ASCII/text for easier visualization.
    
    Args:
        card_numbers: Card numbers in any supported format
    
    Returns:
        str: ASCII visualization of the card
    """
    try:
        # Parse the card to our standard format
        numbers = parse_card_numbers(card_numbers)
        
        # Format header
        result = "   B    I    N    G    O  \n"
        result += "  ------------------------\n"
        
        # Format each row
        for row in range(5):
            result += "| "
            for col in range(5):
                pos = row * 5 + col
                if pos < len(numbers):
                    value = numbers[pos]
                    if value == 0:
                        # This is the free space
                        value_str = "FREE"
                    else:
                        value_str = str(value).rjust(2)
                else:
                    value_str = "??"
                    
                # Add space padding
                result += f"{value_str:4} "
            
            result += "|\n"
        
        # Add bottom border
        result += "  ------------------------\n"
        
        return result
    except Exception as e:
        logger.error(f"Error formatting card for display: {str(e)}", exc_info=True)
        return f"Error formatting card: {str(e)}"

def format_pattern_for_display(pattern_positions):
    """
    Format a pattern as ASCII/text for easier visualization.
    
    Args:
        pattern_positions: List of positions (0-24) that form this pattern
    
    Returns:
        str: ASCII visualization of the pattern
    """
    try:
        # Initialize a 5x5 grid with spaces
        grid = [[' ' for _ in range(5)] for _ in range(5)]
        
        # Place X for positions in the pattern
        for pos in pattern_positions:
            if 0 <= pos < 25:
                row = pos // 5
                col = pos % 5
                grid[row][col] = 'X'
        
        # Format header
        result = "   B  I  N  G  O \n"
        result += "  --------------\n"
        
        # Format each row
        for i, row in enumerate(grid):
            result += f"{i+1}| {' '.join(row)} |\n"
        
        # Add bottom border
        result += "  --------------\n"
        
        return result
    except Exception as e:
        logger.error(f"Error formatting pattern for display: {str(e)}", exc_info=True)
        return f"Error formatting pattern: {str(e)}"
