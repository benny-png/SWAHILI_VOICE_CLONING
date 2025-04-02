# app/main.py
from fastapi import FastAPI, APIRouter,HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.services.tts_service import generate_audio, is_swahili
from app.services.text_service import TextService
from app.services.user_service import UserService
from app.services.user_text_service import UserTextService
from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse
from app.models.schemas import (
    TrainingTextCreate, 
    TrainingTextUpdate, 
    TrainingTextInDB,
    TTSRequest,
    UserInDB,
    Token,
    UserCreate,
    UserLogin,
    LoginResponse,
    UserTrainingTextInDB,
    UserTrainingTextUpdate

)

router = APIRouter(prefix="/texts", tags=["texts for all"])

async def get_text_service():
    return TextService()


# Training text endpoints
@router.get("/", response_model=list[TrainingTextInDB], description="""
List all training texts with optional pagination and filtering.

Example using curl:
```bash
curl -X GET "http://localhost:8000/texts?skip=0&limit=10&status=pending"
```

Example using Python:
```python
import requests

response = requests.get(
    "http://localhost:8000/texts",
    params={
        "skip": 0,
        "limit": 10,
        "status": "pending"
    }
)
print(response.json())
```

The API will:
1. Return a list of training texts
2. Apply pagination if specified
3. Filter by status if provided (pending/approved/rejected)
""")
async def list_texts(
    skip: int = 0,
    limit: int | None = None,
    status: str = None,
    service: TextService = Depends(get_text_service)
):
    """
    List training texts with optional pagination and status filter.
    
    Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: None, returns all)
    - status: Filter by status (pending/approved/rejected)
    """
    texts = await service.list_texts(skip=skip, limit=limit, status=status)
    return texts

@router.get("/{text_id}", response_model=TrainingTextInDB, description="""
Get a specific training text by ID.

Example using curl:
```bash
curl -X GET "http://localhost:8000/texts/123456789"
```

Example using Python:
```python
import requests

response = requests.get(
    "http://localhost:8000/texts/123456789"
)
print(response.json())
```

The API will:
1. Check if the text exists
2. Return the text details
""")
async def get_text(text_id: str, service: TextService = Depends(get_text_service)):
    text = await service.get_text(text_id)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text

@router.put("/{text_id}", response_model=TrainingTextInDB, description="""
Update an existing training text.

Example using curl:
```bash
curl -X PUT "http://localhost:8000/texts/123456789" \\
     -H "Content-Type: application/json" \\
     -d '{
           "client_id": "client123",
           "path": "/audio/updated.wav",
           "sentence": "Updated Swahili text",
           "status": "approved"
         }'
```

Example using Python:
```python
import requests

response = requests.put(
    "http://localhost:8000/texts/123456789",
    json={
        "client_id": "client123",
        "path": "/audio/updated.wav",
        "sentence": "Updated Swahili text",
        "status": "approved"
    }
)
print(response.json())
```

The API will:
1. Check if the text exists
2. Update the specified fields
3. Return the updated text
""")
async def update_text(
    text_id: str, 
    text_update: TrainingTextUpdate, 
    service: TextService = Depends(get_text_service)
):
    text = await service.update_text(text_id, text_update)
    if not text:
        raise HTTPException(status_code=404, detail="Text not found")
    return text

@router.delete("/{text_id}", description="""
Delete a training text.

Example using curl:
```bash
curl -X DELETE "http://localhost:8000/texts/123456789"
```

Example using Python:
```python
import requests

response = requests.delete(
    "http://localhost:8000/texts/123456789"
)
print(response.json())
```

The API will:
1. Check if the text exists
2. Delete the text
3. Return a success message
""")
async def delete_text(text_id: str, service: TextService = Depends(get_text_service)):
    success = await service.delete_text(text_id)
    if not success:
        raise HTTPException(status_code=404, detail="Text not found")
    return {"message": "Text deleted successfully"}

@router.post("/import-training-data/", description="""
Import training data in JSON format.

Example using curl:
```bash
curl -X POST "http://localhost:8000/texts/import-training-data" \\
     -H "Content-Type: application/json" \\
     -d '[
           {
             "client_id": "123",
             "path": "/audio/sample1.wav",
             "sentence": "Habari za asubuhi"
           },
           {
             "client_id": "124",
             "path": "/audio/sample2.wav",
             "sentence": "Karibu nyumbani"
           }
         ]'
```

Example using Python:
```python
import requests

data = [
    {
        "client_id": "123",
        "path": "/audio/sample1.wav",
        "sentence": "Habari za asubuhi"
    },
    {
        "client_id": "124",
        "path": "/audio/sample2.wav",
        "sentence": "Karibu nyumbani"
    }
]

response = requests.post(
    "http://localhost:8000/texts/import-training-data",
    json=data
)
print(response.json())
```

The API will:
1. Validate the JSON data format
2. Import all provided training texts
3. Return the number of imported texts
""")
async def import_training_data(
    data: list[dict],
    service: TextService = Depends(get_text_service)
):
    count = await service.import_training_data(data)
    return {"message": f"Successfully imported {count} training texts"}

@router.get("/export-training-data/")
async def export_training_data(
    status: str = None,
    service: TextService = Depends(get_text_service)
):
    return await service.export_texts_to_csv(status)

@router.post("/import-training-data-csv/", description="""
Import training data from a CSV file.

Example using curl:
```bash
curl -X POST "http://localhost:8000/texts/import-training-data-csv" \\
     -F "file=@training_data.csv"
```

Example using Python:
```python
import requests

files = {"file": open("training_data.csv", "rb")}
response = requests.post(
    "http://localhost:8000/texts/import-training-data-csv",
    files=files
)
print(response.json())
```

The API will:
1. Validate the CSV file format
2. Process and import the data
3. Return the number of imported texts

CSV Format:
- Required columns: client_id, path, sentence
- Example:
  ```csv
  client_id,path,sentence
  123,/audio/sample1.wav,Habari za asubuhi
  124,/audio/sample2.wav,Karibu nyumbani
  ```
""")
async def import_training_data_csv(
    file: UploadFile = File(...),
    service: TextService = Depends(get_text_service)
):
    """
    Import training data from CSV file.
    CSV should have columns: client_id, path, sentence
    """
    count = await service.import_training_data_csv(file)
    return {
        "message": f"Successfully imported {count} training texts",
        "imported_count": count
    }
