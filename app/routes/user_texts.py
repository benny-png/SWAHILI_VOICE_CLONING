# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from jose import JWTError, jwt
from pydantic import BaseModel
from app.services.user_service import UserService
from app.services.user_text_service import UserTextService
from app.config import settings
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse
from app.models.schemas import (
    Token,
    UserCreate,
    UserLogin,
    LoginResponse,
    UserTrainingTextInDB,
    UserTrainingTextUpdate
)


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

app = FastAPI()

# Dependency to get current user from token
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user_id

# User texts router with authentication
router = APIRouter(
    prefix="/user",
    tags=["Authenticated user texts"],
    dependencies=[Depends(get_current_user)]  # This applies to all routes in this router
)

async def get_user_text_service():
    return UserTextService()

async def get_user_service():
    return UserService()

# User training text endpoints
@router.get("/texts", response_model=list[UserTrainingTextInDB], description="""
List training texts for the authenticated user with optional filtering.

Example using curl:
```bash
curl -X GET "http://localhost:8000/user/texts?skip=0&limit=10&status=pending" \\
     -H "Authorization: Bearer your_access_token"
```

Example using Python:
```python
import requests

headers = {"Authorization": "Bearer your_access_token"}
response = requests.get(
    "http://localhost:8000/user/texts",
    params={"skip": 0, "limit": 10, "status": "pending"},
    headers=headers
)
print(response.json())
```

The API will:
1. Validate the access token
2. Return the user's training texts with pagination
3. Optionally filter by status (pending/approved/rejected)
""")
async def list_user_texts(
    current_user: Annotated[str, Depends(get_current_user)],
    skip: int = 0,
    limit: int | None = None,
    status: str = None,
    service: UserTextService = Depends(get_user_text_service)
):
    """List user training texts with optional filters"""
    return await service.list_texts(
        skip=skip,
        limit=limit,
        status=status,
        user_id=current_user  # Use authenticated user_id
    )

@router.get("/texts/{text_id}", response_model=UserTrainingTextInDB, description="""
Get a specific training text by ID.

Example using curl:
```bash
curl -X GET "http://localhost:8000/user/texts/123456789" \\
     -H "Authorization: Bearer your_access_token"
```

Example using Python:
```python
import requests

headers = {"Authorization": "Bearer your_access_token"}
response = requests.get(
    "http://localhost:8000/user/texts/123456789",
    headers=headers
)
print(response.json())
```

The API will:
1. Validate the access token
2. Check if the text exists and belongs to the user
3. Return the text details
""")
async def get_user_text(
    text_id: str,
    current_user: Annotated[str, Depends(get_current_user)],
    service: UserTextService = Depends(get_user_text_service)
):
    """Get a specific user training text by ID"""
    text = await service.get_text(text_id)
    if not text or text.user_id != current_user:
        raise HTTPException(status_code=404, detail="Text not found or unauthorized")
    return text

@router.put("/texts/{text_id}", response_model=UserTrainingTextInDB, description="""
Update an existing training text.

Example using curl:
```bash
curl -X PUT "http://localhost:8000/user/texts/123456789" \\
     -H "Authorization: Bearer your_access_token" \\
     -H "Content-Type: application/json" \\
     -d '{
           "sentence": "Updated Swahili text",
           "status": "approved"
         }'
```

Example using Python:
```python
import requests

headers = {"Authorization": "Bearer your_access_token"}
response = requests.put(
    "http://localhost:8000/user/texts/123456789",
    headers=headers,
    json={
        "sentence": "Updated Swahili text",
        "status": "approved"
    }
)
print(response.json())
```

The API will:
1. Validate the access token
2. Check if the text exists and belongs to the user
3. Update the specified fields
4. Return the updated text
""")
async def update_user_text(
    text_id: str,
    text_update: UserTrainingTextUpdate,
    current_user: Annotated[str, Depends(get_current_user)],
    service: UserTextService = Depends(get_user_text_service)
):  
    """Update an existing user training text"""
    text = await service.get_text(text_id)
    if not text or text.user_id != current_user:
        raise HTTPException(status_code=404, detail="Text not found or unauthorized")
    user_id = current_user
    if user_id:
        result = await service.update_text(text_id, text_update,user_id)
        await service.update_user_status_from_usertexts(user_id)
        return result
    else:
        raise HTTPException(status_code=404, detail="user not found or unauthorized")


@router.delete("/texts/{text_id}", response_model=dict, description="""
Delete a training text.

Example using curl:
```bash
curl -X DELETE "http://localhost:8000/user/texts/123456789" \\
     -H "Authorization: Bearer your_access_token"
```

Example using Python:
```python
import requests

headers = {"Authorization": "Bearer your_access_token"}
response = requests.delete(
    "http://localhost:8000/user/texts/123456789",
    headers=headers
)
print(response.json())
```

The API will:
1. Validate the access token
2. Check if the text exists and belongs to the user
3. Delete the text
4. Return a success message
""")
async def delete_user_text(
    text_id: str,
    current_user: Annotated[str, Depends(get_current_user)],
    service: UserTextService = Depends(get_user_text_service)
):
    """Delete a user training text"""
    text = await service.get_text(text_id)
    if not text or text.user_id != current_user:
        raise HTTPException(status_code=404, detail="Text not found or unauthorized")
    success = await service.delete_text(text_id)
    return {"message": "Text deleted successfully"}

@router.post("/texts/import-csv/{user_id}", response_model=dict, description="""
Import training data from a CSV file.

Example using curl:
```bash
curl -X POST "http://localhost:8000/user/texts/import-csv/your_user_id" \\
     -H "Authorization: Bearer your_access_token" \\
     -F "file=@training_data.csv"
```

Example using Python:
```python
import requests

headers = {"Authorization": "Bearer your_access_token"}
files = {"file": open("training_data.csv", "rb")}
response = requests.post(
    "http://localhost:8000/user/texts/import-csv/your_user_id",
    headers=headers,
    files=files
)
print(response.json())
```

The API will:
1. Validate the access token
2. Verify the user is importing for their own account
3. Process and import the CSV data
4. Return the number of imported texts

CSV Format:
- Required columns: path, sentence
- Example:
  ```csv
  path,sentence
  /audio/sample1.wav,Habari za asubuhi
  /audio/sample2.wav,Karibu nyumbani
  ```
""")
async def import_training_data_csv(
    user_id: str,
    current_user: Annotated[str, Depends(get_current_user)],
    service: UserTextService = Depends(get_user_text_service),
    file: UploadFile = File(...)
):
    """Import training data from CSV file"""
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Cannot import data for another user")
    count = await service.import_training_data_csv(file, user_id)
    return {"message": f"Successfully imported {count} training texts"}

@router.get("/total_audio_length")
async def get_total_audio_length(
    user_id: str,
    current_user: Annotated[str, Depends(get_current_user)],
    service: UserService = Depends(get_user_service)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Cannot get data for another user")
    
    total_audio_length = await service.get_total_audio_length(user_id)
    return {"total_audio_length": total_audio_length}

@router.get("/export-training-data/")
async def export_training_data(
    current_user: Annotated[str, Depends(get_current_user)],
    status: str = None,
    service: UserTextService = Depends(get_user_text_service),
):
    return await service.export_texts_to_csv(user_id=current_user,status=status)