# 📱 Simple Social Media API

A clean, fast, minimal social media API built with FastAPI, PostgreSQL, and Redis.

##  Features

- **Authentication**: JWT-based login/register
- **Posts**: Create, view, like, save, comment
- **Recommendations**: Smart content suggestions
- **Caching**: Redis-powered for optimal performance
- **Clean GUI**: Minimal, responsive web interface

## 🚀 Quick Start

### Windows
```bash
# Run the startup script
start.bat
```

### Manual Setup
```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment (copy .env.example to .env and configure)
cp .env.example .env

# 4. Start Redis (via Docker)
docker run -d -p 6379:6379 redis:alpine

# 5. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 Access Points

- **Ultra-Simple GUI**: http://localhost:8000/static/simple.html
- **Full-Featured GUI**: http://localhost:8000/static/social.html
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Posts
- `POST /api/posts` - Create new post
- `GET /api/posts` - Get posts (cached)
- `POST /api/posts/{id}/like` - Like/unlike post
- `POST /api/posts/{id}/save` - Save/unsave post
- `POST /api/posts/{id}/comment` - Add comment
- `GET /api/posts/recommendations` - Get personalized recommendations

## 🏗️ Architecture

```
app/
├── main.py              # FastAPI app with routes
├── auth.py              # JWT authentication
├── database.py          # PostgreSQL async connection
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── crud/                # Database operations
├── routers/             # API routes
├── cache/               # Redis caching
└── recommendations.py   # ML recommendations
```

## 🔧 Configuration

Create `.env` file:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost/social_media
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📱 GUI Features

The minimal GUI (`simple.html`) includes:
- ✅ Clean, mobile-first design
- ✅ Login/Register
- ✅ Create posts
- ✅ Like, save, comment on posts
- ✅ Personalized recommendations
- ✅ Real-time updates
- ✅ Responsive layout

## 🚀 Production Ready

- **Async**: Full async/await PostgreSQL + Redis
- **Cached**: Smart Redis caching minimizes DB hits
- **Secure**: JWT authentication with password hashing
- **Fast**: Optimized queries and response models
- **Clean**: Minimal codebase, no unnecessary dependencies

## 📊 Performance

- **Database**: Async PostgreSQL with connection pooling
- **Cache**: Redis for posts, users, and interactions
- **Queries**: Optimized with selectinload for relationships
- **API**: FastAPI with automatic OpenAPI documentation

## 💡 Demo Data

Use the demo credentials:
- **Username**: `john_doe`
- **Password**: `password123`

Or register a new account through the GUI.

---

**Built with**: FastAPI, PostgreSQL, Redis, SQLAlchemy, Pydantic, JWT
**License**: MIT
