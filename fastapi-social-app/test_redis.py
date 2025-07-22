"""
Test Redis connection and cache functionality
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

async def test_redis_connection():
    """Test if Redis is running and accessible"""
    
    print("🔍 Testing Redis connection...")
    print(f"📍 Redis Host: {os.getenv('REDIS_HOST', 'localhost')}")
    print(f"📍 Redis Port: {os.getenv('REDIS_PORT', '6379')}")
    
    try:
        # Try direct Redis connection
        import redis.asyncio as redis
        
        client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        
        # Test ping
        result = await client.ping()
        print(f"✅ Redis PING successful: {result}")
        
        # Test set/get
        await client.set("test_key", "test_value", ex=60)
        value = await client.get("test_key")
        print(f"✅ Redis SET/GET test: {value}")
        
        # Check existing keys
        keys = await client.keys("*")
        print(f"📊 Total keys in Redis: {len(keys)}")
        if keys:
            print(f"🔑 Sample keys: {keys[:5]}")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 To fix this:")
        print("   1. Install Redis: https://redis.io/download")
        print("   2. Or use Docker: docker run -d -p 6379:6379 redis")
        print("   3. Make sure Redis is running on localhost:6379")
        return False

async def test_app_cache():
    """Test the app's cache system"""
    print("\n🧪 Testing app cache system...")
    
    try:
        from app.cache.redis import cache
        
        await cache.connect()
        
        # Test cache operations
        test_data = {"message": "Hello Cache!", "timestamp": "2025-01-01"}
        
        await cache.set("test_app_cache", test_data, expire=300)
        print("✅ Cache SET successful")
        
        retrieved = await cache.get("test_app_cache")
        print(f"✅ Cache GET successful: {retrieved}")
        
        # List all keys
        keys = await cache.redis_client.keys("*")
        print(f"📊 App cache keys: {len(keys)}")
        for key in keys[:10]:  # Show first 10 keys
            print(f"   🔑 {key}")
        
        await cache.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ App cache test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_redis_connection())
    asyncio.run(test_app_cache())
