from django.db import migrations
import uuid

def create_default_patterns(apps, schema_editor):
    # Get the models using the historical versions from apps
    WinningPattern = apps.get_model('bingo', 'WinningPattern')
    CustomUser = apps.get_model('users', 'CustomUser')
    
    # Try to get an admin user to set as creator
    try:
        admin_user = CustomUser.objects.filter(is_superuser=True).first()
    except:
        # If no admin exists or there's an error, try to get any user
        try:
            admin_user = CustomUser.objects.first()
        except:
            # If still no user, proceed without a user reference
            admin_user = None
    
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
    
    # Create patterns
    for pattern_data in default_patterns:
        # Skip if pattern already exists
        if WinningPattern.objects.filter(name=pattern_data['name']).exists():
            continue
            
        # Create pattern with or without a creator user
        pattern_kwargs = {
            'id': uuid.uuid4(),
            'name': pattern_data['name'],
            'display_name': pattern_data['display_name'],
            'positions': pattern_data['positions'],
            'is_active': True,
        }
        
        # Only add created_by if we have a valid user
        if admin_user is not None:
            pattern_kwargs['created_by'] = admin_user
            
        WinningPattern.objects.create(**pattern_kwargs)

def reverse_migration(apps, schema_editor):
    # Delete default patterns if needed
    WinningPattern = apps.get_model('bingo', 'WinningPattern')
    WinningPattern.objects.filter(name__in=[
        'row_1', 'row_2', 'row_3', 'row_4', 'row_5',
        'col_1', 'col_2', 'col_3', 'col_4', 'col_5',
        'diag_1', 'diag_2', 'corners', 'center', 'blackout',
        'x_shape', 'plus_sign'
    ]).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('bingo', '0006_add_winning_patterns'),
    ]

    operations = [
        migrations.RunPython(create_default_patterns, reverse_migration),
    ]
