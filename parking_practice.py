import sys

from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import Vec3, Point3, NodePath, Vec2
from panda3d.core import load_prc_file_data

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock

from car import Car
from my_car import Cart
from scene import Scene


load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    window-title Panda3D Practice Parking
    filled-wireframe-apply-shader true
    stm-max-views 8
    stm-max-chunk-count 2048""")


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
        self.scene.reparent_to(self.render)

        # ********************************************************
        # self.car = Car(self.world)
        # self.car = Cart(self.world)
        # self.car.reparent_to(self.render)

        # self.floater = NodePath('floater')
        # self.floater.set_pos(Point3(0, 0, 2))
        # self.floater.reparent_to(self.car)
        # self.camera.set_pos(self.car.get_pos() + Vec3(0, -10, 5))
        # self.camera.reparent_to(self.car)
        # self.camera.look_at(self.floater)
        # self.camera.look_at(self.car)
        # ********************************************************

        # self.camera_root = NodePath('camera_root')
        # self.camera.reparent_to(self.camera_root)
        # self.camera_root.set_pos(-128, -128, 100)
        # self.camera_root.reparent_to(self.render)
        self.camera.reparent_to(self.render)
        self.camera.set_pos(-128, -128, 100)
        self.camera.look_at(0, 0, 0)

        self.dragging = False
        self.before_mouse_pos = None

        self.accept('escape', sys.exit)
        self.accept('d', self.toggle_debug)
        self.accept('mouse1', self.mouse_click)
        self.accept('mouse1-up', self.mouse_release)

        self.taskMgr.add(self.update, 'update')

    def toggle_debug(self):
        if self.debug.is_hidden():
            self.debug.show()
        else:
            self.debug.hide()

    def mouse_click(self):
        self.dragging = True
        self.dragging_start_time = globalClock.get_frame_time()

    def mouse_release(self):
        self.dragging = False
        self.before_mouse_pos = None

    def rotate_camera(self, mouse_pos, dt):
        if self.before_mouse_pos:
            angle = Vec3()

            if (delta := mouse_pos.x - self.before_mouse_pos.x) < 0:
                angle.x -= 90
            elif delta > 0:
                angle.x += 90

            if (delta := mouse_pos.y - self.before_mouse_pos.y) < -0.01:  # 0
                angle.y += 90
            elif delta > 0.01:  # 0
                angle.y -= 90

            angle *= dt
            self.camera.set_hpr(self.camera.get_hpr() + angle)

        self.before_mouse_pos = Vec2(mouse_pos.x, mouse_pos.y)

    def update(self, task):
        dt = globalClock.get_dt()
        # self.car.control(dt)

        if self.mouseWatcherNode.has_mouse():
            mouse_pos = self.mouseWatcherNode.get_mouse()

            if self.dragging:
                if globalClock.get_frame_time() - self.dragging_start_time >= 0.2:
                    self.rotate_camera(mouse_pos, dt)

        self.scene.wave(task.time)

        self.world.do_physics(dt)
        return task.cont



if __name__ == '__main__':
    app = PracticeParking()
    app.run()