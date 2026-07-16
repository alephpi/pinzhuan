import freetype
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable
from skimage.morphology import skeletonize


def pad(arr, target=(1000, 1000)):
    h, w = arr.shape
    target_h, target_w = target
    if h >= target_h and w >= target_w:
        return arr
    pad_h = (target_h - h) // 2
    pad_w = (target_w - w) // 2
    padded_arr = np.pad(
        arr,
        ((pad_h, target_h - h - pad_h), (pad_w, target_w - w - pad_w)),
        mode="constant",
        constant_values=0,
    )
    return padded_arr

def fill_zeros_interp(arr):
    """
    使用 np.interp 进行插值（最简洁）
    """
    arr = arr.copy().astype(float)
    n = len(arr)

    # 找到非0点的索引和值
    valid_idx = np.where(arr != 0)[0]
    valid_vals = arr[valid_idx]

    if len(valid_idx) == 0:
        return arr

    # 对所有位置进行插值
    # 注意：np.interp 默认线性插值
    interpolated = np.interp(np.arange(n), valid_idx, valid_vals)

    # 只替换原来的0位置
    zero_mask = arr == 0
    arr[zero_mask] = interpolated[zero_mask]

    return arr

def find_grid_idx(ref_axis, grid_axis):
    ref_x_to_grid_x = {}
    grid_x_assigned = set()
    for ref_axis in ref_axis:
        closest_grid = grid_axis[np.argmin(np.abs(grid_axis - ref_axis))]
        if closest_grid not in grid_x_assigned:
            ref_x_to_grid_x[ref_axis] = closest_grid
            grid_x_assigned.add(closest_grid)
        else:
            ref_x_to_grid_x[ref_axis] = int(ref_axis)
    x_idx = np.asarray(list(ref_x_to_grid_x.values()), dtype=np.int32)
    return x_idx

def rasterize(glyph, plot=False):
    """ rasterization by heuristics : find the grid by histogram and downsample the glyph to the grid.
    """
    glyph = pad(glyph)
    skeleton = skeletonize(glyph)

    if plot:
        plt.imshow(glyph, cmap="gray")
        plt.savefig("mask.png", dpi=1000)

        plt.imshow(skeleton, cmap="gray")
        plt.savefig("skeleton.png", dpi=1000)

    ys, xs = np.where(skeleton)

    # x histogram
    hist_x = np.bincount(xs, minlength=skeleton.shape[1])
    ref_x = np.linspace(0, skeleton.shape[1], 11)[1:-1]

    # y histogram
    hist_y = np.bincount(ys, minlength=skeleton.shape[0])
    ref_y = np.linspace(0, skeleton.shape[0], 11)[1:-1]
    if plot:
        fig, ax = plt.subplots(figsize=(6, 6), dpi=1000)
        ax.imshow(skeleton, cmap="gray")  # 默认 origin='upper'

        divider = make_axes_locatable(ax)
        ax_top = divider.append_axes("top", size=1.0, pad=0.1, sharex=ax)
        ax_right = divider.append_axes("right", size=1.0, pad=0.1, sharey=ax)

        ax_top.bar(np.arange(len(hist_x)), hist_x, width=1.0)
        ax_top.vlines(
            ref_x,
            ymin=0,
            ymax=hist_x.max(),
            colors="r",
            linestyles="dashed",
        )
        ax_top.tick_params(labelbottom=False)

        ax_right.barh(np.arange(len(hist_y)), hist_y, height=1.0)
        ax_right.hlines(
            ref_y,
            xmin=0,
            xmax=hist_x.max(),
            colors="r",
            linestyles="dashed",
        )

        ax_right.tick_params(labelleft=False)

        # plt.show()
        plt.savefig("histogram.png", dpi=1000)
        plt.close()

    # diag = xs - ys
    # hist_diag = np.bincount(diag - diag.min())
    # anti = xs + ys
    # hist_anti = np.bincount(anti)

    # plt.figure(figsize=(6, 6), dpi=len(hist_diag))
    # plt.bar(np.arange(len(hist_diag)), hist_diag)
    # plt.title("y=x direction")
    # plt.figure(figsize=(6, 6), dpi=len(hist_anti))
    # plt.bar(np.arange(len(hist_anti)), hist_anti)
    # plt.title("y=-x direction")

    grid_x = hist_x.argsort()[-9:]  # 最大的9个索引
    grid_y = hist_y.argsort()[-9:]  # 最大的9个索引

    # find stroke indices
    x_idx = find_grid_idx(ref_x, grid_x)
    y_idx = find_grid_idx(ref_y, grid_y)

    stroke_size = 1
    hop_size = 1
    w_strokes = 9
    h_strokes = 9
    W = w_strokes * stroke_size + hop_size * (w_strokes - 1)
    H = h_strokes * stroke_size + hop_size * (h_strokes - 1)

    # create the grid with stroke axis and blank axis
    x_idx_ = np.zeros(W, dtype=np.int32)
    x_idx_[:: stroke_size + hop_size] = x_idx
    x_idx_ = fill_zeros_interp(x_idx_).astype(np.int32)
    y_idx_ = np.zeros(H, dtype=np.int32)
    y_idx_[:: stroke_size + hop_size] = y_idx
    y_idx_ = fill_zeros_interp(y_idx_).astype(np.int32)

    # downsample the mask instead of the skeleton to avoid corner case
    # downsampling_grid = skeleton[np.meshgrid(y_idx, x_idx), indexing="ij"]
    downsampling_grid = glyph[np.meshgrid(y_idx_, x_idx_, indexing="ij")]
    if plot:
        plt.imshow(downsampling_grid, "gray")
        plt.savefig("downsampling_grid.png", dpi=1000)



if __name__ == "__main__":
    font_path = "./fonts/字悦九叠印篆.ttf"  # 替换为你的字体路径
    face = freetype.Face(font_path)
    face.set_pixel_sizes(0, face.units_per_EM)
    face.load_char("好", freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)

    bmp = face.glyph.bitmap
    glyph = np.array(bmp.buffer).reshape(bmp.rows, bmp.width) > 0

    rasterize(glyph, plot=False)