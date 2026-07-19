from pathlib import Path

import cv2
import freetype
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, box
from tqdm import tqdm
from utils import iter_glyph


def draw(points, contours, color=None, label_points=False, figure=None):
    if figure is None:
        fig, ax = plt.subplots(figsize=(8, 8))
    else:
        fig, ax = figure

    start = 0

    for end in contours:
        contour = points[start : end + 1]

        x = [p[0] for p in contour]
        y = [p[1] for p in contour]

        # 闭合
        x.append(contour[0][0])
        y.append(contour[0][1])

        ax.plot(x, y, "-", color=color)
        ax.scatter(x[:-1], y[:-1], s=15, color=color)

        # 标注点编号（可选）
        if label_points:
            for idx, p in enumerate(contour, start):
                ax.text(p[0], p[1], str(idx), fontsize=8)

        start = end + 1

    ax.set_aspect("equal")
    ax.invert_yaxis()
    return fig, ax

def compute_edges(points, contours):
    edges = {}

    start = 0

    for end in contours:
        # 当前轮廓的所有点索引
        indices = list(range(start, end + 1))

        # 相邻点
        for i in range(len(indices)):
            idx1 = indices[i]
            idx2 = indices[(i + 1) % len(indices)]  # 最后一个自动连回第一个

            x1, y1 = points[idx1]
            x2, y2 = points[idx2]

            edges[(idx1, idx2)] = ((x2 - x1), (y2 - y1))

        start = end + 1
    return edges

def smod(x, n):
    return ((x + n / 2) % n) - n / 2

def sdivide(x, n):
    k = round(x / n)
    return k * n

def compute_gcd_stage1(edges):
    ds = []
    for dx, dy in edges.values():
        ds.extend([dx, dy])
    ds = np.asarray(ds)
    ds = np.abs(ds)
    v_s, n_s = np.unique(ds[ds != 0], return_counts=True)
    gcd_candidate = v_s[n_s.argmax()]
    return gcd_candidate, v_s, n_s

def compute_gcd_stage2(gcd_candidate, v_s, n_s, search_range=5):
    gcd_min = max(1, gcd_candidate - search_range)
    gcds = np.arange(gcd_min, gcd_candidate + search_range + 1)
    loss = np.zeros_like(gcds)
    for i, d in enumerate(gcds):
        loss[i] = np.sum(np.abs(smod(v_s, d)) * n_s)
    gcd = gcds[loss.argmin()].item()
    return gcd, loss

def calibrate(points, edges, gcd):
    """
    将点坐标和边长校准到公度量的整数倍，即以公度值gcd为步长的网格上
    """
    calibrated_edges = {}
    for pair, edge in edges.items():
        dx, dy = edge
        calibrated_edges[pair] = (sdivide(dx, gcd), sdivide(dy, gcd))

    # coordinate calibration
    # calibrate point 0, get the offset
    x, y = points[0]
    x_ = sdivide(x, gcd)
    y_ = sdivide(y, gcd)
    offset = (x - x_, y - y_)
    calibrated_points = [(x_, y_)]
    is_start_of_contour = False
    for pair, edge in calibrated_edges.items():
        i, j = pair
        # if i is the start of a contour, we need to minus the offset first, then calibrate it
        if is_start_of_contour:
            x, y = points[i]
            x_ = sdivide(x - offset[0], gcd)
            y_ = sdivide(y - offset[1], gcd)
            calibrated_points.append((x_, y_))
            is_start_of_contour = False
        if i < j:
            x, y = calibrated_points[i]
            dx, dy = edge
            calibrated_points.append((x + dx, y + dy))
        else:
            is_start_of_contour = True
    return calibrated_points

def calibrate_font(outline: freetype.Outline, plot=False):

    points = outline.points
    contours = outline.contours

    edges = compute_edges(points, contours)
    # gcd_candidate, v_s, n_s = compute_gcd_stage1(edges)
    # gcd_candidate = gcd_candidate // 2 # 考虑公度量的一半，因为斜线笔画可能采用其一半
    # print(gcd_candidate)
    # gcd, loss = compute_gcd_stage2(gcd_candidate, v_s, n_s)
    # print(gcd)

    # check hint.py, we obtain gcd = 18
    calibrated_points = calibrate(points, edges, 18)

    if plot:
        # 可视化
        fig, ax = plt.subplots(figsize=(8, 8))
        draw(points, contours, color="gray", label_points=False, figure=(fig, ax))
        draw(calibrated_points, contours, label_points=True, figure=(fig, ax))
        plt.show()
    return calibrated_points, contours

