from enum import Enum, auto

from panda3d.bullet import BulletBoxShape, ZUp, BulletConvexHullShape
from panda3d.bullet import BulletRigidBodyNode, BulletVehicle
from panda3d.core import NodePath
from panda3d.core import Vec3, Point3, TransformState, BitMask32, LColor
from direct.showbase.InputStateGlobal import inputState

from shapes import CubeModel, CylinderModel


class Wheels(Enum):

    front_right = auto()
    front_left = auto()
    back_right = auto()
    back_left = auto()


class Status(Enum):

    TURN_LEFT = auto()
    TURN_RIGHT = auto()
    STOP_TURN = auto()
    ACCELERATE = auto()
    DECELERATE = auto()
    BACK = auto()


class BulletCart(NodePath):

    def __init__(self, pos, hpr):
        super().__init__(BulletRigidBodyNode('bullet_cart'))
        self.create_cart()
        self.create_wheels()
        self.set_collide_mask(BitMask32.bit(1))
        self.set_pos_hpr(pos, hpr)
        # self.set_pos(pos)
        self.node().set_mass(800)
        self.node().set_deactivation_enabled(False)

    def create_cart(self):
        model = CubeModel(width=2, depth=4, height=0.5, segs_w=2, segs_d=4).create()
        pos = Point3(0, 0, 1)
        model.set_name('cart')
        model.set_pos(pos)

        end, tip = model.get_tight_bounds()
        shape = BulletBoxShape((tip - end) / 2)
        self.node().add_shape(shape, TransformState.make_pos(pos))

        tex = base.loader.loadTexture('textures/board.jpg')
        model.set_texture(tex)
        model.reparent_to(self)

    def create_wheels(self):
        wheel_pos = {
            Wheels.front_right: Point3(0.75, 1.5, 0.5),
            Wheels.front_left: Point3(-1, 1.5, 0.5),
            Wheels.back_right: Point3(0.75, -1.5, 0.5),
            Wheels.back_left: Point3(-1, -1.5, 0.5),
        }

        tex = base.loader.loadTexture('textures/metalboard.jpg')
        model_maker = CylinderModel(radius=0.25, height=0.25)

        for wh, pos in wheel_pos.items():
            model = model_maker.create()
            model.set_pos_hpr(pos, Vec3(90, 90, 0))
            model.set_texture(tex)

            # shift the center.
            pivot = model.get_bounds().get_center()
            new_np = self.attach_new_node(wh.name)
            new_np.set_pos(pivot)
            model.wrt_reparent_to(new_np)


