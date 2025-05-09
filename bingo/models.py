from django.db import models, transaction
from django.db.models import F
from django.conf import settings
import uuid
import string
import random

User = settings.AUTH_USER_MODEL


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    prize = models.DecimalField(max_digits=10, decimal_places=2)
    start = models.DateTimeField()
    end = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_live = models.BooleanField(default=False)
    allowed_patterns = models.ManyToManyField(
        'WinningPattern', blank=True, related_name='events')
    disabled_patterns = models.ManyToManyField(
        'WinningPattern', blank=True, related_name='disabled_in_events')

    def __str__(self):
        return self.name

    def should_be_live(self):
        """
        Determina si un evento debe estar en línea basándose en la hora actual
        Un evento debe estar en línea si la hora actual está entre start y end
        """
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        return self.is_active and self.start <= now <= self.end

    def update_live_status(self):
        """
        Actualiza el estado en línea del evento basándose en la hora actual
        Retorna True si el estado cambió, False si permaneció igual
        """
        should_be_live = self.should_be_live()
        if should_be_live != self.is_live:
            self.is_live = should_be_live
            self.save(update_fields=['is_live'])
            return True
        return False

    @classmethod
    def update_all_live_statuses(cls):
        """
        Actualiza el estado en línea de todos los eventos activos
        Retorna una lista de eventos actualizados
        """
        active_events = cls.objects.filter(is_active=True)
        updated_events = []

        for event in active_events:
            if event.update_live_status():
                updated_events.append(event)

        return updated_events


class BingoCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    numbers = models.JSONField()
    is_winner = models.BooleanField(default=False)
    hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Agregar campo correlativo para identificar cartones de forma secuencial por evento
    correlative_id = models.CharField(
        max_length=20, null=True, blank=True, db_index=True)
    # Agregar campo de metadatos para almacenar información adicional como el ID de transacción
    metadata = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        # Asegurar que el correlative_id sea único por evento
        unique_together = [['event', 'correlative_id']]

    @classmethod
    def generate_correlative_id(cls, event):
        """
        Genera un ID correlativo único para un cartón de bingo.
        El formato es: {primeras_2_letras}{ultimas_2_letras}{mes}{año}-{secuencia}

        Por ejemplo: CHMD42025-0001, CHMD42025-0002, etc.
        """
        # Extraer iniciales del evento (primeras 2 letras y últimas 2 letras)
        event_name = event.name.strip()
        prefix = ""

        # Obtener las primeras 2 letras
        if event_name:
            first_letters = ''.join(c for c in event_name if c.isalpha())
            prefix += first_letters[:2].upper()
        else:
            prefix += "EV"  # Prefijo por defecto si no hay nombre

        # Obtener las últimas 2 letras
        if event_name and len(event_name) >= 2:
            last_letters = ''.join(c for c in event_name if c.isalpha())
            prefix += last_letters[-2:].upper()
        else:
            prefix += "XX"  # Sufijo por defecto si no hay suficientes letras

        # Añadir información de fecha (mes y año)
        import datetime
        today = datetime.date.today()
        month = str(today.month).zfill(1)  # Mes con un dígito
        year = str(today.year)[-4:]  # Los 4 dígitos del año

        prefix += f"{month}{year}"

        # Obtener el último correlativo para este evento con el nuevo formato
        with transaction.atomic():
            last_card = cls.objects.filter(
                event=event,
                correlative_id__startswith=f"{prefix}-"
            ).order_by('-correlative_id').first()

            if last_card and last_card.correlative_id:
                # Extraer el número de secuencia del último correlativo
                try:
                    last_seq = int(last_card.correlative_id.split('-')[1])
                    next_seq = last_seq + 1
                except (ValueError, IndexError):
                    next_seq = 1
            else:
                next_seq = 1

            # Formatear el correlativo con ceros a la izquierda (4 dígitos)
            return f"{prefix}-{next_seq:04d}"


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class Number(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='numbers')
    value = models.IntegerField()
    called_at = models.DateTimeField(auto_now_add=True)
    # Track if this number has been drawn
    drawn = models.BooleanField(default=True)

    class Meta:
        ordering = ['-called_at']
        unique_together = ['event', 'value']

    def __str__(self):
        return f"{self.value} - {self.event}"


