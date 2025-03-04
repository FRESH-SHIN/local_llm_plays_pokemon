import asyncio
from pyboy import PyBoy
from memory_reader import MemoryReader
from llm_client import send_to_llm, capture_screen  # LLM과 이미지 캡처 함수 가져오기
from PIL import Image

async def llm_worker(game_state_queue, command_queue, is_working, pyboy):
    """
    게임 상태를 큐에서 받아 LLM에 요청하고, 응답을 명령 큐에 추가하는 비동기 작업.
    """
    while True:
        game_state, game_screen_ascii = await game_state_queue.get()  # 게임 상태 가져오기
        is_working.set()  # LLM 작업 시작 표시

        image_data = capture_screen(pyboy)  # 게임 화면 캡처 및 Base64 인코딩
        command = await send_to_llm(game_screen_ascii, game_state, image_data)  # LLM 호출

        is_working.clear()  # LLM 작업 종료 표시

        if command and "function" in command and command["function"] == "press_button":
            button = command["args"].get("button", "")
            if button in ["start", "select", "a", "b", "up", "down", "left", "right"]:
                await command_queue.put(button)  # 버튼 입력을 큐에 추가
            else:
                print(f"[ERROR] Invalid button received: {button}")

async def game_loop(pyboy, memory_reader, game_state_queue, command_queue, is_working):
    """
    게임 실행 루프: LLM이 응답할 때까지는 계속 게임을 진행하면서 입력을 대기.
    """
    tick = 0
    while pyboy.tick():
        # LLM이 실행 중이지 않을 때만 새로운 게임 상태를 전송
        if game_state_queue.empty() and not is_working.is_set():
            #print(f"LLM Working: {is_working.is_set()}")  # LLM이 실행 중인지 확인
            tick += 1
            if tick > 60 * 5:  # 5초마다 LLM에 새로운 상태 전송
                tick = 0
                game_state = memory_reader.get_game_state()
                game_screen_ascii = memory_reader.generate_overworld_markdown_from_memory()
                await game_state_queue.put((game_state, game_screen_ascii))

        # LLM이 보낸 명령을 적용
        if not command_queue.empty():
            button = await command_queue.get()
            print(f"Pressing button: {button}")
            pyboy.button(button, 3)

        await asyncio.sleep(1/60)  # 게임 루프가 너무 빠르게 실행되지 않도록 조절

async def main():
    rom_path = "data/pokered.gb"
    pyboy = PyBoy(rom_path, window="SDL2")
    pyboy.set_emulation_speed(0)  # 실시간 실행

    memory_reader = MemoryReader(pyboy)

    # LLM과 PyBoy 간 데이터 교환을 위한 큐 생성
    game_state_queue = asyncio.Queue()  # LLM에 보낼 게임 상태 저장
    command_queue = asyncio.Queue()  # LLM의 응답을 저장

    # LLM 작업 상태를 관리하는 Event 객체 생성
    is_working = asyncio.Event()

    # LLM 작업을 백그라운드에서 실행 (종료될 필요 없음)
    asyncio.create_task(llm_worker(game_state_queue, command_queue, is_working, pyboy))

    # 게임 루프 실행
    await game_loop(pyboy, memory_reader, game_state_queue, command_queue, is_working)

    pyboy.stop()

if __name__ == "__main__":
    asyncio.run(main())
