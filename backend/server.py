import sys
import asyncio

# -------------------------------- NOTE FOR CONTRIBUTORS ---------------------------------------
# Keep this line before ANY imports that might trigger event loop creation or spawn subprocesses
# You can also set uvicorn's loop param to asyncio in run() or create a server config with 
# uvicorn.config() and set the loop attribute to asyncio. Just make sure uvicorn respects the 
# asyncio policy
# ----------------------------------------------------------------------------------------------
if sys.platform.startswith("win"):
    print(f"On {sys.platform}")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn
from app.config import settings


env = settings.APP_ENVIRONMENT or "production"
PORT = settings.PORT or 8000
RELOAD: bool = env.lower() in ["development", "dev"]

async def main():
    """Main async entry point"""
    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=RELOAD,
        reload_dirs=["app"],
    )
    server = uvicorn.Server(config)
    await server.serve()



if __name__=="__main__":
    asyncio.run(main())
    