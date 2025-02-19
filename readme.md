# Swahili Voice Cloning API

A FastAPI-based service for Swahili text-to-speech (TTS) generation using fine-tuned models.

## Overview

This API provides endpoints for:
1. Text-to-speech conversion using various Swahili voice models
2. Managing training text data for voice models
3. Importing and exporting training data

## API Endpoints

### Documentation Endpoints

## Example Usage
Using curl:
```bash
curl -X POST "http://localhost:8000/tts/briget" \
     -H "Content-Type: application/json" \
     -d '{"text":"Kijana huyu ni msataarabu sana sana"}' \
     --output output.wav
```

Using Python requests:
```python
import requests

response = requests.post(
    "http://localhost:8000/tts/briget",
    json={"text": "Kijana huyu ni msataarabu sana sana"}
)

with open("output.wav", "wb") as f:
    f.write(response.content)
```

#### Get API Documentation
```
GET /docs
```
Interactive API documentation (Swagger UI)

#### Get Readme
```
GET /readme
```
Returns the API readme as text/markdown

#### Download Readme
```
GET /readme/download
```
Downloads the API readme as a markdown file

### Text-to-Speech (TTS) Endpoints

#### Generate Speech with Benny's Voice
```
POST /tts/benny
```
Converts Swahili text to speech using the Benny voice model.

**Request Body:**
```json
{
  "text": "Habari, ninaitwa Benny."
}
```
**Response:** Audio file (WAV format)

#### Generate Speech with Briget's Voice
```
POST /tts/briget
```
Converts Swahili text to speech using the Briget voice model.

**Request Body:**
```json
{
  "text": "Habari, ninaitwa Briget."
}
```
**Response:** Audio file (WAV format)

#### Generate Speech with Emanuela's Voice
```
POST /tts/emanuela
```
Converts Swahili text to speech using the Emanuela voice model.

**Request Body:**
```json
{
  "text": "Habari, ninaitwa Emanuela."
}
```
**Response:** Audio file (WAV format) (NOTE numbers get normalized automatically)

#### Debug Number Conversion
```
POST /debug/number-conversion
```
Debug endpoint to test number normalization in Swahili text.

**Request Body:**
```json
{
  "text": "Nina umri wa miaka 25 na shilingi 100.50"
}
```

**Response:**
```json
{
  "original_text": "Nina umri wa miaka 25 na shilingi 100.50",
  "normalized_text": "Nina umri wa miaka ishirini na tano na shilingi mia moja na nusu"
}
```

### Training Text Management

#### List Training Texts
```
GET /texts/
```
Returns a list of training texts with optional pagination and filtering.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return
- `status` (optional): Filter by status (pending/approved/rejected)

#### Get Training Text
```
GET /texts/{text_id}
```
Retrieves a specific training text by ID.

#### Update Training Text
```
PUT /texts/{text_id}
```
Updates a specific training text.

**Request Body:**
```json
{
  "swahili_text": "Text in Swahili",
  "english_translation": "English translation",
  "status": "approved"
}
```

#### Delete Training Text
```
DELETE /texts/{text_id}
```
Deletes a specific training text.

### Data Import/Export

#### Import Training Data
```
POST /import-training-data/
```
Imports training data in JSON format.

**Request Body:**
```json
[
  {
    "client_id": "123",
    "path": "/audio/sample1.wav",
    "sentence": "Habari za asubuhi"
  }
]
```

#### Import Training Data from CSV
```
POST /import-training-data-csv/
```
Imports training data from a CSV file.

**Request:** Form data with CSV file
**CSV Format:** Should contain columns: client_id, path, sentence

#### Export Training Data
```
GET /export-training-data/
```
Exports training data to CSV format.

**Query Parameters:**
- `status` (optional): Filter by status (pending/approved/rejected)

## Authentication

The API currently allows all origins (`*`) through CORS middleware. (For current prototyping phase).

## Database

The API uses MongoDB for storing training text data. Database connections are managed at application startup and shutdown.

## Models

The API uses three fine-tuned Swahili TTS models for different voice personalities:
1. Benny's voice
2. Briget's voice 
3. Emanuela's voice

## Text Normalization

The API includes automatic number normalization for Swahili text:
- Numbers in text are converted to their Swahili word equivalents
- Supports both integers and decimal numbers
- Improves speech naturalness and pronunciation accuracy  
- Uses the `tarakimu` library for accurate Swahili number conversion

## Audio Processing

The API performs audio normalization to ensure consistent output quality:
- Audio is normalized to 16-bit PCM WAV format
- Sample values are scaled to the range of -32767 to 32767
- Proper amplitude scaling ensures optimal volume levels
- The API returns audio at the model's native sample rate

## Error Handling

The API validates that input text is in Swahili before processing TTS requests and returns appropriate HTTP error codes for invalid requests.
