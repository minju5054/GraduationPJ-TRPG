import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from database.database import collection
from models.type_model import ChatMessage
from models.type_model import ChatLog
from models.type_model import DiceMessage
from models.type_model import UserCharacterInfo
from models.type_model import AiCharacterInfo
from services.prompt_service import build_message_chain
from services.judge import dicejudgement

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
async def chat(request: ChatMessage):
    # (설명) UI 상에서 입력한 text에 대해서 pydantic- > Models의 ChatMessage 를 참고해서 받아온 메시지
    # (설명) db에 저장하기 전에 지정한 변수에 해당
    created_at = f"{request.date} {request.time}"
    user_log = ChatLog(
        room_id=request.room_id,
        role="user",
        type="talk",
        sender = UserCharacterInfo(id=request.senderId,name=request.sender),
        content = request.content,
        created_at = created_at
    )
    await collection.insert_one(user_log.model_dump())
    # (설명)gpt 생성
    # 프롬프트 생성 들어갈 part
    
    gpt_messages = await build_message_chain(request.content)

    #
    completion = client.chat.completions.create(
        model="gpt-5.1",
        messages = gpt_messages
    )
    # (설명)생성된 text 변수
    response = completion.choices[0].message.content
    # (미구현)입력 메시지인데 지금은 어차피 유저 text하나만 들어가지만 나중에 프롬프트에 여러개 들어갈까봐
    #따로 지정해둠
    user_msg = request.content
    #gpt가 답변 생성한 시간을 구현 (ai_log -> created_at에 활용하고자)
    unix_time = completion.created
    dt_obj = datetime.fromtimestamp(unix_time)
    ai_created_at = dt_obj.strftime("%Y/%m/%d %H:%M")

    ai_log = ChatLog(
        room_id=request.room_id,
        role="assistant",
        type="talk",
        sender = AiCharacterInfo(id=999, name="character_name"),
        content = response,
        created_at = ai_created_at
    )
    await collection.insert_one(ai_log.model_dump())

    date_part, time_part = ai_created_at.split(" ")
    response_obj = ChatMessage(
        room_id = ai_log.room_id,
        id=int(unix_time*1000),
        sender = ai_log.sender.name,
        senderId = ai_log.sender.id,
        date = date_part,
        time = time_part,
        content = response
    )
    return response_obj

async def dice(request:DiceMessage):
    print("---------------------------------------판정 알고리즘 시작(...chat_openai-dice)----------------------------------------------")
    created_at = f"{request.date} {request.time}"
    dice_log = ChatLog(
        room_id=request.room_id,
        role="user",
        type="dice",
        sender = UserCharacterInfo(id=request.senderId,name=request.sender),
        content = str(request.diceval),
        created_at = created_at
    )
    await collection.insert_one(dice_log.model_dump())
    #dice judgemnet 실행 -> rag + 캐릭터 수치 가져오기 판정 진행 
    
                        #(아직 미구현 코드 구현 필요 -> services.judge로 가서 구현할 예정)
    message = await dicejudgement(request)
    #return 성공 여부 message = {"성공/실패"}
    print("============================== 판정 성공 여부 =======================================")
    print(message)
    gpt_messages = await build_message_chain(message)
    print("============================== gpt api 생성 중 ======================================")
    completion = client.chat.completions.create(
        model="gpt-5.1",
        messages = gpt_messages
    )
    response = completion.choices[0].message.content
    unix_time = completion.created
    dt_obj = datetime.fromtimestamp(unix_time)
    ai_created_at = dt_obj.strftime("%Y/%m/%d %H:%M")

    ai_log = ChatLog(
        room_id=request.room_id,
        role="assistant",
        type="talk",
        sender = AiCharacterInfo(id=999, name="character_name"),
        content = response,
        created_at = ai_created_at
    )
    await collection.insert_one(ai_log.model_dump())

    date_part, time_part = ai_created_at.split(" ")
    response_obj = ChatMessage(
        room_id = ai_log.room_id,
        id=int(unix_time*1000),
        sender = ai_log.sender.name,
        senderId = ai_log.sender.id,
        date = date_part,
        time = time_part,
        content = response
    )
    return response_obj