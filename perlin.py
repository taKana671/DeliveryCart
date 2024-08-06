from math import floor

import numpy as np
import cv2


class Perlin():

    def __init__(self, size=256):
        self.size = size
        self._hash = np.arange(size, dtype=int) % size
        np.random.shuffle(self._hash)
        self._hash = self._hash.astype(np.int8)
        self._grad = 2 * np.random.random((128, 2)) - 1

    def create_noise(self, grid):
        arr = np.array([val for val in self.noise(grid)])
        arr = arr.reshape(self.size, self.size)

        temp = np.abs(arr)
        temp = temp * 65535
        img = temp.astype(np.uint16)

        cv2.imwrite('mysample2.png', img)


        temp2 = (arr * -100).astype(np.uint8)
        cv2.imwrite('mysample1.png', temp2)

    def hash(self, i, j):
        idx = self._hash[i] + j
        return self._hash[idx]

    def fade(self, x):
        return 6 * x**5 - 15 * x**4 + 10 * x**3

    def weight(self, ix, iy, dx, dy):
        ix %= 256
        iy %= 256
        idx = self.hash(ix, iy)
        ax, ay = self._grad[idx]
        return ax * dx + ay * dy

    def lerp(self, a, b, t):
        return a + (b - a) * t

    def noise(self, grid):
        for y in np.linspace(0, grid, self.size):
            for x in np.linspace(0, grid, self.size):
                ix = floor(x)
                iy = floor(y)
                dx = x - floor(x)
                dy = y - floor(y)

                w00 = self.weight(ix, iy, dx, dy)
                w10 = self.weight(ix + 1, iy, dx - 1, dy)
                w01 = self.weight(ix, iy + 1, dx, dy - 1)
                w11 = self.weight(ix + 1, iy + 1, dx - 1, dy - 1)

                wx = self.fade(dx)
                wy = self.fade(dy)

                y0 = self.lerp(w00, w10, wx)
                y1 = self.lerp(w01, w11, wx)
                yield (self.lerp(y0, y1, wy) - 1) / 2


if __name__ == '__main__':
    Perlin(size=257).create_noise(4)