class Cart:

    def __init__(self, world, pos, hpr):
        self.world = world
        self.model = BulletCart(pos, hpr)
        self.model.reparent_to(base.render)
        self.world.attach(self.model.node())

        self.setup()
        self.setup_key()

        self.steering_state = None
        self.driving_state = None

    def setup_key(self):
        base.accept('q', self.turn, [Status.TURN_LEFT])
        base.accept('q-up', self.turn, [Status.STOP_TURN])
        base.accept('e', self.turn, [Status.TURN_RIGHT])
        base.accept('e-up', self.turn, [Status.STOP_TURN])
        base.accept('w', self.accelerate, [Status.ACCELERATE])
        base.accept('w-up', self.accelerate, [Status.DECELERATE])
        base.accept('s', self.accelerate, [Status.BACK])
        base.accept('s-up', self.accelerate, [Status.DECELERATE])

    def setup(self):
        # vehicle
        self.vehicle = BulletVehicle(self.world, self.model.node())
        self.vehicle.set_coordinate_system(ZUp)
        self.world.attach_vehicle(self.vehicle)

        for wh in Wheels:
            np = self.model.find(wh.name)
            pos = np.get_pos()
            front = wh.name.startswith('front')
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

    def turn(self, state):
        self.steering_state = state

    def accelerate(self, state):
        self.driving_state = state

    def get_steering_clamp(self):
        match speed := abs(self.vehicle.get_current_speed_km_hour()):

            case speed if speed > 50:
                steering_clamp = self.steering_clamp * 0.25

            case speed if speed > 40:
                steering_clamp = self.steering_clamp * 0.5

            case speed if speed > 30:
                steering_clamp = self.steering_clamp * 0.75

            case _:
                steering_clamp = self.steering_clamp

        print('steering_clamp', steering_clamp, 'speed', speed)
        return steering_clamp

    def turn_left(self, dt, min_value):
        self.steering += dt * self.steering_increment
        self.steering = min(self.steering, min_value)

    def turn_right(self, dt, max_value):
        self.steering -= dt * self.steering_increment
        self.steering = max(self.steering, max_value)

    def steer(self, dt):
        match self.steering_state:

            case Status.TURN_LEFT:
                steering_clamp = self.get_steering_clamp()
                self.turn_left(dt, steering_clamp)

            case Status.TURN_RIGHT:
                steering_clamp = self.get_steering_clamp()
                self.turn_right(dt, -steering_clamp)

            case Status.STOP_TURN:
                if self.steering != 0:
                    if sum(self.vehicle.get_wheel(i).get_engine_force() for i in (2, 3)) != 0:
                        if self.steering > 0:
                            self.turn_right(dt, 0)
                        else:
                            self.turn_left(dt, 0)

        # Apply steering to front wheels
        self.vehicle.set_steering_value(self.steering, 0)
        self.vehicle.set_steering_value(self.steering, 1)

    def drive(self, dt):
        engine_force = 0.0
        brake_force = 0.0

        match self.driving_state:

            case Status.ACCELERATE:
                engine_force += 1000

            case Status.DECELERATE:
                brake_force += 100

            case Status.BACK:
                engine_force -= 1000

        # Apply engine and brake to rear wheels
        self.vehicle.apply_engine_force(engine_force, 2)
        self.vehicle.apply_engine_force(engine_force, 3)
        self.vehicle.set_brake(brake_force, 2)
        self.vehicle.set_brake(brake_force, 3)

        # wh2 = self.vehicle.get_wheel(2)
        # print(wh2.get_brake(), wh2.get_engine_force())
        # wh3 = self.vehicle.get_wheel(3)
        # print(wh3.get_brake(), wh3.get_engine_force())
        # print('speed', self.vehicle.getCurrentSpeedKmHour())

    def control(self, dt):
        self.steer(dt)
        self.drive(dt)


# class Cart(NodePath):

#     def __init__(self, world):
#         super().__init__(BulletRigidBodyNode('vehicle'))
#         self.world = world
#         self.setup()

#         inputState.watch_with_modifiers('forward', 'w')
#         # inputState.watch_with_modifiers('left', 'a')
#         inputState.watch_with_modifiers('reverse', 's')
#         # inputState.watch_with_modifiers('right', 'd')
#         inputState.watch_with_modifiers('turn_left', 'q')
#         inputState.watch_with_modifiers('turn_right', 'e')

#     def setup(self):
#         # vehicle
#         self.vehicle = BulletVehicle(self.world, self.node())
#         self.vehicle.set_coordinate_system(ZUp)
#         self.world.attach_vehicle(self.vehicle)

#         self.model = self.attach_new_node(cube.node())
#         self.model.set_pos(Point3(0, 0, 1))
#         self.model.set_scale(Vec3(2, 4, 0.5))
#         tex = base.loader.loadTexture('textures/board.jpg')
#         self.model.set_texture(tex)
#         # self.model.reparent_to(self)

#         # chassis
#         end, tip = self.model.get_tight_bounds()
#         size = tip - end
#         shape = BulletBoxShape(size / 2)
#         ts = TransformState.make_pos(Point3(0, 0, 1))
#         self.node().add_shape(shape, ts)

#         self.set_pos(Point3(0, 0, 20))
#         self.set_pos(Point3(-124, 0, 21))
#         self.node().set_mass(800)
#         self.node().set_deactivation_enabled(False)
#         # np.set_collide_mask(BitMask32.bit(1))
#         self.world.attach(self.node())
#         # self.set_collide_mask(BitMask32.bit(1))


