import itertools
import pyglet
from pyglet.gl import *
from collections import deque
import time
import math
import random
import threading
import sys

from settings import Settings
from blocks import blocks, images
import matrixon
import base

def tex_coord(x, y):
    m = 1.0 / 4
    n = 1.0 / 4
    dx = x * m
    dy = y * n
    return (dx, dy, dx + m, dy, dx + m, dy + m, dx, dy + m)

tex_coords = [
    *tex_coord(0, 0),
    *tex_coord(0, 1),
    *tex_coord(1, 1),
    *tex_coord(1, 0),
    *tex_coord(2, 1),
    *tex_coord(2, 0),
]

def cube_vertices(x, y, z, n):
    return [
        x-n,y+n,z-n, x-n,y+n,z+n, x+n,y+n,z+n, x+n,y+n,z-n,  # top
        x-n,y-n,z-n, x+n,y-n,z-n, x+n,y-n,z+n, x-n,y-n,z+n,  # bottom
        x-n,y-n,z-n, x-n,y-n,z+n, x-n,y+n,z+n, x-n,y+n,z-n,  # left
        x+n,y-n,z+n, x+n,y-n,z-n, x+n,y+n,z-n, x+n,y+n,z+n,  # right
        x-n,y-n,z+n, x+n,y-n,z+n, x+n,y+n,z+n, x-n,y+n,z+n,  # front
        x+n,y-n,z-n, x-n,y-n,z-n, x-n,y+n,z-n, x+n,y+n,z-n,  # back
    ]

def normalize(position):
    x, y, z = position
    return int(round(x)), int(round(y)), int(round(z))

def sectorize(position):
    x, y, z = normalize(position)
    x, z = x // Settings.sector_size, z // Settings.sector_size
    return (x, 0, z)

from noise import Noise2d, Noise3d

