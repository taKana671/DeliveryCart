import math

from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletTriangleMeshShape, BulletHeightfieldShape, ZUp
from panda3d.bullet import BulletConvexHullShape, BulletTriangleMesh
from panda3d.core import NodePath, PandaNode
from panda3d.core import BitMask32, Vec3, Point3, LColor
from panda3d.core import Filename, PNMImage
from panda3d.core import GeoMipTerrain
from panda3d.core import Shader, TextureStage, TransformState
from panda3d.core import TransparencyAttrib

from shapes.src import Cylinder, Plane
from lights import BasicAmbientLight, BasicDayLight


class Sky(NodePath):

    def __init__(self):
        super().__init__(PandaNode('sky'))
        model = base.loader.load_model('models/blue-sky/blue-sky-sphere')
        model.set_color(LColor(2, 2, 2, 1))
        model.set_scale(0.2)
        model.set_z(0)
        model.reparent_to(self)
        self.set_shader_off()


class Terrain(NodePath):

    def __init__(self, heightmap_path, height=100):
        super().__init__(BulletRigidBodyNode('terrain'))
        self.height = height
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

    def __init__(self, w=256, d=256, segs_w=16, segs_d=16):
        super().__init__(BulletRigidBodyNode('water_surface'))
        plane = Plane(w, d, segs_w, segs_d)
        self.stride = plane.stride

        self.model = plane.create()
        self.model.set_transparency(TransparencyAttrib.MAlpha)
        self.model.set_texture(base.loader.loadTexture('textures/water.png'))
        self.model.set_pos(0, 0, 0)
        self.model.reparent_to(self)

        mesh = BulletTriangleMesh()
        mesh.add_geom(self.model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape)

        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(1))
        self.set_shader_off()

    def wave(self, time, wave_h=3.0):
        geom_node = self.model.node()
        geom = geom_node.modify_geom(0)
        vdata = geom.modify_vertex_data()
        vdata_arr = vdata.modify_array(0)
        vdata_mem = memoryview(vdata_arr).cast('B').cast('f')

        for i in range(0, len(vdata_mem), self.stride):
            x, y = vdata_mem[i: i + 2]
            z = (math.sin(time + x / wave_h) + math.sin(time + y / wave_h)) * wave_h / 2
            # z = (math.sin(time + x / wave_h) + math.sin(y + x) / wave_h) * wave_h / 2
            vdata_mem[i + 2] = z


class Road(NodePath):

    def __init__(self, segs_x=4, size=256, height=20, col_radius=4, road_width=6):
        super().__init__(BulletRigidBodyNode('cylinder'))
        self.size = size - col_radius * 2
        self.height = height

        self.create_columns(col_radius)
        self.create_road(segs_x, road_width)
        self.set_texture(base.loader.load_texture('textures/concrete_01.jpg'))

        self.node().set_mass(0)
        self.set_collide_mask(BitMask32.bit(1))

    def get_start_location(self, direction=-1):
        x = self.size / 2 * direction
        z = self.get_z() + self.height
        start_pos = Point3(x, 0, z)
        start_hpr = Vec3(180, 0, 0)

        return start_pos, start_hpr

    def create_columns(self, col_radius):
        model_maker = Cylinder(
            radius=col_radius, height=self.height, segs_a=10)
        x = self.size / 2

        for direction in [-1, 1]:
            pos = Point3(x * direction, 0, 0)
            model = model_maker.create()
            model.set_pos(pos)
            model.reparent_to(self)

            shape = BulletConvexHullShape()
            shape.add_geom(model.node().get_geom(0))
            self.node().add_shape(shape, TransformState.make_pos(pos))

    def create_road(self, segs_x, road_width):
        seg = self.size / segs_x
        radius = seg / 2 + 3
        inner_radius = radius - road_width

        model_maker = Cylinder(
            radius=radius,
            inner_radius=inner_radius,
            ring_slice_deg=180,
            height=1,
        )

        for i in range(segs_x):
            if i == 0:
                geom_node = model_maker.get_geom_node()
                continue

            new_geom_node = model_maker.get_geom_node()
            rotation_deg = 0 if i % 2 == 0 else 180
            bottom_center = Point3(seg * i, 0, 0)
            model_maker.merge_geom(geom_node, new_geom_node, Vec3(0, 0, 1), bottom_center, rotation_deg)

        pos = Point3(-self.size / 2 + seg - seg / 2, 0, self.height - 1.001)
        model = model_maker.modeling(geom_node)
        model.set_pos(pos)
        model.set_tex_scale(TextureStage.get_default(), 5, 3)
        model.reparent_to(self)

        # If using BulletConvexHullShape, hollow is lost because of the shape.
        mesh = BulletTriangleMesh()
        mesh.add_geom(model.node().get_geom(0))
        shape = BulletTriangleMeshShape(mesh, dynamic=False)
        self.node().add_shape(shape, TransformState.make_pos(pos))


class Scene(NodePath):

    def __init__(self):
        super().__init__(PandaNode('scene'))
        self.reparent_to(base.render)
        self.ambient_light = BasicAmbientLight()
        self.day_light = BasicDayLight()
        self.sky = Sky()
        self.sky.reparent_to(self)

        self.terrain = Terrain('terrains/heightmap.png')
        self.terrain.reparent_to(self)
        self.terrain.set_pos(Point3(0, 0, 0))
        base.world.attach(self.terrain.node())

        self.water_surface = WaterSurface()
        self.water_surface.reparent_to(self)
        self.water_surface.set_pos(0, 0, 0)
        base.world.attach(self.water_surface.node())

        self.road = Road()
        self.road.set_pos(0, 0, 1)
        self.road.reparent_to(self)
        base.world.attach(self.road.node())

    def update(self, task_time, shadow_target):
        self.water_surface.wave(task_time)
        self.day_light.update(shadow_target)