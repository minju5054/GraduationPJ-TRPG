# 변경 이력 (Change Log)

> 작업하면서 **무엇을** 바꿨고 **왜** 바꿨는지 기록하는 문서입니다.
> 가장 최근 변경이 위로 오도록 작성합니다.

---

## #17. 놀이공원 배경 안 뜸 + 판정 안 뜸 수정 (`main.py`, `prompts/trpg_rules.txt`)
**증상**: 놀이공원에서 배경이 안 바뀌고, 판정이 계속 안 나옴.

**원인**
1. 배경: GM이 `[장소: 놀이공원 입구]`를 냈는데 `LOCATION_IMAGES` 키는 `"놀이공원"` → 정확 매칭 실패 → 404.
2. 판정: 로그 확인 결과 **39개 메시지 중 [판정 요청] 0개**. #14(GM 최소화)+#15(페이싱 STAY=KPC만)가 GM의 판정 트리거를 억눌렀음. (scene_public엔 '행운 판정' 등 판정 지점이 있음에도)

**수정**
- 배경: `get_background`에 **부분 매칭** 추가 — 정확 키 없으면 장소명에 키가 포함되는지로 매칭("놀이공원 입구/내부" → "놀이공원"). 검증: 입구/내부 200, 회전목마 404(폴백).
- 판정: [판정 규칙]을 **[페이싱]·[GM 등장 조건]보다 우선**으로 명시 + 판정 키워드에 행운/정신력/심리학 추가. [페이싱 판단 규칙]에도 "판정 지점이면 STAY/ADVANCE 무관하게 판정 우선" 명시.

**주의**: 프롬프트 변경 → 백엔드 재시작 필요. (장소 세부명이 더 늘면 LOCATION_IMAGES 키 추가 or 별칭 매핑 보강)

---

## #16. GM/KPC 분리 버그 수정 — 빈 KPC 줄 (`TRPG/src/App.jsx`)
**증상**: GM/KPC가 잘 분리되다가, 어떤 메시지에서 갑자기 안 됨(GM 내레이션이 KPC 말풍선에 'GM:' 글자째 뭉쳐서 표시).

**원인**: `splitGmKpc`의 정규식 `KPC:\s*...`에서 `\s*`가 **빈 KPC 줄 뒤의 줄바꿈까지 소비** → 다음 `GM:`을 줄머리 마커로 인식 못 함. #14(GM 조건부) 이후 모델이 가끔 `KPC: <빈칸>\nGM: ...` 형태로 출력하며 드러남.

**수정**: 정규식 → **줄 단위 파싱**으로 교체. 줄머리가 `GM:`/`KPC:`면 새 발화 시작, 그 외 줄은 직전 발화에 이어붙임(멀티라인 지원), 빈 세그먼트는 제거.
- 검증: 빈KPC+GM → GM 1개로 올바르게 분리, KPC만/KPC+GM/멀티라인 모두 정상.

---

## #15. 적응형 페이싱 — `[페이싱]` 자가판단 태그 (`prompts/trpg_rules.txt`, `TRPG/src/App.jsx`)
**문제**: `PROGRESS%`가 매 턴 일정하게 오르는 선형 카운터라, 장면별로 필요한 대화량이 달라도 같은 속도로 진행 → 어떤 장면은 빨리 지나가고 어떤 장면은 질질 끌림.

**해결(가벼운 버전)**: scene_public은 그대로 두고, GM이 **매 턴 '현재 장면의 목적이 충분히 다뤄졌는가'를 자가판단**하도록 규칙 추가.
- **STAY**(목적 미충족): GM 없이 KPC 대화로 머묾, PROGRESS 거의 안 올림(±0~3%).
- **ADVANCE**(목적 충족): GM이 다음 사건을 한 걸음 전개, PROGRESS 의미 있게 상승.
- 판단 근거: 현재 순간의 목적 + **최근 PC·KPC 대화**(이전 대화 참고) + 플레이어 입력 신호(긴 RP→STAY, 짧은 행동지향→ADVANCE).
- 응답 끝에 내부 제어 태그 `[페이싱 충족=<t/f> 판단=<STAY/ADVANCE>]` 출력.

**프론트**: `stripDisplayTags`에 `\[페이싱[^\]]*\]` 제거 추가 → 화면 비표시(내부용).

