from pathlib import Path

import freetype
import numpy as np
from tqdm import tqdm

from scripts.rasterize import rasterize
from scripts.utils import iter_glyph, load_glyph

root_dir = Path(__file__).parent

from argparse import ArgumentParser

from PIL import Image


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
        for glyph, char in iter_glyph(font_path):
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
