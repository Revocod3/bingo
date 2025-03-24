# Bingo API

## Winning Patterns System

The Bingo API now includes a full winning patterns system that allows:

1. **Creating Custom Patterns**: Define any pattern on the 5x5 bingo grid
2. **Verifying Wins**: Check if a card has completed a winning pattern
3. **Managing Patterns**: Enable/disable patterns for different events

### Card Structure

Bingo cards are stored as a list of strings in the format `B1`, `I16`, etc., representing the value in each position on the card. The middle position (row 3, column 3) is reserved for the free space, represented as `N0`.

### Pattern Structure

Patterns are defined as arrays of positions (0-24) on the 5x5 grid, with positions numbered from left to right, top to bottom:

### Default Patterns

The system comes pre-loaded with these patterns:

- **Horizontal Lines**: All 5 rows (top, second, middle, fourth, bottom)
- **Vertical Lines**: All 5 columns
- **Diagonal Lines**: Both diagonals
- **Special Patterns**: Four corners, center square, X shape, plus sign

### Endpoints

#### Winning Patterns

- `GET /api/winning-patterns/`: List all winning patterns
- `POST /api/winning-patterns/`: Create a winning pattern
- `GET /api/winning-patterns/{id}/`: Get pattern details
- `PUT /api/winning-patterns/{id}/`: Update a pattern
- `DELETE /api/winning-patterns/{id}/`: Delete a pattern
- `GET /api/winning-patterns/active/`: Get only active patterns
- `GET /api/winning-patterns/with_positions_map/`: Get patterns with grid representation
- `GET /api/winning-patterns/{id}/visualize/`: ASCII visualization of a pattern
- `POST /api/winning-patterns/validate/`: Validate pattern positions

#### Event Pattern Management

- `GET /api/events/{id}/patterns/`: Get patterns allowed for an event
- `POST /api/events/{id}/set_patterns/`: Set allowed patterns for an event
- `POST /api/events/{id}/add_pattern/`: Add a pattern to an event
- `POST /api/events/{id}/remove_pattern/`: Remove a pattern from an event

#### Card Win Verification

- `POST /api/cards/claim/`: Claim a bingo win for a card
- `GET /api/cards/{id}/verify_pattern/`: Check if a card has a specific pattern

### Testing Pattern Detection

Use the management command to test pattern detection:

```bash
# Test all patterns with all card formats
python manage.py test_patterns

# Test a specific pattern
python manage.py test_patterns --pattern row_1

# Test with a specific card
python manage.py test_patterns --card-id <uuid>

# Test cards from a specific event
python manage.py test_patterns --event-id <uuid>
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis (for caching and websocket support)

### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bingo-api.git
   cd bingo-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (create a `.env` file):
   ```
   DEBUG=True
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgres://user:password@localhost:5432/bingo
   REDIS_URL=redis://localhost:6379/0
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Load default patterns:
   ```bash
   python manage.py load_default_patterns
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## API Usage Examples

### Creating a New Pattern

```python
import requests

response = requests.post('http://localhost:8000/api/winning-patterns/', json={
    'name': 'My Custom Pattern',
    'description': 'A custom pattern in the shape of a star',
    'cells': [2, 6, 8, 12, 16, 18, 22],
    'is_active': True
})

pattern = response.json()
print(f"Created pattern with ID: {pattern['id']}")
```

### Checking if a Card Has a Winning Pattern