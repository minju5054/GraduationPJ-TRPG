from models.prompt_base import construct_prompt
from database.database import collection
async def build_message_chain(input_text:str):#(scenario_id:int 넣을 예정)
    system_prompt = construct_prompt(1)
    messages = [{"role": "system","content": system_prompt}]

    cursor = collection.find({"room_id": "3"}).sort("created_at",1)
    msghistory = await cursor.to_list(length = None)
    if msghistory:
        for doc in msghistory:
            messages.append({"role": doc['role'],"content": doc['content']})
        messages.append({"role": "user", "content": input_text})
    else:
        messages.append({"role": "user", "content": input_text}) 
    return messages