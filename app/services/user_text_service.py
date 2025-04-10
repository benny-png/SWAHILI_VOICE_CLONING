from ..database.mongodb import Database
from ..models.schemas import UserTrainingTextCreate, UserTrainingTextUpdate, UserTrainingTextInDB
from bson import ObjectId
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import csv
import io
import codecs
from app.config import settings
from app.services.user_service import UserService

class UserTextService:
    def __init__(self):
        self.db = Database.client[settings.DB_NAME]
        self.collection = self.db.user_training_texts

    async def create_text(self, text: UserTrainingTextCreate) -> UserTrainingTextInDB:
        user = await self.db.users.find_one({"_id": ObjectId(text.user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        text_dict = text.model_dump()
        text_dict["created_at"] = datetime.now(timezone.utc)
        text_dict["updated_at"] = datetime.now(timezone.utc)
        text_dict["status"] = "pending"
        result = await self.collection.insert_one(text_dict)
        created_text = await self.collection.find_one({"_id": result.inserted_id})
        created_text["id"] = str(created_text["_id"])
        del created_text["_id"]
        return UserTrainingTextInDB(**created_text)

    async def get_text(self, text_id: str) -> UserTrainingTextInDB:
        text = await self.collection.find_one({"_id": ObjectId(text_id)})
        if text:
            text["id"] = str(text["_id"])
            del text["_id"]
            return UserTrainingTextInDB(**text)
        return None

    async def update_text(self, text_id: str, text_update: UserTrainingTextUpdate,user_id:str) -> UserTrainingTextInDB:
        text_dict = text_update.model_dump(exclude_unset=True)
        text_dict["updated_at"] = datetime.now(timezone.utc)
        await self.collection.update_one(
            {"_id": ObjectId(text_id)},
            {"$set": text_dict}
        )
        updated_text = await self.collection.find_one({"_id": ObjectId(text_id)})
        if updated_text:
            updated_text["id"] = str(updated_text["_id"])
            del updated_text["_id"]
            user_service = UserService()
            await user_service.increment_total_audio_length(user_id, length=text_update.audio_length)
            return UserTrainingTextInDB(**updated_text)
        raise HTTPException(status_code=404, detail="Text not found")

    async def delete_text(self, text_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(text_id)})
        return result.deleted_count > 0
    
    async def delete_texts_by_user(self, user_id: str) -> int:
        result = await self.collection.delete_many({"user_id": user_id})
        return result.deleted_count > 0

    async def list_texts(self, skip: int = 0, limit: int | None = None, status: str = None, user_id: str = None):
        query = {}
        if status:
            query["status"] = status
        if user_id:
            query["user_id"] = user_id
        cursor = self.collection.find(query).skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)
            texts = await cursor.to_list(length=limit)
        else:
            texts = await cursor.to_list(None)
        for text in texts:
            text["id"] = str(text["_id"])
            del text["_id"]
        return [UserTrainingTextInDB(**text) for text in texts]

    async def import_training_data_csv(self, file: UploadFile,user_id:str) -> int:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        try:
            csvReader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
            texts = []
            for row in csvReader:
                required_fields = [ 'sentence']
                if not all(field in row for field in required_fields):
                    raise HTTPException(
                        status_code=400,
                        detail=f"CSV must contain columns: {', '.join(required_fields)}"
                    )
                user = await self.db.users.find_one({"_id": ObjectId(user_id)})
                if not user:
                    raise HTTPException(status_code=404, detail=f"User {user_id} not found")
                text_dict = {
                    "user_id": user_id,
                    "sentence": row["sentence"],
                    "status": "pending",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                texts.append(text_dict)
            if texts:
                result = await self.collection.insert_many(texts)
                return len(result.inserted_ids)
            return 0
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")
        finally:
            file.file.close()

    async def export_texts_to_csv(self, user_id:str, status: str = None) -> StreamingResponse:
        try:
            print(f"Starting export for user: {user_id}, status: {status}")
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['text_id', 'path', 'sentence', 'status','audio_length'])
        
            
            query = {}
            if status:
                query["status"] = status
            if user_id:
                query["user_id"] = user_id
        
            print(f"Finding texts with query: {query}")
            cursor = self.collection.find(query)
        
            count = 0
            async for text in cursor:
                count += 1
                writer.writerow([
                    text['_id'],
                    text.get('path', ''),  # Use get with default in case 'path' is missing
                    text['sentence'],
                    text.get('status', 'pending'),
                    text.get('audio_length','')
                ])
        
            print(f"Found {count} texts")
            output.seek(0)
        
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    'Content-Disposition': f'attachment; filename=training_texts_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.csv'
                }
            )
        except Exception as e:
            print(f"Error in export_texts_to_csv: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))