class Model:
    def __init__(self, seed):
        self.seed = seed
        self.terrain_noise = Noise2d(seed)
        self.cave_noise = Noise3d(seed)
        self.tree_noise = Noise2d(seed + Settings.tree_seed)

        self.batch = pyglet.graphics.Batch()

        self.world = {}
        self.shown = {}
        self._shown = {}
        self.sectors = {}
        self.queue = deque()
        self.waiting = {}

        self.mutex = threading.RLock()

    def init(self):
        n = 3
        for x, z in itertools.product(range(-n, n + 1), range(-n, n + 1)):
            self.make_sector((x, 0, z), immediate=False)

    def drop_test(self, position):
        x, y, z = position
        maxy = 0
        self.mutex.acquire()
        for pos in self.world.keys():
            if pos[0] == x and pos[2] == z and pos[1] > maxy:
                maxy = pos[1]
        self.mutex.release()
        return maxy

    def make_sector(self, sector, immediate=True, real=True):
        trees = []
        terrain_pn = self.terrain_noise.perlin_noise
        tree_pn = self.tree_noise.perlin_noise
        cave_pn = self.cave_noise.perlin_noise
        bx, bz = sector[0] * Settings.sector_size, sector[2] * Settings.sector_size
        for x, z in itertools.product(range(bx, bx + Settings.sector_size), range(bz, bz + Settings.sector_size)):
            height = terrain_pn((x + 1000000) / 4, (z + 1000000) / 4) * 8
            height = int(round(max(-8, height) + 9))
            if x % 4 == 0 and z % 4 == 0:
                tree = tree_pn((x + 1000000) / 4, (z + 1000000) / 4)
                if tree >= 0.15:
                    tree = int(round(tree * 20 + 3))
                    trees.append(((x, 30 + height, z), tree))
            for y in range(1, 26 + height):
                self.add_block((x, y, z), 'stone', immediate, real)
            for y in range(4):
                self.add_block((x, 26 + height + y, z), 'soil', immediate, real)
            if self.seed == 666:
                self.add_block((x, 30 + height, z), 'tnt', immediate, real)
            else:
                self.add_block((x, 30 + height, z), 'grass_block', immediate, real)
            self.add_block((x, 0, z), 'bedrock', immediate, real)
            for y in range(3, height):
                if cave_pn((x + 1000000) / 4, (z + 1000000) / 4, y / 8) <= -0.3:
                    self.remove_block((x, y, z))
        for tree in trees:
            if tree[1] <= 11:
                self.make_tree(tree[0], tree[1], immediate, real)
            else:
                self.make_tall_tree(tree[0], tree[1], immediate, real)
        if sector in Settings.window.changes:
            for pos, block in Settings.window.changes[sector].items():
                if block == '':
                    self.remove_block(pos, immediate, real)
                else:
                    self.add_block(pos, block, immediate, real)

    def make_area(self, block, num, n=80, minh=0, maxh=255, seed=None, immediate=True, real=True):
        x, y, z = seed
        made = []
        directions = Settings.faces.copy()
        total = 0
        while total < num:
            dx, dy, dz = random.choice(directions)
            directions = Settings.faces.copy()
            directions.remove((dx, dy, dz))
            x, y, z = x + dx, y + dy, z + dz
            if y < minh or y > maxh:
                continue
            if x < -n or x > n or z < -n or z > n:
                continue
            if (x, y, z) in made:
                continue
            self.add_block((x, y, z), block, immediate, real)
            made.append((x, y, z))
            total += 1

    def make_tree(self, position, height, immediate=True, real=True):
        x, y, z = position
        for i in range(height + 1):
            if height - i <= 2:
                d = height - i + 2
                for dx, dz in itertools.product(list(range(d)) + list(range(-d + 1, 0)), list(range(d)) + list(range(-d + 1, 0))):
                    if abs(dx) <= 2 and abs(dz) <= 2:
                        self.add_block((x + dx, y + i, z + dz), 'oak_leaf', immediate, real)
            if i != height:
                self.add_block((x, y + i, z), 'oak_timber', immediate, real)

    def make_tall_tree(self, position, height, immediate=True, real=True):
        x, y, z = position
        for i in range(height + 1):
            if height - i <= 5:
                d = height - i + 2
                for dx, dz in itertools.product(list(range(d)) + list(range(-d + 1, 0)), list(range(d)) + list(range(-d + 1, 0))):
                    if abs(dx) <= 4 and abs(dz) <= 4:
                        self.add_block((x + dx, y + i, z + dz), 'oak_leaf', immediate, real)
            if i != height:
                self.add_block((x, y + i, z), 'oak_timber', immediate, real)
                self.add_block((x + 1, y + i, z), 'oak_timber', immediate, real)
                self.add_block((x, y + i, z + 1), 'oak_timber', immediate, real)
                self.add_block((x + 1, y + i, z + 1), 'oak_timber', immediate, real)

    def exposed(self, position):
        x, y, z = position
        return any(
            (x + dx, y + dy, z + dz) not in self.world
            or blocks[self.world[(x + dx, y + dy, z + dz)].name].alpha
            for dx, dy, dz in Settings.faces
        )

    def add_block(self, position, block, immediate=True, real=True):
        if position in self.world:
            self.remove_block(position, immediate, real)
        self.mutex.acquire()
        self.world[position] = blocks[block](self, *position)
        self.mutex.release()
        self.sectors.setdefault(sectorize(position), []).append(position)
        if immediate:
            if self.exposed(position):
                self.show_block(position, real=real)
            self.check_neighbours(position, real)

    def remove_block(self, position, immediate=True, real=True):
        self.mutex.acquire()
        del self.world[position]
        self.mutex.release()
        self.sectors[sectorize(position)].remove(position)
        if immediate:
            if position in self.shown:
                self.hide_block(position)
            self.check_neighbours(position, real)

    def check_neighbours(self, position, real=True):
        x, y, z = position
        for dx, dy, dz in Settings.faces:
            key = (x + dx, y + dy, z + dz)
            if key not in self.world:
                continue
            if self.exposed(key):
                if key not in self.shown:
                    self.show_block(key, real=real)
            elif key in self.shown:
                self.hide_block(key)

    def show_block(self, position, immediate=True, real=True):
        block = self.world[position].name
        self.shown[position] = block
        if immediate:
            self._show_block(position, block, real)
        else:
            self._enqueue(self._show_block, position, block, real)

    def hide_block(self, position, immediate=True):
        self.shown.pop(position)
        if immediate:
            self._hide_block(position)
        else:
            self._enqueue(self._hide_block, position)

    def _show_block(self, position, block, real=True):
        x, y, z = position
        vertex_data = cube_vertices(x, y, z, 0.5)
        if real:
            self._shown[position] = self.batch.add(24, GL_QUADS, blocks[block].textures,
                ('v3f/static', vertex_data),
                ('t2f/static', tex_coords))
        else:
            self.mutex.acquire()
            self.waiting[position] = ((24, GL_QUADS, blocks[block].textures,
                ('v3f/static', vertex_data),
                ('t2f/static', tex_coords)))
            self.mutex.release()

    def _hide_block(self, position):
        try:
            self._shown.pop(position).delete()
        except KeyError:
            self.mutex.acquire()
            try:
                del self.waiting[position]
            except:
                pass
            self.mutex.release()

    def change_sectors(self, before, after):
        before_set = set()
        after_set = set()
        pad = 4
        dy = 0
        for dx, dz in itertools.product(range(-pad, pad + 1), range(-pad, pad + 1)):
            if dx ** 2 + dy ** 2 + dz ** 2 > (pad + 1) ** 2:
                continue
            if before:
                x, y, z = before
                before_set.add((x + dx, y + dy, z + dz))
            if after:
                x, y, z = after
                after_set.add((x + dx, y + dy, z + dz))
        show = after_set - before_set
        hide = before_set - after_set
        for sector in show:
            self.show_sector(sector)
        for sector in hide:
            self.hide_sector(sector)

    def show_sector(self, sector, immediate=False, real=True):
        for position in self.sectors.get(sector, []):
            if position not in self.shown and self.exposed(position):
                self.show_block(position, immediate, real)

    def hide_sector(self, sector):
        for position in self.sectors.get(sector, []):
            if position in self.shown:
                self.hide_block(position, False)

    def hit_test(self, position, vector, max_distance=8):
        m = 8
        x, y, z = position
        dx, dy, dz = vector
        previous = None
        for _ in range(max_distance * m):
            key = normalize((x, y, z))
            if key != previous and key in self.world:
                return key, previous
            previous = key
            x, y, z = x + dx / m, y + dy / m, z + dz / m
        return None, None

    def _enqueue(self, func, *args):
        self.queue.append((func, args))

    def _dequeue(self):
        func, args = self.queue.popleft()
        func(*args)

    def process_queue(self):
        start = time.perf_counter()
        while self.queue and time.perf_counter() - start < 1.0 / Settings.ticks_per_sec:
            self._dequeue()

    def process_entire_queue(self):
        while self.queue:
            self._dequeue()


