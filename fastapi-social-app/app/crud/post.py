from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc, func, and_
from typing import Optional, List, Dict, Any
from ..models.post import Post, Category, PostLike, Comment, SavedPost
from ..models.user import User
from ..schemas.post import PostCreate, PostUpdate, CommentCreate
from ..cache.redis import cache

async def create_category(db: AsyncSession, name: str, description: str = None) -> Category:
    """Create a new category"""
    category = Category(name=name, description=description)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

async def get_categories(db: AsyncSession) -> List[Category]:
    """Get all categories"""
    result = await db.execute(select(Category))
    return result.scalars().all()

async def get_category(db: AsyncSession, category_id: int) -> Optional[Category]:
    """Get category by ID"""
    result = await db.execute(select(Category).where(Category.id == category_id))
    return result.scalars().first()

async def create_post(db: AsyncSession, post: PostCreate, author_id: int) -> Post:
    """
    Create a new post
    Associates the post with specified categories
    """
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
    
    # Clear cache for user posts
    await cache.delete_pattern(f"user_posts:{author_id}:*")
    await cache.delete_pattern("posts:*")
    
    return db_post

async def get_post(db: AsyncSession, post_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Get post by ID with all related data
    Includes like/save status for the current user
    """
    # Try to get from cache first
    cache_key = f"post:{post_id}:{user_id or 'anonymous'}"
    cached_post = await cache.get(cache_key)
    if cached_post:
        return cached_post
    
    # Query from database
    result = await db.execute(
        select(Post).options(
            selectinload(Post.author),
            selectinload(Post.categories),
            selectinload(Post.likes),
            selectinload(Post.comments).selectinload(Comment.user)
        ).where(Post.id == post_id)
    )
    post = result.scalars().first()
    
    if not post:
        return None
    
    # Get counts and user interaction status
    likes_count = len(post.likes)
    comments_count = len(post.comments)
    is_liked_by_user = False
    is_saved_by_user = False
    
    if user_id:
        # Check if user liked this post
        like_result = await db.execute(
            select(PostLike).where(
                and_(PostLike.post_id == post_id, PostLike.user_id == user_id)
            )
        )
        is_liked_by_user = like_result.scalars().first() is not None
        
        # Check if user saved this post
        save_result = await db.execute(
            select(SavedPost).where(
                and_(SavedPost.post_id == post_id, SavedPost.user_id == user_id)
            )
        )
        is_saved_by_user = save_result.scalars().first() is not None
    
    # Format response
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
            for cat in post.categories
        ],
        "likes_count": likes_count,
        "comments_count": comments_count,
        "is_liked_by_user": is_liked_by_user,
        "is_saved_by_user": is_saved_by_user
    }
    
    # Cache the result for 30 minutes
    await cache.set(cache_key, post_data, expire=1800)
    
    return post_data

async def get_posts(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 20, 
    user_id: Optional[int] = None,
    category_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get posts with pagination and optional filtering
    Returns posts ordered by creation date (newest first)
    """
    # Try to get from cache first
    cache_key = f"posts:{skip}:{limit}:{user_id or 'all'}:{category_id or 'all'}"
    cached_posts = await cache.get(cache_key)
    if cached_posts:
        return cached_posts
    
    # Build query
    query = select(Post).options(
        selectinload(Post.author),
        selectinload(Post.categories),
        selectinload(Post.likes),
        selectinload(Post.comments)
    ).where(Post.is_active == True)
    
    # Filter by category if specified
    if category_id:
        query = query.join(Post.categories).where(Category.id == category_id)
    
    # Order and paginate
    query = query.order_by(desc(Post.created_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    posts = result.scalars().all()
    
    # Format posts with interaction data
    posts_data = []
    for post in posts:
        likes_count = len(post.likes)
        comments_count = len(post.comments)
        is_liked_by_user = False
        is_saved_by_user = False
        
        if user_id:
            # Check user interactions
            is_liked_by_user = any(like.user_id == user_id for like in post.likes)
            
            save_result = await db.execute(
                select(SavedPost).where(
                    and_(SavedPost.post_id == post.id, SavedPost.user_id == user_id)
                )
            )
            is_saved_by_user = save_result.scalars().first() is not None
        
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
                for cat in post.categories
            ],
            "likes_count": likes_count,
            "comments_count": comments_count,
            "is_liked_by_user": is_liked_by_user,
            "is_saved_by_user": is_saved_by_user
        }
        posts_data.append(post_data)
    
    # Cache the result for 15 minutes
    await cache.set(cache_key, posts_data, expire=900)
    
    return posts_data

async def get_user_posts(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """Get posts by a specific user"""
    cache_key = f"user_posts:{user_id}:{skip}:{limit}"
    cached_posts = await cache.get(cache_key)
    if cached_posts:
        return cached_posts
    
    result = await db.execute(
        select(Post).options(
            selectinload(Post.author),
            selectinload(Post.categories),
            selectinload(Post.likes),
            selectinload(Post.comments)
        ).where(
            and_(Post.author_id == user_id, Post.is_active == True)
        ).order_by(desc(Post.created_at)).offset(skip).limit(limit)
    )
    posts = result.scalars().all()
    
    # Format posts (similar to get_posts but simpler since we know the user)
    posts_data = []
    for post in posts:
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
                for cat in post.categories
            ],
            "likes_count": len(post.likes),
            "comments_count": len(post.comments),
            "is_liked_by_user": True,  # User's own posts
            "is_saved_by_user": False  # Users don't typically save their own posts
        }
        posts_data.append(post_data)
    
    # Cache for 10 minutes
    await cache.set(cache_key, posts_data, expire=600)
    
    return posts_data

