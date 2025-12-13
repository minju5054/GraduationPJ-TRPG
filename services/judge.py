from database.database_stat import collection2
from database.database import collection
from models.type_model import DiceMessage
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class StatCheckRequirement(BaseModel):
    target_key: str = Field(description="캐릭터 데이터에서 가져와야 할 스탯의 정확한 키 이름 (예: 'INT', 'STR', '관찰력')")
    operator: str = Field(description="비교 연산자 (<=, >=, == 중 하나). 크툴루 룰은 보통 '<=' 임")
    reasoning: str = Field(description="이 스탯을 선택한 이유")

async def dicejudgement(request: DiceMessage):
    # rag part 
        # 이전 대화 assistant message(content) 가져와서 rag의 querytext로 활용
    cursor = (
        collection.find({"room_id": request.room_id})
        .sort("created_at", -1)
        .skip(1)
        .limit(1)
    )
    result_list = await cursor.to_list(length=1)
    user_context = result_list[0].get("content", "") if result_list else ""
        # return rule 출력 
    rule_text = "판정의 성공과 실패 판정의 최종결과는 성공 아니면 실패입니다. 나온 숫자에 비례해서 더 크게 성공하거나 더 적게 성공하는 것은 아닙니다. 판정은 플레이어가 목표를 밝힌 다음에 합니다. 판정 결과가 필 요한 값 이하이면 목표를 완전히 달성합니다. 결과가 기능수치의 절반이나 5분의 1 이하로 나온다고 해서 꼭 더 크게 성공하는 것은 아닙니다. 결과의 자세한 해석은 수호자의 판단에 따릅니다.성공 판정을 해서 수호자가 설정한 값 이하로 나오면 탐사자는 판정 전에 정한 목표를 달성합니다. 결과를 묘사할 때 플레이어의 참여를 장려하세요. 플레이어가 탐사자의 행동만이 아니라 NPC와 주변 상황에 관한 묘사까지 해도 괜찮습니다. 수호자와 대화를 통해 얼마든지 조율이 가능하기 때문입니다. 따라서, 성공한 판정의 결과는 플레이어와 수호자가 함께 묘사하게 됩니다. 관찰 판정은 지능 스탯으로 정해집니다" 

    # 캐릭터 stat 가져오기. ui-> fastapi -> db(update)/ dicejudgement- > db불러오기 및 업데이트로 구상
    data = await collection2.find_one(
        {"character_id": request.senderId},
        {"_id": 0}
    )
    available_keys = list(data["stat"].keys()) #출력할 수 있는 키를 주어진 값으로 제한
    
    # rule 기반 stat + Dice 로 판정 결과 출력 
    # - 고민사항 : rag의 출력 문장을 어떻게 스탯과 매칭시킬까(이해할까)?
    # - 고민사항 : 어떻게 판정에 필요한 스텟을 잘 뽑아낼것인가? 여러 스탯중에 필요한 스탯만 뽑아내는 거를 어떤 방식으로? => llm을 parser로 이용하는 형태 이용되는 stat과 연산자를 판정 로직으로 활용
    llm = ChatOpenAI(model="gpt-5.1", temperature=0)
    structured = llm.with_structured_output(StatCheckRequirement)
    #프롬프트 구성 => key를 뽑아내는걸 목표로 설정.
    prompt = f"""
[상황]
{user_context}
[규칙]
{rule_text}
[데이터베이스 가능한 키 목록]
{available_keys}

위 상황과 규칙을 고려할 때, 판정을 위해 캐릭터의 어떤 스탯(Key)이 필요한가요?
반드시 키 목록 안의 정확한 단어만 사용하세요.
보통 성공 조건은 '주사위 값 <= 스탯 값' 입니다.
"""
    print(prompt)

    try:
        parsed_req = await structured.ainvoke(prompt)
    except AttributeError:
        parsed_req = structured.invoke(prompt)

    key = parsed_req.target_key
    print(key)
    if key not in data["stat"]:
        key = "INT" if "INT" in data["stat"] else available_keys[0] #혹시 key값이 주어진 거 이외의 값이 나왔을 때를 대비해서 추가 처리하였음
    
    target_stat = int(data["stat"][key])
    print(target_stat)
    print(parsed_req.reasoning)
    dice_result = int(request.diceval)
    print(dice_result)
    op = parsed_req.operator
    print(op)
    if op == "<=":
        is_success = dice_result <= target_stat
    elif op == ">=":
        is_success = dice_result >= target_stat
    elif op == "==":
        is_success = dice_result == target_stat
    else:
        is_success = dice_result <= target_stat 
    
    return "성공" if is_success else "실패"
  
