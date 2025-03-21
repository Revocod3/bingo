from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Updated pattern to handle both cases: with event_id or empty string
    re_path(r'ws/event/(?P<event_id>\w*)/$', consumers.BingoConsumer.as_asgi()),
]
