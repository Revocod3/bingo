import logging
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

User = get_user_model()
logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware:
    """
    Custom middleware that takes a token from the query string and authenticates the user
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Get query parameters
        query_params = parse_qs(scope["query_string"].decode())
        token = query_params.get("token", [None])[0]
        scope["user"] = AnonymousUser()

        if token:
            try:
                # Verify the token and get the user
                token_obj = AccessToken(token)
                user_id = token_obj["user_id"]
                scope["user"] = await get_user(user_id)
                logger.info(f"WebSocket authenticated for user ID {user_id}")
            except (InvalidTokenError, ExpiredSignatureError) as e:
                logger.error(f"WebSocket auth error: {str(e)}")

        return await self.app(scope, receive, send)

def TokenAuthMiddlewareStack(app):
    return TokenAuthMiddleware(app)
