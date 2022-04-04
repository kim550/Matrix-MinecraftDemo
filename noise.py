import random
import _noise

class Noise2d:
    def __init__(self, seed):
        self.random = random.Random(seed)
        self.persistence = self.random.uniform(0.01, 0.15)
        self.octaves = self.random.randint(3, 5)

    def perlin_noise(self, x, y):
        return _noise.perlin_noise2d(self.persistence, self.octaves, x, y)


class Noise3d:
    def __init__(self, seed):
        self.random = random.Random(seed)
        self.persistence = self.random.uniform(0.01, 0.15)
        self.octaves = self.random.randint(3, 5)

    def perlin_noise(self, x, y, z):
        return _noise.perlin_noise3d(self.persistence, self.octaves, x, y, z)
