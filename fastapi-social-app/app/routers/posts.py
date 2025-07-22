from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..schemas.post import PostCreate, PostResponse
from ..crud.post_optimized import (
    create_post_cached, get_posts_cached, like_post_cached, 
    save_post_cached, comment_post_cached
)
from ..auth import get_current_active_user
from ..recommendations_simple import get_recommendations_for_user

router = APIRouter(prefix="/posts", tags=["Posts"])

@router.post("/", response_model=PostResponse, status_code=201)
async def create_post(
    post: PostCreate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    API 1: Create new post
    - Creates post in database
    - Updates Redis cache
    - Returns created post
    """
    new_post = await create_post_cached(db, post, current_user.id)
    return new_post

@router.get("/", response_model=List[PostResponse])
async def get_posts(
    skip: int = Query(0, ge=0, description="Skip posts"),
    limit: int = Query(20, ge=1, le=50, description="Limit posts"),
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    API 2: Get posts list (CACHED)
    - First checks Redis cache
    - If cache miss, loads from database and caches
    - For new users: shows latest posts
    - For existing users: shows recommendations + latest
    - Minimizes database hits
    """
    posts = await get_posts_cached(db, current_user.id, skip, limit)
    return posts

@router.post("/{post_id}/like")
async def like_post(
    post_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Like/unlike a post (updates cache)"""
    result = await like_post_cached(db, post_id, current_user.id)
    return {"liked": result}

@router.post("/{post_id}/save")  
async def save_post(
    post_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Save/unsave a post (updates cache)"""
    result = await save_post_cached(db, post_id, current_user.id)
    return {"saved": result}

@router.post("/{post_id}/comment")
async def comment_post(
    post_id: int,
    content: str,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add comment to post (updates cache)"""
    comment = await comment_post_cached(db, post_id, current_user.id, content)
    return comment

@router.get("/recommendations")
async def get_recommendations(
    limit: int = Query(10, ge=1, le=20),
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized recommendations based on user interactions"""
    try:
        recommendations = await get_recommendations_for_user(db, current_user.id, limit)
        return recommendations
    except Exception as e:
        print(f"❌ Error in recommendations endpoint: {e}")
        # Return fallback response
        return [
            {
                "id": 0,
                "title": "Recommendations Unavailable",
                "content": f"Sorry, recommendations are temporarily unavailable. Error: {str(e)}",
                "author": {"username": "system", "full_name": "System", "id": 0},
                "author_id": 0,
                "created_at": "2025-01-01T00:00:00",
                "updated_at": None,
                "is_active": True,
                "likes_count": 0,
                "comments_count": 0,
                "is_liked_by_user": False,
                "is_saved_by_user": False,
                "categories": [],
                "recommendation_reason": "Error fallback"
            }
        ]
