# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.services.user_service import UserService
from app.services.user_text_service import UserTextService
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse
from app.models.schemas import (
    Token,
    UserCreate,
    UserLogin,
    LoginResponse,
    UserInDB
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

async def get_user_service():
    return UserService()

#authentication endpoints

# Registration endpoint
@router.post("/register/", response_model=UserInDB, description="""
Register a new user account.

Example using curl:
```bash
curl -X POST "http://localhost:8000/auth/register" \\
     -H "Content-Type: application/json" \\
     -d '{
           "username": "user123",
           "email": "user@example.com",
           "password": "securepassword"
         }'
```

Example using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/auth/register",
    json={
        "username": "user123",
        "email": "user@example.com",
        "password": "securepassword"
    }
)
print(response.json())
```

The API will:
1. Validate the email format
2. Check if the email is already registered
3. Hash the password securely
4. Create a new user account
5. Return the created user details (excluding password)
""")
async def register_user(user: UserCreate, service: UserService = Depends(get_user_service)):
    return await service.create_user(user)

# Login endpoint
@router.post("/login/", response_model=LoginResponse, description="""
Authenticate a user and get an access token.

Example using curl:
```bash
curl -X POST "http://localhost:8000/auth/login" \\
     -H "Content-Type: application/x-www-form-urlencoded" \\
     -d "username=user@example.com&password=securepassword"
```

Example using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/auth/login",
    data={
        "username": "user@example.com",
        "password": "securepassword"
    }
)
print(response.json())
```

The API will:
1. Validate the credentials
2. Generate a JWT access token
3. Return the token with user details

Note: The access token should be included in the Authorization header for protected endpoints:
```bash
curl -H "Authorization: Bearer your_access_token" http://localhost:8000/protected-endpoint
```
""")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), service: UserService = Depends(get_user_service)):
    user_login = UserLogin(username=form_data.username, password=form_data.password)  # username field is email
    return await service.login(user_login)
