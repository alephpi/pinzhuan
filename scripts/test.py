import matplotlib.pyplot as plt

points = outline.points
contours = outline.contours

def draw(points, contours):
    fig, ax = plt.subplots(figsize=(8, 8))

    start = 0

    for end in contours:
        contour = points[start : end + 1]

        x = [p[0] for p in contour]
        y = [p[1] for p in contour]

    # 闭合
        x.append(contour[0][0])
        y.append(contour[0][1])

        ax.plot(x, y, "-")
        ax.scatter(x[:-1], y[:-1], s=15)

    # 标注点编号（可选）
        for idx, p in enumerate(contour, start):
            ax.text(p[0], p[1], str(idx), fontsize=8)

        start = end + 1

    ax.set_aspect("equal")
    ax.invert_yaxis()
    plt.show()

draw(points, contours)