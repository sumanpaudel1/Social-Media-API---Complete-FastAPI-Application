from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, Base, get_db
from .routers import auth, posts
from .cache.redis import cache
from .models import *

# Simple & Clean Social Media API
app = FastAPI(
    title="Simple Social Media API",
    description="Clean, fast social media API with Redis caching and smart recommendations",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api")
app.include_router(posts.router, prefix="/api")

# Serve static files (our simple GUI)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {
        "message": "🎉 Simple Social Media API",
        "gui": "/static/simple.html - Ultra-minimal social media interface",
        "gui_alt": "/static/social.html - Full-featured interface",
        "docs": "/docs - Interactive API documentation",
        "status": "✅ Ready! All systems operational"
    }

@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute("SELECT 1")
        await cache.set("test", "ok", expire=60)
        cache_ok = await cache.get("test")
        return {"status": " HEALTHY", "db": "OK", "cache": "OK" if cache_ok else "ERROR"}
    except Exception as e:
        return {"status": " ERROR", "error": str(e)}

@app.get("/debug/cache")
async def debug_cache():
    """Debug endpoint to see what's cached in Redis"""
    try:
        if not cache.redis_client:
            # Redis not connected - show memory cache
            return {
                "status": "Memory Cache (Redis not connected)",
                "total_keys": len(cache.memory_cache),
                "cache_keys": list(cache.memory_cache.keys()),
                "cache_data": {k: v['value'] for k, v in cache.memory_cache.items()},
                "tip": "Run setup_redis.py to set up Redis for better performance"
            }
        
        # Get all Redis keys
        redis_client = cache.redis_client
        all_keys = await redis_client.keys("*")
        
        # Convert bytes keys to strings
        string_keys = [k.decode() if isinstance(k, bytes) else str(k) for k in all_keys]
        
        cache_data = {}
        for key in string_keys:
            try:
                value = await redis_client.get(key)
                cache_data[key] = value
            except:
                cache_data[key] = "Could not retrieve"
        
        return {
            "status": "Redis Cache",
            "total_keys": len(string_keys),
            "cache_keys": string_keys,
            "cache_data": cache_data
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test")
async def test_endpoint():
    """Test endpoint - no authentication required"""
    return {
        "status": " API is working!",
        "message": "Your FastAPI social media API is running correctly",
        "endpoints": {
            "docs": "/docs",
            "login": "POST /api/auth/login",
            "register": "POST /api/auth/register",
            "posts": "GET /api/posts (requires auth)",
            "cache_debug": "/debug/cache"
        }
    }

@app.get("/cache-status")
async def cache_status():
    """Simple cache status - see what's cached"""
    try:
        if not cache.redis_client:
            # Redis not connected - show memory cache status
            memory_keys = list(cache.memory_cache.keys())
            return {
                "status": "🗂️ Cache Overview (Memory Fallback)",
                "redis_connected": False,
                "cache_summary": {
                    "total_keys": len(memory_keys),
                    "posts_lists": len([k for k in memory_keys if k.startswith("posts:list:")]),
                    "recommendations": len([k for k in memory_keys if k.startswith("recommendations:")]),
                    "user_posts": len([k for k in memory_keys if k.startswith("user:") and ":posts" in k]),
                    "other": len([k for k in memory_keys if not any(k.startswith(prefix) for prefix in ["posts:", "recommendations:", "user:"])]),
                    "all_keys": memory_keys
                },
                "tip": "Redis not connected. Using memory cache. Run setup_redis.py to set up Redis."
            }
        
        redis_client = cache.redis_client
        all_keys = await redis_client.keys("*")
        
        # Convert bytes keys to strings first
        string_keys = [k.decode() if isinstance(k, bytes) else str(k) for k in all_keys]
        
        # Group keys by type
        cache_summary = {
            "total_keys": len(string_keys),
            "posts_lists": len([k for k in string_keys if k.startswith("posts:list:")]),
            "recommendations": len([k for k in string_keys if k.startswith("recommendations:")]),
            "user_posts": len([k for k in string_keys if k.startswith("user:") and ":posts" in k]),
            "other": len([k for k in string_keys if not any(k.startswith(prefix) for prefix in ["posts:", "recommendations:", "user:"])]),
            "all_keys": string_keys
        }
        
        return {
            "status": "🗂️ Cache Overview (Redis)",
            "redis_connected": True,
            "cache_summary": cache_summary,
            "tip": "Use /debug/cache for detailed values"
        }
    except Exception as e:
        return {"error": str(e)}

@app.on_event("startup")
async def startup():
    print("🚀 Starting Simple Social Media API...")
    await cache.connect()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Ready! Redis + PostgreSQL connected")

@app.on_event("shutdown") 
async def shutdown():
    await cache.disconnect()
    print("👋 API shutdown complete")
