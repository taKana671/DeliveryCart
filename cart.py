from enum import Enum, auto

import numpy as np
from panda3d.bullet import BulletBoxShape, ZUp
from panda3d.bullet import BulletRigidBodyNode, BulletVehicle
from panda3d.core import NodePath
from panda3d.core import Vec3, Point3, TransformState, BitMask32

from shapes import CubeModel, CylinderModel


class Status(Enum):

    TURN_LEFT = auto()
    TURN_RIGHT = auto()
    STOP_TURN = auto()
    ACCELERATE = auto()
    DECELERATE = auto()
    BACK = auto()


class BulletCart(NodePath):

    def __init__(self, width=2, depth=4, height=0.5):
        super().__init__(BulletRigidBodyNode('cart'))
        self.size = Vec3(width, depth, height)

        self.set_collide_mask(BitMask32.bit(1))
        self.node().set_mass(800)
        self.node().set_deactivation_enabled(False)
        self.node().set_friction(1)
        self.node().set_restitution(0.1)

        self.vehicle = BulletVehicle(base.world, self.node())
        self.vehicle.set_coordinate_system(ZUp)
        base.world.attach_vehicle(self.vehicle)

        self.create_cart_board()
        self.create_cart_wheels()
        self.reparent_to(base.render)
        base.world.attach(self.node())

        self.steering_clamp = 45.0       # degree
        # self.steering_increment = 120.0  # degree per second
        self.steering_increment = 60

    def create_cart_board(self):
        self.board = CubeModel(
            self.size.x, self.size.y, self.size.z, segs_w=2, segs_d=4).create()
        self.board.set_name('board')
        self.board.set_pos(Vec3(0, 0, 1))

        end, tip = self.board.get_tight_bounds()
        shape = BulletBoxShape((tip - end) / 2)
        self.node().add_shape(shape, TransformState.make_pos(Vec3(0, 0, 1)))

        tex = base.loader.loadTexture('textures/board.jpg')
        self.board.set_texture(tex)
        self.board.reparent_to(self)

    def create_cart_wheels(self):
        model_maker = CylinderModel(radius=0.25, height=0.25)
        tex = base.loader.loadTexture('textures/metalboard.jpg')

        wheel_pos = {
            'front_right': Point3(0.875, 1.75, 0.875),
            'front_left': Point3(-0.875, 1.75, 0.875),
            'back_right': Point3(0.875, -1.75, 0.875),
            'back_left': Point3(-0.875, -1.75, 0.875),
        }

        for name, pos in wheel_pos.items():
            model = model_maker.create()
            model.set_pos_hpr(pos, Vec3(90, 90, 0))
            model.set_texture(tex)
            model.reparent_to(self)

            new_np = self.relocate(name, model)
            front = name.startswith('front')
            self.add_wheel(pos, front, new_np)

    def relocate(self, name, model):
        """Create the new parent node under the original parent, bring the new parent
           to the center, and relocate the node without changing any of it's transformation.
        """
        pivot = model.get_bounds().get_center()
        new_np = self.attach_new_node(name)
        new_np.set_pos(pivot)
        model.wrt_reparent_to(new_np)
        return new_np

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

    def get_abs_speed(self):
        return abs(self.vehicle.get_current_speed_km_hour())

    def get_rear_wheel_engine_forces(self):
        return sum(self.vehicle.get_wheel(i).get_engine_force() for i in (2, 3))

    def apply_steering(self, steering):
        # Apply steering to front wheels
        self.vehicle.set_steering_value(steering, 0)
        self.vehicle.set_steering_value(steering, 1)

    def apply_engine_and_brake(self, engine_force, brake_force):
        # Apply engine and brake to rear wheels
        self.vehicle.apply_engine_force(engine_force, 2)
        self.vehicle.apply_engine_force(engine_force, 3)
        self.vehicle.set_brake(brake_force, 2)
        self.vehicle.set_brake(brake_force, 3)