**주의**: trpg_rules.txt 변경이므로 **백엔드 재시작 필요**.
**향후**: 효과 보고 더 정밀하게 가려면 scene_public을 '비트+목적' 구조로 재구성(옵션 A) 고려.

---

## #14. GM 등장 빈도 조정 (`prompts/trpg_rules.txt`)
**문제**: 출력 형식이 매 턴 `GM:` 라인을 필수로 두어 GM이 거의 매 턴 등장 → PC와 KPC의 대화가 충분히 진행되지 않음.

**변경**: [출력 형식 - 엄수]에서 순서를 `PROGRESS / KPC(기본) / GM(조건부)`로 바꾸고 **[GM 등장 조건]** 블록 추가.
- 기본은 KPC만 출력. PC↔KPC 대화 중에는 GM 라인 생략.
- GM은 ①새 장면/장소 ②새 사건·정보 ③판정 요청 ④행동의 직관적 결과 묘사 때만 등장.
- 일상 RP 구간은 연속 여러 턴 GM 없이 KPC만 가능. (PROGRESS 라인은 매 턴 유지)

**주의**: `trpg_rules.txt`는 prompt_base 임포트 시 1회 로드 → **백엔드 재시작 필요**.

**관련(섹션 전환 디버깅)**: 로그 확인 결과 `end of section`이 저장되고 유저가 수동 입력해야 진행됨 = 실행 중 백엔드가 #12-1 이전 코드. 디스크 코드는 정상 → **재시작으로 해결**. 추가로 GM이 PROGRESS 100%에서도 `end of section`을 잘 안 내보내 '질질 끄는' 현상 있음 → 향후 백엔드 강제 전환(PROGRESS 100% 시 advance) 옵션 검토.

---

## #13. 비주얼노벨 연출 — 배경 위 스탠딩 + SD 아바타 + 발화자 페이드
**파일**: [main.py](main.py), [TRPG/src/App.jsx](TRPG/src/App.jsx), [TRPG/src/App.css](TRPG/src/App.css)

**목표**: 배경 위에 캐릭터 전신 스탠딩을 올리고, 발화자 전환 시 페이드. 채팅 아바타는 별도 SD 이미지.
정정: #11 에서 전신 PC/KPC 를 채팅 아바타로 썼으나, 전신=스탠딩 / SD=채팅 아바타로 역할 분리.

**구현**
- 백엔드: `generated_assets/sds/{PC,KPC}_sd.png` → `GET /sd/{role}` 신설. (전신은 기존 `/character/{role}` 유지)
- 프론트 아바타: `getDisplayBubbles` 에서 KPC→`/sd/KPC`, 플레이어→`/sd/PC`, GM→gptRobot. 각 말풍선에 `speaker`("GM"/"KPC"/"PC") 부여.
- 스탠딩: `.screen-image` 안에 PC(좌)·KPC(우) 전신 2개 상시 렌더. `currentSpeaker` state(최신 발화 말풍선 추적)에 따라 발화자=`speaking`(또렷)/그 외=`dim`(어둡게). CSS `transition`(opacity/filter/transform 0.45s)로 발화자 전환 시 페이드.

**결정 반영**: PC·KPC 둘 다 표시, 발화자 전환 시 페이드(상시 표시 + 밝기 전환 방식).

**검증**: `/sd/{PC,KPC}` 200, `npm run build` 성공. (실제 페이드 연출은 브라우저 플레이로 확인)

**비고**: 하단 PC 초상화(screen-portraits, 4슬롯)는 아직 전신 `/character/PC` 사용 — 스탠딩과 중복될 수 있어 정리 여부는 추후 논의.

### 13-1. VN 화면 정리 (불필요 패널 제거 + 스탠딩 톤 조정)
- **하단 PC1~4 초상화(screen-portraits) 제거.**
- **왼쪽 패널(left-panel: 캐릭터 리스트/이성/옵션룰/주사위봇) 숨김** — `{false && ...}` 로 감싸 보존(되살리려면 true). 레이아웃 3컬럼→**2컬럼**(`minmax(0,1fr) 360px`).
- 스탠딩 `dim` 완화(opacity 0.5→0.78, brightness 0.5→0.72) — 너무 유령처럼 보이던 것 개선.
- **남은 핵심 이슈(사용자 작업)**: 스탠딩 전신 PC/KPC 이미지가 **흰 배경**이라 배경 위에 박스로 떠 어색함 → **누끼(투명 배경) PNG로 교체** 필요. CSS로는 해결 불가.

