import itertools
import pyglet
import os
import sys

from settings import Settings

textures = {}

def load_textures():
    for file in os.listdir(Settings.texture_path):
        if file.endswith('.jpg') or file.endswith('.png'):
            textures[file[:-4]] = pyglet.image.load(Settings.texture_path + file)

load_textures()

images = {}

def load_images():
    for file in os.listdir(Settings.image_path):
        if file.endswith('.jpg') or file.endswith('.png'):
            images[file[:-4]] = pyglet.image.load(Settings.image_path + file)

load_images()

class BlockData:
    def __init__(self, model, x, y, z, name, init, update):
        self.model = model
        self.position = (x, y, z)
        self.name = name
        self.init = init
        self.update = update
        if self.init is not None:
            if interval := self.init(self):
                pyglet.clock.schedule_interval(self._update, interval)
    def _update(self, dt):
        if self.position in self.model.shown:
            self.update(self)

class Block:
    def __init__(self, name, chname, images, hardness, wooden_pickaxe_hardness, diamond_pickaxe_hardness, alpha, drop, recipe, choose):
        self.name = name
        self.chname = chname
        self.hardness = hardness
        self.wooden_pickaxe_hardness = wooden_pickaxe_hardness
        self.diamond_pickaxe_hardness = diamond_pickaxe_hardness
        self.alpha = alpha
        self.drop = drop
        self.recipe = recipe
        self.choose = choose

        self.images = images  # top bottom left right front back
        image = pyglet.image.Texture.create(1024, 1024)
        for x, y in itertools.product(range(3), range(2)):
            image.blit_into(textures[images[x * 2 + y]], x * 256, y * 256, 0)
        self.textures = pyglet.graphics.TextureGroup(image)
    def __call__(self, model, x, y, z):
        data = blockdatas[self.name]
        return BlockData(model, x, y, z, self.name, data[0], data[1])


class Recipe4:
    def __init__(self, recipe, times):
        self.recipe = recipe
        self.times = times

    def valid4(self, recipe):
        return self.recipe == recipe
    
    def valid9(self, recipe):
        return tuple(recipe[i][:2] for i in range(2)) == self.recipe

    def valid81(self, recipe):
        return tuple(recipe[i][:2] for i in range(2)) == self.recipe


class DisorderedRecipe4:
    def __init__(self, recipe, times):
        self.recipe = recipe
        self.times = times

    def valid4(self, recipe):
        recipe = tuple(recipe[i][j] for i in range(2) for j in range(2))
        result = tuple(self.recipe[i][j] for i in range(2) for j in range(2))
        counts_recipe = {}
        counts_result = {}
        for i in recipe:
            if i not in counts_recipe:
                counts_recipe[i] = 0
            counts_recipe[i] += 1
        for i in result:
            if i not in counts_result:
                counts_result[i] = 0
            counts_result[i] += 1
        return counts_recipe == counts_result
    
    def valid9(self, recipe):
        recipe = tuple(recipe[i][j] for i in range(3) for j in range(3))
        result = tuple(self.recipe[i][j] for i in range(2) for j in range(2))
        counts_recipe = {}
        counts_result = {'': 5}
        for i in recipe:
            if i not in counts_recipe:
                counts_recipe[i] = 0
            counts_recipe[i] += 1
        for i in result:
            if i not in counts_result:
                counts_result[i] = 0
            counts_result[i] += 1
        return counts_recipe == counts_result
    
    def valid81(self, recipe):
        recipe = tuple(recipe[i][j] for i in range(9) for j in range(9))
        result = tuple(self.recipe[i][j] for i in range(2) for j in range(2))
        counts_recipe = {}
        counts_result = {'': 77}
        for i in recipe:
            if i not in counts_recipe:
                counts_recipe[i] = 0
            counts_recipe[i] += 1
        for i in result:
            if i not in counts_result:
                counts_result[i] = 0
            counts_result[i] += 1
        return counts_recipe == counts_result


class Recipe9:
    def __init__(self, recipe, times):
        self.recipe = recipe
        self.times = times

    def valid4(self, recipe):
        return False
    
    def valid9(self, recipe):
        return self.recipe == recipe

    def valid81(self, recipe):
        return tuple(recipe[i][:3] for i in range(3)) == self.recipe


class DisorderedRecipe9:
    def __init__(self, recipe, times):
        self.recipe = recipe
        self.times = times

    def valid4(self, recipe):
        return False
    
    def valid9(self, recipe):
        recipe = tuple(recipe[i][j] for i in range(3) for j in range(3))
        result = tuple(self.recipe[i][j] for i in range(3) for j in range(3))
        counts_recipe = {}
        counts_result = {}
        for i in recipe:
            if i not in counts_recipe:
                counts_recipe[i] = 0
            counts_recipe[i] += 1
        for i in result:
            if i not in counts_result:
                counts_result[i] = 0
            counts_result[i] += 1
        return counts_recipe == counts_result
    
    def valid81(self, recipe):
        recipe = tuple(recipe[i][j] for i in range(9) for j in range(9))
        result = tuple(self.recipe[i][j] for i in range(3) for j in range(3))
        counts_recipe = {}
        counts_result = {'': 72}
        for i in recipe:
            if i not in counts_recipe:
                counts_recipe[i] = 0
            counts_recipe[i] += 1
        for i in result:
            if i not in counts_result:
                counts_result[i] = 0
            counts_result[i] += 1
        return counts_recipe == counts_result


