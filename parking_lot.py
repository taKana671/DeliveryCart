from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletBoxShape
from panda3d.core import NodePath, LineSegs
from panda3d.core import BitMask32, Point3, Vec3, LColor
from panda3d.core import TransparencyAttrib

from create_geomnode import Cube


class Block(NodePath):

    def __init__(self, name, pos, scale):
        super().__init__(BulletRigidBodyNode(name))
        cube = Cube()
        self.model = self.attach_new_node(cube.node())

        self.set_pos(pos)
        self.set_scale(scale)
        self.set_collide_mask(BitMask32.bit(1))

        end, tip = self.model.get_tight_bounds()
        self.node().add_shape(BulletBoxShape((tip - end) / 2))
        self.node().set_mass(0)


def create_line_node(from_pos, to_pos, color, thickness=2.0):
    """Return a NodePath for line node.
       Args:
            from_pos (Vec3): the point where a line starts;
            to_pos (Vec3): the point where a line ends;
            color (LColor): the line color;
            thickness (float): the line thickness;
    """
    lines = LineSegs()
    lines.set_color(color)
    lines.move_to(from_pos)
    lines.draw_to(to_pos)
    lines.set_thickness(thickness)
    node = lines.create()
    return NodePath(node)


class ParkingLot:

    def __init__(self, world):
        self.world = world
        root = NodePath('root')
        root.reparent_to(base.render)

        blocks_np = NodePath('blocks')
        blocks_np.reparent_to(root)
        floor = Block('floor', Point3(0, 0, 0), Vec3(50, 50, 0.5))
        floor.reparent_to(blocks_np)
        self.world.attach(floor.node())

        column1 = Block('col1', Point3(-4, 0, 4), Vec3(1, 1, 8))
        column2 = Block('col2', Point3(4, 0, 4), Vec3(1, 1, 8))
        column1.reparent_to(blocks_np)
        column2.reparent_to(blocks_np)
        self.world.attach(column1.node())
        self.world.attach(column2.node())

        tex = base.loader.loadTexture('textures/concrete.jpg')
        blocks_np.set_texture(tex)

        lines = [
            [Point3(-9, 1, 0.251), Point3(-4, 1, 0.251)],
            [Point3(-9, 3, 0.251), Point3(-4, 3, 0.251)],
            [Point3(-9, 5, 0.251), Point3(-4, 5, 0.251)],
        ]

        for from_pos, to_pos in lines:
            line = create_line_node(from_pos, to_pos, LColor(1, 1, 1, 0.6), )
            line.set_transparency(TransparencyAttrib.MAlpha)
            line.reparent_to(root)