class CartController:

    def __init__(self, cart):
        self.cart = cart
        self.setup_cart()
        self.accept_control_keys()

        self.steering = 0   # degree
        self.steering_state = None
        self.driving_state = None

        self.tail = NodePath(BulletRigidBodyNode('tail'))
        self.tail.set_pos(Vec3(0, -5, 3))
        self.tail.node().set_linear_factor(Vec3(1, 1, 0))
        self.tail.reparent_to(self.cart)


    def accept_control_keys(self):
        base.accept('q', self.monitor_key, [Status.TURN_LEFT, True])
        base.accept('q-up', self.monitor_key, [Status.STOP_TURN, True])
        base.accept('e', self.monitor_key, [Status.TURN_RIGHT, True])
        base.accept('e-up', self.monitor_key, [Status.STOP_TURN, True])
        base.accept('w', self.monitor_key, [Status.ACCELERATE, False])
        base.accept('w-up', self.monitor_key, [Status.DECELERATE, False])
        base.accept('s', self.monitor_key, [Status.BACK, False])
        base.accept('s-up', self.monitor_key, [Status.DECELERATE, False])

    def setup_cart(self):
        start_pos, start_hpr = base.scene.road.get_start_location()
        start_pos += Vec3(0, 0, 1)
        self.cart.set_pos_hpr(start_pos, start_hpr)

        # self.angular_speed = 0
        # self.start_xy = start_pos.xy

    def monitor_key(self, status, steering_control):
        if steering_control:
            self.steering_state = status
        else:
            self.driving_state = status

    def get_steering_clamp(self):
        match speed := self.cart.get_abs_speed():

            case speed if speed > 50:
                return self.cart.steering_clamp * 0.25

            case speed if speed > 40:
                return self.cart.steering_clamp * 0.5

            case speed if speed > 30:
                return self.cart.steering_clamp * 0.75

            case _:
                return self.cart.steering_clamp

    def turn_left(self, dt, min_value):
        self.steering += dt * self.cart.steering_increment
        self.steering = min(self.steering, min_value)

    def turn_right(self, dt, max_value):
        self.steering -= dt * self.cart.steering_increment
        self.steering = max(self.steering, max_value)

    def relax_steering_angle(self, dt):
        if self.cart.get_rear_wheel_engine_forces() != 0:
            if self.steering > 0:
                self.turn_right(dt, 0)
            else:
                self.turn_left(dt, 0)

    def control_steering_angle(self, dt):
        match self.steering_state:

            case Status.TURN_LEFT:
                steering_clamp = self.get_steering_clamp()
                self.turn_left(dt, steering_clamp)

            case Status.TURN_RIGHT:
                steering_clamp = self.get_steering_clamp()
                self.turn_right(dt, -steering_clamp)

            case Status.STOP_TURN:
                if self.steering != 0:
                    self.relax_steering_angle(dt)

        # Apply steering to front wheels
        self.cart.apply_steering(self.steering)

    def control_engine_and_brake(self, dt):
        engine_force = 0.0
        brake_force = 0.0

        match self.driving_state:

            case Status.ACCELERATE:
                engine_force += 500  # 1000

            case Status.DECELERATE:
                brake_force += 50    # 100

            case Status.BACK:
                engine_force -= 500  # 1000

        # Apply engine and brake to rear wheels
        self.cart.apply_engine_and_brake(engine_force, brake_force)

    def control(self, dt):
        # print(self.cart.board.get_pos(base.render), self.cart.get_pos())
        self.control_steering_angle(dt)
        self.control_engine_and_brake(dt)

        # cart_pos = self.cart.get_pos(base.render)
        # self.angular_speed = self.get_angle(Vec3(-92, 0, 0), cart_pos.xy, self.start_xy)
        # self.start_xy = cart_pos.xy
        # print(self.angular_speed)

    
    def get_angle(self, center, pt1, pt2):
        vec_a = pt1 - center.xy
        vec_b = pt2 - center.xy

        vec_a_length = self.norm(center, pt1)
        vec_b_length = self.norm(center, pt2)
        # inner = np.inner(vec_a_length, vec_b_length)
        inner_product = vec_a.x * vec_b.x + vec_a.y * vec_b.y
        cos = inner_product / (vec_a_length * vec_b_length)
        # print(inner_product, cos)
        rad = np.arccos(cos)
        deg = np.rad2deg(rad)
        return deg

    def norm(self, pt1, pt2):
        return ((pt2.x - pt1.x) ** 2 + (pt2.y - pt1.y) ** 2) ** 0.5