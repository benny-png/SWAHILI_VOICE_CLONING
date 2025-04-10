# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.mongodb import connect_to_mongo, close_mongo_connection
import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Import route files
from .routes.auth import router as auth_router
from .routes.user_texts import router as user_texts_router
from .routes.texts import router as texts_router
from .routes.tts import router as tts_router
from .routes.utils import router as utils_router
from .routes.admin import router as admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger("swahili-voice-api")

app = FastAPI()

# Request timing middleware
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"Request to {request.url.path} took {process_time:.4f} seconds")
        return response

# Add timing middleware
app.add_middleware(TimingMiddleware)

@app.middleware("http")
async def set_scheme_https(request, call_next):
    if request.headers.get("x-forwarded-proto") == "https":
        request.scope["scheme"] = "https"
    response = await call_next(request)
    return response



# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Log startup event
@app.on_event("startup")
async def startup_event():
    logger.info("API server started")



# Register routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(user_texts_router)
app.include_router(texts_router)
app.include_router(tts_router)
app.include_router(utils_router)






