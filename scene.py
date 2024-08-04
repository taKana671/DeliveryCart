import math
import random

from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletTriangleMeshShape, BulletTriangleMesh, BulletConvexHullShape, BulletPlaneShape, BulletHeightfieldShape, ZUp
from panda3d.core import NodePath, PandaNode, CardMaker, BitMask32, Vec3, Point3, Vec2
from panda3d.core import Filename, PNMImage
from panda3d.core import GeoMipTerrain
from panda3d.core import Shader, TextureStage, TransformState
from panda3d.core import TransparencyAttrib
from panda3d.core import Triangulator, GeomVertexFormat, GeomVertexData, Triangulator3
from panda3d.core import Geom, GeomVertexWriter, GeomTriangles, GeomNode, GeomVertexRewriter
from panda3d.core import GeomVertexArrayFormat

from parking_lot import ParkingLot


class Terrain(NodePath):

    def __init__(self, height=30):
        super().__init__(BulletRigidBodyNode('terrain'))
        self.height = height
        self.set_pos(Point3(0, 0, 0))
        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(1))
        # self.set_collide_mask(BitMask32.all_on())

        img = PNMImage(Filename('terrains/city_3.png'))
        shape = BulletHeightfieldShape(img, self.height, ZUp)
        shape.set_use_diamond_subdivision(True)
        self.node().add_shape(shape)

        self.terrain = GeoMipTerrain('geomip_terrain')
        self.terrain.set_heightfield('terrains/city_3.png')
        self.terrain.set_border_stitching(True)
        self.terrain.set_block_size(8)
        # self.terrain.set_block_size(32)
        self.terrain.set_min_level(2)
        self.terrain.set_focal_point(base.camera)

        size_x, size_y = img.get_size()
        x = (size_x - 1) / 2
        y = (size_y - 1) / 2

        pos = Point3(-x, -y, -(self.height / 2))
        self.root = self.terrain.get_root()
        self.root.set_scale(Vec3(1, 1, self.height))
        self.root.set_pos(pos)
        self.terrain.generate()
        self.root.reparent_to(self)

        # **********************************************************
        # self.root.set_shader_input('HeightMap', base.loader.loadTexture('terrains/test1.png'))
        # ***********************************************************

        shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_f.glsl')
        self.root.set_shader(shader)

        # texes = [
        #     ('concrete.jpg', 30),
        #     ('grass_02.png', 10),
        #     ('grass_03.jpg', 10),
        #     ('grass_04.jpg', 10)
        # ]

        texes = [
            ('grass_03.jpg', 30),
            ('grass_02.png', 30),
            ('grass_02.png', 10),
            ('grass_01.jpg', 30)
        ]

        for i, (name, tex_scale) in enumerate(texes):
            ts = TextureStage(f'ts{i}')
            ts.set_sort(i)
            self.root.set_shader_input(f'tex_ScaleFactor{i}', tex_scale)
            tex = base.loader.load_texture(f'textures/{name}')
            self.root.set_texture(ts, tex)


