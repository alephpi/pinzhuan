import freetype
import numpy as np

CJK_RANGES = [
    (0x4E00, 0x9FFF),   # CJK统一汉字
    (0x3400, 0x4DBF),   # CJK扩展A
    (0x20000, 0x2A6DF), # CJK扩展B
    (0x2A700, 0x2B73F), # CJK扩展C
    (0x2B740, 0x2B81F), # CJK扩展D
    (0x2B820, 0x2CEAF), # CJK扩展E
    (0x2CEB0, 0x2EBEF), # CJK扩展F
    (0x30000, 0x3134F), # CJK扩展G
    (0x31350, 0x323AF), # CJK扩展H
    (0x2F800, 0x2FA1F), # CJK兼容汉字
    (0xFA70, 0xFAD9),   # CJK兼容汉字
    (0xF900, 0xFAFF),   # CJK兼容汉字
]

def load_glyph(face: freetype.Face, char: str):
    try:
        face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        bmp = face.glyph.bitmap
        if bmp.buffer is None or bmp.rows == 0 or bmp.width == 0:
            return None
        glyph = np.array(bmp.buffer).reshape(bmp.rows, bmp.width) > 0
        return glyph
        
    except Exception as e:
        print(f"'{e}'字不存在，跳过\n")
        return None

def iter_glyph():
    for ranges in CJK_RANGES:
        for code in range(ranges[0], ranges[1]+1):
            # char = chr(code)
            yield code