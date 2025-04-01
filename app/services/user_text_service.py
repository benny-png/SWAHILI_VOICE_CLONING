from ..database.mongodb import Database
from ..models.schemas import UserTrainingTextCreate, UserTrainingTextUpdate, UserTrainingTextInDB
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException, UploadFile
import csv
import io
import codecs
from app.config import settings

class UserTextService:
    def __init__(self):
        self.db = Database.client[settings.DB_NAME]
        self.collection = self.db.user_training_texts

    async def create_text(self, text: UserTrainingTextCreate) -> UserTrainingTextInDB:
        user = await self.db.users.find_one({"_id": ObjectId(text.user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        text_dict = text.model_dump()
        text_dict["created_at"] = datetime.utcnow()
        text_dict["updated_at"] = datetime.utcnow()
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

    async def update_text(self, text_id: str, text_update: UserTrainingTextUpdate) -> UserTrainingTextInDB:
        text_dict = text_update.model_dump(exclude_unset=True)
        text_dict["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(text_id)},
            {"$set": text_dict}
        )
        updated_text = await self.collection.find_one({"_id": ObjectId(text_id)})
        if updated_text:
            updated_text["id"] = str(updated_text["_id"])
            del updated_text["_id"]
            return UserTrainingTextInDB(**updated_text)
        raise HTTPException(status_code=404, detail="Text not found")

    async def delete_text(self, text_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(text_id)})
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
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
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