class Ground(NodePath):

    def __init__(self):
        super().__init__(BulletRigidBodyNode('ground'))
        # model = self.create_ground()
        # model.reparent_to(self)
        # # self.set_collide_mask(BitMask32.all_on())
        # self.set_collide_mask(BitMask32.bit(1))
        # self.node().add_shape(BulletPlaneShape(Vec3.up(), 0))

        # self.set_transparency(TransparencyAttrib.MAlpha)

    def create_ground(self):
        model = NodePath(PandaNode('ground_model'))
        card = CardMaker('card')
        # card.set_frame(-1, 1, -1, 1)
        card.set_frame(-128, 128, -128, 128)
        g = model.attach_new_node(card.generate())
        g.set_p(-90)
        # g.set_pos(0, 0, 0)

        for y in range(-50, 50):
            for x in range(-50, 50):
                g = model.attach_new_node(card.generate())
                g.set_p(-90)
                g.set_pos(x, y, 0)

        tex = base.loader.loadTexture('textures/concrete.jpg')
        model.set_texture(tex)
        model.flatten_strong()
        model.set_pos(0, 0, 0)
        model.reparent_to(self)
        return model

    def get_vertices(self):
        step = 32

        for row in range(0, 256, step):
            for col in range(0, 256, step):
                top_left = (col, row)
                bottom_left = (col, row + step)
                bottom_right = (col + step, row + step)
                top_right = (col + step, row)
                yield [top_left, bottom_left, bottom_right, top_right]

    def make_node2(self):
        arr_format = GeomVertexArrayFormat()
        arr_format.add_column('vertex', 3, Geom.NT_float32, Geom.C_point)
        arr_format.add_column('color', 4, Geom.NT_float32, Geom.C_color)
        arr_format.add_column('normal', 3, Geom.NT_float32, Geom.C_color)
        arr_format.add_column('texcoord', 2, Geom.NT_float32, Geom.C_texcoord)
        fmt = GeomVertexFormat.register_format(arr_format)

        t = Triangulator()
        # fmt = GeomVertexFormat.get_v3()
        vdata = GeomVertexData('vdata', fmt, Geom.UH_static)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')

        prim = GeomTriangles(Geom.UH_static)

        w = 256
        d = 256
        segs_w = 16
        segs_d = 16

        dim1_start = w * -0.5
        dim2_start = d * -0.5
        # dim1_start = 0
        # dim2_start = 0

        segs_u = segs_w * 2 + segs_d * 2
        offset_u = 0

        for j in range(segs_w + 1):
            x = dim1_start + j / segs_w * w
            # u = j / segs_w
            u = (j + offset_u) / segs_u

            for k in range(segs_d + 1):
                y = dim2_start + k / segs_d * d
                v = k / segs_d
                print(x, y)

                t.add_polygon_vertex(t.add_vertex(x, y))
                vertex.add_data3f((x, y, 0))
                color.add_data4f((1.0, 1.0, 1.0, 1.0))
                normal.add_data3((0, 0, 1))
                # print(((x + 128) / 100, (y + 128) / 100))
                texcoord.add_data2f(((x + 128) / 100, (y + 128) / 100))
                # texcoord.add_data2f((u, v))

            if j > 0:
                for k in range(segs_d):
                    idx = j * (segs_d + 1) + k
                    prim.add_vertices(idx, idx - segs_d - 1, idx - segs_d)
                    prim.add_vertices(idx, idx - segs_d, idx + 1)

        prim.close_primitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode('geom_node')
        node.add_geom(geom)
        return node


    def make_node(self):
        # pointmap = lambda x, y = Point3(x, y, 0)
        # vertices = [(0,0), (0,100), (100,100), (100,0)]
        # vertices = [(0,0), (0,10), (10,10), (10,0), (0, 5), (5, 10), (5, 5), (5, 0), (10, 5)]
        # vertices = [(0, 0), (0, 50), (0,100), (50,100), (100, 100), (100, 50), (100, 0), (50, 0), (50, 50)]
        # vertices = [
        #     (0, 0), (0, 50), (50, 50), (50, 0),
        #     (0, 50), (0, 100), (50, 100), (50, 50),
        #     (50, 50), (50, 100), (100, 100), (100, 50),
        #     (50, 0), (50, 50), (100, 50), (100, 0),
        # ]

        # vertices = [
        #     (0, 0), (0, 50), (25, 50), (25, 0),
        #     (0, 50), (0, 100), (25, 100), (25, 50),
        #     (25, 50), (25, 100), (50, 100), (50, 50),
        #     (50, 50), (50, 100), (100, 100), (100, 50),
        #     (50, 0), (50, 50), (100, 50), (100, 0),
        #     (25, 0), (25, 50), (50, 50), (50, 0),
        # ]

        # vertices = [
        #     (0, 0), (0, 50), (25, 50), (25, 0),
        #     (25, 0), (25, 50), (50, 50), (50, 0),
        #     (50, 0), (50, 50), (100, 50), (100, 0),
        #     (0, 50), (0, 100), (25, 100), (25, 50),
        #     (25, 50), (25, 100), (50, 100), (50, 50),
        #     (50, 50), (50, 100), (100, 100), (100, 50),
        # ]



        arr_format = GeomVertexArrayFormat()
        arr_format.add_column('vertex', 3, Geom.NT_float32, Geom.C_point)
        arr_format.add_column('color', 4, Geom.NT_float32, Geom.C_color)
        arr_format.add_column('normal', 3, Geom.NT_float32, Geom.C_color)
        arr_format.add_column('texcoord', 2, Geom.NT_float32, Geom.C_texcoord)
        fmt = GeomVertexFormat.register_format(arr_format)

        t = Triangulator()
        # fmt = GeomVertexFormat.get_v3()
        vdata = GeomVertexData('vdata', fmt, Geom.UH_static)
        vertex = GeomVertexWriter(vdata, 'vertex')

        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        texcoord = GeomVertexWriter(vdata, 'texcoord')

        # for x, y in vertices:
        for vertices in self.get_vertices():
            # print(vertices)
            for x, y in vertices:
                t.add_polygon_vertex(t.add_vertex(x, y))
                vertex.add_data3f((x, y, 0))
                color.add_data4f((1.0, 1.0, 1.0, 1.0))
                normal.add_data3((0, 0, 1))
                print(x / 100, y / 100)
                texcoord.add_data2f((x / 100, y / 100))

        t.triangulate()
        prim = GeomTriangles(Geom.UH_static)

        # for n in range(t.get_num_triangles()):
        #     print(t.get_triangle_v0(n), t.get_triangle_v1(n), t.get_triangle_v2(n))
        #     prim.add_vertices(t.get_triangle_v0(n), t.get_triangle_v1(n), t.get_triangle_v2(n))

        # for i in range(int(len(vertices) / 4)):
        for i in range(64):
            prim.add_vertices(3 + i, i, i + 1)
            prim.add_vertices(3 + i, i + 1, 3 + i + 1)
        # for i in range(64 * 2):
        #     prim.add_vertices(i, i + 1, i + 2)
        #     # prim.add_vertices(3 + i, i + 1, 3 + i + 1)

        prim.close_primitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode('geom_node')
        node.add_geom(geom)
        return node




