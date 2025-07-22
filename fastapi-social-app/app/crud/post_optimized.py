"""
Optimized CRUD operations with Redis caching
Minimizes database hits by aggressive caching strategy
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc, func, and_
from typing import List, Dict, Any, Optional
import json

from ..models.post import Post, PostLike, Comment, SavedPost, Category
from ..models.user import User
from ..schemas.post import PostCreate
from ..cache.redis import cache

# Cache keys
POSTS_LIST_KEY = "posts:list:{skip}:{limit}"
USER_POSTS_KEY = "user:{user_id}:posts"
POST_DETAIL_KEY = "post:{post_id}:user:{user_id}"
USER_INTERACTIONS_KEY = "user:{user_id}:interactions"

async def create_post_cached(db: AsyncSession, post: PostCreate, author_id: int) -> Dict[str, Any]:
    """
    Create post and update cache
    1. Save to database
    2. Clear relevant caches
    3. Return formatted post
    """
    # Create post in database
    db_post = Post(
        title=post.title,
        content=post.content,
        image_url=post.image_url,
        author_id=author_id
    )
    
    # Add categories if specified
    if post.category_ids:
        categories = await db.execute(
            select(Category).where(Category.id.in_(post.category_ids))
        )
        db_post.categories = categories.scalars().all()
    
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    
    # Clear caches that need updating
    await cache.delete_pattern("posts:list:*")  # Clear all post lists
    await cache.delete(USER_POSTS_KEY.format(user_id=author_id))  # Clear user's posts
    
    # Load post with relationships for response
    result = await db.execute(
        select(Post).options(
            selectinload(Post.author),
            selectinload(Post.categories),
            selectinload(Post.likes),
            selectinload(Post.comments)
        ).where(Post.id == db_post.id)
    )
    post_with_relations = result.scalars().first()
    
    return await format_post_response(post_with_relations, author_id)

async def get_posts_cached(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get posts with aggressive caching
    1. Check Redis cache first
    2. If cache miss, load from database and cache
    3. Return formatted posts
    """
    cache_key = POSTS_LIST_KEY.format(skip=skip, limit=limit)
    
    # Try to get from cache first
    cached_posts = await cache.get(cache_key)
    if cached_posts:
        print(f"📋 Serving posts from cache for user {user_id}")
        # Add user-specific interaction data to cached posts
        return await add_user_interactions_to_posts(cached_posts, user_id, db)
    
    print(f"🗄️ Loading posts from database for user {user_id}")
    
    # Load from database
    result = await db.execute(
        select(Post).options(
            selectinload(Post.author),
            selectinload(Post.categories),
            selectinload(Post.likes),
            selectinload(Post.comments).selectinload(Comment.user)
        ).where(Post.is_active == True)
        .order_by(desc(Post.created_at))
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()
    
    # Format posts for cache (without user-specific data)
    cached_data = []
    for post in posts:
        post_data = await format_post_response(post, user_id=None)  # No user-specific data for cache
        cached_data.append(post_data)
    
    # Cache for 10 minutes
    await cache.set(cache_key, cached_data, expire=600)
    
    # Add user-specific interactions before returning
    return await add_user_interactions_to_posts(cached_data, user_id, db)

async def add_user_interactions_to_posts(posts: List[Dict], user_id: int, db: AsyncSession) -> List[Dict]:
    """
    Add user-specific interaction data (liked, saved) to cached posts
    This allows us to cache posts globally but add user context
    """
    if not posts:
        return posts
    
    post_ids = [post["id"] for post in posts]
    
    # Get user's likes for these posts
    likes_result = await db.execute(
        select(PostLike.post_id).where(
            and_(PostLike.user_id == user_id, PostLike.post_id.in_(post_ids))
        )
    )
    liked_post_ids = set(row[0] for row in likes_result.fetchall())
    
    # Get user's saved posts
    saves_result = await db.execute(
        select(SavedPost.post_id).where(
            and_(SavedPost.user_id == user_id, SavedPost.post_id.in_(post_ids))
        )
    )
    saved_post_ids = set(row[0] for row in saves_result.fetchall())
    
    # Add user interaction flags to posts
    for post in posts:
        post["is_liked_by_user"] = post["id"] in liked_post_ids
        post["is_saved_by_user"] = post["id"] in saved_post_ids
    
    return posts

async def like_post_cached(db: AsyncSession, post_id: int, user_id: int) -> bool:
    """
    Like/unlike post and update cache
    Returns True if liked, False if unliked
    """
    # Check if already liked
    result = await db.execute(
        select(PostLike).where(
            and_(PostLike.post_id == post_id, PostLike.user_id == user_id)
        )
    )
    existing_like = result.scalars().first()
    
    if existing_like:
        # Unlike
        await db.delete(existing_like)
        await db.commit()
        liked = False
    else:
        # Like
        like = PostLike(post_id=post_id, user_id=user_id)
        db.add(like)
        await db.commit()
        liked = True
    
    # Clear relevant caches
    await cache.delete_pattern("posts:list:*")
    await cache.delete_pattern(f"post:{post_id}:*")
    await cache.delete(USER_INTERACTIONS_KEY.format(user_id=user_id))
    
    return liked

async def save_post_cached(db: AsyncSession, post_id: int, user_id: int) -> bool:
    """
    Save/unsave post and update cache
    Returns True if saved, False if unsaved
    """
    # Check if already saved
    result = await db.execute(
        select(SavedPost).where(
            and_(SavedPost.post_id == post_id, SavedPost.user_id == user_id)
        )
    )
    existing_save = result.scalars().first()
    
    if existing_save:
        # Unsave
        await db.delete(existing_save)
        await db.commit()
        saved = False
    else:
        # Save
        save = SavedPost(post_id=post_id, user_id=user_id)
        db.add(save)
        await db.commit()
        saved = True
    
    # Clear relevant caches
    await cache.delete_pattern("posts:list:*")
    await cache.delete(USER_INTERACTIONS_KEY.format(user_id=user_id))
    
    return saved

async def comment_post_cached(db: AsyncSession, post_id: int, user_id: int, content: str) -> Dict[str, Any]:
    """
    Add comment to post and update cache
    """
    comment = Comment(
        content=content,
        post_id=post_id,
        user_id=user_id
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    
    # Clear relevant caches
    await cache.delete_pattern("posts:list:*")
    await cache.delete_pattern(f"post:{post_id}:*")
    
    # Load comment with user info
    result = await db.execute(
        select(Comment).options(selectinload(Comment.user)).where(Comment.id == comment.id)
    )
    comment_with_user = result.scalars().first()
    
    return {
        "id": comment_with_user.id,
        "content": comment_with_user.content,
        "post_id": comment_with_user.post_id,
        "user_id": comment_with_user.user_id,
        "created_at": comment_with_user.created_at.isoformat(),
        "user": {
            "id": comment_with_user.user.id,
            "username": comment_with_user.user.username,
            "full_name": comment_with_user.user.full_name
        }
    }

async def format_post_response(post: Post, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Format post for API response
    If user_id is None, don't include user-specific interaction data (for caching)
    """
    post_data = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "image_url": post.image_url,
        "author_id": post.author_id,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        "is_active": post.is_active,
        "author": {
            "id": post.author.id,
            "username": post.author.username,
            "full_name": post.author.full_name,
            "profile_picture": post.author.profile_picture
        },
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "created_at": cat.created_at.isoformat()
            }
            for cat in (post.categories or [])
        ],
        "likes_count": len(post.likes or []),
        "comments_count": len(post.comments or []),
    }
    
    # Add user-specific data only if user_id provided
    if user_id is not None:
        post_data.update({
            "is_liked_by_user": any(like.user_id == user_id for like in (post.likes or [])),
            "is_saved_by_user": False  # Will be set by add_user_interactions_to_posts
        })
    else:
        post_data.update({
            "is_liked_by_user": False,
            "is_saved_by_user": False
        })
    
    return post_data
