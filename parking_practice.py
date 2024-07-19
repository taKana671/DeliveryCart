from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import Vec3
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock

from scene import Scene


class PracticeParking(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()
        self.camera.set_pos(0, -100, 100)
        self.camera.look_at(0, 0, 0)

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))

        self.debug = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug.node())
        self.debug.show()
        self.scene = Scene()

        self.taskMgr.add(self.update, 'update')

    def update(self, task):
        dt = globalClock.get_dt()

        self.world.do_physics(dt)
        return task.cont


if __name__ == '__main__':
    app = PracticeParking()
    app.run()