#         # wheel
#         # r_tire = 'models/yugo/yugotireR.egg'
#         # l_tire = 'models/yugo/yugotireL.egg'
#         # wheels = [
#         #     (Point3(0.7, 1.05, 0.3), True, r_tire),
#         #     (Point3(-0.7, 1.05, 0.3), True, l_tire),
#         #     (Point3(0.7, -1.05, 0.3), False, r_tire),
#         #     (Point3(-0.7, -1.05, 0.3), False, l_tire),
#         # ]

#         wheels = [
#             (Point3(0.75, 1.5, 0.5), True),
#             (Point3(-1, 1.5, 0.5), True),
#             (Point3(0.75, -1.5, 0.5), False),
#             (Point3(-1, -1.5, 0.5), False),
#         ]

#         for i, (pos, front) in enumerate(wheels):
#             tex = base.loader.loadTexture('textures/metalboard.jpg')
#             model = Cylinder(radius=0.5, segs_c=30, height=0.25)
#             model.reparent_to(self)

#             shape = BulletConvexHullShape()
#             shape.add_geom(model.node().get_geom(0))
#             self.node().add_shape(shape, TransformState.make_pos_hpr(pos, Vec3(90, 90, 0)))
#             model.set_pos(pos)

#             model.set_texture(tex)
#             model.set_hpr(Vec3(90, 90, 0))
#             # model.set_pos(Point3(0.7, 1.05, 1.5))
#             # np = base.loader.load_model(path)
#             # model.reparent_to(base.render)
#             pivot = model.get_bounds().get_center()
#             new_np = self.attach_new_node(f'new_nd{i}')
#             new_np.set_pos(pivot)
#             model.wrt_reparent_to(new_np)
#             # model.reparent_to(new_np)

#             self.add_wheel(pos, front, new_np)

#         self.steering = 0.0              # degree
#         self.steering_clamp = 45.0       # degree
#         self.steering_increment = 120.0  # degree per second


#     def add_wheel(self, pos, front, np):
#         wheel = self.vehicle.create_wheel()

#         wheel.set_node(np.node())
#         wheel.set_chassis_connection_point_cs(pos)
#         wheel.set_front_wheel(front)

#         wheel.set_wheel_direction_cs(Vec3(0, 0, -1))
#         wheel.set_wheel_axle_cs(Vec3(1, 0, 0))
#         wheel.set_wheel_radius(0.25)
#         wheel.set_max_suspension_travel_cm(40.0)

#         wheel.set_suspension_stiffness(40.0)
#         wheel.set_wheels_damping_relaxation(2.3)
#         wheel.set_wheels_damping_compression(4.4)
#         wheel.set_friction_slip(100.0)
#         wheel.set_roll_influence(0.1)
#         # import pdb; pdb.set_trace()

#     def control(self, dt):
#         engine_force = 0.0
#         brake_force = 0.0

#         if inputState.is_set('forward'):
#             engine_force = 1000.0
#             brake_force = 0.0

#         if inputState.is_set('reverse'):
#             # engine_force = 0
#             engine_force = -1000.0
#             brake_force = 100.0

#         if inputState.is_set('turn_left'):
#             self.steering += dt * self.steering_increment
#             self.steering = min(self.steering, self.steering_clamp)

#         if inputState.isSet('turn_right'):
#             self.steering -= dt * self.steering_increment
#             self.steering = max(self.steering, -self.steering_clamp)

#         # Apply steering to front wheels
#         self.vehicle.set_steering_value(self.steering, 0)
#         self.vehicle.set_steering_value(self.steering, 1)

#         # Apply engine and brake to rear wheels
#         self.vehicle.apply_engine_force(engine_force, 2)
#         self.vehicle.apply_engine_force(engine_force, 3)
#         self.vehicle.set_brake(brake_force, 2)
#         self.vehicle.set_brake(brake_force, 3)
