"""
Redis Setup Helper for Windows
This script helps you set up Redis for the social media app
"""

import subprocess
import socket
import time
import os

def check_redis_running():
    """Check if Redis is running on localhost:6379"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('localhost', 6379))
        sock.close()
        return result == 0
    except:
        return False

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def start_redis_docker():
    """Start Redis using Docker"""
    try:
        print(" Starting Redis with Docker...")
        
        # Stop any existing Redis container
        subprocess.run(['docker', 'stop', 'redis-social'], capture_output=True)
        subprocess.run(['docker', 'rm', 'redis-social'], capture_output=True)
        
        # Start new Redis container
        result = subprocess.run([
            'docker', 'run', '-d', 
            '--name', 'redis-social',
            '-p', '6379:6379',
            'redis:latest'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(" Redis container started successfully!")
            
            # Wait a moment for Redis to start
            time.sleep(3)
            
            if check_redis_running():
                print(" Redis is now running on localhost:6379")
                return True
            else:
                print(" Redis container started but not accessible")
                return False
        else:
            print(f" Failed to start Redis container: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Redis with Docker: {e}")
        return False

def main():
    print("🔧 Redis Setup Helper for Simple Social Media App")
    print("=" * 50)
    
    # Check if Redis is already running
    if check_redis_running():
        print("✅ Redis is already running on localhost:6379")
        print("🎉 Your app should work with caching!")
        return
    
    print("❌ Redis is not running on localhost:6379")
    print()
    
    # Check available options
    has_docker = check_docker()
    
    if has_docker:
        print("✅ Docker is available")
        choice = input("Start Redis with Docker? (y/N): ").lower().strip()
        
        if choice in ['y', 'yes']:
            if start_redis_docker():
                print("\n🎉 Redis is now running! Your app will have fast caching.")
                print("💡 To stop Redis later: docker stop redis-social")
            else:
                print("\n❌ Failed to start Redis. The app will work but without caching.")
        else:
            print("📝 You can start Redis manually with:")
            print("   docker run -d --name redis-social -p 6379:6379 redis:latest")
    else:
        print("❌ Docker is not available")
        print("\n📝 To install Redis, you have these options:")
        print("1. Install Docker Desktop and run:")
        print("   docker run -d --name redis-social -p 6379:6379 redis:latest")
        print()
        print("2. Use Windows Subsystem for Linux (WSL):")
        print("   sudo apt install redis-server")
        print("   sudo service redis-server start")
        print()
        print("3. The app will work without Redis (but slower)")
    
    print("\n🚀 You can now start your app with:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    main()
