import logging
from django.core.management.base import BaseCommand, CommandError
from bingo.models import BingoCard, Number, WinningPattern
from bingo.win_patterns import check_win_pattern, parse_card_numbers

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Verifica si un cartón ganó exactamente cuando se llamó un número específico'

    def add_arguments(self, parser):
        parser.add_argument('card_id', type=str, help='ID del cartón a verificar')
        parser.add_argument('number', type=int, help='Número específico a verificar')

    def handle(self, *args, **options):
        card_id = options['card_id']
        specific_number = options['number']

        try:
            # Obtener el cartón
            card = BingoCard.objects.get(id=card_id)
            self.stdout.write(f"Verificando cartón #{card.id} para el evento #{card.event_id}")

            # Obtener todos los números llamados para este evento
            called_numbers = list(Number.objects.filter(
                event_id=card.event_id
            ).order_by('created_at').values_list('value', flat=True))
            
            if not called_numbers:
                self.stdout.write(self.style.ERROR("No hay números llamados para este evento"))
                return
                
            if specific_number not in called_numbers:
                self.stdout.write(self.style.ERROR(f"El número {specific_number} no ha sido llamado en este evento"))
                return
                
            # Encontrar la posición del número específico en la secuencia de números llamados
            number_index = called_numbers.index(specific_number)
            
            # Obtener los números llamados hasta ese momento (inclusive)
            numbers_before = set(called_numbers[:number_index])
            numbers_including = set(called_numbers[:number_index+1])
            
            # Obtener todos los patrones activos para este evento
            event = card.event
            if event.allowed_patterns.exists():
                patterns = event.allowed_patterns.filter(is_active=True)
            else:
                patterns = WinningPattern.objects.filter(is_active=True)
                
            # Verificar cada patrón
            winning_patterns = []
            
            for pattern in patterns:
                # Verificar si el cartón estaba a un número de ganar
                was_almost_winner, _ = check_win_pattern(card.numbers, numbers_before, pattern.name)
                
                # Verificar si ahora es ganador con el número incluido
                is_winner, win_details = check_win_pattern(card.numbers, numbers_including, pattern.name)
                
                # Si pasó de casi ganador a ganador, entonces este número completó el patrón
                if not was_almost_winner and is_winner:
                    winning_patterns.append({
                        'pattern_name': pattern.display_name,
                        'details': win_details
                    })
            
            if winning_patterns:
                self.stdout.write(self.style.SUCCESS(f"¡GANADOR con el número {specific_number}!"))
                for wp in winning_patterns:
                    self.stdout.write(f"Patrón ganador: {wp['pattern_name']}")
                    self.stdout.write(f"Posiciones: {wp['details']['positions']}")
                    self.stdout.write(f"Números coincidentes: {wp['details']['matched_numbers']}")
            else:
                self.stdout.write(self.style.WARNING(
                    f"El cartón NO ganó exactamente cuando se llamó el número {specific_number}"))
                
        except BingoCard.DoesNotExist:
            raise CommandError(f"Cartón con ID {card_id} no encontrado")
        except Exception as e:
            logger.error(f"Error verificando victoria: {str(e)}", exc_info=True)
            raise CommandError(f"Error verificando victoria: {str(e)}")
