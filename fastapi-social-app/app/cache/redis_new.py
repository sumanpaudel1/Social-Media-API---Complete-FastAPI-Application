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
            print(" Redis connected successfully")
            print(f" Redis server: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}")
        except Exception as e:
            print(f" Redis not available: {e}")
            print(" Using in-memory cache fallback")
            self.redis_client = None
        
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get data from cache by key - Redis first, memory fallback"""
        # Try Redis first
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(key)
                if cached_data:
                    print(f" Redis cache HIT: {key}")
                    return json.loads(cached_data)
            except Exception as e:
                print(f"Redis GET error: {e}")
        
        # Fallback to memory cache
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            # Check if expired
            if cache_entry.get('expire', 0) > time.time():
                print(f" Memory cache HIT: {key}")
                return cache_entry['data']
            else:
                # Remove expired entry
                del self.memory_cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, expire: int = 3600):
        """Set data in cache with expiration - Redis first, memory fallback"""
        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.set(key, json.dumps(value), ex=expire)
                print(f" Redis cache SET: {key}")
                return
            except Exception as e:
                print(f"Redis SET error: {e}")
        
        # Fallback to memory cache
        self.memory_cache[key] = {
            'data': value,
            'expire': time.time() + expire
        }
        print(f" Memory cache SET: {key}")
    
    async def delete(self, key: str):
        """Delete a key from cache"""
        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
                print(f" Redis cache DELETE: {key}")
            except Exception as e:
                print(f"Redis DELETE error: {e}")
        
        # Remove from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
            print(f" Memory cache DELETE: {key}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching a pattern"""
        # Try Redis first
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                    print(f" Redis DELETE PATTERN: {pattern} ({len(keys)} keys)")
            except Exception as e:
                print(f"Redis DELETE PATTERN error: {e}")
        
        # Remove from memory cache (simple pattern matching)
        keys_to_delete = []
        pattern_clean = pattern.replace('*', '')  # Simple pattern matching
        for key in self.memory_cache:
            if pattern_clean in key:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.memory_cache[key]
        
        if keys_to_delete:
            print(f" Memory cache DELETE PATTERN: {pattern} ({len(keys_to_delete)} keys)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        # Clean up expired entries
        now = time.time()
        expired_keys = [k for k, v in self.memory_cache.items() if v.get('expire', 0) <= now]
        for key in expired_keys:
            del self.memory_cache[key]
        
        stats = {
            "redis_connected": self.redis_client is not None,
            "memory_cache_keys": len(self.memory_cache),
            "memory_cache_entries": list(self.memory_cache.keys()),
            "cache_type": "Redis" if self.redis_client else "Memory"
        }
        return stats

# Global cache instance
cache = RedisCache()
