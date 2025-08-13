import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # Use import string format
        host="0.0.0.0",  # Allow external access
        port=8001,
        reload=True,
        reload_dirs=["c:\\Users\\Shannon\\OneDrive\\Desktop\\shanbot"],
        timeout_keep_alive=300,
        timeout_graceful_shutdown=300,
        limit_concurrency=100,
        backlog=2048
    )
