from panda3d.bullet import BulletBoxShape, ZUp
from panda3d.bullet import BulletRigidBodyNode, BulletVehicle
from panda3d.core import NodePath
from panda3d.core import Vec3, Point3, TransformState, BitMask32
from direct.showbase.InputStateGlobal import inputState


class Car(NodePath):

    def __init__(self, world):
        super().__init__(BulletRigidBodyNode('vehicle'))
        self.world = world
        self.setup()

        inputState.watch_with_modifiers('forward', 'w')
        # inputState.watch_with_modifiers('left', 'a')
        inputState.watch_with_modifiers('reverse', 's')
        # inputState.watch_with_modifiers('right', 'd')
        inputState.watch_with_modifiers('turn_left', 'q')
        inputState.watch_with_modifiers('turn_right', 'e')

    def setup(self):
        # chassis
        shape = BulletBoxShape(Vec3(0.6, 1.4, 0.5))
        ts = TransformState.make_pos(Point3(0, 0, 0.5))
        self.node().add_shape(shape, ts)
        self.set_pos(Point3(0, -10, 1))
        self.node().set_mass(800)
        self.node().set_deactivation_enabled(False)
        # np.set_collide_mask(BitMask32.bit(1))
        self.world.attach(self.node())

        # vihecle
        self.vehicle = BulletVehicle(self.world, self.node())
        self.vehicle.set_coordinate_system(ZUp)
        self.world.attach_vehicle(self.vehicle)
        self.model = base.loader.load_model('models/yugo/yugo.egg')
        self.model.reparent_to(self)

        # wheel
        r_tire = 'models/yugo/yugotireR.egg'
        l_tire = 'models/yugo/yugotireL.egg'
        wheels = [
            (Point3(0.7, 1.05, 0.3), True, r_tire),
            (Point3(-0.7, 1.05, 0.3), True, l_tire),
            (Point3(0.7, -1.05, 0.3), False, r_tire),
            (Point3(-0.7, -1.05, 0.3), False, l_tire),
        ]

        for pos, front, path in wheels:
            np = base.loader.load_model(path)
            np.reparent_to(self)
            self.add_wheel(pos, front, np)

        self.steering = 0.0              # degree
        self.steering_clamp = 45.0       # degree
        self.steering_increment = 120.0  # degree per second

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

    def control(self, dt):
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
