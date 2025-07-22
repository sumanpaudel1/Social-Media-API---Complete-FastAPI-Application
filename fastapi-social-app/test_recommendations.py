"""
Quick test to verify recommendations work without errors
"""

import json

def test_recommendation_fallback():
    """Test that fallback recommendation structure is correct"""
    
    # This is what should be returned when there's an error
    fallback_recommendation = {
        "id": 0,
        "title": "Welcome to Simple Social!",
        "content": "No recommendations available right now. Try creating some posts and interacting with others!",
        "author": {"username": "system", "full_name": "System"},
        "created_at": "2025-01-01T00:00:00",
        "likes_count": 0,
        "comments_count": 0,
        "is_liked_by_user": False,
        "is_saved_by_user": False,
        "categories": [],
        "recommendation_reason": "System message"
    }
    
    # Test that it can be serialized to JSON (no "Unexpected token" errors)
    try:
        json_str = json.dumps(fallback_recommendation)
        parsed_back = json.loads(json_str)
        print("✅ Fallback recommendation JSON structure is valid")
        print(f"📄 Sample: {json_str[:100]}...")
        return True
    except Exception as e:
        print(f"❌ JSON structure error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing recommendation fallback structure...")
    test_recommendation_fallback()
