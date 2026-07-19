<p align="center">
      <img src="./seals/拼.png" alt="拼">
      <img src="./seals/篆.png" alt="篆">
</p>

# 拼豆 x 篆书 = 拼篆

篆书横平竖直，笔画粗细均匀，适合像素化。将篆书字体转换成像素图纸，适用于拼豆等像素艺术。

## 流程
- [x] 1. 提取篆书字体轮廓
- [x] 2. 找到轮廓的笔画粗细
- [x] 3. 校正轮廓至笔画粗细的网格上，得到最简像素图
- [ ] 4. 纯前端网站交付

- 在实现过程中，注意到需要使用 hinting 技术，即在渲染字体时，使用字体的 hinting 信息来调整字形的轮廓，以便在低分辨率下显示更清晰的字体。本质上我们做的事情就是字体像素化，因而要找到笔画粗细的公度量（对篆书这种笔画粗细均匀的字体来说，公度量就是笔画粗细），然后将字形轮廓上的每个点校正到公度量尺寸的网格上。

1. `hint.py`：这一步是将字形填充部分骨架化，然后计算字形轮廓上的每个点到骨架的最短距离，得到笔画粗细的公度量的 $\sqrt{2}$倍。
运行该脚本得到结果为
```
[16 17 18 23 24 25 26] [    2   545  7363 88274  1416     4   646]
```
即最多的距离约为 23，公度量约为 18。

2. `calibrate.py`：这一步是将字形轮廓上的每个点校正到公度量尺寸的网格上，除去公度量，得到最简像素图。根据这个像素草图可以升采样或降采样，得到不同分辨率的像素图。

报错的字：胬腾諺谚闈闱駑騰驁驽骜鷙鷳鸷鹇嬀捣搗樓櫂毗濯稗

## 制作

润心 alephpi 2026

<p align="center">
      <img src="./seals/润.png" alt="润">
      <img src="./seals/心.png" alt="心">
</p>

<p align="center">
      <img src="./seals/a.png" alt="a">
      <img src="./seals/l.png" alt="l">
      <img src="./seals/e.png" alt="e">
      <img src="./seals/p.png" alt="p">
      <img src="./seals/h.png" alt="h">
      <img src="./seals/p.png" alt="p">
      <img src="./seals/i.png" alt="i">
</p>

<p align="center">
      <img src="./seals/2.png" alt="2">
      <img src="./seals/0.png" alt="0">
      <img src="./seals/2.png" alt="2">
      <img src="./seals/6.png" alt="6">
</p>


