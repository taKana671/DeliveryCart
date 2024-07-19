import sys
from panda3d.core import LColor, Vec3, Point3, BitMask32
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import TransformState

from panda3d.bullet import BulletWorld, BulletDebugNode, BulletRigidBodyNode
from panda3d.bullet import BulletPlaneShape, BulletBoxShape
from panda3d.bullet import BulletVehicle
from panda3d.bullet import ZUp

from direct.showbase.ShowBase import ShowBase
from direct.showbase.InputStateGlobal import inputState
from direct.showbase.ShowBaseGlobal import globalClock


class Game(ShowBase):

    def __init__(self):
        super().__init__()
        # self.set_background_color(LColor(0.1, 0.1, 0.8, 1))
        self.set_frame_rate_meter(True)

        self.camera.set_pos(0, -100, 100)
        self.camera.look_at(0, 0, 0)

        ambient_light = AmbientLight('ambient_light')
        ambient_light.set_color(LColor(0.5, 0.5, 0.5, 1))
        ambient_np = self.render.attach_new_node(ambient_light)

        direct_light = DirectionalLight('directional_light')
        direct_light.set_direction(Vec3(1, 1, -1))
        direct_light.set_color(LColor(0.7, 0.7, 0.7, 1))
        direct_np = self.render.attach_new_node(direct_light)

        self.render.clear_light()
        self.render.set_light(ambient_np)
        self.render.set_light(direct_np)

        self.accept('escape', sys.exit)
        self.accept('r', self.reset)
        self.accept('f1', self.toggle_wireframe)
        self.accept('f2', self.toggle_texture)
        self.accept('f3', self.toggle_debug)
        self.accept('f5', self.screen_shot)

        inputState.watch_with_modifiers('forward', 'w')
        inputState.watch_with_modifiers('left', 'a')
        inputState.watch_with_modifiers('reverse', 's')
        inputState.watch_with_modifiers('right', 'd')
        inputState.watch_with_modifiers('turn_left', 'q')
        inputState.watch_with_modifiers('turn_right', 'e')

        self.taskMgr.add(self.update, 'update')
        self.setup()

    def reset(self):
        self.world = None
        self.world_np.remove_node()
        self.setup()

    def toggle_debug(self):
        if self.debug_nd.is_hidden():
            self.debug_nd.show()
        else:
            self.debug_nd.hide()

    def screen_shot(self):
        self.screenshot('bullet')

    def setup(self):
        self.world_np = self.render.attach_new_node('world')
        self.debug_nd = self.world_np.attach_new_node(BulletDebugNode('debug'))
        self.debug_nd.show()

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))
        self.world.set_debug_node(self.debug_nd.node())

        # plane
        shape = BulletPlaneShape(Vec3(0, 0, 1), 0)
        np = self.world_np.attach_new_node(BulletRigidBodyNode('Ground'))
        np.node().add_shape(shape)
        np.set_pos(Point3(0, 0, -1))
        np.set_collide_mask(BitMask32.all_on())
        self.world.attach(np.node())

        # chassis
        shape = BulletBoxShape(Vec3(0.6, 1.4, 0.5))
        ts = TransformState.make_pos(Point3(0, 0, 0.5))
        np = self.world_np.attach_new_node(BulletRigidBodyNode('vehicle'))
        np.node().add_shape(shape, ts)
        np.set_pos(Point3(0, 20, 1))
        np.node().set_mass(800)
        np.node().set_deactivation_enabled(False)
        self.world.attach(np.node())

        # vihecle
        self.vehicle = BulletVehicle(self.world, np.node())
        self.vehicle.set_coordinate_system(ZUp)
        self.world.attach_vehicle(self.vehicle)
        self.yugo_np = self.loader.load_model('models/yugo/yugo.egg')
        self.yugo_np.reparent_to(np)

        # *************************************************
        # right front wheel
        np = self.loader.load_model('models/yugo/yugotireR.egg')
        np.reparent_to(self.world_np)
        self.add_wheel(Point3(0.7, 1.05, 0.3), True, np)
        # import pdb; pdb.set_trace()

        # *************************************************
        # left front wheel
        np = self.loader.load_model('models/yugo/yugotireL.egg')
        np.reparent_to(self.world_np)
        self.add_wheel(Point3(-0.7, 1.05, 0.3), True, np)

        # *************************************************
        # right rear wheel
        np = self.loader.load_model('models/yugo/yugotireR.egg')
        np.reparent_to(self.world_np)
        self.add_wheel(Point3(0.7, -1.05, 0.3), False, np)

        # *************************************************
        # left rear wheel
        np = self.loader.load_model('models/yugo/yugotireL.egg')
        np.reparent_to(self.world_np)
        self.add_wheel(Point3(-0.7, -1.05, 0.3), False, np)

        # *************************************************

        self.steering = 0.0             # degree
        self.steering_clamp = 45.0      # degree
        self.steering_increment = 120.0  # degree per second

    def process_input(self, dt):
        engine_force = 0.0
        brake_force = 0.0

        if inputState.is_set('forward'):
            engine_force = 1000.0
            brake_force = 0.0

        if inputState.is_set('reverse'):
            # engine_force = 0
            engine_force = -1000.0
            brake_force = 100.0

        if inputState.is_set('turn_left'):
            self.steering += dt * self.steering_increment
            self.steering = min(self.steering, self.steering_clamp)

        if inputState.isSet('turn_right'):
            self.steering -= dt * self.steering_increment
            self.steering = max(self.steering, -self.steering_clamp)

        # Apply steering to front wheels
        self.vehicle.set_steering_value(self.steering, 0)
        self.vehicle.set_steering_value(self.steering, 1)

        # Apply engine and brake to rear wheels
        self.vehicle.apply_engine_force(engine_force, 2)
        self.vehicle.apply_engine_force(engine_force, 3)
        self.vehicle.set_brake(brake_force, 2)
        self.vehicle.set_brake(brake_force, 3)

    def add_wheel(self, pos, front, np):
        wheel = self.vehicle.create_wheel()

        wheel.set_node(np.node())
        wheel.set_chassis_connection_point_cs(pos)
        wheel.set_front_wheel(front)

        wheel.set_wheel_direction_cs(Vec3(0, 0, -1))
        wheel.set_wheel_axle_cs(Vec3(1, 0, 0))
        wheel.set_wheel_radius(0.25)
        wheel.set_max_suspension_travel_cm(40.0)
        
        wheel.set_suspension_stiffness(40.0)
        wheel.set_wheels_damping_relaxation(2.3)
        wheel.set_wheels_damping_compression(4.4)
        wheel.set_friction_slip(100.0)
        wheel.set_roll_influence(0.1)
        # import pdb; pdb.set_trace()

    def update(self, task):
        dt = globalClock.getDt()
        self.process_input(dt)
        self.world.do_physics(dt)
        # self.world.do_physics(dt, 10, 0.008)

        # print(self.vehicle.get_wheel(0).get_raycast_info().is_in_contact())
        # print(self.vehicle.get_wheel(0).get_raycast_info().get_contact_point_ws())
        # print(self.vehicle.get_chassis().is_kinematic())

        return task.cont


if __name__ == '__main__':
    game = Game()
    game.run()
    


