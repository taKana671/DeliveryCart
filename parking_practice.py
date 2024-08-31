import sys
import math
from enum import Enum, auto


from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import Vec3, Point3, NodePath, Vec2, BitMask32, LColor
from panda3d.core import load_prc_file_data

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock

from panda3d.core import TransparencyAttrib, CardMaker
from direct.interval.IntervalGlobal import Sequence, Func, Wait

from cart import CartController, BulletCart
from scene import Scene
from cart_baggage import Baggages
from level_select_frame import SelectorFrame


load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    window-title Panda3D Practice Parking
    filled-wireframe-apply-shader true
    stm-max-views 8
    stm-max-chunk-count 2048""")


class Status(Enum):
    
    SHOW_SELECTOR = auto()
    SELECT_LEVEL = auto()
    PLAY = auto()
    SETUP_GAME = auto()
    START = auto()



class PracticeParking(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))

        self.debug = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug.node())
        # self.debug.show()

        self.scene = Scene(self.world)
        self.scene.reparent_to(self.render)

        cart = BulletCart()
        self.cart_controller = CartController(cart)
        self.floater = NodePath('floater')
        self.floater.set_pos(Point3(0, 0, 2))
        self.floater.reparent_to(cart)

        self.camLens.set_fov(90)
        self.camera.set_pos(Point3(0, 124, 60))
        self.camera.look_at(Point3(124, -124, 0))

        # self.camera.set_pos(Vec3(0, -5, 3))
        # self.camera.set_pos(Vec3(5, 0, 3))
        # self.camera.reparent_to(cart.board)
        # self.camera.look_at(self.floater)

        self.baggages = Baggages()
        self.selector_frame = SelectorFrame()
        # self.level_selector.reparent_to(self.aspect2d)
        self.screen = Screen()

        self.state = Status.START
        self.dragging = False
        self.before_mouse_pos = None

        self.accept('escape', sys.exit)
        self.accept('d', self.toggle_debug)
        self.accept('mouse1', self.mouse_click)
        self.accept('mouse1-up', self.mouse_release)

        self.accept('l', self.load_baggages)
        self.accept('m', self.move_camera)

        self.taskMgr.add(self.update, 'update')

    def load_baggages(self):
        self.baggages.load(2)

    def move_camera(self):
        self.state = True

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
        # self.cart_controller.control(dt)

        ########################################################################################
        # option 1
        # if not self.state:
        #     if self.camera.get_z(self.render) < 23:
        #         self.state = True
        #         pos = self.camera.get_pos(self.render)
        #         hpr = self.camera.get_hpr(self.render)

        #         self.camera.reparent_to(self.render)
        #         self.camera.set_pos_hpr(pos, hpr)
        # else:
        #     pos = self.render.get_relative_point(self.cart_controller.cart, Vec3(0, -5, 0))
        #     # maybe prevent jitter?
        #     self.camera.set_x(round(pos.x, 3))
        #     self.camera.set_y(round(pos.y, 3))
        #     # self.camera.set_x(pos.x)
        #     # self.camera.set_y(pos.y)
        #     self.camera.look_at(self.floater)
        #########################################################################################

        match self.state:
            case Status.SHOW_SELECTOR:
                if not self.selector_frame.appeared:
                    self.selector_frame.appear(self.change_status, Status.SELECT_LEVEL)

            case Status.SELECT_LEVEL:
                if self.selector_frame.selected_level:
                    self.selector_frame.disappear(self.change_status, Status.SETUP_GAME)

            case Status.SETUP_GAME:
                # self.screen.switch(self.setup_game, Status.PLAY)
                props = self.win.get_properties()
                size = props.get_size()
                buffer = self.win.make_texture_buffer(
                    'tex_buffer', *size)
                # buffer = self.win.make_texture_buffer(
                #     'tex_buffer', self.win.get_x_size(), self.win.get_y_size())

                buffer.set_clear_color_active(True)
                # buffer.set_clear_depth_active(True)
                # col = self.get_background_color()
                # import pdb; pdb.set_trace()
                # col[3] = 1
                buffer.set_clear_color((0.5, 0.5, 0.5, 1))
                # buffer.set_clear_color(col)
                # buffer.set_clear_depth(1.0)
                cam2 = self.make_camera(buffer)
                cam2.node().get_lens().set_fov(90)
                cam2.reparent_to(self.cart_controller.cart.board)
                # cam2.reparent_to(self.render)
                cam2.set_pos(Vec3(0, -5, 3))
                cam2.look_at(self.floater)

                # cam2.reparent_to(self.render)
                # cam2.set_pos(Point3(0, 124, 60))
                # cam2.look_at(Point3(124, -124, 0))

                # cm = CardMaker('display')
                # cm.set_frame(-1, 1, -1, 1)
                # cm.set_uv_range(buffer.get_texture())
                card = buffer.get_texture_card()
                card.reparent_to(self.render2d)
                # card = self.render2d.attach_new_node(cm.generate())
                card.set_transparency(TransparencyAttrib.M_alpha)

                # card.set_texture(buffer.get_texture())

                Sequence(
                    card.colorScaleInterval(4, 1, 0),
                    Func(self.setup_game),
                    Func(card.remove_node),
                    Func(cam2.remove_node),
                    Func(self.graphicsEngine.remove_window, buffer)
                ).start()

                self.state = Status.PLAY

                # if self.level_selector.selected_level:

                    # self.state = Status.PLAY
                    # import pdb; pdb.set_trace()
                    # self.level_selector.scaleInterval(1, Vec3(0.01)).start()
                    # self.level_selector.hprInterval(0.5, Vec3(0, 90, 0)).start()
                    # self.level_selector.posInterval(1, Point3(0, -1, 1.5)).start()



                    # self.screen.fade_in(self.change_status, Status.SETUP_GAME)
                    # # self.level_selector.detach_node()
                    # cm = CardMaker('card')
                    # cm.set_frame_fullscreen_quad()

                    # self.background = NodePath(cm.generate())
                    # self.background.reparent_to(self.render2d)
                    # # self.background = self.render2d.attach_new_node(cm.generate())
                    # self.background.set_transparency(1)
                    # self.background.set_color(1, 1, 1, 0)
                    # # Sequence(
                    # #     self.background.colorInterval(1, (1, 1, 1, 1)),
                    # #     Func(self.setup_game),
                    # #     self.background.colorInterval(1, (1, 1, 1, 0)),
                    # # ).start()
                    
                    # self.background.colorInterval(3, (1, 1, 1, 1)).start()

           
            
            case Status.PLAY:
                if self.mouseWatcherNode.has_mouse():
                    mouse_pos = self.mouseWatcherNode.get_mouse()

                    if self.dragging:
                        if globalClock.get_frame_time() - self.dragging_start_time >= 0.2:
                            self.rotate_camera(mouse_pos, dt)

            case _:
                self.state = Status.SHOW_SELECTOR
                # self.level_selector.appear()
                # self.level_selector.posInterval(1, Point3(0, -1, 0.7)).start()


        self.scene.water_surface.wave(task.time)
        # self.scene.day_light.update(self.cart_controller.cart)

        self.world.do_physics(dt)
        return task.cont

    def change_status(self, status):
        self.state = status


    # def setup_game(self, status):
    def setup_game(self):
        self.camera.set_pos(Vec3(0, -5, 3))
        # self.camera.set_pos(Vec3(5, 0, 3))
        self.camera.reparent_to(self.cart_controller.cart.board)
        self.camera.look_at(self.floater)
        # self.change_status(status)



class Screen(NodePath):

    def __init__(self):
        cm = CardMaker('card')
        cm.set_frame_fullscreen_quad()
        super().__init__(cm.generate())
        # self.screen = NodePath(cm.generate())
        self.set_transparency(1)
        self.color_start = LColor(1, 1, 1, 0)
        self.color_end = LColor(1, 1, 1, 1)

        self.set_color(self.color_start)

    def switch(self, func, *args, **kwargs):
        self.reparent_to(base.render2d)
        Sequence(
            Wait(0.5),
            self.colorInterval(0.5, self.color_end),
            Func(func, *args, **kwargs),
            self.colorInterval(0.5, self.color_start),
            Func(self.detach_node)
        ).start()

    # def __call__(self, func, duration=1, *args, **kwargs):
    #     self.reparent_to(base.render2d)
    #     Sequence(
    #         Wait(0.5),
    #         self.colorInterval(duration, self.color_end),
    #         Func(func, *args, **kwargs),
    #         self.colorInterval(duration, self.color_start),
    #         Func(lambda: self.detach_node())
    #     ).start()

    # def fade_in(self, callback, *args, **kwargs):
    #     self.reparent_to(base.render2d)
    #     Sequence(
    #         Wait(1),
    #         self.colorInterval(1, self.color_end),
    #         Func(callback, *args, **kwargs)
    #     ).start()

    # def fade_out(self, callback, *args, **kwargs):
    #     # self.reparent_to(base.render2d)
    #     Sequence(
    #         Wait(1),
    #         self.colorInterval(1, self.color_end),
    #         Func(callback, *args, **kwargs),
    #         Func(self.detach_node)
    #     ).start()





if __name__ == '__main__':
    app = PracticeParking()
    app.run()