import pyglet
from pyglet.gl import *

from settings import Settings
import records

import base
import world
import builtin_workbench
import self_workbench
import workbench
import death


imgs = Settings.images
imgs['heart'] = pyglet.image.load('images/heart.png')
imgs['half_heart'] = pyglet.image.load('images/half_heart.png')
imgs['empty_heart'] = pyglet.image.load('images/empty_heart.png')


class Window(world.World, builtin_workbench.BuiltinWorkbench, self_workbench.SelfWorkbench, workbench.Workbench, death.Death):
    def __init__(self, savedata, init=True, *args, **kwargs):
        Settings.window = self
        base.Base.__init__(self, *args, **kwargs)
        world.World.__init__(self, savedata, init)
        builtin_workbench.BuiltinWorkbench.__init__(self)
        self_workbench.SelfWorkbench.__init__(self)
        workbench.Workbench.__init__(self)
        death.Death.__init__(self)

        self.state = 'world'

        pyglet.clock.schedule_interval(self.update, 1.0 / Settings.ticks_per_sec)

    def update(self, dt):
        if self.state == 'world':
            self.update_world(dt)
        elif self.state == 'builtin_workbench':
            self.update_builtin_workbench(dt)
        elif self.state == 'self_workbench':
            self.update_self_workbench(dt)
        elif self.state == 'workbench':
            self.update_workbench(dt)

    def on_resize(self, width, height):
        if self.state == 'world':
            self.world_event_resize(width, height)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == 'world':
            self.world_event_mouse_press(x, y, button, modifiers)
        elif self.state == 'builtin_workbench':
            self.builtin_workbench_event_mouse_press(x, y, button, modifiers)
        elif self.state == 'self_workbench':
            self.self_workbench_event_mouse_press(x, y, button, modifiers)
        elif self.state == 'workbench':
            self.workbench_event_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.state == 'world':
            self.world_event_mouse_release(x, y, button, modifiers)

    def on_text(self, text):
        if self.state == 'world':
            self.world_event_text(text)

    def on_key_press(self, symbol, modifiers):
        if self.state == 'world':
            self.world_event_key_press(symbol, modifiers)
        elif self.state == 'builtin_workbench':
            self.builtin_workbench_event_key_press(symbol, modifiers)
        elif self.state == 'self_workbench':
            self.self_workbench_event_key_press(symbol, modifiers)
        elif self.state == 'workbench':
            self.workbench_event_key_press(symbol, modifiers)
        elif self.state == 'death':
            self.death_event_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        if self.state == 'world':
            self.world_event_key_release(symbol, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.state == 'world':
            self.world_event_mouse_motion(x, y, dx, dy)

    def on_draw(self):
        if self.state == 'world':
            self.world_event_draw()
        elif self.state == 'builtin_workbench':
            self.builtin_workbench_event_draw()
        elif self.state == 'self_workbench':
            self.self_workbench_event_draw()
        elif self.state == 'workbench':
            self.workbench_event_draw()
        elif self.state == 'death':
            self.death_event_draw()


if __name__ == '__main__':
    data = records.ask_open()

    if data == {}:
        raise SystemExit

    Settings.gamemode = data['savedata'].gamemode
    win = Window(data['savedata'], caption='The Matrix', resizable=True, fullscreen=True)
    win.set_exclusive_mouse(True)

    world.setup()

    pyglet.app.run()

    records.save_record(data['name'])
