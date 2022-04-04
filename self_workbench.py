import pyglet
from pyglet.gl import *
import sys

import base
from blocks import images, blocks
from settings import Settings

class Lattice:
    def __init__(self, block, number):
        self.block = block
        self.number = number
    
    def __repr__(self):
        return f'<{__name__}.Lattice object, block={self.block}>'
    
    def draw(self, x, y):
        glColor3f(0.5, 0.5, 0.5)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f/static', (x, y, x + 44, y, x + 44, y + 44, x, y + 44)))
        glColor3f(0.3, 0.3, 0.3)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f/static', (x + 2, y + 2, x + 42, y  + 2, x + 42, y + 42, x + 2, y + 42)))
        glColor3d(1, 1, 1)
        if self.number > 0:
            images[self.block].blit(x + 4, y + 4)
            pyglet.text.Label(str(self.number), font_size=10, color=(0, 0, 0, 255),
                x=x + 42, y=y + 1, anchor_x='right', anchor_y='bottom').draw()
            pyglet.text.Label(str(self.number), font_size=10, color=(255, 255, 255, 255),
                x=x + 43, y=y + 2, anchor_x='right', anchor_y='bottom').draw()
        if Settings.window.focused_lattice is self:
            glColor3f(0.8, 0.8, 0.8)
            pyglet.graphics.draw(4, GL_LINE_LOOP, ('v2f/static', (x + 2, y + 1, x + 43, y + 1, x + 43, y + 42, x + 2, y + 42)))
        if Settings.window.selected_lattice is self:
            glColor4f(1.0, 1.0, 1.0, 0.4)
            pyglet.graphics.draw(4, GL_QUADS, ('v2f/static', (x, y, x + 44, y, x + 44, y + 44, x, y + 44)))


class SelfWorkbench(base.Base):
    def __init__(self):
        self.lattices = [Lattice('', 0) for _ in range(70)]
        self.recipes = [Lattice('', 0) for _ in range(9)]
        self.target = Lattice('', 0)
        self.focused_lattice = None
        self.selected_lattice = None
    
    def get_lattice(self, mx, my):
        startx = (self.width - 1150) / 2
        x = startx
        y = self.height - 64
        for lattice in self.lattices:
            if x <= mx < x + 44 and y <= my < y + 44:
                return lattice
            x += 44
            if x >= startx + 440:
                x = startx
                y -= 44
        x = startx + 650
        y = (self.height + 44) / 2
        for recipe in self.recipes:
            if x <= mx < x + 44 and y <= my < y + 44:
                return recipe
            x += 44
            if x >= startx + 782:
                x = startx + 650
                y -= 44
        x, y = startx + 890, (self.height - 44) / 2
        if x <= mx < x + 44 and y <= my < y + 44:
            return self.target
    
    def add_lattice(self, block, num):
        for lattice in self.lattices:
            if lattice.block == block:
                lattice.number += num
                return
        for lattice in self.lattices:
            if lattice.number == 0:
                lattice.block = block
                lattice.number = num
                return
    
    def set_focused_lattice(self, lattice):
        self.focused_lattice = lattice
        if self.focused_lattice == self.target:
            self.focused_lattice = None
            if self.target.number > 0:
                n = blocks[self.target.block].recipe.times
                for recipe in self.recipes:
                    recipe.number -= 1
                    if recipe.number <= 0:
                        recipe.block = ''
                        recipe.number = 0
                self.add_lattice(self.target.block, n)
                self.target.block = ''
                self.target.number = 0

    def update_self_workbench(self, dt):
        if nums := list(
            map(lambda l: l.number, filter(lambda l: l.block, self.recipes))
        ):
            recipe = tuple(tuple(self.recipes[i * 3 + j].block for j in range(3)) for i in range(3))
            min_num = min(nums)
            for key, value in blocks.items():
                if value.recipe is not None and value.recipe.valid9(recipe):
                    self.target.block = key
                    self.target.number = min_num * value.recipe.times
                    break

    def self_workbench_event_mouse_press(self, mx, my, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            lattice = self.get_lattice(mx, my)
            if self.selected_lattice is None or (lattice.block not in  ('', self.selected_lattice.block) and self.selected_lattice == lattice):
                self.set_focused_lattice(lattice)
            else:
                lattice.block = self.selected_lattice.block
                lattice.number += 1
                self.selected_lattice.number -= 1
                if self.selected_lattice.number <= 0:
                    self.selected_lattice = None
        elif button == pyglet.window.mouse.RIGHT:
            if self.selected_lattice is None:
                self.selected_lattice = self.get_lattice(mx, my)
                if self.selected_lattice is not None and self.selected_lattice.number <= 0 or self.selected_lattice == self.target:
                    self.selected_lattice = None
            else:
                self.selected_lattice = None

    def self_workbench_event_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.Q:
            for i in range(70):
                self.inventory[i][0] = self.lattices[i].block
                self.inventory[i][1] = self.lattices[i].number
            for recipe in self.recipes:
                self.add_inventory(recipe.block, recipe.number)
            self.state = 'world'
            self.set_exclusive_mouse(True)
            sys.modules['world'].setup()
        elif symbol == pyglet.window.key.ESCAPE:
            self.close()

    def self_workbench_event_draw(self):
        self.clear()
        startx = self.draw_lattices()
        x = startx + 650
        y = (self.height + 44) / 2
        for i in range(9):
            self.recipes[i].draw(x, y)
            x += 44
            if x >= startx + 782:
                x = startx + 650
                y -= 44
        x = startx + 800
        y = self.height / 2
        glColor3f(0.2, 0.2, 0.2)
        pyglet.graphics.draw(7, GL_LINE_LOOP, ('v2f/static',
            (x, y + 10, x + 50, y + 10, x + 50, y + 20, x + 70, y, x + 50, y - 20, x + 50, y - 10, x, y - 10)))
        self.target.draw(startx + 890, (self.height - 44) / 2)
    
    def draw_lattices(self):
        startx = (self.width - 1150) / 2
        x = startx
        y = self.height - 64
        for lattice in self.lattices:
            lattice.draw(x, y)
            x += 44
            if x >= startx + 440:
                x = startx
                y -= 44
        return startx


def setup():
    glClearColor(0.9, 0.9, 0.9, 1.0)
    Settings.window.lattices = [Lattice(*Settings.window.inventory[i]) if i < 10 else Lattice('', 0) for i in range(70)]
    Settings.window.recipes = [Lattice('', 0) for _ in range(9)]
    Settings.window.focused_lattice = None
    Settings.window.selected_lattice = None
