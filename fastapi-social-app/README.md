# 🚀 Social Media API - Complete FastAPI Application

A full-featured social media API built with FastAPI, featuring user management, posts, social interactions, smart recommendations, and Redis caching.

## ✨ Features

### 🔐 Authentication & User Management
- User registration and login with JWT tokens
- Password hashing with bcrypt
- Protected routes and user profiles
- User profile management

### 📝 Post Management
- Create, read, update, delete posts
- Multiple categories per post
- Image support for posts
- Post pagination and filtering

### 💫 Social Features
- Like/unlike posts
- Comment on posts
- Save posts for later
- View user's own posts and saved posts

### 🤖 Smart Recommendation System
- **Content-based filtering**: Uses TF-IDF to find similar posts
- **Collaborative filtering**: Recommends posts liked by similar users
- **Hybrid approach**: Combines both methods for better recommendations
- **New user handling**: Shows popular recent posts for new users

### ⚡ Performance & Caching
- Redis caching for frequently accessed data
- Automatic cache invalidation on updates
- Pattern-based cache cleanup
- Optimized database queries with SQLAlchemy

### 🏗️ Architecture
- Clean modular structure
- Async/await throughout for better performance
- Proper error handling and validation
- Comprehensive API documentation

## 🛠️ Tech Stack

- **FastAPI**: Modern, fast web framework
- **PostgreSQL**: Robust relational database
- **Redis**: In-memory caching
- **SQLAlchemy**: ORM with async support
- **Pydantic**: Data validation and serialization
- **JWT**: Secure authentication
- **scikit-learn**: Machine learning for recommendations
- **bcrypt**: Password hashing

## 📋 Prerequisites

1. **Python 3.8+**
2. **PostgreSQL** - Install and create a database named `social_db`
3. **Redis** - Install and run Redis server

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Edit the `.env` file with your database and Redis settings:
```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/social_db
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
```

### 3. Start PostgreSQL and Redis
```bash
# Start PostgreSQL (varies by system)
sudo service postgresql start  # Linux
brew services start postgresql  # macOS

# Start Redis
redis-server  # All systems
```

### 4. Setup Database
```bash
python setup_database.py
```

### 5. Run the Application
```bash
# Option 1: Direct command
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Use the startup script
# Windows:
run.bat

# Linux/macOS:
chmod +x run.sh
./run.sh
```

### 6. Access the API
- **Main API**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - Login user
- `GET /api/users/me` - Get current user profile

### Posts & Social Features
- `POST /api/posts/` - Create new post
- `GET /api/posts/` - Get all posts (with pagination)
- `GET /api/posts/recommendations` - Get personalized recommendations
- `POST /api/posts/{post_id}/like` - Like/unlike post
- `POST /api/posts/{post_id}/save` - Save/unsave post
- `POST /api/posts/{post_id}/comment` - Add comment

## 🧠 How the Recommendation System Works

### For New Users:
- Shows latest posts with highest engagement
- Focuses on recent content (last 30 days)

### For Existing Users:
1. **Content Analysis**: Uses TF-IDF to find similar posts
2. **Collaborative Filtering**: Finds users with similar preferences
3. **Hybrid Approach**: Combines both methods for better results

## 💾 Caching Strategy

- Individual posts with user interaction status
- Post lists and recommendations
- Automatic cache invalidation on updates
- TTL-based expiration (15 minutes to 1 hour)

## 🎉 You're Ready!

Your complete social media API is now ready to use! Visit http://localhost:8000/docs to explore all the features.
