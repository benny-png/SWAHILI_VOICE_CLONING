# app/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, APIRouter

from fastapi.responses import StreamingResponse, FileResponse, PlainTextResponse


import os


router = APIRouter(prefix="/utils", tags=["utils"])

# Readme file path
README_PATH = "readme.md"

@router.get("/readme", response_class=PlainTextResponse)
async def get_readme():
    """
    Returns the API readme as text/markdown
    """
    try:
        with open(README_PATH, "r") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="README.md not found")

@router.get("/readme/download")
async def download_readme():
    """
    Downloads the API readme as a markdown file
    """
    if not os.path.isfile(README_PATH):
        raise HTTPException(status_code=404, detail="README.md not found")
    
    return FileResponse(
        path=README_PATH,
        filename="swahili-voice-api-readme.md",
        media_type="text/markdown"
    )