class World(base.Base):
    def __init__(self, savedata, init=True):
        self.init = init

        self.strafe = [0, 0]
        self.sector = None

        self.reticle = None

        self.dy = savedata.dy
        self.flying = savedata.flying

        self.inventory = savedata.inventory
        self.block = savedata.block
        self.blocktime = 0
        self.progress = 0

        self.max_health = savedata.max_health
        self.health = savedata.health
        self.respwan = savedata.respwan
        self.position = savedata.position
        self.lasthurt = 0
        self.hurtcause = ''

        self.changes = savedata.changes

        self.matrixon = False
        self.script = ''

        self.model = Model(savedata.seed)
        if init:
            self.model.init()

        self.mouse_press = 0

        if init:
            if self.respwan[1] is None:
                self.position = (self.respwan[0], self.model.drop_test(self.respwan) + 2, self.respwan[2])
                self.respwan = self.position

            pyglet.clock.schedule_interval_soft(self.update_sector, 0.1)

    def die(self):
        self.state = 'death'
        sys.modules['death'].setup()

    def hurt(self, num, cause):
        self.hurtcause = cause
        if Settings.gamemode != 2:
            current = time.time()
            if current - self.lasthurt >= 1:
                self.health -= int(num)
                self.lasthurt = current
                if self.health <= 0:
                    self.die()

    def add_inventory(self, block, num):
        for i in self.inventory:
            if i[0] == block:
                i[1] += num
                return
        for i in self.inventory:
            if i[1] == 0:
                i[0] = block
                i[1] = num
                return

    def put_block(self, position, block):
        sp = sectorize(position)
        self.changes.setdefault(sp, {})[normalize(position)] = block
        self.model.add_block(position, block)
        return True

    def del_block(self, position):
        sp = sectorize(position)
        self.changes.setdefault(sp, {})[normalize(position)] = ''
        self.model.remove_block(position)
        return True

    def get_hardness(self, block):
        curr = self.inventory[self.block]
        if curr[1] == 0:
            return blocks[block].hardness
        if curr[0] == 'wooden_pickaxe':
            return blocks[block].wooden_pickaxe_hardness
        if curr[0] == 'diamond_pickaxe':
            return blocks[block].diamond_pickaxe_hardness
        return blocks[block].hardness

    def make_sector(self, sector):
        self.model.make_sector(sector, False, False)
        self.model.show_sector(sector, True, False)

    def get_sight_vector(self):
        x, y = self.rotation
        m = math.cos(math.radians(y))
        dy = math.sin(math.radians(y))
        dx = math.cos(math.radians(x - 90)) * m
        dz = math.sin(math.radians(x - 90)) * m
        return (dx, dy, dz)

    def get_motion_vector(self):
        if any(self.strafe):
            x, y = self.rotation
            strafe = math.degrees(math.atan2(*self.strafe))
            y_angle = math.radians(y)
            x_angle = math.radians(x + strafe)
            if Settings.gamemode == 2 and self.flying:
                m = math.cos(y_angle)
                dy = math.sin(y_angle)
                if self.strafe[1]:
                    dy = 0.0
                    m = 1
                if self.strafe[0] > 0:
                    dy *= -1
                dx = math.cos(x_angle) * m
                dz = math.sin(x_angle) * m
            else:
                dy = 0.0
                dx = math.cos(x_angle)
                dz = math.sin(x_angle)
        else:
            dx = 0.0
            dy = 0.0
            dz = 0.0
        return (dx, dy, dz)

    def update_sector(self, dt):
        x, y, z = self.sector
        for dx in [0, 1, -1, 2, -2, 3, -3]:
            for dz in [0, 1, -1, 2, -2, 3, -3]:
                sx = x + dx
                sz = z + dz
                if (sx, 0, sz) not in self.model.sectors:
                    self.model.sectors[(sx, 0, sz)] = []
                    threading.Thread(target=self.make_sector, args=((sx, 0, sz),), daemon=True).start()

    def update_world(self, dt):
        waiting = self.model.waiting
        batch = self.model.batch
        start = time.time()
        skip = 1.0 / Settings.ticks_per_sec
        self.model.mutex.acquire()
        for key, item in list(waiting.items()):
            if time.time() - start < skip:
                batch.add(*item)
                del waiting[key]
            else:
                break
        self.model.mutex.release()

        sector = sectorize(self.position)
        if sector != self.sector:
            self.model.change_sectors(self.sector, sector)
            if self.sector is None:
                self.model.process_entire_queue()
            self.sector = sector

        vector = self.get_sight_vector()
        block, previous = self.model.hit_test(self.position, vector)
        if block:
            self.progress = 0
            interval = self.get_hardness(self.model.world[block].name) / 100
            if self.mouse_press != 0 and (Settings.gamemode == 2 or interval > 0):
                skip = time.time() - self.mouse_press
                if Settings.gamemode == 1:
                    self.progress = skip / interval
                    ok = skip >= interval
                elif Settings.gamemode == 2:
                    ok = skip >= 0.3
                if ok:
                    if Settings.gamemode != 2:
                        drop = blocks[self.model.world[block].name].drop
                        if drop[1] > 0:
                            self.add_inventory(drop[0], drop[1])
                    self.del_block(block)
                    self.mouse_press += skip + 0.1
                    self.blocktime = time.time()

        m = 8
        dt = min(dt, 0.2)
        for _ in range(m):
            self._update_world(dt / m)

    def _update_world(self, dt):
        speed = Settings.walking_speed if Settings.gamemode == 1 or not self.flying else Settings.flying_speed
        d = dt * speed
        dx, dy, dz = self.get_motion_vector()
        dx, dy, dz = dx * d, dy * d, dz * d
        if not self.flying or Settings.gamemode == 1:
            self.dy -= dt * Settings.gravity
            self.dy = max(self.dy, -50)
            dy += self.dy * dt
        x, y, z = self.position
        lastdy = self.dy
        x, y, z = self.collide((x + dx, y + dy, z + dz), Settings.player_height)
        y = max(y, -80)
        self.position = (x, y, z)
        if y <= -70:
            self.hurt(5, '掉出了这个世界')
        else:
            if self.dy == 0 and lastdy <= -15:
                if lastdy <= -30:
                    self.hurt(-(lastdy + 15) * 19 / 35 + 1, '坠落了')
                else:
                    self.hurt(-(lastdy + 15) * 19 / 35 + 1, '落地过猛')

    def collide(self, position, height):
        pad = 0.25
        p = list(position)
        np = normalize(position)
        for face in Settings.faces:
            for i in range(3):
                if not face[i]:
                    continue
                d = (p[i] - np[i]) * face[i]
                if d < pad:
                    continue
                for dy in range(height):
                    op = list(np)
                    op[1] -= dy
                    op[i] += face[i]
                    if tuple(op) not in self.model.world:
                        continue
                    p[i] -= (d - pad) * face[i]
                    if face in [(0, -1, 0), (0, 1, 0)]:
                        self.dy = 0
                    break
        return tuple(p)

    def world_event_resize(self, width, height):
        if self.reticle:
            self.reticle.delete()
        x, y = self.width // 2, self.height // 2
        n = 10
        self.reticle = pyglet.graphics.vertex_list(4,
            ('v2i', (x - n, y, x + n, y, x, y - n, x, y + n))
        )

    def world_event_mouse_press(self, x, y, button, modifiers):
        if self.exclusive:
            if button == pyglet.window.mouse.LEFT:
                self.mouse_press = time.time()
            elif button == pyglet.window.mouse.RIGHT:
                if block := self.model.hit_test(
                    self.position, self.get_sight_vector()
                )[0]:
                    if choose := blocks[self.model.world[block].name].choose:
                        choose(self, block)

    def world_event_mouse_release(self, x, y, button, modifiers):
        if self.exclusive:
            if button == pyglet.window.mouse.LEFT:
                if self.inventory[self.block][1] > 0:
                    vector = self.get_sight_vector()
                    block, previous = self.model.hit_test(self.position, vector)
                    if (
                        self.blocktime == 0
                        and time.time() - self.mouse_press < 0.2
                        and previous
                        and self.inventory[self.block][0] in blocks
                        and self.put_block(previous, self.inventory[self.block][0])
                    ):
                        if Settings.gamemode != 2:
                            self.inventory[self.block][1] -= 1
                            if self.inventory[self.block][1] <= 0:
                                self.inventory[self.block] = ['', 0]
                self.mouse_press = 0
                self.blocktime = 0
                self.progress = 0
        else:
            self.set_exclusive_mouse(True)

    def world_event_text(self, text):
        if self.matrixon:
            self.script += text

    def world_event_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.close()
        if self.matrixon:
            if symbol == pyglet.window.key.RETURN:
                try:
                    matrixon.run(self.script)
                except:
                    pass
                self.script = ''
                self.matrixon = False
            elif symbol == pyglet.window.key.BACKSPACE:
                self.script = self.script[:-1]
        elif symbol == pyglet.window.key.W:
            self.strafe[0] -= 1
        elif symbol == pyglet.window.key.S:
            self.strafe[0] += 1
        elif symbol == pyglet.window.key.A:
            self.strafe[1] -= 1
        elif symbol == pyglet.window.key.D:
            self.strafe[1] += 1
        elif symbol == pyglet.window.key.B:
            self.set_exclusive_mouse(False)
            self.state = 'builtin_workbench'
            sys.modules['builtin_workbench'].setup()
        elif symbol == pyglet.window.key.TAB:
            if Settings.gamemode == 2:
                self.flying = not self.flying
                self.dy = 0
        elif symbol == pyglet.window.key.SPACE:
            if (Settings.gamemode == 1 or not self.flying) and self.dy == 0:
                self.dy = Settings.jump_speed
        elif symbol == pyglet.window.key.SLASH:
            self.matrixon = True
            self.strafe = [0, 0]
        elif pyglet.window.key._0 <= symbol <= pyglet.window.key._9:
            i = symbol - pyglet.window.key._0 - 1
            self.block = i % 10

    def world_event_key_release(self, symbol, modifiers):
        if not self.matrixon:
            if symbol == pyglet.window.key.W:
                self.strafe[0] += 1
            elif symbol == pyglet.window.key.S:
                self.strafe[0] -= 1
            elif symbol == pyglet.window.key.A:
                self.strafe[1] += 1
            elif symbol == pyglet.window.key.D:
                self.strafe[1] -= 1
            elif symbol == pyglet.window.key.UP:
                if Settings.gamemode == 1 and self.flying:
                    self.dy -= 1
            elif symbol == pyglet.window.key.DOWN:
                if Settings.gamemode == 1 and self.flying:
                    self.dy += 1

    def world_event_mouse_motion(self, x, y, dx, dy):
        if self.exclusive:
            m = 0.15
            x, y = self.rotation
            x, y = x + dx * m, y + dy * m
            y = max(-90, min(90, y))
            self.rotation = (x, y)

    def world_event_draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.clear()
        self.set_3d()
        glColor3d(1, 1, 1)
        self.model.batch.draw()
        self.draw_focused_block()
        glFlush()
        self.set_2d()
        self.draw_reticle()
        self.draw_progress()
        self.draw_inventory()
        self.draw_position()
        self.draw_script()
        self.draw_health()

    def draw_focused_block(self):
        vector = self.get_sight_vector()
        if block := self.model.hit_test(self.position, vector)[0]:
            x, y, z = block
            vertex_data = cube_vertices(x, y, z, 0.51)
            glColor3d(0, 0, 0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', vertex_data))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    def draw_reticle(self):
        glColor3d(0, 0, 0)
        self.reticle.draw(GL_LINES)

    def draw_progress(self):
        glColor3d(1, 1, 1)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f/static',
            (0, self.height - 10, self.width, self.height - 10, self.width, self.height, 0, self.height)))
        glColor3d(0, 0, 0)
        w = self.width * self.progress
        pyglet.graphics.draw(4, GL_QUADS, ('v2f/static',
            (0, self.height - 10, w, self.height - 10, w, self.height, 0, self.height)))

    def draw_inventory(self):
        glColor3f(0.5, 0.5, 0.5)
        startx = (self.width - 440) / 2
        endx = (self.width + 440) / 2
        pyglet.graphics.draw(4, GL_QUADS, ('v2f/static',
            (startx, 5, endx, 5, endx, 49, startx, 49)))
        for i in range(10):
            glColor3f(0.3, 0.3, 0.3)
            pyglet.graphics.draw(4, GL_QUADS, ('v2f/static',
                (startx + 2 + i * 44, 7, startx + 42 + i * 44, 7, startx + 42 + i * 44, 47, startx + 2 + i * 44, 47)))
            if self.block == i:
                glColor3f(0.8, 0.8, 0.8)
                pyglet.graphics.draw(8, GL_LINES, ('v2f/static',
                    (startx + 2 + i * 44, 7, startx + 42 + i * 44, 7, startx + 42 + i * 44, 7, startx + 42 + i * 44, 47, startx + 42 + i * 44, 47,
                     startx + 2 + i * 44, 47, startx + 2 + i * 44, 47, startx + 2 + i * 44, 7)))
            if self.inventory[i][1] > 0:
                glColor3d(1, 1, 1)
                images[self.inventory[i][0]].blit(startx + 4 + i * 44, 9)
                pyglet.text.Label(str(self.inventory[i][1]), font_size=10, color=(0, 0, 0, 255),
                    x=startx + 43 + i * 44, y=6, anchor_x='right', anchor_y='bottom').draw()
                pyglet.text.Label(str(self.inventory[i][1]), font_size=10, color=(255, 255, 255, 255),
                    x=startx + 44 + i * 44, y=7, anchor_x='right', anchor_y='bottom').draw()

    def draw_position(self):
        glColor3f(0.2, 0.2, 0.2)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f/static', (4, self.height - 36, 304, self.height - 36, 304, self.height - 14, 4, self.height - 14)))
        pyglet.text.Label(str(normalize(self.position))[1:-1], font_size=15, color=(255, 255, 255, 255),
            x=5, y=self.height - 15, anchor_x='left', anchor_y='top').draw()

    def draw_script(self):
        if self.matrixon:
            pyglet.text.Label(self.script, font_size=15, color=(0, 0, 0, 255),
                x=4, y=self.height - 31, anchor_x='left', anchor_y='top').draw()
            pyglet.text.Label(self.script, font_size=15, color=(255, 255, 255, 255),
                x=5, y=self.height - 30, anchor_x='left', anchor_y='top').draw()

    def draw_health(self):
        if Settings.gamemode == 1:
            glColor3d(1, 1, 1)
            startx = (self.width - 440) / 2
            di = int(time.time() * 18) % 4
            for i in range(0, 20, 2):
                if self.health > i:
                    if self.health == i + 1:
                        imgname = 'half_heart'
                    else:
                        imgname = 'heart'
                else:
                    imgname = 'empty_heart'
                if self.health <= 5:
                    y = [52, 53, 52, 51][(di + i) % 4]
                else:
                    y = 52
                Settings.images[imgname].blit(startx + i * 9, y)


def setup_fog():
    glEnable(GL_FOG)
    glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.69, 1.0, 1))
    glHint(GL_FOG_HINT, GL_DONT_CARE)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogf(GL_FOG_START, 20.0)
    glFogf(GL_FOG_END, 60.0)

def setup():
    glClearColor(0.5, 0.69, 1.0, 1)
    glEnable(GL_CULL_FACE)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    setup_fog()
