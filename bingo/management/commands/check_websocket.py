from django.core.management.base import BaseCommand
import redis
import os
import logging
import channels.layers
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    help = 'Check WebSocket configuration and Redis connection'

    def handle(self, *args, **kwargs):
        self.stdout.write('Checking WebSocket configuration...')
        
        # Check Redis connection
        self.check_redis_connection()
        
        # Check Channel Layers
        self.check_channel_layers()

    def check_redis_connection(self):
        try:
            redis_host = os.environ.get('REDIS_HOST', 'localhost')
            redis_port = int(os.environ.get('REDIS_PORT', 6379))
            redis_db = int(os.environ.get('REDIS_DB', 0))
            
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                socket_connect_timeout=5
            )
            
            if client.ping():
                self.stdout.write(self.style.SUCCESS(f"✅ Redis connection successful at {redis_host}:{redis_port}/{redis_db}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Redis ping failed at {redis_host}:{redis_port}/{redis_db}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Redis connection error: {e}"))
    
    def check_channel_layers(self):
        try:
            # Get channel layer configuration
            channel_layer = channels.layers.get_channel_layer()
            self.stdout.write(self.style.SUCCESS(f"✅ Channel layer configured: {channel_layer.__class__.__name__}"))
            
            # Try to send a test message
            test_channel = "test_websocket_channel"
            async_to_sync(channel_layer.group_add)(test_channel, "test_consumer")
            async_to_sync(channel_layer.group_send)(
                test_channel, {"type": "test.message", "text": "Hello World"}
            )
            self.stdout.write(self.style.SUCCESS("✅ Successfully sent test message through channel layer"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Channel layer error: {e}"))
