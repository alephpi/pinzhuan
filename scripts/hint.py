from functools import partial
from multiprocessing import Pool, cpu_count

import cv2
import freetype
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import cdist
from skimage.morphology import skeletonize
from tqdm import tqdm
from utils import iter_glyph


def get_glyph_mask_and_points(font_path: str, char: str):
    """
    加载指定字符的矢量轮廓，并生成完美 Even-Odd 填充的 NumPy Mask 及原始控制点。

    参数:
        font_path: 字体文件的路径
        char: 要提取的单个字符

    返回:
        mask: np.ndarray, 二维灰度图像矩阵（含128灰度值的控制点圈）
        polygons: list of np.ndarray, 包含每个闭合轮廓坐标的列表（已转换到图像坐标系）
    """
    # 1. 载入字体并以矢量原始单位加载
    face = freetype.Face(font_path)
    face.load_char(char, freetype.FT_LOAD_NO_SCALE)
    glyph = face.glyph
    if glyph is None:
        return None, None

    outline = glyph.outline

    points = np.array(outline.points, dtype=np.int32)
    contours = outline.contours

    # 2. 计算全局边界
    x_min, y_min = points.min(axis=0)
    x_max, y_max = points.max(axis=0)

    width = int(x_max - x_min)
    height = int(y_max - y_min)

    # 3. 一次性转换所有点的坐标：平移 + Y轴翻转
    new_points = points.copy()
    new_points[:, 0] = new_points[:, 0] - x_min
    new_points[:, 1] = height - (new_points[:, 1] - y_min)

    # 4. 解析轮廓，直接使用已转换的坐标
    polygons = []
    start = 0
    for end in contours:
        contour_pts = new_points[start : end + 1]
        polygons.append(contour_pts)
        start = end + 1

    # 5. 初始化画布
    mask = np.zeros((height, width), dtype=np.uint8)

    # 6. 异或绘制 Mask 填充 (Even-Odd 规则)
    for poly in polygons:
        cv_poly = poly.reshape((-1, 1, 2))
        temp_mask = np.zeros_like(mask)
        cv2.drawContours(temp_mask, [cv_poly], -1, 255, thickness=cv2.FILLED)
        mask = cv2.bitwise_xor(mask, temp_mask)

    return mask, new_points

def hinting(font_path: str, char: str):
    try:
        mask, points = get_glyph_mask_and_points(font_path, char)
        if mask is None or points is None:
            return np.inf

        skeleton = skeletonize(mask)
        skeleton_points = np.nonzero(skeleton)
        # if len(skeleton_points[0]) == 0:  # 没有骨架点
        #     return np.inf
            
        skeleton_xy = np.stack(skeleton_points, axis=1)
        x, y = points[:, 0], points[:, 1]

        new_points = np.stack((y, x), axis=1)
        ds = cdist(new_points, skeleton_xy).min(axis=1).astype(int)
        values, counts = np.unique(ds, return_counts=True)
        d = values[counts.argmax()]

        return d
    except freetype.FT_Exception as e:
        # 忽略渲染错误，返回无穷大
        print(f"跳过字符 '{char}' (U+{ord(char):04X}): {e}")
        return np.inf
    except Exception as e:
        print(f"处理字符 '{char}' (U+{ord(char):04X}) 时发生未知错误: {e}")
        return np.inf

def main():
    font_path = "./fonts/字悦九叠印篆.ttf"
    # char = "右"
    # d = hinting(font_path, char)
    # print(d)
    # return

    
    chars = list(iter_glyph())
    print(f"总共 {len(chars)} 个字符")
    
    num_processes = cpu_count()
    print(f"使用 {num_processes} 个进程")
    
    process_func = partial(hinting, font_path)
    
    with Pool(processes=num_processes) as pool:
        hints = list(tqdm(
            pool.imap(process_func, chars),
            total=len(chars),
            desc="处理字符"
        ))
    
    # 过滤掉无效值
    valid_hints = [h for h in hints if h != np.inf]
    print(f"有效字符: {len(valid_hints)} / {len(chars)}")
    
    if valid_hints:
        plt.hist(valid_hints)
        values, counts = np.unique(valid_hints, return_counts=True)
        print(values, counts)
        print(values[counts.argmax()])
    else:
        print("没有有效的字符数据")

if __name__ == "__main__":
    main()