from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.utils.html import format_html
import json
from django.contrib import messages
from .models import CardPurchase, Event, BingoCard, Number, PaymentMethod, TestCoinBalance, Wallet, WinningPattern, DepositRequest, SystemConfig, RatesConfig
from .views import BingoCardViewSet
from django.core.management import call_command
from io import StringIO
import sys
from django import forms

# Register models using custom admin classes
admin.site.register(Event)
admin.site.register(Number)
admin.site.register(WinningPattern)
admin.site.register(Wallet)
admin.site.register(TestCoinBalance)
admin.site.register(CardPurchase)
admin.site.register(DepositRequest)
admin.site.register(SystemConfig)

# Formulario para verificar cartón con número específico
class VerifyWinWithNumberForm(forms.Form):
    card_id = forms.CharField(label="ID del Cartón", max_length=100, required=True)
    number = forms.IntegerField(label="Número Específico", min_value=1, max_value=75, required=True)

# Custom BingoCard admin with seller functionality
@admin.register(BingoCard)
class BingoCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'user', 'is_winner', 'created_at', 'admin_actions')
    list_filter = ('event', 'is_winner', 'created_at')
    search_fields = ('id', 'user__email')
    readonly_fields = ('hash',)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-cards/', self.admin_site.admin_view(self.generate_cards_view), name='generate-cards'),
            path('download-cards-pdf/', self.admin_site.admin_view(self.download_cards_pdf_view), name='download-cards-pdf'),
            path('email-cards/', self.admin_site.admin_view(self.email_cards_view), name='email-cards'),
            path('verify-win-with-number/', self.admin_site.admin_view(self.verify_win_with_number_view), 
                 name='verify-win-with-number'),
        ]
        return custom_urls + urls
    
    def generate_cards_view(self, request):
        # Handle form submission
        if request.method == 'POST':
            event_id = request.POST.get('event_id')
            quantity = int(request.POST.get('quantity', 1))
            
            # Use the ViewSet method to generate cards
            card_viewset = BingoCardViewSet()
            card_viewset.request = request
            response = card_viewset.generate_bulk(request._request)
            
            # Store the generated cards in session for next steps
            request.session['generated_cards'] = response.data['cards']
            request.session['event_id'] = event_id
            
            self.message_user(request, f"Successfully generated {quantity} cards")
            return redirect('admin:download-cards-pdf')
        
        # Display form
        events = Event.objects.all()
        return render(request, 'admin/generate_cards_form.html', {
            'events': events,
            'title': 'Generate Bingo Cards'
        })
    
    def download_cards_pdf_view(self, request):
        if request.method == 'POST':
            # Get cards from session
            cards = request.session.get('generated_cards', [])
            event_id = request.session.get('event_id')
            
            if not cards or not event_id:
                self.message_user(request, "No hay cartones disponibles, debes tener cartones", level='error')
                return redirect('admin:generate-cards')
            
            # Create a request object for the viewset
            request._request.data = {
                'cards': cards,
                'event_id': event_id
            }
            
            # Use the ViewSet method to generate PDF
            card_viewset = BingoCardViewSet()
            card_viewset.request = request._request
            return card_viewset.download_pdf(request._request)
        
        # Display confirmation page
        card_count = len(request.session.get('generated_cards', []))
        return render(request, 'admin/download_cards_confirmation.html', {
            'card_count': card_count,
            'title': 'Download Bingo Cards'
        })
    
    def email_cards_view(self, request):
        if request.method == 'POST':
            # Get cards from session
            cards = request.session.get('generated_cards', [])
            event_id = request.session.get('event_id')
            email = request.POST.get('email')
            subject = request.POST.get('subject', 'Cartones de Bingo')
            message = request.POST.get('message', 'Tengo tus cartones de bingo adjuntos.')
            
            if not cards or not event_id or not email:
                self.message_user(request, "Missing required information", level='error')
                return redirect('admin:generate-cards')
            
            # Create a request object for the viewset
            request._request.data = {
                'cards': cards,
                'event_id': event_id,
                'email': email,
                'subject': subject,
                'message': message
            }
            
            # Use the ViewSet method to send email
            card_viewset = BingoCardViewSet()
            card_viewset.request = request._request
            response = card_viewset.email_cards(request._request)
            
            if response.data.get('success'):
                self.message_user(request, f"Email fue enviado exitosamente a {email}", level='success')
            else:
                self.message_user(request, f"Hubo un error enviando el email: {response.data.get('message')}", level='error')
            
            return redirect('admin:bingo_bingocard_changelist')
        
        # Display form
        card_count = len(request.session.get('generated_cards', []))
        return render(request, 'admin/email_cards_form.html', {
            'card_count': card_count,
            'title': 'Email Bingo Cards'
        })
    
    def verify_win_with_number_view(self, request):
        # Contexto inicial para la plantilla
        context = {
            'title': 'Verificar si un cartón ganó con un número específico',
            'form': VerifyWinWithNumberForm(),
            'result': None,
        }
        
        if request.method == 'POST':
            form = VerifyWinWithNumberForm(request.POST)
            context['form'] = form
            
            if form.is_valid():
                card_id = form.cleaned_data['card_id']
                number = form.cleaned_data['number']
                
                # Capturar la salida del comando
                output = StringIO()
                try:
                    call_command('verify_win_with_number', card_id, number, stdout=output)
                    context['result'] = {
                        'success': True,
                        'output': output.getvalue().split('\n'),
                    }
                except Exception as e:
                    context['result'] = {
                        'success': False,
                        'output': [str(e)],
                    }
        
        return render(request, 'admin/verify_win_with_number.html', context)
    
    def admin_actions(self, obj):
        """Añade botones de acción en la lista de cartones"""
        return format_html(
            '<a class="button" href="{}">Verificar con número</a>',
            reverse('admin:verify-win-with-number')
        )
    admin_actions.short_description = 'Acciones'
    
    def generate_cards_button(self, obj):
        return format_html(
            '<a class="button" href="{}">Generar Cartones</a> '
            '<a class="button" style="background-color: #417690; color: white;" href="{}">Verificar Victoria</a>',
            'generate-cards',
            'verify-win-with-number'
        )
    generate_cards_button.short_description = 'Acciones de Cartones'
    
    actions = ['generate_cards_action', 'verify_win_action']
    
    def generate_cards_action(self, request, queryset):
        return redirect('admin:generate-cards')
    
    def verify_win_action(self, request, queryset):
        """Acción para verificar victoria por número"""
        return redirect('admin:verify-win-with-number')
    verify_win_action.short_description = "Verificar victoria por número específico"

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('payment_method', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('payment_method',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('payment_method', 'is_active')
        }),
        ('Details', {
            'fields': ('details',),
            'description': 'Enter JSON format data for payment method details',
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RatesConfig)
class RatesConfigAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'last_updated')
    readonly_fields = ('last_updated',)
    fieldsets = (
        (None, {
            'fields': ('rates', 'description')
        }),
        ('Metadata', {
            'fields': ('last_updated',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        try:
            # Asegurar que el campo rates es JSON válido
            if isinstance(obj.rates, str):
                obj.rates = json.loads(obj.rates)
            super().save_model(request, obj, form, change)
        except json.JSONDecodeError:
            messages.error(request, "El campo de tasas no contiene JSON válido")
