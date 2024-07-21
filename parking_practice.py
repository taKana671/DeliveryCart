import sys

from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import Vec3, Point3, NodePath

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock

from car import Car
from my_car import Cart
from scene import Scene


class PracticeParking(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))

        self.debug = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug.node())
        self.debug.show()
        self.scene = Scene(self.world)
        # self.car = Car(self.world)
        self.car = Cart(self.world)
        self.car.reparent_to(self.render)

        self.floater = NodePath('floater')
        self.floater.set_pos(Point3(0, 0, 2))
        self.floater.reparent_to(self.car)

        self.camera.set_pos(self.car.get_pos() + Vec3(0, -10, 3))
        # self.camera.look_at(0, 0, 0)
        # self.camera.set_pos(0, -10, 3)
        # self.camera.reparent_to(self.car)
        self.camera.look_at(self.floater)

        self.accept('escape', sys.exit)
        self.accept('d', self.toggle_debug)
        self.taskMgr.add(self.update, 'update')

    def toggle_debug(self):
        if self.debug.is_hidden():
            self.debug.show()
        else:
            self.debug.hide()

    def update(self, task):
        dt = globalClock.get_dt()
        # self.process_input(dt)
        self.car.control(dt)

        self.world.do_physics(dt)
        return task.cont



if __name__ == '__main__':
    app = PracticeParking()
    app.run()