---

## #12. 장면(섹션) 진행 구현 — `end of section` → 다음 장 전환
**파일**: [database/database.py](database/database.py), [services/prompt_service.py](services/prompt_service.py), [services/chat_openai.py](services/chat_openai.py)

**문제**: `construct_prompt(1)` 하드코딩으로 영원히 scene_public1 만 로드 → 1장이 소진된 채 GM 이 `end of section` 을 무한 반복.

**설계 결정**: 처음엔 "end of section 개수 세기"를 고려했으나, `end of section`이 chat_log 에 중복 저장되면 섹션을 건너뛰는 문제가 있어 폐기. → **명시적 상태 + 감지 즉시 전환** 방식 채택.

**구현**
- `room_state` 컬렉션 신설(`{room_id, section_id}`).
- prompt_service: `get_section`/`advance_section`(상한 `MAX_SECTION`=scene_public 파일 수, 현재 7). `build_message_chain(input_text, room_id)` 가 현재 섹션의 scene_public 을 로드 (덤으로 기존 `room_id:"3"` 하드코딩 버그도 해소).
- chat_openai: `_generate_with_section_progress()` — 응답이 `end of section` 이면 **섹션 전진 후 새 섹션으로 1회 재생성**. 그 결과(다음 장 내용)를 저장하므로 `end of section` 은 로그에 남지 않고 같은 턴에 반복되지 않음. `chat()`·`dice()` 양쪽 적용.

**효과**: `end of section` 중복 저장/반복/로그 오염 없이 섹션이 1→2→…→7 로 자동 전진.

**보완(12-1)**: 재생성 시 유저의 이전 입력을 재탕하면 또 `end of section`이 나기 쉬워 유저가 "다음"을 입력해야 넘어가는 어색함이 있었음.
→ 재생성 쿼리를 명시적 전환 지시("이전 장면이 끝났습니다. 새 scene_public 도입부를 시작하세요")로 교체.
유저가 별도 입력 없이 **같은 턴에 다음 장 도입부가 자동 생성**됨(이 지시 문구는 저장하지 않음).

**검증**: get/advance/상한(7에서 멈춤) DB 로 확인. (실제 GM 의 `end of section` 발화→전환은 브라우저 플레이로 확인 필요)

---

## #11. 생성 이미지 백엔드 서빙 + 배경 동적 교체 (`main.py`, `TRPG/src/App.jsx`)
**목표**: 생성 배경/캐릭터 이미지를 **백엔드에서 서빙**하고, GM의 `[장소: X]` 태그에 따라 배경을 동적 교체.

**백엔드** [main.py](main.py)
- `generated_assets/{backgrouds,characters}` 를 서빙. 장소명→파일 매핑(`LOCATION_IMAGES`)과 역할→파일(`CHARACTER_IMAGES`)을 백엔드에 둠(단일 소스, 이미지 추가 시 여기만 수정).
- `GET /background/{location}` → 매핑된 배경 `FileResponse`, 없으면 404(프론트 폴백).
- `GET /character/{role}` → PC/KPC 이미지 `FileResponse`.
- 검증: `/background/거실`=200(1.46MB png), `/background/회전목마`=404, `/character/{PC,KPC}`=200.

**프론트** [TRPG/src/App.jsx](TRPG/src/App.jsx)
- `backgroundUrl` state 추가.
- `applyLocationBackground(text)`: GM 응답 content에서 `/\[장소:\s*([^\]]+)\]/` 파싱 → `GET /background/{장소}` 가 200이면 배경 교체, 404면 이전 배경 유지(폴백).
- `/gpt`·`/dice` 응답 직후 호출.
- 배경 `div.screen-image` 를 `backgroundUrl` 인라인 스타일(cover/center)로 렌더.
- `npm run build` 성공(36 모듈).

