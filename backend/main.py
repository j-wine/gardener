import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("app.app:app", host="0.0.0.0", port=port, log_level="info")