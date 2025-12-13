import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.type_model import ChatMessage
from models.type_model import DiceMessage
from models.type_model import UserStatInfo

from services.chat_openai import chat
from services.chat_openai import dice

from dotenv import load_dotenv


from database.database_stat import collection2
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers=["*"],
)

@app.post("/gpt")
async def chat_end(req: ChatMessage):
    print(req)
    result = await chat(req)
    return result
@app.post("/dice")
async def dice_end(req: DiceMessage):
    print(req)
    result = await dice(req)
    return result
@app.post("/judge")
async def judge_end(req: DiceMessage):
    print("-------------판정 부분 시작-------------")
    result = await dice(req)
    print("결과 값 리턴 받음 : ", result )
    return result
@app.post("/stats")
async def save_stats(req: UserStatInfo):
    stat_dict = req.model_dump()
    filter = {"character_id":req.character_id}
    content = {"$set": stat_dict}
    await collection2.update_one(filter,content,upsert=True)
    return {"message": "업데이트 성공"}

    
