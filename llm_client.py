import asyncio
import json
import base64
from io import BytesIO
from pyboy import PyBoy
from ollama import AsyncClient
import re

MODEL_NAME = "deepseek-r1:14b"
async def send_to_llm(screen_ascii_data ,game_state, image_data):
    """
    LLaVA 모델을 사용하여 게임 상태 및 화면 이미지를 LLM에 전송하고, 스트리밍으로 응답을 받아 실시간 출력하는 함수.

    Args:
        game_screen_ascii (str): game screen ascii data
        game_state (dict): 현재 게임 상태를 포함한 JSON 데이터.
        image_data (str): Base64 인코딩된 게임 화면 PNG.

    Returns:
        dict: 최종적으로 수신된 JSON 형식의 명령.
    """
    prompt = f"""
You are an AI controlling a Gameboy Pokémon Red game using a Game Boy controller.
Your ultimate objective is to defeat the Elite Four and view the ending credits.

Your task is to decide the next action based on the current game state and the provided game screen.

## Game State:
{json.dumps(game_state, indent=2)}

## Your Game Screen
When isTextBoxVisible is true, you can read the text information via the next table.
- **Note**: Any entry shown as 0x## (e.g., 0xAA) denotes a *background tile code*, not regular text.
- If the displayed text ends with a **"▼"** symbol, it indicates that pressing `"a"` will progress the dialogue.

{screen_ascii_data}

## Controls:
You must always select and press one of the following buttons:
- **"start"**: Opens the in-game menu.
- **"select"**: Used for special functions in some menus. Don't use this button because the button is not usable under any circumstances.
- **"a"**: Confirms selections, interacts with NPCs, or uses items.
- **"b"**: Cancels selections, closes menus.
- **"up"**: Moves the player or menu cursor upward.
- **"down"**: Moves the player or menu cursor downward.
- **"left"**: Moves the player or menu cursor to the left.
- **"right"**: Moves the player or menu cursor to the right.
### Additional Conditions:
- The **"start"** button **cannot** be used when `isTextMenuWindowVisible` is `true`.
- The **"select"** button **must never be used** under any circumstances.
- You can't move your player when isTextBoxVisible is True, but you CAN move menu cursor(▶).
## Output Restrictions:
- You **must always** return a `"press_button"` command.
- You **must not** return any other function.
- If no action is needed, choose a reasonable button press, such as `"b"` to cancel.
## Output Format:
- Return a JSON object **inside a triple backtick block (\`\`\`json\\n{{}}\`\`\`)** like this:
```json
{{
    "function": "press_button",
    "args": {{"button": "<one of the buttons listed above>"}}
}}
```
- The JSON **must always** contain a `"press_button"` command.
- After the JSON response, provide a **short explanation** (one or two sentences) of why the selected button is pressed.
    """

    client = AsyncClient()
    response_data = ""
    print(prompt)
    async for chunk in await client.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt, 'images': [image_data]}],
        stream=True,
    ):
        response_text = chunk.get("message", {}).get("content", "")
        print(response_text, end="", flush=True)  # 실시간 출력
        response_data += response_text

    # JSON 블록 추출 (```json ~~~ ``` 사이의 내용만 가져오기)
    match = re.search(r"```json*\n(.*?)\n```", response_data, re.DOTALL)
    
    if match:
        json_content = match.group(1)
        try:
            return json.loads(json_content)  # 추출된 JSON을 파싱
        except json.JSONDecodeError:
            print("\n[ERROR] Failed to parse extracted JSON block.")
    else:
        print("\n[ERROR] No valid JSON block found in response.")

    return {}

def capture_screen(pyboy):
    """
    PyBoy의 현재 화면을 PNG로 캡처하고, Base64로 인코딩하여 반환.

    Args:
        pyboy (PyBoy): PyBoy 인스턴스.

    Returns:
        str: Base64로 인코딩된 PNG 이미지.
    """
    screen = pyboy.screen.image  # PIL 이미지 객체로 캡처
    buffer = BytesIO()
    screen.save(buffer, format="PNG")  # PNG로 저장
    return base64.b64encode(buffer.getvalue()).decode()  # Base64로 인코딩

