"""
Test the cache system to make sure it works
"""

import asyncio
import time

async def test_cache():
    """Test the cache system"""
    
    try:
        # Import our cache
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app.cache.redis import cache
        
        print("🧪 Testing cache system...")
        
        # Connect to cache
        await cache.connect()
        
        # Test set and get
        test_data = {"message": "Hello cache!", "timestamp": time.time()}
        
        print("📝 Setting test data...")
        await cache.set("test_key", test_data, expire=60)
        
        print("📖 Getting test data...")
        retrieved = await cache.get("test_key")
        
        if retrieved:
            print(f"✅ Cache working! Retrieved: {retrieved}")
        else:
            print("❌ Cache not working - no data retrieved")
        
        # Test delete
        print("🗑️ Testing delete...")
        await cache.delete("test_key")
        
        deleted_check = await cache.get("test_key")
        if deleted_check is None:
            print("✅ Delete working!")
        else:
            print("❌ Delete not working")
        
        print("\n🎉 Cache test completed!")
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cache())
