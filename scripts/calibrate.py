import freetype
import matplotlib.pyplot as plt
import numpy as np


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
    gcd_candidate, v_s, n_s = compute_gcd_stage1(edges)
    gcd_candidate = gcd_candidate // 2 # 考虑公度量的一半，因为斜线笔画可能采用其一半
    print(gcd_candidate)
    gcd, loss = compute_gcd_stage2(gcd_candidate, v_s, n_s)
    print(gcd)

    calibrated_points = calibrate(points, edges, gcd)

    if plot:
        # 可视化
        fig, ax = plt.subplots(figsize=(8, 8))
        draw(points, contours, color="gray", label_points=False, figure=(fig, ax))
        draw(calibrated_points, contours, label_points=True, figure=(fig, ax))
        plt.show()

def main(font, char, plot):
    face = freetype.Face(font)
    face.load_char(char, freetype.FT_LOAD_NO_SCALE | freetype.FT_LOAD_NO_HINTING)
    outline = face.glyph.outline
    calibrate_font(outline, plot=plot)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--font", type=str, default="./fonts/字悦九叠印篆.ttf", help="Path to the font file")
    parser.add_argument("--char", type=str, default="爽", help="Character to calibrate")
    parser.add_argument("--plot", action="store_true", help="Whether to plot the calibration result")

    args = parser.parse_args()
    main(args.font, args.char, args.plot)