def make_block(name, chname, init, update, textures, hardness=100, wooden_pickaxe_hardness=None, diamond_pickaxe_hardness=None, alpha=False, drop=None, recipe=None, choose=None):
    if wooden_pickaxe_hardness is None:
        wooden_pickaxe_hardness = hardness
    if diamond_pickaxe_hardness is None:
        diamond_pickaxe_hardness = hardness
    if drop is None:
        drop = (name, 1)
    blocks[name] = Block(name, chname, textures, hardness, wooden_pickaxe_hardness, diamond_pickaxe_hardness, alpha, drop, recipe, choose)
    blockdatas[name] = (init, update)

blocks = {}
blockdatas = {}

oak_board_recipe4 = DisorderedRecipe4(
    (
        ('oak_timber'       ,''                 ),
        (''                 ,''                 ),
    ),
    4
)
workbench_recipe4 = Recipe4(
    (
        ('oak_board'        ,'oak_board'        ),
        ('oak_board'        ,'oak_board'        ),
    ),
    1
)
super_workbench_recipe9 = Recipe9(
    (
        ('workbench'        ,'workbench'        ,'workbench'        ),
        ('workbench'        ,'workbench'        ,'workbench'        ),
        ('workbench'        ,'workbench'        ,'workbench'        ),
    ),
    1
)
furnace_recipe9 = Recipe9(
    (
        ('round_stone'      ,'round_stone'      ,'round_stone'      ),
        ('round_stone'      ,''                 ,'round_stone'      ),
        ('round_stone'      ,'round_stone'      ,'round_stone'      ),
    ),
    1
)

def workbench_choose(window, block):
    window.set_exclusive_mouse(False)
    window.state = 'self_workbench'
    sys.modules['self_workbench'].setup()

def super_workbench_choose(window, block):
    window.set_exclusive_mouse(False)
    window.state = 'workbench'
    sys.modules['workbench'].setup()

make_block('soil', '泥土', None, None, ['soil'] * 6)
make_block('grass_block', '草方块', None, None, ['grass', 'soil', 'halfgrass', 'halfgrass', 'halfgrass', 'halfgrass'], drop=('soil', 1))
make_block('stone', '石头', None, None, ['stone'] * 6, 1500, wooden_pickaxe_hardness=250, diamond_pickaxe_hardness=100, drop=('round_stone', 1))
make_block('round_stone', '圆石', None, None, ['roundstone'] * 6, 1500, wooden_pickaxe_hardness=200, diamond_pickaxe_hardness=80)
make_block('bedrock', '基岩', None, None, ['bedrock'] * 6, -1)
make_block('coal_ore', '煤炭矿石', None, None, ['coalore'] * 6, 1800, wooden_pickaxe_hardness=350, diamond_pickaxe_hardness=130, drop=('coal', 1))
make_block('iron_ore', '铁矿石', None, None, ['ironore'] * 6, 2300)
make_block('brass_ore', '黄铜矿石', None, None, ['brassore'] * 6, 1800)
make_block('diamond_ore', '钻石矿石', None, None, ['diamondore'] * 6, 5000, drop=('diamond', 1))
make_block('pink_diamond_ore', '粉钻矿石', None, None, ['pinkdiamondore'] * 6, 5500)
make_block('colorful_stone', '彩石', None, None, ['colorfulstone'] * 6, 8000)
make_block('oak_timber', '橡树原木', None, None, ['oakring', 'oakring', 'oakbark', 'oakbark', 'oakbark', 'oakbark'], 200)
make_block('oak_leaf', '橡树树叶', None, None, ['oakleaf'] * 6, 40, alpha=True, drop=('', 0))
make_block('oak_board', '橡树木板', None, None, ['oakboard'] * 6, 150, recipe=oak_board_recipe4)
make_block('workbench', '工作台', None, None, ['workbenchtop', 'oakboard', 'workbenchleft', 'workbenchleft', 'workbenchfront', 'workbenchfront'], 500, recipe=workbench_recipe4, choose=workbench_choose)
make_block('super_workbench', '超级工作台', None, None, ['superworkbenchtop', 'superworkbenchtop', 'superworkbenchleft', 'superworkbenchleft', 'superworkbenchfront', 'superworkbenchfront'], 800, recipe=super_workbench_recipe9, choose=super_workbench_choose)
make_block('tnt', '炸药', None, None, ['tnttop', 'tntbottom', 'tntside', 'tntside', 'tntside', 'tntside'], 400)
make_block('furnace_off', '熔炉', None, None, ['furnacetop', 'furnacetop', 'furnaceoff', 'furnaceoff', 'furnaceoff', 'furnaceoff'], 2000, wooden_pickaxe_hardness=600, diamond_pickaxe_hardness=200, recipe=furnace_recipe9)
make_block('glass_block', '玻璃方块', None, None, ['glass'] * 6, 200, alpha=True, drop=('', 0))
make_block('error_block', '错误方块', None, None, ['error'] * 6, 1000)
