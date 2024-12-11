# main.py
import uvicorn
from app.main import app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    # Get host from environment variable or default to 0.0.0.0
    host = os.getenv("HOST", "0.0.0.0")
    
    # Get reload setting from environment variable or default to False
    reload = os.getenv("RELOAD", "False").lower() == "true"
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=3
    )

if __name__ == "__main__":
    main()