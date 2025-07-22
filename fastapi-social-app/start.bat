@echo off
echo  Starting Simple Social Media API...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Set environment variables (optional, use .env file instead)
REM set DATABASE_URL=postgresql+asyncpg://user:password@localhost/social_media
REM set REDIS_URL=redis://localhost:6379
REM set SECRET_KEY=your-secret-key

REM Start the application
echo.
echo  Starting server on http://localhost:8000
echo  GUI available at: http://localhost:8000/static/social.html
echo  API docs at: http://localhost:8000/docs
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
