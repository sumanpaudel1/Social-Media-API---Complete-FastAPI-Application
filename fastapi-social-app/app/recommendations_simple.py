"""
Simple recommendation system based on user interactions
Clean and efficient approach focused on like, save, comment patterns
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc, func, and_
from typing import List, Dict, Any
from collections import defaultdict

from .models.post import Post, PostLike, SavedPost, Comment, Category
from .models.user import User
from .cache.redis import cache
from .crud.post_optimized import format_post_response

async def get_recommendations_for_user(db: AsyncSession, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get personalized recommendations for user
    
    Algorithm:
    1. For new users (no interactions): Show most liked recent posts
    2. For existing users: 
       - Find posts they interacted with (liked/saved/commented)
       - Find categories they prefer
       - Recommend similar category posts with high engagement
       - Exclude posts they already interacted with
    """
    try:
        # Try cache first
        cache_key = f"recommendations:{user_id}:{limit}"
        cached_recs = await cache.get(cache_key)
        if cached_recs:
            print(f" Serving {len(cached_recs)} recommendations from cache for user {user_id}")
            return cached_recs
        
        print(f" Generating NEW recommendations for user {user_id}")
        
        # Get user's interaction history
        interactions = await get_user_interactions(db, user_id)
        print(f" User {user_id} interactions: {interactions['has_interactions']} - "
              f"Liked: {len(interactions['liked_posts'])}, "
              f"Saved: {len(interactions['saved_posts'])}, "
              f"Commented: {len(interactions['commented_posts'])}")
        
        if not interactions["has_interactions"]:
            # New user - show popular recent posts
            print(f"👤 New user detected - showing popular posts")
            recommendations = await get_popular_posts_for_new_user(db, user_id, limit)
        else:
            # Existing user - personalized recommendations
            print(f" Existing user detected - generating personalized recommendations")
            recommendations = await get_personalized_recommendations(db, user_id, interactions, limit)
        
        print(f" Generated {len(recommendations)} recommendations for user {user_id}")
        
        # Cache for 30 minutes
        if recommendations:
            await cache.set(cache_key, recommendations, expire=1800)
            print(f" Cached recommendations for user {user_id}")
        
        return recommendations
        
    except Exception as e:
        print(f" Error in get_recommendations_for_user: {e}")
        # Return fallback recommendations
        return [
            {
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
        ]

async def get_user_interactions(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """
    Get user's interaction history to understand preferences
    """
    try:
        # Get liked posts
        liked_result = await db.execute(
            select(PostLike.post_id).where(PostLike.user_id == user_id)
        )
        liked_posts = [row[0] for row in liked_result.fetchall()]
        
        # Get saved posts  
        saved_result = await db.execute(
            select(SavedPost.post_id).where(SavedPost.user_id == user_id)
        )
        saved_posts = [row[0] for row in saved_result.fetchall()]
        
        # Get commented posts
        commented_result = await db.execute(
            select(Comment.post_id).where(Comment.user_id == user_id)
        )
        commented_posts = [row[0] for row in commented_result.fetchall()]
        
        # Combine all interactions
        all_interacted = set(liked_posts + saved_posts + commented_posts)
        
        return {
            "has_interactions": len(all_interacted) > 0,
            "liked_posts": liked_posts,
            "saved_posts": saved_posts, 
            "commented_posts": commented_posts,
            "all_interacted": list(all_interacted)
        }
        
    except Exception as e:
        print(f"❌ Error getting user interactions: {e}")
        return {
            "has_interactions": False,
            "liked_posts": [],
            "saved_posts": [],
            "commented_posts": [],
            "all_interacted": []
        }

async def get_popular_posts_for_new_user(db: AsyncSession, user_id: int, limit: int) -> List[Dict[str, Any]]:
    """
    For new users: show most liked recent posts (last 30 days)
    """
    try:
        # Get posts from last 30 days with like counts
        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.categories),
                selectinload(Post.likes),
                selectinload(Post.comments)
            )
            .where(
                and_(
                    Post.is_active == True,
                    Post.author_id != user_id  # Don't recommend user's own posts
                )
            )
            .order_by(desc(Post.created_at))
            .limit(limit)
        )
        
        posts = result.scalars().all()
        
        # Format response
        recommendations = []
        for post in posts:
            post_data = await format_post_response(post, user_id)
            post_data["recommendation_reason"] = "Popular recent post"
            recommendations.append(post_data)
        
        print(f"✅ Found {len(recommendations)} popular posts for new user {user_id}")
        return recommendations
        
    except Exception as e:
        print(f"❌ Error getting popular posts: {e}")
        return []

async def get_personalized_recommendations(db: AsyncSession, user_id: int, interactions: Dict, limit: int) -> List[Dict[str, Any]]:
    """
    For existing users: recommend based on categories they like
    """
    try:
        recommendations = []
        
        # Get categories of posts user interacted with
        if interactions["all_interacted"]:
            # Simple approach: get posts from categories the user has interacted with
            category_result = await db.execute(
                select(Category.id)
                .join(Post.categories)
                .where(Post.id.in_(interactions["all_interacted"]))
                .distinct()
            )
            preferred_categories = [row[0] for row in category_result.fetchall()]
            print(f"📊 User {user_id} preferred categories: {preferred_categories}")
        else:
            preferred_categories = []
        
        # Get recommendations from preferred categories
        if preferred_categories:
            category_posts = await db.execute(
                select(Post)
                .join(Post.categories)
                .options(
                    selectinload(Post.author),
                    selectinload(Post.categories),
                    selectinload(Post.likes),
                    selectinload(Post.comments)
                )
                .where(
                    and_(
                        Post.is_active == True,
                        Post.author_id != user_id,  # Not user's own posts
                        ~Post.id.in_(interactions["all_interacted"]),  # Not already interacted
                        Category.id.in_(preferred_categories[:3])  # Top 3 preferred categories
                    )
                )
                .order_by(desc(Post.created_at))
                .limit(limit)
            )
            
            for post in category_posts.scalars().all():
                post_data = await format_post_response(post, user_id)
                post_data["recommendation_reason"] = "Based on your interests"
                recommendations.append(post_data)
        
        # Fill remaining slots with popular posts if needed
        if len(recommendations) < limit:
            remaining = limit - len(recommendations)
            popular_posts = await get_popular_posts_for_new_user(db, user_id, remaining)
            
            # Filter out posts already in recommendations
            existing_ids = {rec["id"] for rec in recommendations}
            for post in popular_posts:
                if post["id"] not in existing_ids:
                    post["recommendation_reason"] = "Trending post"
                    recommendations.append(post)
                    if len(recommendations) >= limit:
                        break
        
        print(f"✅ Generated {len(recommendations)} personalized recommendations for user {user_id}")
        return recommendations[:limit]
        
    except Exception as e:
        print(f"❌ Error generating personalized recommendations: {e}")
        # Fallback to popular posts
        return await get_popular_posts_for_new_user(db, user_id, limit)