**캐릭터 이미지 프론트 적용(11-1)**: `getPortraitById` 를 정적 import(pc1~4) → 백엔드 URL 로 교체.
- `senderId === 999`(AI 동행 KPC) → `/character/KPC`, 그 외 truthy id(플레이어) → `/character/PC`.
- 채팅 아바타·하단 초상화·캐릭터 목록 아바타가 모두 이 함수를 쓰므로 한 곳 수정으로 전체 반영.
- 안 쓰는 `pc1~4.png` import 제거(번들 36→32 모듈). `npm run build` 성공.
- 비고: 1:1 플레이 기준(플레이어 PC + AI KPC). 멀티면 플레이어 전원이 PC.png 로 동일하게 표시됨.

**GM/KPC 말풍선 분리(11-2)**: AI 응답은 한 메시지(senderId=999) 안에 `GM:`(내레이션)과 `KPC:`(대사)가 함께 들어있어, KPC.png 를 통째로 적용하면 GM 내레이션까지 KPC 얼굴이 됨 → 잘못됨.
- `splitGmKpc()`: `GM:`/`KPC:` 줄머리 마커로 본문을 세그먼트 분리. `getDisplayBubbles(msg)`: AI 메시지를 GM/KPC 말풍선들로 펼침(`flatMap`).
- 아바타: **KPC → /character/KPC**, **GM → gptRobot 아이콘(내레이터)**. `PROGRESS:` 라인 제외, `[장소: X]` 태그는 표시에서 제거(stripDisplayTags).
- 검증: 실제 메시지로 GM/KPC 2개 말풍선 분리 확인. `npm run build` 성공.

---

## #10. 배경 전환용 `[장소: X]` 태그 규칙 추가 (`prompts/trpg_rules.txt`)
**목표(작업2 일부)**: 생성 배경 이미지를 장면 장소에 따라 동적 교체하기 위한 **신호** 마련.

**방식**: scene_public 을 일일이 수정하지 않고, `[판정 요청]` 과 동일한 패턴으로 **일반 규칙 한 블록**만 trpg_rules.txt 에 추가. GM(LLM)이 시나리오를 읽고 현재 장소를 판단해 `[장소: X]` 를 자동 출력.

**추가한 규칙**
```
[장소 태그 규칙]
장면의 장소가 새로 정해지거나 바뀌면, 응답 맨 끝에 [장소: X] 한 줄 출력.
X = 시나리오에 표기된 장소명 그대로(거실/화장실/현관/놀이공원/회전목마/관람차/귀신의 집 등).
임의 변형 금지(이미지 매핑 일관성), 장소 안 바뀐 턴은 생략 가능, 항상 맨 끝 한 줄.
```

**이유**: 시나리오가 플레이어 선택으로 분기하므로 경로를 미리 고정할 수 없음 →
GM이 런타임에 현재 장소를 태그로 반영하게 하면 분기와 무관하게 동작.
(이미지 없는 장소는 프론트에서 폴백 예정 — 다음 단계.)

---

## #9. 스탯 불러오기 (DB → UI) (`main.py`, `TRPG/src/App.jsx`)
**목표**: 스탯 저장(POST)은 이미 있었음. 빠져 있던 **불러오기**(캐릭터 선택 시 저장된 스탯을 폼에 복원)를 추가.

**백엔드** [main.py](main.py) — GET 엔드포인트 신설
```python
@app.get("/stats/{character_id}")
async def load_stats(character_id: int):
    doc = await collection2.find_one({"character_id": character_id}, {"_id": 0})
    if not doc:
        return {"character_id": character_id, "stat": None}   # 없으면 null
    return doc
```

**프론트** [TRPG/src/App.jsx](TRPG/src/App.jsx)
- 스탯 기본값을 `DEFAULT_STATS` 상수로 분리(로드 실패/미저장 시 폴백 재사용).
- `loadStatsFromDB(characterId)`: `GET /stats/{id}` 호출 → `setStats(data.stat ?? DEFAULT_STATS)`.
- `useEffect([selectedCharacterId])`: 캐릭터가 바뀔 때마다 해당 스탯을 자동 로드.

**검증**: 서버 기동 후 `GET /stats/1` → 저장된 스탯(STR:20...) 반환, `GET /stats/999` → `stat:null` 확인.

