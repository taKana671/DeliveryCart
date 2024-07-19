from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletPlaneShape
from panda3d.core import NodePath, PandaNode, CardMaker, BitMask32, Vec3


class Ground(NodePath):

    def __init__(self):
        super().__init__(BulletRigidBodyNode('ground'))
        model = self.create_ground()
        model.reparent_to(self)
        self.set_collide_mask(BitMask32.all_on())
        self.node().add_shape(BulletPlaneShape(Vec3.up(), 0))

    def create_ground(self):
        model = NodePath(PandaNode('ground_model'))
        card = CardMaker('card')
        card.set_frame(-1, 1, -1, 1)

        for y in range(50):
            for x in range(50):
                g = model.attach_new_node(card.generate())
                g.set_p(-90)
                g.set_pos(x, y, 0)

        tex = base.loader.loadTexture('textures/concrete.jpg')
        model.set_texture(tex)
        model.flatten_strong()
        model.set_pos(0, 0, 0)
        model.reparent_to(self)
        return model


class Scene(NodePath):

    def __init__(self):
        super().__init__(PandaNode('scene'))
        ground = Ground()
        ground.reparent_to(self)
        self.reparent_to(base.render)