class Scene(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('scene'))
        self.world = world

        ground = Ground()
        ground.reparent_to(self)
        # import pdb; pdb.set_trace()
        # ground.set_pos(0, 0, -5)
        self.reparent_to(base.render)
        # world.attach(ground.node())

        # shader = Shader.load(Shader.SL_GLSL, 'shaders/water_v.glsl', 'shaders/6_1_fdistImproved_2.frag')
        # # shader = Shader.load(Shader.SL_GLSL, 'shaders/water2_v.glsl', 'shaders/water2_f.glsl')
        # ground.set_shader(shader)
        # # ground.set_shader_input('Heightmap', base.loader.loadTexture('terrains/test2.png'))
        # # ground.set_shader_input('tex1', base.loader.loadTexture('textures/stones_01.jpg'))
        # # ground.set_shader_input('tex2', base.loader.loadTexture('textures/grass_02.png'))

        # props = base.win.get_properties()
        # # import pdb; pdb.set_trace()
        # ground.set_shader_input('u_resolution', props.get_size())
        # # ground.set_shader_input('u_resolution', Vec2(256, 256))

        # # ground.set_shader_input('noise', base.loader.loadTexture('terrains/gauss2.png'))
        # # ground.set_shader_input('tex1', base.loader.loadTexture('textures/stones_01.jpg'))

        self.terrain = Terrain()
        self.terrain.reparent_to(self)
        self.world.attach(self.terrain.node())


        nd = ground.make_node2()
        self.test_np = NodePath(BulletRigidBodyNode('ground'))
        self.model = self.test_np.attach_new_node(nd)
        self.model.set_two_sided(True)
        self.model.reparent_to(base.render)
        # self.model = NodePath(nd).reparent_to(self)

        self.model.set_color((0.52, 0.80, 0.98, 1.0))
        self.model.set_transparency(TransparencyAttrib.MAlpha)
        self.model.set_texture(base.loader.loadTexture('textures/water.png'))
        self.model.set_pos(0, 0, 0)
        # self.model.set_p(90)

        # shape = BulletConvexHullShape()
        # shape.add_geom(nd.get_geom(0))
        # test_np.node().add_shape(shape)
        mesh = BulletTriangleMesh()
        mesh.add_geom(nd.get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.test_np.node().add_shape(shape)

        self.test_np.reparent_to(self)
        self.world.attach(self.test_np.node())

        # import pdb; pdb.set_trace()

    def wave(self, time):
        geom_node = self.model.node()
        # geom_node = self.test_np.node()
        dic = {}

        for i in range(geom_node.get_num_geoms()):
            geom = geom_node.modify_geom(i)
            vdata = geom.modify_vertex_data()
            vertex = GeomVertexRewriter(vdata, 'vertex')


            while not vertex.is_at_end():
                v = vertex.get_data3f()
                x, y = v[0], v[1]
    
                if (x, y) in dic:
                    z = dic[(x, y)]
                else:
                    z = (math.sin(time + x / 3) + math.sin(y + x) / 3) * 3 / 2
                    dic[(x, y)] = z
                # # print(x, y, z)
                vertex.set_data3f(x, y, z)


        # print('------------------------------')


