from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from ..schemas.post import (
    PostCreate, PostUpdate, PostResponse, CommentCreate, CommentResponse,
    CategoryCreate, CategoryResponse
)
from ..crud.post import (
    create_post, get_post, get_posts, get_user_posts, update_post, delete_post,
    like_post, save_post, create_comment, get_post_comments, create_category, get_categories, get_category, get_saved_posts
)
from ..auth import get_current_active_user
from ..recommendations import recommendation_system

router = APIRouter(prefix="/posts", tags=["posts"])

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_new_post(
    post: PostCreate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new post for the current user
    """
    db_post = await create_post(db, post, current_user.id)
    return db_post

@router.get("/{post_id}", response_model=PostResponse)
async def get_single_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get a single post by ID
    """
    post = await get_post(db, post_id, user_id=current_user.id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.get("/", response_model=List[PostResponse])
async def get_all_posts(
    skip: int = Query(0, ge=0, description="Number of posts to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of posts to return"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get all posts with pagination and optional category filtering
    
    Features:
    - Pagination with skip/limit
    - Filter by category
    - Shows like/save status for current user
    - Cached for better performance
    """
    posts = await get_posts(
        db, 
        skip=skip, 
        limit=limit, 
        user_id=current_user.id,
        category_id=category_id
    )
    return posts

@router.get("/feed/recommendations")
async def get_recommended_posts(
    limit: int = Query(20, ge=1, le=50, description="Number of recommendations"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get personalized post recommendations
    
    Uses machine learning to recommend posts based on:
    - User's liked/saved/commented posts (content similarity)
    - Posts liked by users with similar preferences (collaborative filtering)
    - Popular recent posts for new users
    """
    try:
        recommendations = await recommendation_system.get_recommendations(
            db, current_user.id, limit
        )
        return {
            "message": "Recommendations generated successfully",
            "total": len(recommendations),
            "posts": recommendations
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=List[PostResponse])
async def get_posts_by_user(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all posts by a specific user
    
    Public endpoint to view any user's posts
    """
    posts = await get_user_posts(db, user_id, skip, limit)
    return posts

@router.get("/saved", response_model=List[PostResponse])
async def get_user_saved_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get posts saved by the current user
    
    Protected endpoint for user's saved posts collection
    """
    saved_posts = await get_saved_posts(db, current_user.id, skip, limit)
    return {
        "message": "Saved posts retrieved successfully",
        "total": len(saved_posts),
        "posts": saved_posts
    }

@router.put("/{post_id}", response_model=PostResponse)
async def update_existing_post(
    post_id: int,
    post_update: PostUpdate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a post (only by the author)
    
    Users can only update their own posts
    Updatable fields: title, content, image_url, categories
    """
    post = await update_post(db, post_id, post_update, current_user.id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_post(
    post_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a post (only by the author)
    
    Soft delete - marks post as inactive rather than permanent deletion
    """
    success = await delete_post(db, post_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")

@router.post("/{post_id}/like", status_code=status.HTTP_200_OK)
async def like_or_unlike_post(
    post_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Like or unlike a post
    
    Toggle functionality:
    - If post is not liked: adds like
    - If post is already liked: removes like
    
    This data is used for recommendations and engagement metrics
    """
    try:
        like = await like_post(db, post_id, current_user.id)
        if like:
            return {"message": "Post liked successfully", "action": "liked"}
        else:
            return {"message": "Post unliked successfully", "action": "unliked"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to toggle like: {str(e)}"
        )

@router.post("/{post_id}/save", status_code=status.HTTP_200_OK)
async def save_or_unsave_post(
    post_id: int,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save or unsave a post
    
    Toggle functionality for saving posts to user's collection:
    - If post is not saved: adds to saved posts
    - If post is already saved: removes from saved posts
    
    Saved posts can be accessed via GET /posts/saved
    """
    try:
        save = await save_post(db, post_id, current_user.id)
        if save:
            return {"message": "Post saved successfully", "action": "saved"}
        else:
            return {"message": "Post unsaved successfully", "action": "unsaved"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to toggle save: {str(e)}"
        )

@router.post("/{post_id}/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment_to_post(
    post_id: int,
    comment: CommentCreate,
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a comment to a post
    
    Users can comment on any post to engage with content
    Comments are used in the recommendation system to gauge user interest
    """
    try:
        # Set the post_id from URL parameter
        comment.post_id = post_id
        
        comment = await create_comment(db, comment, current_user.id)
        return {
            "message": "Comment added successfully",
            "comment_id": comment.id,
            "comment": {
                "id": comment.id,
                "content": comment.content,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "created_at": comment.created_at.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add comment: {str(e)}"
        )

@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments_for_post(
    post_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comments for a post
    
    Returns comments with author information, ordered by creation time
    """
    comments = await get_post_comments(db, post_id, skip, limit)
    return comments

@router.post("/category", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_new_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new post category
    """
    db_category = await create_category(db, category.name, category.description)
    return db_category

@router.get("/category", response_model=List[CategoryResponse])
async def get_all_categories(db: AsyncSession = Depends(get_db)):
    """
    Get all post categories
    """
    categories = await get_categories(db)
    return categories

@router.get("/category/{category_id}", response_model=CategoryResponse)
async def get_single_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get a single category by ID
    """
    category = await get_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category
