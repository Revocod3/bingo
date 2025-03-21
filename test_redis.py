import os
import redis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_connection():
    """Test Redis connection with the configured settings."""
    try:
        # Get Redis connection parameters from environment or use defaults
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = int(os.environ.get('REDIS_PORT', 6379))
        redis_db = int(os.environ.get('REDIS_DB', 0))
        
        # Create Redis client
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            socket_connect_timeout=5
        )
        
        # Test connection with a ping
        response = client.ping()
        if response:
            logger.info(f"✅ Successfully connected to Redis at {redis_host}:{redis_port}/{redis_db}")
            return True
        else:
            logger.error(f"❌ Failed to ping Redis at {redis_host}:{redis_port}/{redis_db}")
            return False
    except redis.exceptions.ConnectionError as e:
        logger.error(f"❌ Redis connection error: {e}")
        logger.info("Make sure Redis server is running with: sudo service redis-server status")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error connecting to Redis: {e}")
        return False

if __name__ == "__main__":
    test_redis_connection()
