from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    """Schema for creating categories"""
    pass

class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    """Base post schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    image_url: Optional[str] = None

class PostCreate(PostBase):
    """Schema for creating new posts"""
    category_ids: List[int] = Field(default_factory=list)

class PostUpdate(BaseModel):
    """Schema for updating posts"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = None
    category_ids: Optional[List[int]] = None

class PostResponse(PostBase):
    """Schema for post response with all related data"""
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    
    # Related data
    author: dict  # Will contain basic user info
    categories: List[CategoryResponse]
    likes_count: int = 0
    comments_count: int = 0
    is_liked_by_user: bool = False
    is_saved_by_user: bool = False
    
    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    """Base comment schema"""
    content: str = Field(..., min_length=1)

class CommentCreate(CommentBase):
    """Schema for creating comments"""
    post_id: int

class CommentResponse(CommentBase):
    """Schema for comment response"""
    id: int
    user_id: int
    post_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    user: dict  # Will contain basic user info
    
    class Config:
        from_attributes = True

class PostLikeResponse(BaseModel):
    """Schema for post like response"""
    id: int
    user_id: int
    post_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SavedPostResponse(BaseModel):
    """Schema for saved post response"""
    id: int
    user_id: int
    post_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
