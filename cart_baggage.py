from panda3d.core import NodePath
from panda3d.bullet import BulletBoxShape, BulletCylinderShape, BulletBoxShape, ZUp
from panda3d.bullet import BulletRigidBodyNode, BulletVehicle
from panda3d.core import NodePath
from panda3d.core import Vec3, Point3, TransformState, BitMask32, LColor

from shapes import CylinderModel, CubeModel


class Baggage(NodePath):

    def __init__(self, name, pos, w=2, d=2):
        super().__init__(BulletRigidBodyNode(name))
        self.model = CubeModel(width=w, depth=d, height=0.5).create()
        self.model.reparent_to(self)
        self.set_pos(pos)
        self.set_texture(base.loader.load_texture('textures/paper_03.jpg'))

        self.set_collide_mask(BitMask32.bit(1))
        self.node().set_friction(1)
        self.node().set_restitution(0.1)
        self.node().set_mass(0.01)
        # self.node().set_deactivation_enabled(False)

        end, tip = self.model.get_tight_bounds()
        shape = BulletBoxShape((tip - end) / 2)
        self.node().add_shape(shape)
        # self.node().add_shape(shape, TransformState.make_pos(Vec3(0, 0, 0.25)))


class Baggages:

    def __init__(self, world):
        self.world = world
        self.root_np = NodePath('baggages')
        self.root_np.reparent_to(base.render)
        self.cart = base.cart.board

    def load(self):
        cart_center = self.cart.get_pos()
        print(cart_center)
        end, tip = self.cart.get_tight_bounds()
        cart_size = tip - end
        # center = base.cart.model.get_pos()   # LPoint3f(-124, 0, 21)
        # end, tip = base.cart.model.get_tight_bounds()  # LVector3f(2, 4, 1)
        # cart_size = tip - end

        # bag = Baggage('bag_1', Point3(-124, 0, cart_center.z + 0.25 + 0.25))
        # bag.reparent_to(self.root_np)
        # self.world.attach(bag.node())

        # bag = Baggage('bag_2', Point3(-124, 0, cart_center.z + 0.25 + 0.5))
        # bag.reparent_to(self.root_np)
        # self.world.attach(bag.node()) 