**이유**: 작업1(스탯 UI↔DB 연동)의 나머지 절반. 이제 저장↔불러오기 왕복 완성.

---

## #8. judge.py 크래시 방어 — `data`/`diceval` None 체크 (`judge.py`)
**파일**: [judge.py](services/judge.py)

**문제**: 두 곳에서 None 입력 시 모호한 `TypeError` 로 500 에러.
1. `data = collection2.find_one(...)` 가 캐릭터를 못 찾으면 `None` → 다음 줄 `data["stat"]` 에서 터짐.
   (`DiceMessage.senderId` 가 `Optional[int]=None` 이라 None 조회도 가능)
2. `int(request.diceval)` — `diceval` 이 `Optional[int]=None` 이라 None 이면 변환 실패.

**이후** (B안: 예외로 원인 명확화)
```python
if not data or "stat" not in data:
    raise ValueError(f"캐릭터(character_id={request.senderId})의 스탯을 찾을 수 없습니다")
...
if request.diceval is None:
    raise ValueError("주사위 값(diceval)이 없어 판정할 수 없습니다")
```
**이유**: "캐릭터 없음"을 `"실패"` 로 떨어뜨리면 진짜 판정 실패와 구분 불가 → 예외로 원인을 분명히 드러냄.

---

## #7. judge.py에 RAG 연결 — 하드코딩 룰 → 동적 검색 (`judge.py`)
**파일**: [judge.py](services/judge.py)

**이전**: `rule_text` 가 상황과 무관한 **고정 하드코딩 문자열**. 어떤 판정이든 같은 룰만 사용.

**이후**
```python
import asyncio
from Retrieval import search_with_references
...
if user_context:
    retrieved = await asyncio.to_thread(search_with_references, user_context, 5)
    rule_text = "\n\n".join(r["text"] for r in retrieved)
else:
    rule_text = ""
```
- 직전 GM 서사(`user_context`)를 쿼리로 룰북을 검색해 `rule_text` 를 **동적 생성**.
- 동기 함수(faiss/임베딩)를 `asyncio.to_thread` 로 감싸 async 이벤트 루프 블로킹 방지.
- 판정 원리(`주사위 <= 스탯`)는 프롬프트 본문(`보통 성공 조건은...`)에 이미 있어, 룰 텍스트가 비어도 판정은 동작.

**이유**: RAG의 원래 목표 = "현재 진행 중인 대화 상황에 맞는 룰을 룰북에서 끌어와 판정에 반영".

### 7-1. RAG 쿼리 정제 — 분위기 서사 → `기능` 기반 (검증 후 개선)
**문제**: 처음엔 쿼리로 `user_context`(GM 서사) 전체를 썼더니, 서사가 공포 분위기 묘사라 검색이 **판정 룰이 아니라 괴물/분위기 내용**을 가져옴.

**원인 분석(데이터로 확인)**
- 판정 종류 신호는 GM 메시지의 **`[판정 요청]` 블록** 안에 `기능: 관찰력(Spot Hidden)...` 형태로 명시돼 있음.
- 분위기 서사 전체로 검색하면 이 신호가 묻혀 노이즈만 나옴.

**개선**
```python
skill_match = re.search(r"기능:\s*([^\n(（]+)", user_context)
skill = skill_match.group(1).strip() if skill_match else ""
rag_query = f"{skill} 판정" if skill else user_context   # 기능 없으면 상황 전체로 폴백
```
- 쿼리를 `기능`("관찰력 판정")으로 좁힘 → **"관찰력 (25%) 비밀문이나 숨겨진 공간을 발견하고..."** 처럼 실제 기능 정의/판정 메커니즘이 검색됨.

**역할 정리**: RAG = "판정 종류가 정해졌을 때 그 판정을 *어떻게* 하는지" 룰을 가져오는 용도.
판정 *종류*("관찰 판정")는 scene_public 기반으로 GM이 `[판정 요청]`에 명시 → RAG가 그 메커니즘을 보강.

---

## #6. 정렬 안정화 — `role` 필터 + `_id` tie-break (`judge.py`, `prompt_service.py`)