class TestCoinBalance(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='test_coins')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'test_coin_balance'
        indexes = [
            models.Index(fields=['user']),  # Index for quick user lookups
        ]

    def __str__(self):
        return f"{self.user.email}: {self.balance} coins"

    @classmethod
    @transaction.atomic
    def deduct_coins(cls, user_id, amount):
        """Safely deduct coins with optimistic concurrency control"""
        # Select for update to prevent race conditions
        balance = cls.objects.select_for_update().get(user_id=user_id)

        # Convert amount to Decimal to ensure proper decimal arithmetic
        from decimal import Decimal, ROUND_DOWN

        # Normalize both values to 2 decimal places to avoid precision issues
        amount = Decimal(str(amount)).quantize(
            Decimal('0.01'), rounding=ROUND_DOWN)
        current_balance = Decimal(str(balance.balance)).quantize(
            Decimal('0.01'), rounding=ROUND_DOWN)

        # Compare the normalized values
        if current_balance < amount:
            return False, f"No tienes saldo suficiente. Necesitas tener {amount:.2f}, y tu saldo es {current_balance:.2f}."

        # Update the balance using the normalized amount
        balance.balance = current_balance - amount
        balance.save()
        balance.refresh_from_db()
        return True, balance


class DepositRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='deposit_requests')
    amount = models.PositiveIntegerField()
    unique_code = models.CharField(max_length=10, unique=True)
    reference = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_deposits')
    admin_notes = models.TextField(blank=True, null=True)
    payment_method = models.CharField(
        max_length=50, blank=True, null=True)  # Add this field

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['unique_code']),
        ]

    def __str__(self):
        return f"{self.user.email}: {self.amount} coins - {self.get_status_display()}"

    @staticmethod
    def generate_unique_code():
        """Generate a random, unique code for the deposit"""
        while True:
            # Generate a code with 8 characters (letters and numbers)
            code = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=8))
            # Check if code already exists
            if not DepositRequest.objects.filter(unique_code=code).exists():
                return code

    @classmethod
    @transaction.atomic
    def approve(cls, deposit_id, staff_user):
        """Approve deposit and update user balance"""
        deposit = cls.objects.select_for_update().get(id=deposit_id, status='pending')

        # Update balance
        balance, created = TestCoinBalance.objects.select_for_update().get_or_create(
            user=deposit.user, defaults={"balance": 0}
        )
        balance.balance += deposit.amount
        balance.save()

        # Update deposit status
        deposit.status = 'approved'
        deposit.approved_by = staff_user
        deposit.save()

        return deposit, balance


class CardPurchase(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='card_purchases')
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='card_purchases')
    cards_owned = models.PositiveIntegerField(default=0)
    purchase_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        # Check if the existing migrations created a different table name
        # For example, if it created "bingo_cardpurchase" instead
        db_table = 'card_purchases'  # You might need to change this to match existing table
        unique_together = ['user', 'event']
        indexes = [
            models.Index(fields=['user', 'event']),
        ]

    def __str__(self):
        return f"{self.user.email}: {self.cards_owned} cards for {self.event.name}"


class WinningPattern(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    positions = models.JSONField(
        help_text="JSON array of positions that form this pattern")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_patterns')

    def __str__(self):
        return self.display_name


class SystemConfig(models.Model):
    """System configuration settings"""
    card_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.20,
                                     verbose_name="Card Price")
    seller_card_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.15,
                                            verbose_name="Seller Card Price")
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configuration"

    @classmethod
    def get_card_price(cls, user=None):
        """Get the current card price, or create with default if none exists
        If user is a seller, returns the discounted seller price
        """
        config, created = cls.objects.get_or_create(pk=1)

        # Check if user is a seller and apply discount
        if user and hasattr(user, 'groups') and user.groups.filter(name='Seller').exists():
            return config.seller_card_price

        return config.card_price

    @classmethod
    def update_card_price(cls, price, user=None):
        """Update the card price"""
        config, created = cls.objects.get_or_create(pk=1)
        config.card_price = price
        config.updated_by = user
        config.save()
        return config

    @classmethod
    def update_seller_card_price(cls, price, user=None):
        """Update the seller card price"""
        config, created = cls.objects.get_or_create(pk=1)
        config.seller_card_price = price
        config.updated_by = user
        config.save()
        return config

    def __str__(self):
        return f"System Configuration (Card Price: {self.card_price}, Seller Price: {self.seller_card_price})"


class PaymentMethod(models.Model):
    """
    Model to store payment method configurations that can be managed by admin
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_method = models.CharField(max_length=50, unique=True)
    details = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.payment_method


class RatesConfig(models.Model):
    """
    Model to store exchange rates configuration
    """
    rates = models.JSONField(default=dict)
    description = models.CharField(max_length=255, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Tasas"
        verbose_name_plural = "Configuración de Tasas"

    def __str__(self):
        return f"Configuración de Tasas (Actualizado: {self.last_updated.strftime('%Y-%m-%d %H:%M')})"

    @classmethod
    def get_current(cls):
        """Get the current rates configuration or create a default one"""
        rates_config, _ = cls.objects.get_or_create(
            pk=1,
            defaults={'rates': {},
                      'description': 'Configuración de tasas predeterminada'}
        )
        return rates_config
