import math
import array

from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletCylinderShape
from panda3d.bullet import BulletTriangleMeshShape, BulletTriangleMesh, BulletHeightfieldShape, ZUp
from panda3d.bullet import BulletConvexHullShape
from panda3d.core import NodePath, PandaNode, BitMask32, Vec3, Point3
from panda3d.core import Mat4
from panda3d.core import Filename, PNMImage
from panda3d.core import GeoMipTerrain
from panda3d.core import Shader, TextureStage, TransformState
from panda3d.core import TransparencyAttrib
from panda3d.core import GeomVertexArrayFormat, GeomVertexFormat
from panda3d.core import Geom, GeomTriangles, GeomNode, GeomVertexData

from shapes import CylinderModel, PlaneModel
from lights import BasicAmbientLight, BasicDayLight
from cart import BulletCart


class Terrain(NodePath):

    def __init__(self, heightmap_path, height=100):
        super().__init__(BulletRigidBodyNode('terrain'))
        self.height = height
        self.set_pos(Point3(0, 0, 0))
        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(1))
        self.create_terrain(heightmap_path)

    def create_terrain(self, heightmap_path):
        img = PNMImage(Filename(heightmap_path))
        shape = BulletHeightfieldShape(img, self.height, ZUp)
        shape.set_use_diamond_subdivision(True)
        self.node().add_shape(shape)

        self.terrain = GeoMipTerrain('geomip_terrain')
        self.terrain.set_heightfield(heightmap_path)
        self.terrain.set_border_stitching(True)
        self.terrain.set_block_size(8)
        self.terrain.set_min_level(2)
        self.terrain.set_focal_point(base.camera)

        size_x, size_y = img.get_size()
        x = (size_x - 1) / 2
        y = (size_y - 1) / 2

        pos = Point3(-x, -y, -(self.height / 2))
        scale = Vec3(1, 1, self.height)
        self.root = self.terrain.get_root()
        self.root.set_scale(scale)
        self.root.set_pos(pos)
        self.terrain.generate()
        self.root.reparent_to(self)

        shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
        self.root.set_shader(shader)

        tex_files = [
            ('stones_01.jpg', 20),
            ('grass_02.png', 10),
        ]

        for i, (file_name, tex_scale) in enumerate(tex_files):
            ts = TextureStage(f'ts{i}')
            ts.set_sort(i)
            self.root.set_shader_input(f'tex_ScaleFactor{i}', tex_scale)
            tex = base.loader.load_texture(f'textures/{file_name}')
            self.root.set_texture(ts, tex)


class WaterSurface(NodePath):
    """Create water surface.
        Arges:
            w (int): width; dimension along the x-axis; cannot be negative
            d (int): depth; dimension along the y-axis; cannot be negative
            segs_w (int) the number of subdivisions in width
            segs_d (int) the number of subdivisions in depth
    """

    def __init__(self, w=256, d=256, segs_w=16, segs_d=16):
        super().__init__(BulletRigidBodyNode('water_surface'))
        self.w = w
        self.d = d
        self.segs_w = segs_w
        self.segs_d = segs_d

        self.model = PlaneModel(w, d, segs_w, segs_d).create()
        self.model.set_transparency(TransparencyAttrib.MAlpha)
        self.model.set_texture(base.loader.loadTexture('textures/water.png'))
        self.model.set_pos(0, 0, 0)
        self.model.reparent_to(self)

        mesh = BulletTriangleMesh()
        mesh.add_geom(self.model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)

    def wave(self, time, wave_h=3.0):
        geom_node = self.model.node()
        geom = geom_node.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        for i in range(0, len(vdata_mem), 12):
            x, y = vdata_mem[i: i + 2]
            z = (math.sin(time + x / wave_h) + math.sin(time + y / wave_h)) * wave_h / 2
            # z = (math.sin(time + x / wave_h) + math.sin(y + x) / wave_h) * wave_h / 2
            vdata_mem[i + 2] = z


