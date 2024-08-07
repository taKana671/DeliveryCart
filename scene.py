import math
import array

from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletTriangleMeshShape, BulletTriangleMesh, BulletHeightfieldShape, ZUp
from panda3d.core import NodePath, PandaNode, BitMask32, Vec3, Point3
from panda3d.core import Filename, PNMImage
from panda3d.core import GeoMipTerrain
from panda3d.core import Shader, TextureStage
from panda3d.core import TransparencyAttrib
from panda3d.core import GeomVertexArrayFormat, GeomVertexFormat
from panda3d.core import Geom, GeomTriangles, GeomNode, GeomVertexData


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
    """Create a plane geom node.
        Arges:
            w (int): width; dimension along the x-axis; cannot be negative
            d (int): depth; dimension along the y-axis; cannot be negative
            segs_w (int) the number of subdivisions in width
            segs_d (int) the number of subdivisions in depth
            wave_h (int) the height of wave;
    """

    def __init__(self, w=256, d=256, segs_w=16, segs_d=16):
        super().__init__(BulletRigidBodyNode('water_surface'))
        self.w = w
        self.d = d
        self.segs_w = segs_w
        self.segs_d = segs_d

        nd = self.make_node()
        self.model = self.attach_new_node(nd)
        self.model.set_two_sided(True)

        self.model.set_transparency(TransparencyAttrib.MAlpha)
        self.model.set_texture(base.loader.loadTexture('textures/water.png'))
        self.model.set_pos(0, 0, 0)

        mesh = BulletTriangleMesh()
        mesh.add_geom(nd.get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)

    def make_node(self):
        start_w = self.w * -0.5
        start_d = self.d * -0.5

        offset_u = -start_w
        offset_v = -start_d

        arr_format = GeomVertexArrayFormat()
        arr_format.add_column('vertex', 3, Geom.NT_float32, Geom.C_point)
        arr_format.add_column('color', 4, Geom.NT_float32, Geom.C_color)
        arr_format.add_column('normal', 3, Geom.NT_float32, Geom.C_color)
        arr_format.add_column('texcoord', 2, Geom.NT_float32, Geom.C_texcoord)
        fmt = GeomVertexFormat.register_format(arr_format)

        vdata_arr = array.array('f', [])  # double
        prim_arr = array.array('H', [])   # unsigned short (int)

        color = (1, 1, 1, 1)
        normal = Vec3(0, 0, 1)

        for i in range(self.segs_w + 1):
            x = start_w + i / self.segs_w * self.w
            u = (x + offset_u) / self.w

            for j in range(self.segs_d + 1):
                y = start_d + j / self.segs_d * self.d
                v = (y + offset_v) / self.d

                vdata_arr.extend(Point3(x, y, 0))
                vdata_arr.extend(color)
                vdata_arr.extend(normal)
                vdata_arr.extend((u, v))

            if i > 0:
                for k in range(self.segs_d):
                    idx = i * (self.segs_d + 1) + k
                    prim_arr.extend((idx, idx - self.segs_d - 1, idx - self.segs_d))
                    prim_arr.extend((idx, idx - self.segs_d, idx + 1))

        vertex_cnt = (self.segs_w + 1) * (self.segs_d + 1)
        vdata = GeomVertexData('vdata', fmt, Geom.UH_static)
        vdata.unclean_set_num_rows(vertex_cnt)
        vdata_mem = memoryview(vdata.modify_array(0)).cast('B').cast('f')
        vdata_mem[:] = vdata_arr

        prim = GeomTriangles(Geom.UH_static)
        prim_vertices = prim.modify_vertices()
        prim_vertices.unclean_set_num_rows(len(prim_arr))
        prim_mem = memoryview(prim_vertices).cast('B').cast('H')
        prim_mem[:] = prim_arr

        prim.close_primitive()
        geom = Geom(vdata)
        geom.addPrimitive(prim)
        node = GeomNode('geom_node')
        node.add_geom(geom)
        return node

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


class Scene(NodePath):

    def __init__(self, world):
        super().__init__(PandaNode('scene'))
        self.world = world
        self.reparent_to(base.render)

        self.terrain = Terrain('terrains/mysample3.png')
        self.terrain.reparent_to(self)
        self.world.attach(self.terrain.node())

        self.water_surface = WaterSurface()
        self.water_surface.reparent_to(self)
        self.water_surface.set_pos(0, 0, 0)
        self.world.attach(self.water_surface.node())