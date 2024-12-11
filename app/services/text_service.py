# app/services/text_service.py
from ..database.mongodb import Database
from ..models.schemas import TrainingTextCreate, TrainingTextUpdate, TrainingTextInDB
from bson import ObjectId
from app.config import settings
from datetime import datetime
from fastapi.responses import StreamingResponse
import csv
import io

class TextService:
    def __init__(self):
        self.db = Database.client[settings.DB_NAME]
        self.collection = self.db.training_texts

    async def create_text(self, text: TrainingTextCreate) -> TrainingTextInDB:
        text_dict = text.dict()
        text_dict["created_at"] = datetime.utcnow()
        text_dict["updated_at"] = datetime.utcnow()
        text_dict["status"] = "pending"
        
        result = await self.collection.insert_one(text_dict)
        created_text = await self.collection.find_one({"_id": result.inserted_id})
        return TrainingTextInDB(**created_text)

    async def get_text(self, text_id: str) -> TrainingTextInDB:
        text = await self.collection.find_one({"_id": ObjectId(text_id)})
        if text:
            return TrainingTextInDB(**text)
        return None

    async def update_text(self, text_id: str, text_update: TrainingTextUpdate) -> TrainingTextInDB:
        text_dict = text_update.dict(exclude_unset=True)
        text_dict["updated_at"] = datetime.utcnow()
        
        await self.collection.update_one(
            {"_id": ObjectId(text_id)},
            {"$set": text_dict}
        )
        updated_text = await self.collection.find_one({"_id": ObjectId(text_id)})
        return TrainingTextInDB(**updated_text)

    async def delete_text(self, text_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(text_id)})
        return result.deleted_count > 0

    async def list_texts(self, skip: int = 0, limit: int = 10, status: str = None):
        query = {}
        if status:
            query["status"] = status
            
        cursor = self.collection.find(query).skip(skip).limit(limit)
        texts = await cursor.to_list(length=limit)
        return [TrainingTextInDB(**text) for text in texts]

    async def import_training_data(self, data: list[dict]) -> int:
        texts = []
        for item in data:
            text_dict = {
                "client_id": str(item["client_id"]),
                "path": item["path"],
                "sentence": item["sentence"],
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            texts.append(text_dict)
        
        if texts:
            result = await self.collection.insert_many(texts)
            return len(result.inserted_ids)
        return 0

    async def export_texts_to_csv(self, status: str = None) -> StreamingResponse:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['client_id', 'path', 'sentence', 'status', 'created_at'])
        
        query = {}
        if status:
            query["status"] = status
            
        cursor = self.collection.find(query)
        
        async for text in cursor:
            writer.writerow([
                text['client_id'],
                text['path'],
                text['sentence'],
                text.get('status', 'pending'),
                text.get('created_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                'Content-Disposition': f'attachment; filename=training_texts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
