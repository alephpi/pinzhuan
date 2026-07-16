from pathlib import Path

import freetype
import numpy as np
from tqdm import tqdm

from scripts.rasterize import rasterize

root_dir = Path(__file__).parent

from argparse import ArgumentParser

from PIL import Image

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

def load_glyph(face: freetype.Face, source: str):
    try:
        face.load_char(source, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        bmp = face.glyph.bitmap
        if bmp.buffer is None or bmp.rows == 0 or bmp.width == 0:
            return None
        glyph = np.array(bmp.buffer).reshape(bmp.rows, bmp.width) > 0
        return glyph
        
    except Exception as e:
        print(f"'{e}'字不存在，跳过\n")
        return None

def rasterize_font(font, char, plot):
    rasterized_glyphs = {}
    font_path = root_dir / font  # 替换为你的字体路径
    face = freetype.Face(str(font_path))
    face.set_pixel_sizes(0, face.units_per_EM)
    if char:
        chars = list(char)
        for char in chars:
            glyph = load_glyph(face, char)
            if glyph is not None:
                rasterized_glyph = rasterize(glyph, plot=plot, plot_save_dir=root_dir/"plots"/char)
                rasterized_glyphs[char] = rasterized_glyph
    else:
        # rasterize all chars in the font
        for ranges in CJK_RANGES:
            for code in tqdm(range(ranges[0], ranges[1]+1), total=ranges[1]-ranges[0]+1):
                char = chr(code)
                glyph = load_glyph(face, char)
                if glyph is not None:
                    rasterized_glyph = rasterize(glyph, plot=False)
                    rasterized_glyphs[char] = rasterized_glyph

    return rasterized_glyphs

def save(rasterized_glyphs, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for char, glyph in rasterized_glyphs.items():
        # 将字符编码为 Unicode 编码点
        # img = Image.fromarray(glyph.astype(np.bool_), mode="1")
        arr = glyph.astype(np.uint8) * 255
        img= Image.fromarray(arr, mode="L")
        img.save(output_dir / f"{char}.png")

if __name__ == "__main__":
    parser = ArgumentParser(description="")
    parser.add_argument("--font", type=str, default="./fonts/字悦九叠印篆.ttf", help="字体文件路径")
    parser.add_argument("--char", type=str, default='好爽渊', help="要渲染的字符")
    parser.add_argument("--out", type=str, default="./imgs", help="字体文件路径")
    parser.add_argument("--plot", action="store_true", help="是否绘制图像")

    args = parser.parse_args()
    rasterized_glyphs = rasterize_font(root_dir/args.font, args.char, args.plot)
    save(rasterized_glyphs, root_dir/args.out)
