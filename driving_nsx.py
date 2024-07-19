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

        self.camera.set_pos(0, -100, 10)
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
        np = self.world_np.attach_new_node(BulletRigidBodyNode('vehicle'))

        # This model is made back to front.
        self.nsx_np = self.loader.load_model('models/carnsx/carnsx.egg')
        end, tip = self.nsx_np.get_tight_bounds()
        size = tip - end
        size.z -= 0.3
        # import pdb; pdb.set_trace()
        shape = BulletBoxShape(size / 2)
        ts = TransformState.make_pos(Point3(0, 0.5, 0.8))

        np.node().add_shape(shape, ts)
        # shape = BulletBoxShape(Vec3(0.6, 1.4, 0.5))
        # ts = TransformState.make_pos(Point3(0, 0, 0.5))
        # np.node().add_shape(shape, ts)
        # np.set_pos(Point3(0, 20, 1))
        np.set_pos(Point3(0, 20, 0.5))
        np.node().set_mass(800)
        np.node().set_deactivation_enabled(False)
        self.world.attach(np.node())

        # vihecle
        self.vehicle = BulletVehicle(self.world, np.node())
        self.vehicle.set_coordinate_system(ZUp)
        self.world.attach_vehicle(self.vehicle)
        # self.nsx_np = self.loader.load_model('models/carnsx/carnsx.egg')
        self.nsx_np.reparent_to(np)
        # self.nsx_np.set_h(180)

        # body = self.nsx_np.get_children()[1]
        parts = self.nsx_np.get_children()

        body_parts = parts[1].get_children()
        self.rf_wheel = body_parts[5]
        # import pdb; pdb.set_trace()
        # self.lf_wheel = body_parts[-1] not this

        # ************************************************
        # (Pdb) print(self.nsx_np.get_children())
        # render/world/vehicle/carnsx.egg/groundPlane_transform
        # render/world/vehicle/carnsx.egg/body
        # render/world/vehicle/carnsx.egg/B_loc
        # render/world/vehicle/carnsx.egg/FL_loc
        # render/world/vehicle/carnsx.egg/FR_loc
        # render/world/vehicle/carnsx.egg/B_effect
        # render/world/vehicle/carnsx.egg/F_effect
        # ************************************************

        # ************************************************
        # (Pdb) print(body.get_children())
        # render/world/vehicle/carnsx.egg/body/body
        # render/world/vehicle/carnsx.egg/body/polySurface2
        # render/world/vehicle/carnsx.egg/body/polySurface1
        # render/world/vehicle/carnsx.egg/body/F_plate
        # render/world/vehicle/carnsx.egg/body/R_plate
        # render/world/vehicle/carnsx.egg/body/FL_wheel
        # render/world/vehicle/carnsx.egg/body/FL_wheel1
        # render/world/vehicle/carnsx.egg/body/FL_wheel2
        # render/world/vehicle/carnsx.egg/body/FL_wheel3
        # ************************************************
        # import pdb; pdb.set_trace()

        # right front wheel
        # np = self.loader.load_model('models/yugo/yugotireR.egg')
        # np.reparent_to(self.world_np)
        # self.add_wheel(Point3(0.7, 1.05, 0.3), True, np)

        # np = body.get_children()[5]
        # np = parts[4]
        np = body_parts[5]
        # import pdb; pdb.set_trace()
        np.remove_node()
        np = self.loader.load_model('models/carnsx/tire_fl.egg')
        # pivot = np.get_bounds().get_center()
        # end, tip = np.get_tight_bounds()
        # pivot = (tip - end) / 2
        # new_np = self.world_np.attach_new_node('center')
        # new_np.set_pos(pivot)
        # np.reparent_to(new_np)

        # import pdb; pdb.set_trace()
        # np = self.loader.load_model('models/yugo/yugotireR.egg')
        np.reparent_to(self.world_np)
        # self.add_wheel(Point3(-1., 3, 0.8), True, np)
        # self.add_wheel(Point3(0, -2.72002, 0), True, np)
        self.add_wheel(Point3(0.7, -1.05, 0.7), True, np)
        # self.add_wheel(Point3(-1.01183, -2.72002, 0.7), True, np)
   
        # *************************************************

        # left front wheel
        # np = self.loader.load_model('models/yugo/yugotireL.egg')
        # np.reparent_to(self.world_np)
        # self.add_wheel(Point3(-0.7, 1.05, 0.3), True, np)

        # np = body.get_children()[7]
        # np = parts[3]
        np = body_parts[7]
        # np.reparent_to(self.world_np)
        # self.add_wheel(Point3(0.981367, -2.72002, 0), True, np)
        # ★self.add_wheel(Point3(-1.01183, -2.72002, 0), True, np)
        self.add_wheel(Point3(-0.7, -1.05, 0.7), True, np)

        # *************************************************

        # right rear wheel
        # np = self.loader.load_model('models/yugo/yugotireR.egg')
        # np.reparent_to(self.world_np)
        # self.add_wheel(Point3(0.7, -1.05, 0.3), False, np)

        # np = body.get_children()[5]
        np = parts[4]
        # np = body_parts[-2]
        np.reparent_to(self.world_np)
        # self.add_wheel(Point3(-1.01183, 2.72002, 0), False, np)
        # ★self.add_wheel(Point3(0.981367, 2.72002, 0), False, np)
        self.add_wheel(Point3(0.7, 1.8, 0.7), False, np)

        # *************************************************

        # left rear wheel
        # np = self.loader.load_model('models/yugo/yugotireL.egg')
        # np.reparent_to(self.world_np)
        # self.add_wheel(Point3(-0.7, -1.05, 0.3), False, np)

        # np = body.get_children()[7]
        np = parts[3]
        # np = body_parts[-1]
        np.reparent_to(self.world_np)
        # self.add_wheel(Point3(0.981367, 2.72002, 0), False, np)
        # ★self.add_wheel(Point3(-1.01183, 2.72002, 0), False, np)
        self.add_wheel(Point3(-0.7, 1.8, 0.7), False, np)

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

        # if inputState.is_set('turn_left'):
        if inputState.isSet('turn_right'):
            self.steering += dt * self.steering_increment
            self.steering = min(self.steering, self.steering_clamp)

        # if inputState.isSet('turn_right'):
        if inputState.is_set('turn_left'):
            self.steering -= dt * self.steering_increment
            self.steering = max(self.steering, -self.steering_clamp)

            # self.rf_wheel.set_h(45)
            # import pdb; pdb.set_trace()

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
