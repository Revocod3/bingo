from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # WebSocket connection for a specific bingo event
    path('ws/bingo/event/<int:event_id>/', consumers.BingoConsumer.as_asgi()),
]
