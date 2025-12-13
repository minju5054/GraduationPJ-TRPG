import os
import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

uri = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(uri)
db_name = "TRPG"
collection_name = "chat_log"

db = client[db_name]
collection = db[collection_name]