import redis.asyncio as redis
import json
import os
import time
from typing import Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()

class RedisCache:
    """
    Redis cache manager with in-memory fallback
    This reduces database load and improves response times.
    """
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, Dict] = {}  # Fallback cache
        self.cache_enabled = True
    
    async def connect(self):
        """Initialize Redis connection with fallback"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True
            )
            # Test the connection
            await self.redis_client.ping()
            print("🔴 Redis connected successfully")
            print(f"📍 Redis server: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}")
        except Exception as e:
            print(f"⚠️ Redis not available: {e}")
            print("� Using in-memory cache fallback")
            self.redis_client = None
        
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get data from cache by key
        Returns None if key doesn't exist
        """
        if not self.redis_client:
            # Use memory fallback
            if key in self.memory_cache:
                cached = self.memory_cache[key]
                if time.time() < cached['expires']:
                    return cached['value']
                else:
                    # Expired
                    del self.memory_cache[key]
            return None
        
        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            print(f"❌ Error getting from cache: {e}")
            # Try memory fallback
            if key in self.memory_cache:
                cached = self.memory_cache[key]
                if time.time() < cached['expires']:
                    return cached['value']
            return None
    
    async def set(self, key: str, value: Any, expire: int = 3600):
        """
        Set data in cache with expiration time (default 1 hour)
        expire: expiration time in seconds
        """
        if not self.redis_client:
            # Use memory fallback
            self.memory_cache[key] = {
                'value': value,
                'expires': time.time() + expire
            }
            return
        
        try:
            await self.redis_client.set(
                key, 
                json.dumps(value, default=str), 
                ex=expire
            )
        except Exception as e:
            print(f"❌ Error setting cache: {e}")
            # Fallback to memory
            self.memory_cache[key] = {
                'value': value,
                'expires': time.time() + expire
            }
    
    async def delete(self, key: str):
        """Delete specific key from cache"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            print(f"Error deleting from cache: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching a pattern (e.g., 'user_posts:*')"""
        if not self.redis_client:
            return
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Error deleting pattern from cache: {e}")

# Global cache instance
cache = RedisCache()
