from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.html import format_html
from .models import CardPurchase, Event, BingoCard, Number, PaymentMethod, TestCoinBalance, Wallet, WinningPattern, DepositRequest, SystemConfig
from .views import BingoCardViewSet

# Register models using custom admin classes
admin.site.register(Event)
admin.site.register(Number)
admin.site.register(WinningPattern)
admin.site.register(Wallet)
admin.site.register(TestCoinBalance)
admin.site.register(CardPurchase)
admin.site.register(DepositRequest)
admin.site.register(SystemConfig)

# Custom BingoCard admin with seller functionality
@admin.register(BingoCard)
class BingoCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'user', 'is_winner', 'created_at')
    list_filter = ('event', 'is_winner', 'created_at')
    search_fields = ('id', 'user__email')
    readonly_fields = ('hash',)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate-cards/', self.admin_site.admin_view(self.generate_cards_view), name='generate-cards'),
            path('download-cards-pdf/', self.admin_site.admin_view(self.download_cards_pdf_view), name='download-cards-pdf'),
            path('email-cards/', self.admin_site.admin_view(self.email_cards_view), name='email-cards'),
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
                self.message_user(request, "No cards available. Generate cards first.", level='error')
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
            subject = request.POST.get('subject', 'Your Bingo Cards')
            message = request.POST.get('message', 'Here are your bingo cards for the event.')
            
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
                self.message_user(request, f"Cards successfully sent to {email}")
            else:
                self.message_user(request, f"Failed to send email: {response.data.get('message')}", level='error')
            
            return redirect('admin:bingo_bingocard_changelist')
        
        # Display form
        card_count = len(request.session.get('generated_cards', []))
        return render(request, 'admin/email_cards_form.html', {
            'card_count': card_count,
            'title': 'Email Bingo Cards'
        })
    
    def generate_cards_button(self, obj):
        return format_html('<a class="button" href="{}">Generate Cards</a>', 'generate-cards')
    
    generate_cards_button.short_description = 'Generate Cards'
    
    actions = ['generate_cards_action']
    
    def generate_cards_action(self, request, queryset):
        return redirect('admin:generate-cards')
    
    generate_cards_action.short_description = "Generate new bingo cards"

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
