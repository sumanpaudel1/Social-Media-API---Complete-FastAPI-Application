#!/bin/bash

echo " Starting Social Media API Setup..."

# Install dependencies
echo " Installing Python dependencies..."
pip install -r requirements.txt

# Setup database
echo " Setting up database..."
python setup_database.py

# Start the application
echo " Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo " Social Media API is running at http://localhost:8000"
echo " API Documentation: http://localhost:8000/docs"
echo " Alternative docs: http://localhost:8000/redoc"