class Road(NodePath):

    def __init__(self, segs_x=4):
        super().__init__(BulletRigidBodyNode('cylinder'))
        self.create_columns()
        self.create_road(segs_x)
        self.set_texture(base.loader.load_texture('textures/iron.jpg'))

    def create_columns(self):
        model_maker = CylinderModel(radius=4, height=20, segs_a=10, segs_cap=4)
        for x in [-124, 124]:
            pos = Point3(x, 0, 1)
            model = model_maker.create()
            model.set_pos(pos)
            model.reparent_to(self)

            shape = BulletConvexHullShape()
            shape.add_geom(model.node().get_geom(0))
            self.node().add_shape(shape, TransformState.make_pos(pos))

    def create_road(self, segs_x):
        seg = 124 * 2 / segs_x
        radius = seg / 2 + 3
        inner_radius = radius - 6

        model_maker = CylinderModel(
            radius=radius,
            inner_radius=inner_radius,
            slice_angle_deg=180,
            height=1,
            # invert_inner_mantle=False
        )

        for i in range(segs_x):
            model_maker.invert = False if i % 2 == 0 else True

            if i == 0:
                geom_node = model_maker.get_geom_node()
                continue

            new_geom_node = model_maker.get_geom_node()
            new_geom = new_geom_node.modify_geom(0)

            new_vdata = new_geom.modify_vertex_data()
            rotation_deg = 0 if i % 2 == 0 else 180
            bottom_center = Point3(seg * i, 0, 0)
            model_maker.tranform_vertices(new_vdata, Vec3(0, 0, 1), bottom_center, rotation_deg)
            new_vert_cnt = new_vdata.get_num_rows()
            new_vdata_mem = memoryview(new_vdata.modify_array(0)).cast('B').cast('f')

            new_prim = new_geom.modify_primitive(0)
            new_prim_cnt = new_prim.get_num_vertices()
            new_prim_array = new_prim.modify_vertices()
            new_prim_mem = memoryview(new_prim_array).cast('B').cast('H')

            model_maker.add(
                geom_node, new_vdata_mem, new_vert_cnt, new_prim_mem, new_prim_cnt)

        pos = Point3(-124 + seg - seg / 2, 0, 19.99)  # 20
        model = model_maker.modeling(geom_node)
        model.set_pos(pos)
        model.reparent_to(self)

        # If using BulletConvexHullShape, hollow is lost because of the shape.
        mesh = BulletTriangleMesh()
        mesh.add_geom(model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape, TransformState.make_pos(pos))


class Scene(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('scene'))
        self.world = world
        self.reparent_to(base.render)

        self.ambient_light = BasicAmbientLight()
        self.day_light = BasicDayLight()

        self.terrain = Terrain('terrains/mysample3.png')
        self.terrain.reparent_to(self)
        self.world.attach(self.terrain.node())

        self.water_surface = WaterSurface()
        self.water_surface.reparent_to(self)
        self.water_surface.set_pos(0, 0, 0)
        self.world.attach(self.water_surface.node())

        self.road = Road()
        self.road.reparent_to(self)
        self.world.attach(self.road.node())

        # *****shape test*****************
        # cart = BulletCart()
        # cart.reparent_to(self)
        # self.world.attach(cart.node())
        # cart.set_pos(-100, -100, 80)
        # cart.hprInterval(15, Vec3(360)).loop()

        # test_np = NodePath(BulletRigidBodyNode('test'))
        # test_np.reparent_to(self)
        # model = CylinderModel(height=3, inner_radius=5, slice_angle_deg=0, invert=False).create()
        # # model = Cube(width=5, depth=5, height=5, segs_d=0).create()
        # model.reparent_to(test_np)

        # pos = Point3(0, 0, 15)
        # model.set_pos(pos)
        # # scale = Vec3(2)
        # # model.set_scale(scale)

        # # shape = BulletConvexHullShape()
        # # shape.add_geom(model.node().get_geom(0))
        # # test_np.node().add_shape(shape, TransformState.make_pos(pos))

        # mesh = BulletTriangleMesh()
        # mesh.add_geom(model.node().get_geom(0))
        # shape = BulletTriangleMeshShape(mesh, dynamic=False)
        # test_np.node().add_shape(shape, TransformState.make_pos(pos))

        # test_np.set_texture(base.loader.load_texture('textures/metalboard.jpg'))
        # self.world.attach(test_np.node())
        # # cylinder.set_p(180)
        # # test_np.hprInterval(15, Vec3(360)).loop()
        # base.camera.set_pos(-128, -128, 100)
        # base.camera.look_at(test_np)
        # ***********************************