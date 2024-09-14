import sys
from enum import Enum, auto

from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import Vec3, Point3
from panda3d.core import NodePath
from panda3d.core import load_prc_file_data
from panda3d.core import TransparencyAttrib
from direct.interval.IntervalGlobal import Sequence, Func
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock

from cart import CartController, BulletCart
from scene import Scene
from baggage import Baggages
from gui import LevelSelector, Caption


load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    window-title Panda3D Delivery Cart
    filled-wireframe-apply-shader true
    stm-max-views 8
    stm-max-chunk-count 2048""")


class Status(Enum):

    SELECT_LEVEL = auto()
    FADE_CAMERA = auto()
    LOAD_BAGGAGES = auto()
    PLAY = auto()
    GAME_OVER = auto()
    CLEAN_UP = auto()
    START = auto()


class DeliveryCart(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))

        self.debug = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug.node())

        self.scene = Scene()
        self.scene.reparent_to(self.render)

        cart = BulletCart()
        self.controller = CartController(cart)
        self.floater = NodePath('floater')
        self.floater.set_pos(Point3(0, 0, 2))
        self.floater.reparent_to(cart)

        self.camLens.set_fov(90)
        self.cam_initial_pos = Point3(0, 124, 60)
        self.cam_initial_hpr = Point3(124, -124, 0)
        self.camera.set_pos(self.cam_initial_pos)
        self.camera.look_at(self.cam_initial_hpr)
        self.camera.reparent_to(self.render)

        self.baggages = Baggages()
        self.selector = LevelSelector()
        self.caption = Caption()

        self.state = Status.START
        self.cam_faded = False

        self.accept('escape', sys.exit)
        self.accept('d', self.toggle_debug)
        self.taskMgr.add(self.update, 'update')
        # use sort parameter to prevent camera shaking.
        self.taskMgr.add(self.move_camera, "move_camera", sort=25)

    def toggle_debug(self):
        if self.debug.is_hidden():
            self.debug.show()
        else:
            self.debug.hide()

    def fade_camera(self, pos, look_at, duration=2.0):
        """Fade the currently viewed scene to another camera perspective.
            Args:
                pos (Point3): New camera position.
                look_at (NodePath or Point3):  New position that the camera will face.
                duration (float): Fade is done over a period of [duration] seconds.
        """
        self.cam_faded = False

        props = self.win.get_properties()
        size = props.get_size()
        buffer = self.win.make_texture_buffer('tex_buffer', *size)
        buffer.set_clear_color_active(True)
        buffer.set_clear_color((0.5, 0.5, 0.5, 1))

        temp_cam = self.make_camera(buffer)
        temp_cam.node().get_lens().set_fov(90)
        temp_cam.reparent_to(self.render)
        temp_cam.set_pos(pos)
        temp_cam.look_at(look_at)

        card = buffer.get_texture_card()
        card.reparent_to(self.render2d)
        # Screens slowly changes, having afterimage (road).
        card.set_transparency(TransparencyAttrib.M_alpha)
        # Screens quickly changes, having no afterimage.
        # card.set_transparency(TransparencyAttrib.M_multisample)

        Sequence(
            card.colorScaleInterval(duration, 1, 0, blendType='easeInOut'),
            Func(self.camera.set_pos, pos),
            Func(self.camera.look_at, look_at),
            Func(card.remove_node),
            Func(temp_cam.remove_node),
            Func(self.graphicsEngine.remove_window, buffer),
            Func(self.end_fade)
        ).start()

    def end_fade(self):
        self.cam_faded = True

    def clean_up(self):
        self.baggages.clean_up()
        self.selector.selected = None
        self.controller.setup_cart()

    def get_cam_pos(self):
        rel_pos = self.render.get_relative_point(self.controller.cart, Vec3(0, -5, 0))
        pos = Point3(rel_pos.xy, 24)
        return pos

    def move_camera(self, task):
        if self.state == Status.PLAY:
            pos = self.get_cam_pos()
            self.camera.set_pos(pos)
            self.camera.look_at(self.floater)

        return task.cont

    def check_collision(self):
        if self.controller.detect_collision(self.scene.terrain) or \
                self.controller.detect_collision(self.scene.water_surface):
            return True

    def update(self, task):
        dt = globalClock.get_dt()

        match self.state:

            case Status.SELECT_LEVEL:
                if self.selector.appeared and self.selector.selected:
                    self.selector.disappear(wait=0.5)
                    self.state = Status.FADE_CAMERA

            case Status.FADE_CAMERA:
                if not self.selector.appeared:
                    self.fade_camera(self.get_cam_pos(), self.floater)
                    self.state = Status.LOAD_BAGGAGES

            case Status.LOAD_BAGGAGES:
                if self.cam_faded:
                    self.baggages.load(self.selector.selected)
                    self.caption.show('Go!', wait=1.0)
                    self.state = Status.PLAY

            case Status.PLAY:
                self.controller.update(dt)
                self.scene.day_light.update(self.controller.cart)

                if self.check_collision():
                    self.caption.show('Game Over', wait=1.0)
                    self.state = Status.GAME_OVER

            case Status.GAME_OVER:
                if self.caption.ended:
                    self.fade_camera(self.cam_initial_pos, self.cam_initial_hpr)
                    self.state = Status.CLEAN_UP

            case Status.CLEAN_UP:
                if self.cam_faded:
                    self.clean_up()
                    self.state = Status.START

            case Status.START:
                self.selector.appear(wait=0.5)
                self.state = Status.SELECT_LEVEL

        self.scene.update(task.time, self.controller.cart)
        self.world.do_physics(dt)
        return task.cont


if __name__ == '__main__':
    app = DeliveryCart()
    app.run()