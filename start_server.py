"""
EasyExcel Backend Server Starter

This script helps start the backend server with proper configuration.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_api_key():
    """Check if OpenAI API key is configured"""
    # Load .env file from the backend directory
    backend_dir = Path(__file__).parent
    env_path = backend_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "your_openai_api_key_here":
        print("=" * 60)
        print("⚠️  OpenAI API Key Not Configured!")
        print("=" * 60)
        print("\nPlease set your OPENAI_API_KEY in the .env file.")
        print("\nSteps:")
        print("1. Get your API key from: https://platform.openai.com/api-keys")
        print("2. Open the .env file in the backend folder")
        print("3. Replace 'your_openai_api_key_here' with your actual key")
        print("\nExample:")
        print("   OPENAI_API_KEY=sk-...your-actual-key-here")
        print("=" * 60)
        return False
    
    print("✅ OpenAI API Key found!")
    return True

def start_server():
    """Start the FastAPI server"""
    # Load .env file BEFORE checking API key or importing app
    backend_dir = Path(__file__).parent
    env_path = backend_dir / ".env"
    load_dotenv(dotenv_path=env_path)
    
    if not check_api_key():
        return
    
    try:
        import uvicorn
        # Get PORT from environment (DigitalOcean/Railway/Render sets this automatically)
        # For local development, use 8000
        port = int(os.getenv("PORT", "8000"))
        
        print("\n" + "=" * 60)
        print("Starting EasyExcel Backend Server...")
        print("=" * 60)
        print(f"\nServer will be available at: http://localhost:{port}")
        print(f"API Documentation: http://localhost:{port}/docs")
        print("\nPress CTRL+C to stop the server\n")
        print("=" * 60 + "\n")
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=port,
            reload=False,  # Disable reload in production
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  py -m pip install -r requirements.txt")

if __name__ == "__main__":
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Note: .env is now loaded inside start_server() before app.py is imported
    start_server()


