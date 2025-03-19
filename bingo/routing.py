from django.urls import re_path
from . import consumers  # Import consumers module

websocket_urlpatterns = [
    # Your websocket patterns
    # Example: re_path(r'ws/bingo/(?P<room_name>\w+)/$', consumers.BingoConsumer.as_asgi()),
]