**문제**: `created_at` 이 '분' 단위 문자열(`YYYY/MM/DD HH:MM`)이라, 1분에 메시지가 여러 개면 정렬 순서가 모호함.
실측: assistant 메시지 17개 중 **6개 시각에서 같은 분 충돌**(한 분에 assistant 2~3개)이 존재.
ping-pong + `role` 구분으로 "user/assistant 구분"은 됐지만, **같은 role 안에서의 순서는 깨지고 있었음** (크래시 없이 조용히 틀리는 silent bug).

### 6-1. judge.py — 직전 assistant 메시지 조회
**이전**
```python
collection.find({"room_id": request.room_id})
    .sort("created_at", -1).skip(1).limit(1)   # role 무관, '한 칸 건너뛰기'
```
**이후**
```python
collection.find({"room_id": request.room_id, "role": "assistant", "type": "talk"})
    .sort([("created_at", -1), ("_id", -1)]).limit(1)
```
- `role="assistant", type="talk"` 필터 → 주사위/유저 메시지를 검색 단계에서 제외(=skip 불필요).
- `_id`(ObjectId, 삽입순서 보장) 보조 정렬 → 같은 분 충돌 시 진짜 최신 확정.

### 6-2. prompt_service.py — 대화 히스토리 정렬
**이전**: `.sort("created_at", 1)`
**이후**: `.sort([("created_at", 1), ("_id", 1)])`  (정렬만 보강. `room_id:"3"` 하드코딩은 별도 사안으로 남겨둠)

**검증**: 새 judge 쿼리가 최신 GM 서사(11:47)를 정확히 집고, 11:46 같은 분 충돌에서 `_id`로 순서가 확정됨을 DB로 확인.

---

## #5. 목차(TOC) 청크 필터링 (`Retrieval.py`)
**파일**: [Retrieval.py](Retrieval.py)

**문제**: 문서 맨 앞 **목차 텍스트도 하나의 청크로 DB에 저장**되어 있는데, 이 청크 안에는 `제1장~제15장`이 전부 나열돼 있음. 그 결과:
1. 2차 검색(`제10장 ...`) 시 목차 청크가 유사도 높게 잡혀 **내용 없는 노이즈**가 결과에 섞임.
2. (잠재 위험) 목차 청크가 1차에 잡히면 안의 제1~15장이 전부 참조로 감지돼 **모든 장을 2차 검색하는 "장 폭발"** 발생.

**추가한 코드**
```python
def _is_toc_chunk(text: str) -> bool:
    # 한 청크 안에 '제N장'이 5개 이상이면 목차로 간주
    return len(_CHAPTER_REF.findall(text)) >= 5
```
적용 위치 2곳:
- `search()` 결과 루프: 목차 청크는 검색 결과에서 제외 (노이즈 제거)
- `search_with_references()` 참조 감지 루프: 목차 청크의 참조는 무시 (장 폭발 방지)

**이유 / 효과** (실측)
- 본문 청크는 참조가 보통 1~2개뿐인데 목차는 10개 이상 → 개수로 안정적으로 구분 가능.
- 적용 후 검색 결과의 목차 청크 수 **0개** 확인. 이전에 `[9]`로 나오던 *"목차 제1장 소개..."* 노이즈가 실제 제10장 본문으로 대체됨.

---

## #4. RAG 검색기 개선 + Multi-hop 참조 추적 (`Retrieval.py`)

### 4-1. 코사인 유사도 + 재사용 함수화
**파일**: [Retrieval.py](Retrieval.py)

**이전**
```python
index = faiss.IndexFlatL2(dim)        # L2(유클리드) 거리
# ... 1회용 스크립트, 매 실행마다 전체 인덱스 재구축
query_vector = embedding_model.embed_query(query_text)
D, I = index.search(query_vector_np, k=5)
```

**이후**
```python
faiss.normalize_L2(vectors)           # 벡터 정규화
index = faiss.IndexFlatIP(dim)        # 내적 = (정규화 후) 코사인 유사도
# search() / search_text() 함수로 분리, 인덱스는 1회 캐싱(지연 로딩)
```

**이유**
- OpenAI 임베딩(`text-embedding-3-large`)은 **코사인 유사도** 기준으로 학습됨. L2 거리로 검색하면 랭킹이 미묘하게 어긋남.
- `IndexFlatIP`(내적)만 쓰면 벡터 길이에 따라 점수가 왜곡되므로 `normalize_L2`로 정규화해야 진짜 코사인이 됨.
- 1회용 스크립트 → 함수로 만들어 `judge.py` 등에서 재사용 가능하게.

