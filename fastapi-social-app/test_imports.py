"""
Quick test to verify the app starts without import errors
"""
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("🧪 Testing imports...")
    
    # Test basic imports
    from app.main import app
    print("✅ Main app imports successfully")
    
    from app.recommendations_simple import get_recommendations_for_user
    print("✅ Recommendations import successfully")
    
    from app.routers.posts import router
    print("✅ Posts router imports successfully")
    
    from app.routers.auth import router as auth_router
    print("✅ Auth router imports successfully")
    
    print("\n🎉 All imports successful! The app should start without errors.")
    print("\n🚀 To start the server, run:")
    print("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Check your imports and dependencies!")
    
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
