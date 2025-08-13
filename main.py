import Zapier
from fastapi import FastAPI
import uvicorn
import os
from dotenv import load_dotenv
import pathlib
import json

# Load environment variables
current_dir = pathlib.Path(__file__).parent.absolute()
env_path = current_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Display environment variables for debugging
print(f"Loading .env from: {env_path}")
print(f"API_KEY from environment: {os.getenv('API_KEY', 'Not set')}")

# Import the router from the Zapier.py file

# Create the FastAPI application
app = FastAPI(
    title="ManyChat Integration API",
    description="API for integration with ManyChat webhooks",
    version="1.0.0"
)

# Include the router from Zapier.py
app.include_router(Zapier.router)

# Root endpoint for health check


@app.get("/")
async def root():
    return {"status": "API is running", "message": "Welcome to the ManyChat Integration API"}

# Debug endpoint to check API key


@app.get("/debug/check-api-key")
async def check_api_key():
    # Reload .env file
    load_dotenv(dotenv_path=env_path, override=True)

    api_key = os.getenv("API_KEY", "Not found")
    env_file_exists = os.path.exists(env_path)

    # Read the actual content of .env file
    env_content = ""
    if env_file_exists:
        try:
            with open(env_path, "r") as f:
                env_content = f.read()
        except Exception as e:
            env_content = f"Error reading file: {str(e)}"

    return {
        "configured_api_key": api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else api_key,
        "env_file_path": str(env_path),
        "env_file_exists": env_file_exists,
        "env_file_api_key_line": next((line for line in env_content.split("\n") if line.startswith("API_KEY=")), "Not found")
    }

# Run the application
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
