def parse_sym_file(sym_path: str) -> dict:
    """
    pokered.sym 파일을 파싱하여 {심볼 이름: (뱅크, 주소)} 형태의 딕셔너리를 반환합니다.
    
    변환 결과 예시:
    {
        "sBox8": (0x03, 0xA462),
        "sBox9": (0x03, 0xA8C4),
        "wSoundID": (0x00, 0xC001)
    }
    """
    symbol_map = {}
    with open(sym_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) != 2:
                continue  # 예기치 않은 형식 무시

            address_str, symbol_name = parts
            bank, address = address_str.split(":")  # '03:a462' → ['03', 'a462']

            # 16진수 변환
            bank = int(bank, 16)
            address = int(address, 16)

            symbol_map[symbol_name] = (bank, address)

    return symbol_map