async def update_post(db: AsyncSession, post_id: int, post_update: PostUpdate, user_id: int) -> Optional[Post]:
    """Update a post (only by the author)"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    
    if not post or post.author_id != user_id:
        return None
    
    update_data = post_update.dict(exclude_unset=True)
    
    # Handle category updates
    if "category_ids" in update_data:
        category_ids = update_data.pop("category_ids")
        if category_ids is not None:
            categories = await db.execute(
                select(Category).where(Category.id.in_(category_ids))
            )
            post.categories = categories.scalars().all()
    
    # Update other fields
    for field, value in update_data.items():
        setattr(post, field, value)
    
    await db.commit()
    await db.refresh(post)
    
    # Clear cache
    await cache.delete_pattern(f"post:{post_id}:*")
    await cache.delete_pattern(f"user_posts:{user_id}:*")
    await cache.delete_pattern("posts:*")
    
    return post

async def delete_post(db: AsyncSession, post_id: int, user_id: int) -> bool:
    """Delete a post (only by the author)"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    
    if not post or post.author_id != user_id:
        return False
    
    post.is_active = False
    await db.commit()
    
    # Clear cache
    await cache.delete_pattern(f"post:{post_id}:*")
    await cache.delete_pattern(f"user_posts:{user_id}:*")
    await cache.delete_pattern("posts:*")
    
    return True

async def like_post(db: AsyncSession, post_id: int, user_id: int) -> Optional[PostLike]:
    """Like a post (or unlike if already liked)"""
    # Check if already liked
    result = await db.execute(
        select(PostLike).where(
            and_(PostLike.post_id == post_id, PostLike.user_id == user_id)
        )
    )
    existing_like = result.scalars().first()
    
    if existing_like:
        # Unlike the post
        await db.delete(existing_like)
        await db.commit()
        
        # Clear cache
        await cache.delete_pattern(f"post:{post_id}:*")
        await cache.delete_pattern("posts:*")
        
        return None
    else:
        # Like the post
        like = PostLike(post_id=post_id, user_id=user_id)
        db.add(like)
        await db.commit()
        await db.refresh(like)
        
        # Clear cache
        await cache.delete_pattern(f"post:{post_id}:*")
        await cache.delete_pattern("posts:*")
        
        return like

async def save_post(db: AsyncSession, post_id: int, user_id: int) -> Optional[SavedPost]:
    """Save a post (or unsave if already saved)"""
    # Check if already saved
    result = await db.execute(
        select(SavedPost).where(
            and_(SavedPost.post_id == post_id, SavedPost.user_id == user_id)
        )
    )
    existing_save = result.scalars().first()
    
    if existing_save:
        # Unsave the post
        await db.delete(existing_save)
        await db.commit()
        
        # Clear cache
        await cache.delete_pattern(f"post:{post_id}:*")
        
        return None
    else:
        # Save the post
        save = SavedPost(post_id=post_id, user_id=user_id)
        db.add(save)
        await db.commit()
        await db.refresh(save)
        
        # Clear cache
        await cache.delete_pattern(f"post:{post_id}:*")
        
        return save

async def create_comment(db: AsyncSession, comment: CommentCreate, user_id: int) -> Comment:
    """Create a comment on a post"""
    db_comment = Comment(
        content=comment.content,
        post_id=comment.post_id,
        user_id=user_id
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    
    # Clear cache
    await cache.delete_pattern(f"post:{comment.post_id}:*")
    await cache.delete_pattern("posts:*")
    
    return db_comment

async def get_post_comments(db: AsyncSession, post_id: int, skip: int = 0, limit: int = 50) -> List[Comment]:
    """Get comments for a post"""
    result = await db.execute(
        select(Comment).options(
            selectinload(Comment.user)
        ).where(Comment.post_id == post_id).order_by(Comment.created_at).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def get_saved_posts(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
    """Get posts saved by a user"""
    result = await db.execute(
        select(SavedPost).options(
            selectinload(SavedPost.post).selectinload(Post.author),
            selectinload(SavedPost.post).selectinload(Post.categories),
            selectinload(SavedPost.post).selectinload(Post.likes),
            selectinload(SavedPost.post).selectinload(Post.comments)
        ).where(SavedPost.user_id == user_id).order_by(desc(SavedPost.created_at)).offset(skip).limit(limit)
    )
    saved_posts = result.scalars().all()
    
    # Format the saved posts
    posts_data = []
    for saved_post in saved_posts:
        post = saved_post.post
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
                for cat in post.categories
            ],
            "likes_count": len(post.likes),
            "comments_count": len(post.comments),
            "is_liked_by_user": any(like.user_id == user_id for like in post.likes),
            "is_saved_by_user": True,  # Obviously true since these are saved posts
            "saved_at": saved_post.created_at.isoformat()
        }
        posts_data.append(post_data)
    
    return posts_data
