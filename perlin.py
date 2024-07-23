from PIL import Image

from math import floor
# from itertools import product
import numpy as np
import cv2
# import matplotlib.pyplot as plt


def lerp(a, b, t):
    return a + (b - a) * t


class Perlin():
    slopes = 2 * np.random.random((256, 2)) - 1
    rand_index = np.zeros(512, dtype=np.int8)
    for i, rand in enumerate(np.random.permutation(256)):
        rand_index[i] = rand
        rand_index[i + 256] = rand

    @staticmethod
    def hash(i, j):
        # 前提条件: 0 <= i, j <= 256
        return Perlin.rand_index[Perlin.rand_index[i] + j]

    @staticmethod
    def fade(x):
        return 6 * x**5 - 15 * x ** 4 + 10 * x**3

    @staticmethod
    def weight(ix, iy, dx, dy):
        # 格子点(ix, iy)に対する(ix + dx, iy + dy)の重みを求める
        ix %= 256
        iy %= 256
        ax, ay = Perlin.slopes[Perlin.hash(ix, iy)]
        return ax * dx + ay * dy

    @staticmethod
    def noise(x, y):
        ix = floor(x)
        iy = floor(y)
        dx = x - floor(x)
        dy = y - floor(y)

        # 重みを求める
        w00 = Perlin.weight(ix, iy,   dx  , dy)
        w10 = Perlin.weight(ix+1,   iy, dx-1,   dy)
        w01 = Perlin.weight(ix,   iy+1,   dx, dy-1)
        w11 = Perlin.weight(ix+1, iy+1, dx-1, dy-1)

        # 小数部分を変換する
        wx = Perlin.fade(dx)
        wy = Perlin.fade(dy)

        # 線形補間して返す
        y0 = lerp(w00, w10, wx)
        y1 = lerp(w01, w11, wx)
        return (lerp(y0, y1, wy) - 1) / 2 # 値域を[0, 1]に戻す


# 画像の大きさは512x512
width, height = 257, 257
canvas = np.zeros((width, height))
# 格子点を16個配置する
# w = 16  # 2のべき乗
w = 8


canvas = np.array([[Perlin.noise(x, y)
                    for x in np.linspace(0, w, width)]
                   for y in np.linspace(0, w, height)])

temp = np.abs(canvas)
temp = temp * 65535
img = temp.astype(np.uint16)

cv2.imwrite('sample8.png', img)
# img = Image.fromarray(temp.astype(np.uint16))
# img.save('sample5.png')


# import pdb; pdb.set_trace()
# img = Image.fromarray((canvas * -100).astype(np.uint8)
# img.save('sample.jpg')


# # matplotlibを使って表示
# fig, ax = plt.subplots(figsize=(10, 10))
# ax.imshow(canvas, cmap=plt.cm.binary)