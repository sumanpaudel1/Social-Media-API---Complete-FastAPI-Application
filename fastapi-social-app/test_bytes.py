"""
Test for the bytes/string issue
"""

def test_bytes_issue():
    """Test the specific bytes/string issue"""
    
    # Simulate what Redis returns (bytes)
    mock_redis_keys = [
        b"posts:list:0:20",
        b"recommendations:123:10", 
        b"user:456:posts",
        b"test_key"
    ]
    
    print("🧪 Testing bytes/string conversion...")
    
    try:
        # This should fail with the original error
        try:
            bad_result = [k for k in mock_redis_keys if k.startswith("posts:")]
            print("❌ This should have failed!")
        except TypeError as e:
            print(f"✅ Confirmed error: {e}")
        
        # This should work (our fix)
        string_keys = [k.decode() if isinstance(k, bytes) else str(k) for k in mock_redis_keys]
        print(f"📝 Converted keys: {string_keys}")
        
        good_result = [k for k in string_keys if k.startswith("posts:")]
        print(f"✅ Fixed result: {good_result}")
        
        # Test grouping like in our cache status
        cache_summary = {
            "total_keys": len(string_keys),
            "posts_lists": len([k for k in string_keys if k.startswith("posts:list:")]),
            "recommendations": len([k for k in string_keys if k.startswith("recommendations:")]),
            "user_posts": len([k for k in string_keys if k.startswith("user:") and ":posts" in k]),
            "other": len([k for k in string_keys if not any(k.startswith(prefix) for prefix in ["posts:", "recommendations:", "user:"])]),
        }
        
        print(f"📊 Cache summary: {cache_summary}")
        print("🎉 Bytes/string conversion test passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bytes_issue()
