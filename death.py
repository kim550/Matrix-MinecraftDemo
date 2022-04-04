import pyglet
from pyglet.gl import *
import sys

from settings import Settings
import base


class Death(base.Base):
    def __init__(self):
        pass

    def death_event_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.close()
        elif symbol == pyglet.window.key.Q:
            self.position = self.respwan
            self.health = self.max_health
            self.inventory = [['', 0] for i in range(70)]
            self.block = 0
            self.dy = 0
            self.state = 'world'
            sys.modules['world'].setup()

    def death_event_draw(self):
        self.clear()
        pyglet.text.Label(' 你死了！', font_size=80, color=(250, 230, 230, 255), x=self.width / 2, y=self.height - 140,
            anchor_x='center', anchor_y='center').draw()
        pyglet.text.Label('你' + self.hurtcause, font_size=20, color=(250, 230, 230, 255), x=self.width / 2, y=self.height - 340,
            anchor_x='center', anchor_y='center').draw()


def setup():
    glClearColor(0.4, 0.0, 0.0, 0.7)
