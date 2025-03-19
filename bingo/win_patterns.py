import logging

logger = logging.getLogger(__name__)

def check_win_pattern(card_numbers, called_numbers, pattern_type='bingo'):
    """
    Check if the specified pattern is completed with called numbers
    
    Parameters:
    - card_numbers: Dictionary with B, I, N, G, O keys containing lists of numbers
    - called_numbers: Set of numbers that have been called
    - pattern_type: Type of winning pattern to check
    
    Returns:
    - Boolean indicating whether the pattern is completed
    """
    try:
        # Extract the actual numbers from the card format
        b_numbers = card_numbers['B']
        i_numbers = card_numbers['I']
        n_numbers = card_numbers['N']
        g_numbers = card_numbers['G']
        o_numbers = card_numbers['O']
        
        # The 5x5 grid representation of the card
        grid = [
            b_numbers,
            i_numbers,
            n_numbers,
            g_numbers,
            o_numbers
        ]
        
        # Free space in the center
        free_space_col = card_numbers.get('free_space', {}).get('column', 'N')
        free_space_row = card_numbers.get('free_space', {}).get('row', 2)
        
        # Map column letter to index
        col_to_index = {'B': 0, 'I': 1, 'N': 2, 'G': 3, 'O': 4}
        free_space_col_idx = col_to_index.get(free_space_col, 2)
        
        # Regular bingo patterns
        if pattern_type == 'bingo':
            # Full card win (all numbers called)
            for col_idx, col in enumerate(grid):
                for row_idx, number in enumerate(col):
                    # Skip the free space
                    if col_idx == free_space_col_idx and row_idx == free_space_row:
                        continue
                    
                    if number not in called_numbers:
                        return False
            return True
            
        elif pattern_type == 'row':
            # Any horizontal line
            for row_idx in range(5):
                row_complete = True
                for col_idx in range(5):
                    # Skip the free space
                    if col_idx == free_space_col_idx and row_idx == free_space_row:
                        continue
                    
                    number = grid[col_idx][row_idx]
                    if number not in called_numbers:
                        row_complete = False
                        break
                
                if row_complete:
                    return True
            return False
            
        elif pattern_type == 'column':
            # Any vertical line
            for col_idx in range(5):
                col_complete = True
                for row_idx in range(5):
                    # Skip the free space
                    if col_idx == free_space_col_idx and row_idx == free_space_row:
                        continue
                    
                    number = grid[col_idx][row_idx]
                    if number not in called_numbers:
                        col_complete = False
                        break
                
                if col_complete:
                    return True
            return False
            
        elif pattern_type == 'diagonal':
            # Diagonal from top-left to bottom-right
            diagonal1_complete = True
            for i in range(5):
                # Skip the free space
                if i == free_space_col_idx and i == free_space_row:
                    continue
                
                number = grid[i][i]
                if number not in called_numbers:
                    diagonal1_complete = False
                    break
            
            if diagonal1_complete:
                return True
            
            # Diagonal from top-right to bottom-left
            diagonal2_complete = True
            for i in range(5):
                # Skip the free space
                if i == free_space_col_idx and 4-i == free_space_row:
                    continue
                
                number = grid[i][4-i]
                if number not in called_numbers:
                    diagonal2_complete = False
                    break
            
            return diagonal2_complete
        
        # Advanced patterns can be added here
        elif pattern_type == 'corners':
            # Four corners
            corners = [
                grid[0][0],  # Top-left
                grid[0][4],  # Bottom-left
                grid[4][0],  # Top-right
                grid[4][4]   # Bottom-right
            ]
            
            for number in corners:
                if number not in called_numbers:
                    return False
            return True
            
        elif pattern_type == 'postage_stamp':
            # 2x2 in any corner
            # Check top-left
            if all(grid[col_idx][row_idx] in called_numbers for col_idx in [0, 1] for row_idx in [0, 1]):
                return True
            # Check top-right
            if all(grid[col_idx][row_idx] in called_numbers for col_idx in [3, 4] for row_idx in [0, 1]):
                return True
            # Check bottom-left
            if all(grid[col_idx][row_idx] in called_numbers for col_idx in [0, 1] for row_idx in [3, 4]):
                return True
            # Check bottom-right
            if all(grid[col_idx][row_idx] in called_numbers for col_idx in [3, 4] for row_idx in [3, 4]):
                return True
            return False
            
        else:
            logger.warning(f"Unknown pattern type: {pattern_type}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking win pattern: {str(e)}", exc_info=True)
        return False
