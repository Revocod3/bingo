"""
ASGI config for core project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django
from django.core.asgi import get_asgi_application

# Configure Django settings before importing any Django code that uses settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Only import after Django is set up
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
# Import the TokenAuthMiddleware
from bingo.middleware import TokenAuthMiddlewareStack
import bingo.routing

# Simple no-op handler for lifespan protocol
class LifespanApp:
    def __init__(self):
        self.startup_complete = False
        self.shutdown_complete = False

    async def __call__(self, scope, receive, send):
        if scope["type"] != "lifespan":
            return
            
        while True:
            message = await receive()
            
            if message["type"] == "lifespan.startup":
                # Do startup logic here
                self.startup_complete = True
                await send({"type": "lifespan.startup.complete"})
                
            elif message["type"] == "lifespan.shutdown":
                # Do shutdown logic here
                self.shutdown_complete = True
                await send({"type": "lifespan.shutdown.complete"})
                return

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddlewareStack(  # Use our custom auth middleware
            URLRouter(
                bingo.routing.websocket_urlpatterns
            )
        )
    ),
    "lifespan": LifespanApp(),
})