### 4-2. Multi-hop 참조 추적 (`search_with_references`)
**파일**: [Retrieval.py](Retrieval.py)

**문제**: 단순 벡터 검색은 "질문과 비슷한 청크"를 찾을 뿐 "답이 되는 청크"를 못 찾음.
예) `"운 수치는 어떻게 정해?"` → 1등 청크가 *"...운 사용법은 **제5장** 참고하세요"* 로 넘기는데, 정작 5장 본문은 top-5에 없음 (multi-hop 문제).

**추가한 로직**
1. 문서 맨 앞 **목차를 파싱** → `{장번호: 제목/키워드}` 매핑 (`_load_toc`)
2. 1차 검색 결과 본문에서 `제N장` 참조를 정규식으로 감지
3. 참조된 장의 목차 키워드로 **2차 검색** 후 병합

**이유**
- 룰북처럼 "○장 참고" 식 상호참조가 많은 문서는 한 번의 검색으로 답을 못 모음.
- 목차를 활용하면 청크마다 chapter를 일일이 태깅(본문 제목 vs 참조 구분이 까다로움)하지 않고도, **재적재 없이** 참조를 따라갈 수 있음.

---

## #3. RAG 적재 파이프라인 개선 (`chain.py`)
**파일**: [chain.py](chain.py)

**이전**
```python
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=300)
for doc in docs:
    vector = embeddings.embed_query(doc.page_content)   # 청크마다 1회씩 호출
collection.insert_many(data)                            # 기존 데이터 안 지움
```

**이후**
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""])
vectors = embeddings.embed_documents(texts)             # 배치 1회 호출
collection.delete_many({})                              # 적재 전 초기화
collection.insert_many(data)
```

**이유 / 효과** (실측: 219청크 → 165청크)
- **오버랩 300/500 (60%)**: 인접 청크가 60%씩 겹쳐 거의 같은 청크가 양산됨 → 검색 top-k가 중복으로 채워져 다른 관련 내용이 밀려남. → 100(약 12%)으로 정상화.
- **CharacterTextSplitter**: `\n\n`이 없는 구간을 통째로 묶어 **최대 5145자** 거대 청크 발생(지정 500 무시). → `RecursiveCharacterTextSplitter`로 **최대 799자**로 제대로 제한.
- **embed_query 반복 → embed_documents 배치**: API 호출 횟수 감소 → 빠르고 저렴.
- **delete_many 추가**: 재실행 시 청크가 통째로 중복 누적되던 문제 차단.

---

## #2. 빈 `frontend/` 폴더 제거
**이전**: 비어있는 `frontend/` 폴더 존재 (실제 프론트엔드는 `TRPG/`에 있음).
**이후**: `frontend/` 삭제.
**이유**: 빈 폴더가 "프론트엔드 위치"에 대한 혼동을 유발. 실제 UI는 `TRPG/`(React+Vite).

---

## #1. 하드코딩된 자격증명 제거 → `.env` 분리
**파일**: [main.py](main.py), [services/chat_openai.py](services/chat_openai.py), [database/database.py](database/database.py), [database/database_stat.py](database/database_stat.py), [services/rag.py](services/rag.py)

**이전**
```python
os.environ["OPENAI_API_KEY"] = "sk-proj-..."           # 소스에 그대로
uri = "mongodb+srv://land0207:비밀번호@cluster0..."     # 소스에 그대로
```

**이후**
```python
from dotenv import load_dotenv
load_dotenv()
uri = os.environ["MONGODB_URI"]   # .env 에서 로드
```
- 새 파일: `.env`(실제 값), `.env.example`(템플릿), `.gitignore`(.env 제외)

**이유**
- API 키 / DB 비밀번호가 소스코드에 노출 → Git에 올라가면 영구 유출.
- 5곳에 흩어진 자격증명을 `.env` 한 곳으로 모아 관리.

> ⚠️ **남은 조치(직접 해야 함)**: 이미 노출된 키 자체는 폐기/재발급 필요 (OpenAI 키 revoke, MongoDB 비밀번호 변경).