def rasterize(calibrated_points, contours, gcd=18, plot=False):
    x_min, y_min = np.asarray(calibrated_points).min(axis=0)
    calibrated_points = calibrated_points - np.array([x_min, y_min])
    points = np.array([(x//gcd, y//gcd) for x, y in calibrated_points])

    if plot:
        draw(points, contours, label_points=True)
    x_max, y_max = points.max(axis=0)
    width = int(x_max)
    height = int(y_max)

    if plot:
        plt.xticks(np.arange(width), rotation=90)
        plt.yticks(np.arange(height))
        plt.savefig("outline.png")
        plt.close()

    polygons = []
    start = 0
    for end in contours:
        polygons.append(points[start:end+1])
        start = end + 1

    mask = np.zeros((height, width), dtype=np.bool_)
    for poly in polygons:
        temp_mask = np.zeros_like(mask, dtype=np.bool_)
        P = Polygon(poly)
        for y in range(height):
            for x in range(width):
                if P.contains(box(x, y, x+1, y+1)):
                    temp_mask[y, x] = True
        # cv2.fillPoly(temp_mask, [poly], 255)
        mask = cv2.bitwise_xor(mask, temp_mask)

    if plot:
        fig, ax = plt.subplots(figsize=(8, 8))
        draw(points, contours, label_points=False, figure=(fig, ax))
        ax.set_aspect('equal')
        plt.xticks(np.arange(width),rotation=90)
        plt.yticks(np.arange(height))
        plt.imshow(mask, "gray",origin="lower")
        plt.savefig("mask.png", dpi=300)
        plt.close()
    sub_mask = mask[1::2,1::2]
    # sub_mask = mask[0::2,0::2]
    if plot:
        plt.imshow(sub_mask, "gray",origin="lower")
        plt.savefig("mask_sub.png", dpi=300)

    return mask, sub_mask

def main(font, char, plot, save_format):
    face = freetype.Face(font)
    face.load_char(char, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
    glyph = face.glyph
    if glyph is None:
        return
    outline = glyph.outline
    calibrated_points, contours = calibrate_font(outline, plot=plot)
    mask, sub_mask = rasterize(calibrated_points, contours, gcd=18, plot=plot)
    if save_format == "png":
        plt.imshow(mask, "gray", origin="lower")
        plt.axis('off')
        plt.savefig(f"./pngs/{char}.png", dpi=300, bbox_inches='tight', pad_inches=0)
    elif save_format == "arr":
        np.save(f"./arrs/{char}.npy", mask)



def process_glyph(code):
    """
    子进程执行单个字符处理
    """
    char = chr(code)
    try:
        main(args.font, char, args.plot, save_format=args.save_format)
        return None
    except Exception as e:
        print(f"{char}报错: {e}")
        return char

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--font", type=str, default="./fonts/字悦九叠印篆.ttf", help="Path to the font file")
    parser.add_argument("--char", type=str, default="", help="Character to calibrate")
    parser.add_argument("--plot", action="store_true", help="Whether to plot the calibration result")
    parser.add_argument("--save_format", type=str, default="arr", help="Format to save the output images (png or arr)")
    args = parser.parse_args()
    Path("./pngs").mkdir(parents=True, exist_ok=True)
    Path("./arrs").mkdir(parents=True, exist_ok=True)
    if args.char:
        main(args.font, args.char, args.plot, save_format=args.save_format)
    else:
        face = freetype.Face(args.font)
        cjk_glyphs = list(iter_glyph())
        valid_glyphs = []
        charcode, glyph_index = face.get_first_char()
        while glyph_index != 0:
            valid_glyphs.append(charcode)
            charcode, glyph_index = face.get_next_char(charcode, glyph_index)
        valid_glyphs = set(valid_glyphs).intersection(set(cjk_glyphs))


        err_chars = []
        from multiprocessing import Pool, cpu_count
        # 进程数可根据机器调整
        workers = 8

        with Pool(processes=workers) as pool:
            for ret in tqdm(
                pool.imap(process_glyph, valid_glyphs),
                total=len(valid_glyphs)
            ):
                if ret is not None:
                    err_chars.append(ret)

        print(f"报错的字：{''.join(err_chars)}")