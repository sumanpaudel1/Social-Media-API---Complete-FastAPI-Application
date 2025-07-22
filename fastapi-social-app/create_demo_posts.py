"""
Add demo posts for testing recommendations
Run this after database setup to have sample data
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from dotenv import load_dotenv

from app.database import Base
from app.models import User, Post, Category
from app.schemas.post import PostCreate
from app.crud.post_optimized import create_post_cached

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def create_demo_posts():
    """Create demo posts for testing"""
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as db:
        # Get demo users
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("❌ No users found. Run setup_database.py first!")
            return
        
        # Get categories
        cat_result = await db.execute(select(Category))
        categories = cat_result.scalars().all()
        
        if not categories:
            print("❌ No categories found. Run setup_database.py first!")
            return
        
        print(f"📊 Found {len(users)} users and {len(categories)} categories")
        
        # Demo posts
        demo_posts = [
            {
                "title": "Getting Started with Python",
                "content": "Python is an amazing programming language for beginners and experts alike. Here are some tips to get started...",
                "author_id": users[0].id,
                "category_ids": [categories[0].id]  # Technology
            },
            {
                "title": "Best Travel Destinations 2025",
                "content": "Exploring the world's most beautiful places. From mountains to beaches, here are my top recommendations...",
                "author_id": users[1].id,
                "category_ids": [categories[3].id]  # Travel
            },
            {
                "title": "Healthy Cooking Tips",
                "content": "Eating healthy doesn't have to be boring! Here are some delicious and nutritious recipes...",
                "author_id": users[2].id,
                "category_ids": [categories[4].id, categories[5].id]  # Food, Health
            },
            {
                "title": "The Future of AI",
                "content": "Artificial Intelligence is transforming our world. Let's discuss the latest developments and their impact...",
                "author_id": users[0].id,
                "category_ids": [categories[0].id, categories[9].id]  # Technology, Science
            },
            {
                "title": "Top 10 Movies This Year",
                "content": "Cinema has been amazing this year! Here are my top movie recommendations that you shouldn't miss...",
                "author_id": users[1].id,
                "category_ids": [categories[2].id]  # Entertainment
            },
            {
                "title": "Starting Your Own Business",
                "content": "Entrepreneurship is challenging but rewarding. Here's what I learned from building my first startup...",
                "author_id": users[2].id,
                "category_ids": [categories[7].id]  # Business
            },
            {
                "title": "Digital Art Techniques",
                "content": "Exploring modern digital art tools and techniques. From Photoshop to Procreate, here's what works best...",
                "author_id": users[0].id,
                "category_ids": [categories[8].id]  # Art
            },
            {
                "title": "Learning a New Language",
                "content": "Tips and tricks for mastering a foreign language quickly. My journey learning Spanish in 6 months...",
                "author_id": users[1].id,
                "category_ids": [categories[6].id]  # Education
            }
        ]
        
        # Create posts
        for post_data in demo_posts:
            try:
                post_create = PostCreate(
                    title=post_data["title"],
                    content=post_data["content"],
                    category_ids=post_data["category_ids"]
                )
                
                await create_post_cached(db, post_create, post_data["author_id"])
                print(f"✅ Created post: {post_data['title']}")
                
            except Exception as e:
                print(f"❌ Error creating post '{post_data['title']}': {e}")
        
        print("🎉 Demo posts created successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    print("🗂️ Creating demo posts for testing...")
    asyncio.run(create_demo_posts())
