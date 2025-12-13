import os
import certifi
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

uri = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(uri)  
db_name = "TRPG"
collection_name = "character"

db = client[db_name]
collection2 = db[collection_name]
