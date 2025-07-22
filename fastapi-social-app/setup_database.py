"""
Database setup and initialization script for Social Media API

This script creates the database and initial data.
Run this before starting the application for the first time.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Import all models to ensure they're registered
from app.database import Base
from app.models import User, Post, Category, PostLike, Comment, SavedPost
from app.crud.user import create_user
from app.crud.post import create_category
from app.schemas.user import UserCreate

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def create_database():
    """Create all database tables"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Drop all tables (for development - remove in production)
        # await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print(" Database tables created successfully!")
    
    # Create session for adding initial data
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        await create_initial_data(session)
    
    await engine.dispose()

async def create_initial_data(db: AsyncSession):
    """Create initial categories and demo data"""
    
    # Create categories
    categories = [
        {"name": "Technology", "description": "Posts about technology, programming, and innovation"},
        {"name": "Sports", "description": "Sports news, discussions, and updates"},
        {"name": "Entertainment", "description": "Movies, music, games, and entertainment"},
        {"name": "Travel", "description": "Travel experiences, tips, and destinations"},
        {"name": "Food", "description": "Recipes, restaurant reviews, and food experiences"},
        {"name": "Health", "description": "Health tips, fitness, and wellness"},
        {"name": "Education", "description": "Learning resources, courses, and educational content"},
        {"name": "Business", "description": "Business news, entrepreneurship, and career advice"},
        {"name": "Art", "description": "Art, design, creativity, and visual content"},
        {"name": "Science", "description": "Scientific discoveries, research, and innovations"}
    ]
    
    for cat_data in categories:
        try:
            await create_category(db, cat_data["name"], cat_data["description"])
            print(f" Created category: {cat_data['name']}")
        except Exception as e:
            print(f" Category {cat_data['name']} might already exist: {e}")
    
    # Create demo users
    demo_users = [
        {
            "username": "john_doe",
            "email": "john@example.com",
            "full_name": "John Doe",
            "password": "password123",
            "bio": "Tech enthusiast and software developer"
        },
        {
            "username": "jane_smith",
            "email": "jane@example.com", 
            "full_name": "Jane Smith",
            "password": "password123",
            "bio": "Travel blogger and photographer"
        },
        {
            "username": "alex_johnson",
            "email": "alex@example.com",
            "full_name": "Alex Johnson", 
            "password": "password123",
            "bio": "Food lover and chef"
        }
    ]
    
    for user_data in demo_users:
        try:
            user_create = UserCreate(**user_data)
            await create_user(db, user_create)
            print(f" Created demo user: {user_data['username']}")
        except Exception as e:
            print(f" User {user_data['username']} might already exist: {e}")

    print(" Initial data setup completed!")

if __name__ == "__main__":
    print(" Setting up Social Media API database...")
    asyncio.run(create_database())
