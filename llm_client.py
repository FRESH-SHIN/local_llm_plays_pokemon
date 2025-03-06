import asyncio
import json
import base64
from io import BytesIO
from pyboy import PyBoy
from ollama import AsyncClient
import re

MODEL_NAME = "deepseek-r1:14b"
async def send_to_llm(screen_ascii_data ,game_state, image_data, note, current_step):
    """
    이미지 전송을 지원하는 모델일 경우 화면 이미지를 추가하여 게임 상태를 LLM에 전송하고, 스트리밍으로 응답을 받아 실시간 출력하는 함수.

    Args:
        game_screen_ascii (str): game screen ascii data
        game_state (dict): 현재 게임 상태를 포함한 JSON 데이터.
        image_data (str): Base64 인코딩된 게임 화면 PNG.
        note(array): 지금까지의 메모
        current_step: 현재 스텝
    Returns:
        dict: 최종적으로 수신된 response text
    """
    prompt = f"""
You are an AI controlling a Gameboy Pokémon Red game using a Game Boy controller.
Your ultimate objective is to defeat the Elite Four and view the ending credits.

## Command Usage
You can remember new information using the `/take_note {{knowledge}}` command.  
- Example: `/take_note Pikachu evolves with a Thunder Stone`
- You **must** summarize the current situation using /take_note everytime. Additionally, you should check for any differences from the previous step as you progress.

You can simulate button presses using the command `/joypad {{button}}`.
{{button}} could be 'a', 'b', 'start', 'select', 'right', 'left', 'down' or 'up'.
- Example: `/joypad a`

Your task is to decide the next action based on the current game state and the provided game screen.

##Current Step
{current_step}
## Your Note
{note}

## Game State:
{json.dumps(game_state, indent=2)}


## Exploration Objectives:
- Explore unknown regions and reveal new areas.
- Interact with NPCs to collect hints or obtain important items.
- Catch new Pokémon species and expand your Pokédex.
- Prioritize visiting Pokémon Centers when Pokémon health is low.

## Your Game Screen
When isTextBoxVisible is true, you can read the text information via the next table.
- **Note**: Any entry shown as 0x## (e.g., 0xAA) denotes a *background tile code*, not regular text.
- If the displayed text ends with a **"▼"** symbol, it indicates that pressing `"a"` will progress the dialogue.
- The symbols `○` represent NPCs or sprites. When encountering these, you should stand in front of the sprite and press `"a"` to obtain information.
- The symbol ◉ represents the player.
{screen_ascii_data}

## Decision Criteria (Priority Order):
1. Engage storyline-related NPCs or special events.
2. Explore unexplored or promising map regions.
3. Search for hidden items or Pokémon encounters.
4. Maintain Pokémon's health by visiting Pokémon Centers.

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
- When `overworld` is `true`, your movement should be based on the `passable_tiles` list:  
  `{game_state['passable_tiles']}`  
  This list determines which tiles you can walk on.

## Output Format
Always respond using one of the following formats:
```
/joypad {{button1}}
```
```
/take_note {{your note}}
```
- You **must** summarize the current situation using /take_note everytime(a sentense).

- Provide a short explanation (1-2 sentences) of the chosen buttons after the command.
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

    return response_data

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

