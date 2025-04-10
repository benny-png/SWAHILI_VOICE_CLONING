# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database.mongodb import connect_to_mongo, close_mongo_connection

# Import route files
from .routes.auth import router as auth_router
from .routes.user_texts import router as user_texts_router
from .routes.texts import router as texts_router
from .routes.tts import router as tts_router
from .routes.utils import router as utils_router
from .routes.admin import router as admin_router


app = FastAPI() 

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



# Register routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(user_texts_router)
app.include_router(texts_router)
app.include_router(tts_router)
app.include_router(utils_router)






