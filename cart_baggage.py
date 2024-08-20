import random

from panda3d.bullet import BulletBoxShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.core import NodePath
from panda3d.core import Vec3, BitMask32

from shapes import CubeModel


class Baggage(NodePath):

    def __init__(self, name, pos, model, tex):
        super().__init__(BulletRigidBodyNode(name))
        self.model = model
        self.model.reparent_to(self)
        self.set_pos(pos)
        self.set_texture(tex)

        self.set_collide_mask(BitMask32.bit(1))
        self.node().set_friction(1)
        self.node().set_restitution(0.1)
        self.node().set_mass(10)
        # self.node().set_deactivation_enabled(False)

        end, tip = self.model.get_tight_bounds()
        shape = BulletBoxShape((tip - end) / 2)
        self.node().add_shape(shape)


class Baggages:

    def __init__(self, size=0.5):
        self.size = size
        self.root_np = NodePath('baggages')
        self.root_np.reparent_to(base.render)

        self.cart = base.cart_controller.cart
        self.cols = int(self.cart.size.x) * 2   # 2 * 2 = 4
        self.rows = int(self.cart.size.y) * 2   # 4 * 2 = 8
        self.model_maker = CubeModel(
            width=self.size, depth=self.size, height=self.size)

    def load(self, stack_layers=1):
        cart_center = self.cart.model.get_pos(base.render)
        start_x = -self.cart.size.x / 2 + self.size / 2   # -0.75
        start_y = -self.cart.size.y / 2 + self.size / 2   # -1.75
        start_z = self.cart.size.z / 2 + self.size / 2    # 0.5
        half = self.size / 2                              # 0.25

        textures = [
            base.loader.load_texture('textures/paper_03.jpg'),
            base.loader.load_texture('textures/paper_04.jpg')
        ]

        for n in range(stack_layers):
            offset = half * n

            for i in range(self.cols - n):
                x = start_x + i * self.size + offset
                z = start_z + n * self.size

                for j in range(self.rows - n):
                    y = start_y + j * self.size + offset
                    pos = cart_center + Vec3(x, y, z)
                    model = self.model_maker.create()
                    tex = random.choice(textures)
                    baggage = Baggage(f'baggage_{n}{i}{j}', pos, model, tex)
                    baggage.reparent_to(self.root_np)
                    base.world.attach(baggage.node())