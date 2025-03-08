from symbol_parser import parse_sym_file

from consts import *

class MemoryReader:
    def __init__(self, pyboy, sym_path="data/pokered.sym"):
        self.pyboy = pyboy
        self.symbol_map = parse_sym_file(sym_path)

        # charmap 기반 문자 매핑
        self.tile_to_char = {
            0x77: "-", 0x76: "_", 
            # 0x79: "┌", 0x7A: "─",0x7B: "┐", 0x7C: "│",    0x7D: "└",   0x7E: "┘",  0x7F: " ",
             0x79: "", 0x7A: "",0x7B: "", 0x7C: "",    0x7D: "",   0x7E: "",  0x7F: " ",
            0x80: "A", 0x81: "B", 0x82: "C", 0x83: "D", 0x84: "E", 0x85: "F", 0x86: "G",
            0x87: "H", 0x88: "I", 0x89: "J", 0x8A: "K", 0x8B: "L", 0x8C: "M", 0x8D: "N",
            0x8E: "O", 0x8F: "P", 0x90: "Q", 0x91: "R", 0x92: "S", 0x93: "T", 0x94: "U",
            0x95: "V", 0x96: "W", 0x97: "X", 0x98: "Y", 0x99: "Z",

            0x9A: "(", 0x9B: ")", 0x9C: ":", 0x9D: ";", 0x9E: "[", 0x9F: "]",

            0xA0: "a", 0xA1: "b", 0xA2: "c", 0xA3: "d", 0xA4: "e", 0xA5: "f", 0xA6: "g",
            0xA7: "h", 0xA8: "i", 0xA9: "j", 0xAA: "k", 0xAB: "l", 0xAC: "m", 0xAD: "n",
            0xAE: "o", 0xAF: "p", 0xB0: "q", 0xB1: "r", 0xB2: "s", 0xB3: "t", 0xB4: "u",
            0xB5: "v", 0xB6: "w", 0xB7: "x", 0xB8: "y", 0xB9: "z",

            0xBA: "é", 0xBB: "'d", 0xBC: "'l", 0xBD: "'s", 0xBE: "'t", 0xBF: "'v",

            0xE0: "'", 0xE1: "<PK>", 0xE2: "<MN>", 0xE3: "-",
            0xE4: "'r", 0xE5: "'m", 0xE6: "?", 0xE7: "!", 0xE8: ".",

            0xE9: "ァ", 0xEA: "ゥ", 0xEB: "ェ",
            0xEC: "▷", 0xED: "▶", 0xEE: "▼", 0xEF: "♂", 0xF0: "ED", 0xF1: "×",
            0xF2: "<DOT>", 0xF3: "/", 0xF4: ",", 0xF5: "♀",

            0xF6: "0", 0xF7: "1", 0xF8: "2", 0xF9: "3", 0xFA: "4",
            0xFB: "5", 0xFC: "6", 0xFD: "7", 0xFE: "8", 0xFF: "9"
        }


    def read_memory_word(self, symbol):
        """ 메모리에서 2바이트(워드) 값을 읽어 정수로 반환 """
        if symbol not in self.symbol_map:
            raise ValueError(f"Unknown symbol: {symbol}")

        bank, address = self.symbol_map[symbol]
        low_byte = self.pyboy.memory[address]        # LSB (하위 바이트)
        high_byte = self.pyboy.memory[address + 1]  # MSB (상위 바이트)
        return (high_byte << 8) | low_byte  # 리틀 엔디언 변환
    
    def process_collision_data(self, raw_data):
        """
        raw_data로부터 각 타일의 충돌 여부를 판별하는 딕셔너리를 생성합니다.
        여기서는 예시로 타일 ID가 0이 아니면 충돌하는(벽) 것으로 가정합니다.
        """
        collision_dict = {}
        for tile_id in raw_data:
            collision_dict[tile_id] = (tile_id != 0)
        return collision_dict

    def extract_wall_coords(self, tile_map, collision_data, map_width, map_height):
        """
        tile_map: 2차원 배열 형태의 타일 ID 데이터 (행: Y, 열: X)
        collision_data: 각 타일 ID의 충돌 여부를 담은 딕셔너리
        map_width, map_height: 타일 맵의 가로, 세로 크기

        충돌(벽) 타일의 좌표 (x, y)를 리스트로 반환합니다.
        """
        wall_coords = []
        for y in range(map_height):
            for x in range(map_width):
                tile_id = tile_map[y][x]
                if collision_data.get(tile_id, False):
                    wall_coords.append((x, y))
        return wall_coords

    def extract_interactive_objects(self, sprites, sign_coords, hidden_objects):
        """
        sprites: 스프라이트 데이터. 예를 들어, 각 스프라이트가 {'x': 좌표, 'y': 좌표, 'interactive': bool} 형태라고 가정합니다.
        sign_coords: 사인(표지판) 좌표 데이터. [y0, x0, y1, x1, ...] 형식으로 저장되어 있다고 가정.
        hidden_objects: 숨겨진 오브젝트 좌표 리스트. [{'x': 값, 'y': 값}, ...] 형태.

        상호작용 가능한 오브젝트들의 좌표 (x, y)를 리스트로 반환합니다.
        """
        interactive = []
        
        # 스프라이트 데이터에서 상호작용 가능한 오브젝트 추출
        for sprite in sprites:
            if sprite.get('interactive', False):
                interactive.append((sprite['x'], sprite['y']))
        
        # 사인 데이터 처리: 짝수 인덱스가 Y, 홀수 인덱스가 X라고 가정
        for i in range(0, len(sign_coords), 2):
            y = sign_coords[i]
            x = sign_coords[i+1]
            interactive.append((x, y))
        
        # 숨겨진 오브젝트 좌표 추가
        for obj in hidden_objects:
            interactive.append((obj['x'], obj['y']))
        
        return interactive

    def read_window_text(self, width=18, height=20):
        """VRAM에서 윈도우 타일을 읽어 텍스트로 변환"""
        start_addr = 0x9C00
        text_lines = []

        for row in range(height):
            text_line = ""
            for col in range(width):
                tile_id = self.pyboy.memory[start_addr + row * 32 + col]
                text_line += self.tile_to_char.get(tile_id, "")
            text_lines.append(text_line.strip())

        return "\n".join(text_lines).strip()

    def parse_sprite_entries(self, sprite_bytes):
        """
        sprite_bytes: 원시 sprite 데이터(바이트 리스트). 각 엔트리는 4바이트 [y, tile, attr, x]로 구성.
        각 엔트리를 파싱하여 dict 객체 리스트를 반환합니다.
        """
        sprite_entries = []
        entry_size = 4
        for i in range(0, len(sprite_bytes), entry_size):
            if i + entry_size > len(sprite_bytes):
                break
            # 엔트리 파싱
            y_raw, tile, attr, x_raw = sprite_bytes[i:i+entry_size]
            # 사용되지 않은 엔트리 (x나 y가 0이면) 건너뜀
            if y_raw == 0 or x_raw == 0:
                continue
            # Game Boy OAM 좌표 보정 (x: x_raw - 8, y: y_raw - 16)
            x_pixel = x_raw - 8
            y_pixel = y_raw - 16
            # 타일 단위 좌표 (8x8 타일)
            tile_x = x_pixel // 8
            tile_y = y_pixel // 8
            # 간단하게 tile 값이 0이 아니면 인터랙티브하다고 가정
            interactive = (tile != 0)
            sprite_entries.append({
                "x": tile_x,
                "y": tile_y,
                "tile": tile,
                "attr": attr,
                "interactive": interactive
            })
        return sprite_entries


    def get_oam_positions(self, num_entries=40, screen_width=20, screen_height=18):
        """
        num_entries: OAM 버퍼에 포함된 스프라이트 수 (예: 40)
        screen_width, screen_height: 화면의 타일 단위 크기 (기본 20×18)
        
        wShadowOAM 심볼을 읽어 각 스프라이트의 픽셀 좌표를 타일 좌표로 변환합니다.
        사용되지 않은 항목(x 또는 y가 0인 경우)은 걸러내며,
        타일 번호의 하위 4비트를 이용해 NPC의 바라보는 방향을 결정합니다.
        """
        # Game Boy의 OAM은 총 40개의 스프라이트, 각 4바이트 (40*4=160바이트)
        oam_bytes = self.read_memory_bytes("wOAMBuffer", 160)
        oam_list = []
        # 방향 매핑 (타일 번호의 하위 4비트 값 기준)
        direction_map = {0x00: "Down", 0x04: "Up", 0x08: "Left", 0x0C: "Right"}
        direction_icon_map = {"Down": "↓", "Up": "↑", "Left": "←", "Right": "→", "Unknown": "?"}
        
        for i in range(num_entries):
            base = i * 4
            y_raw = oam_bytes[base]
            x_raw = oam_bytes[base + 1]
            tile = oam_bytes[base + 2]
            attr = oam_bytes[base + 3]  # 필요 시 사용 가능
            # 사용되지 않은 스프라이트는 X 또는 Y가 0인 경우가 많음
            if y_raw == 0 or x_raw == 0:
                continue
            
            # Game Boy의 OAM 좌표는 오프셋이 있으므로 보정:
            # X: 실제 좌표 = x_raw - 8, Y: y_raw - 16
            x_pixel = x_raw - 8
            y_pixel = y_raw - 16
            
            # 8x8 타일로 변환 (정수 나눗셈)
            tile_x = x_pixel // 8
            tile_y = y_pixel // 8
            
            # 화면 범위 내에 있는지 확인 (20x18)
            if tile_x < 0 or tile_x >= screen_width or tile_y < 0 or tile_y >= screen_height:
                continue
            
            # 타일 번호의 하위 4비트 중 0x0C 마스크를 사용해 방향 결정
            facing_code = tile & 0x0C
            direction = direction_map.get(facing_code, "Unknown")
            icon = '⚪︎'
            if i <= 3: # player
                icon = '◉'
            oam_list.append({
                "x": tile_x,
                "y": tile_y,
                "direction": direction,
                "icon": icon
            })
            
        return oam_list

    def generate_overworld_markdown_from_memory(self, width=20, height=18):
        """
        width, height: 출력할 표의 타일 크기 (기본 20×18)
        
        MemoryReader의 read_memory_bytes()를 사용하여 'wTileMap' 심볼로부터 BGMAP 데이터를 읽어옵니다.
        그리고 get_oam_positions()를 통해 메모리에서 OAM 위치와 방향(플레이어는 ◉, 그 외는 ⚪︎)을 읽어옵니다.
        
        포켓몬스터는 문자 타일 외에도 스프라이트(플레이어 및 NPC)가 2×2 타일 단위로 사용되므로,
        2×2 블록으로 묶어서 표를 생성하며, 해당 블록 내에 OAM 스프라이트가 있으면 그 아이콘으로 표시합니다.
        """
        # BGMAP 데이터: 'wTileMap' 심볼로부터 width*height 바이트 읽기
        bgmap = self.read_memory_bytes("wTileMap", width * height)
        tile_to_char = self.tile_to_char

        # bgmap의 단일 타일을 문자로 변환하는 헬퍼 함수
        def get_tile_char(x, y):
            index = y * width + x
            tile_id = bgmap[index] if index < len(bgmap) else 0
            return tile_to_char.get(tile_id, f'{tile_id:#x}')

        # OAM 데이터를 가져옴 (플레이어와 NPC 스프라이트)
        oam_positions = self.get_oam_positions(num_entries=40, screen_width=width, screen_height=height)
        # 각 스프라이트는 2×2 블록을 차지하므로, 스프라이트의 좌상단 좌표를 기준으로 블록 좌표로 매핑
        oam_block_dict = {}
        for oam in oam_positions:
            # sprite가 차지하는 블록의 좌표는 (x//2, y//2)
            block_x = oam["x"] // 2
            block_y = (oam["y"] + 1) // 2
            # 이미 해당 블록에 다른 OAM이 등록되어 있으면 플레이어(◉)가 우선하도록 처리
            if (block_x, block_y) in oam_block_dict:
                if oam["icon"] == '◉':
                    oam_block_dict[(block_x, block_y)] = oam
            else:
                oam_block_dict[(block_x, block_y)] = oam

        # 2×2 블록으로 묶을 때의 새 행, 열 수 계산 (예: width=20 -> new_width=10)
        new_width = (width + 1) // 2
        new_height = (height + 1) // 2

        table_rows = []
        for block_row in range(new_height):
            row_cells = []
            for block_col in range(new_width):
                # 해당 블록의 좌표
                if (block_col, block_row) in oam_block_dict:
                    # OAM이 있는 블록이면 해당 아이콘을 사용 (플레이어는 ◉, 그 외는 ⚪︎)
                    cell = oam_block_dict[(block_col, block_row)]["icon"]
                else:
                    # 없으면 2×2 블록의 각 타일을 연결하여 문자열 생성
                    x = block_col * 2
                    y = block_row * 2
                    tl = get_tile_char(x, y)
                    tr = get_tile_char(x + 1, y) if x + 1 < width else ""
                    bl = get_tile_char(x, y + 1) if y + 1 < height else ""
                    br = get_tile_char(x + 1, y + 1) if (x + 1 < width and y + 1 < height) else ""
                    print(tl)
                    if tl.startswith("0x"):
                        cell = tl
                    elif tr.startswith("0x"):
                        cell = tr
                    elif bl.startswith("0x"):
                        cell = bl
                    elif br.startswith("0x"):
                        cell = br
                    else:
                        cell = tl + tr + bl + br
                row_cells.append(cell)
            table_rows.append("| " + " | ".join(row_cells) + " |")
        
        # 옵션: 표 상단에 블록 단위 열 번호 헤더와 구분선 추가
        header = "| " + " | ".join(str(i) for i in range(new_width)) + " |"
        separator = "| " + " | ".join(["---"] * new_width) + " |"
        md_table = header + "\n" + separator + "\n" + "\n".join(table_rows)
        return md_table

    def read_memory(self, symbol):
        """ 심볼 이름을 입력받아 해당 메모리 주소의 값을 읽음 (뱅크 포함) """
        if symbol not in self.symbol_map:
            raise ValueError(f"Unknown symbol: {symbol}")

        bank, address = self.symbol_map[symbol]
        return self.pyboy.memory[address] if bank == 0 else self.pyboy.memory[bank, address]

    def get_passable_tiles(self):
        """
        wTilesetCollisionPtr은 통과 가능한 타일 ID 리스트의 포인터입니다.
        $FF가 나올 때까지 각 바이트를 읽어, 통과 가능한 타일 ID들을 리스트로 반환합니다.
        """
        collision_ptr = self.read_memory_word("wTilesetCollisionPtr")  # 포인터 주소 획득
        passable_tiles = []
        offset = 0
        while True:
            tile = self.read_memory_bytes(collision_ptr + offset, 1)[0]
            if tile == 0xFF:
                break
            passable_tiles.append(tile)
            offset += 1
        return passable_tiles
    def read_memory_bytes(self, symbol_or_addr, length):
        """
        특정 심볼 또는 직접적인 메모리 주소에서 지정한 길이만큼 바이트를 읽어옴.

        symbol_or_addr: 심볼 이름(str) 또는 직접적인 메모리 주소(int).
        length: 읽을 바이트 수.
        """
        if isinstance(symbol_or_addr, str):
            # 심볼 이름이 주어진 경우 기존 방식대로 처리
            if symbol_or_addr not in self.symbol_map:
                raise ValueError(f"Unknown symbol: {symbol_or_addr}")

            bank, address = self.symbol_map[symbol_or_addr]
        elif isinstance(symbol_or_addr, int):
            # 직접적인 주소(포인터)가 주어진 경우
            bank, address = 0, symbol_or_addr  # ROM/RAM에 따라 bank 처리는 다르게 해야 함
        else:
            raise TypeError("symbol_or_addr must be a string (symbol) or an int (memory address)")

        # 메모리에서 length 바이트 읽기
        return [self.pyboy.memory[address + i] for i in range(length)]
    def read_bcd_money(self):
        """ BCD 형식으로 저장된 돈을 정수로 변환 """
        money_bytes = self.read_memory_bytes("wPlayerMoney", 3)
        return (money_bytes[0] & 0xF) + ((money_bytes[0] >> 4) * 10) + \
               ((money_bytes[1] & 0xF) * 100) + ((money_bytes[1] >> 4) * 1000) + \
               ((money_bytes[2] & 0xF) * 10000) + ((money_bytes[2] >> 4) * 100000)
    def get_game_state(self):
        """현재 게임 상태를 JSON 형태로 반환 (모든 ID를 문자열로 변환)"""
        # 예를 들어, 맵 크기를 20x18 타일로 가정합니다.
        map_width = 20
        map_height = 18

        # 타일맵 데이터를 width * height 바이트만큼 읽어와서 2차원 배열로 변환
        tile_map_bytes = self.read_memory_bytes("wCurrentTileBlockMapViewPointer", map_width * map_height)
        tile_map = [tile_map_bytes[i * map_width:(i + 1) * map_width] for i in range(map_height)]
        
        # 기존의 충돌 데이터 처리 대신 통과 가능한 타일 리스트를 가져옴
        passable_tiles = self.get_passable_tiles()
        # 상호작용 가능한 오브젝트 데이터 읽기
        # 먼저 sprite 데이터(예: 40바이트)를 읽고 파싱합니다.
        raw_sprites = self.read_memory_bytes("wMapSpriteData", 40)  # 예시: 40바이트의 sprite 데이터
        sprites = self.parse_sprite_entries(raw_sprites)
        
        sign_coords = self.read_memory_bytes("wSignCoords", 32)  # 예시: 16쌍, 32바이트
        hidden_x = self.read_memory_bytes("wHiddenObjectX", 10)  # 예시: 10개의 x 좌표
        hidden_y = self.read_memory_bytes("wHiddenObjectY", 10)  # 예시: 10개의 y 좌표
        hidden_objects = [{'x': x, 'y': y} for x, y in zip(hidden_x, hidden_y)]
        
        interactive_objects = self.extract_interactive_objects(sprites, sign_coords, hidden_objects)
        
        facing_direction_map = {0x00: "Down", 0x04: "Up", 0x08: "Left", 0x0C: "Right"}

        # 인벤토리 아이템 변환
        inventory_items = self.read_memory_bytes("wBagItems", 20)
        parsed_items = []
        for i in range(0, len(inventory_items), 2):  # 아이템 ID + 개수
            item_id = inventory_items[i]
            item_name = ITEM_ID_TO_NAME.get(item_id, f"UNKNOWN_ITEM_{item_id}")
            item_count = inventory_items[i + 1]
            parsed_items.append({"name": item_name, "count": item_count})

        # 포켓몬 파티 변환
        party_pokemon = []
        party_count = self.read_memory("wPartyCount")
        for i in range(1, party_count + 1):
            species_id = self.read_memory(f"wPartyMon{i}")
            party_pokemon.append({
                "species": POKEMON_ID_TO_NAME.get(species_id, f"UNKNOWN_POKEMON_{species_id}"),
                "level": self.read_memory(f"wPartyMon{i}Level"),
                "hp": self.read_memory_word(f"wPartyMon{i}HP"),
                "max_hp": self.read_memory_word(f"wPartyMon{i}MaxHP"),
                "status": self.read_memory(f"wPartyMon{i}Status"),
            })

        # 적 포켓몬 변환
        enemy_pokemon = None
        if self.read_memory("wIsInBattle") > 0:
            enemy_species_id = self.read_memory("wEnemyMonSpecies")
            enemy_pokemon = {
                "species": POKEMON_ID_TO_NAME.get(enemy_species_id, f"UNKNOWN_POKEMON_{enemy_species_id}"),
                "level": self.read_memory("wEnemyMonLevel"),
                "hp": self.read_memory_word("wEnemyMonHP"),
                "max_hp": self.read_memory_word("wEnemyMonMaxHP"),
                "status": self.read_memory("wEnemyMonStatus"),
            }

        return {
            "current_mode": {
                "overworld": (self.read_memory("wIsInBattle") == 0) and (self.read_memory("hWY") == 0x90),
                "battle": self.read_memory("wIsInBattle") > 0,
                "isTextBoxVisible": self.read_memory("hWY") != 0x90
            },
            "overworld_state": {
                "position": {
                    "x": self.read_memory("wXCoord"),
                    "y": self.read_memory("wYCoord")
                },
                "facing_direction": facing_direction_map.get(self.read_memory("wTrainerFacingDirection"), "Unknown"),
                "current_map": MAP_ID_TO_NAME.get(self.read_memory("wCurMap"), f"UNKNOWN_MAP_{self.read_memory('wCurMap')}")
            },
            "trainer_state": {
                "money": self.read_bcd_money(),
                "play_time": {
                    "hours": self.read_memory("wPlayTimeHours"),
                    "minutes": self.read_memory("wPlayTimeMinutes"),
                    "seconds": self.read_memory("wPlayTimeSeconds")
                },
                "badges": bin(self.read_memory("wObtainedBadges")).count("1")  # 1의 개수만큼 배지 개수
            },
            "passable_tiles": [f'{i:#x}' for i in passable_tiles],
            #"interactive_objects": interactive_objects
            # "inventory": {
            #     "items": parsed_items
            # },
            # "party": party_pokemon,
            # "enemy_pokemon": enemy_pokemon,
            # "window_text": self.read_window_text()
        }
