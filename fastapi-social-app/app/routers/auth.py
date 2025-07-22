from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from ..database import get_db
from ..schemas.user import UserCreate, UserLogin, Token, UserResponse
from ..crud.user import create_user, get_user_by_username, authenticate_user
from ..auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register new user
    Simple registration with username, email, password
    """
    # Check if username exists
    if await get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user
    db_user = await create_user(db, user)
    return db_user

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login user and get JWT token
    Returns token for accessing protected endpoints
    """
    # Authenticate user
    user = await authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Invalid username or password"
        )
    
    # Create JWT token
    token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
