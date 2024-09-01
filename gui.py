# import direct.gui.DirectGuiGlobals as DGG
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectButton import DirectButton
from direct.interval.IntervalGlobal import Sequence, Func, Wait
from panda3d.core import CardMaker, LColor, Point3, Vec3
from panda3d.core import NodePath, TextNode
from panda3d.core import TransparencyAttrib


BASE_TEXT_COLOR = LColor(0.5, 0.5, 0.5, 1)


class SelectorFrame(DirectFrame):

    def __init__(self):
        self.pos_appear = Point3(0, -1, 0.7)
        self.pos_disappear = Point3(0, -1, 1.5)

        super().__init__(
            frameSize=(-0.65, 0.65, 0.2, -0.2),  # (left, right, bottom, top)
            frameColor=(1, 1, 1, 0.2),
            pos=self.pos_disappear
        )
        self.initialiseoptions(type(self))
        self.set_transparency(TransparencyAttrib.MAlpha)

        self.selected_level = None
        self.appeared = False
        self.create_gui()

    def create_gui(self):
        color_high = LColor(0.5, 0.5, 0.5, 1)
        color_normal = LColor(0.66, 0.66, 0.66, 1)
        self.create_label(color_high, 'Select Level')
        self.create_buttons(color_high, color_normal)

    def create_label(self, color, text):
        font = base.loader.load_font('font/Candaral.ttf')

        DirectLabel(
            parent=self,
            text=text,
            pos=Point3(0, 0, 0.08),
            text_fg=BASE_TEXT_COLOR,
            text_font=font,
            text_scale=0.12,
            frameColor=LColor(1, 1, 1, 0)
        )

    def get_text_nd(self, font, text, color):
        nd = TextNode(text)
        nd.set_text(text)
        nd.set_font(font)
        nd.set_text_scale(0.1)
        nd.set_text_color(color)
        nd.set_align(TextNode.ACenter)
        return nd

    def setup_button(self, btn, btn_color, text_nd, text_pos):
        btn.set_transparency(TransparencyAttrib.MAlpha)
        btn.set_color(btn_color)
        text_np = btn.attach_new_node(text_nd)
        text_np.set_pos(text_pos)

    def select_level(self, level):
        self.selected_level = level

    def create_buttons(self, color_high, color_normal):
        font = base.loader.load_font('font/segoeui.ttf')
        text_pos = Point3(0, 0, -0.03)
        color_normal = LColor(BASE_TEXT_COLOR.xyz + 0.16, 1)
        btn_normal_color = LColor(1, 1, 1, 0.5)
        btn_high_color = LColor(1, 1, 1, 0.7)

        cm = CardMaker('card')
        cm.set_frame(-0.1, 0.1, -0.06, 0.06)

        for num, x in enumerate([-0.45, -0.15, 0.15, 0.45], start=1):
            btn_normal = NodePath(cm.generate())
            text_nd = self.get_text_nd(font, str(num), color_normal)
            self.setup_button(btn_normal, btn_normal_color, text_nd, text_pos)

            btn_high = NodePath(cm.generate())
            text_nd = self.get_text_nd(font, str(num), BASE_TEXT_COLOR)
            self.setup_button(btn_high, btn_high_color, text_nd, text_pos)

            DirectButton(
                parent=self,
                relief=None,
                pressEffect=0,
                pos=Point3(x, 0, -0.08),
                geom=(btn_normal, btn_high, btn_high, btn_normal),
                command=self.select_level,
                extraArgs=[int(num)]
            )

    def change_status(self, status):
        self.appeared = status

    def appear(self, wait=0.5, duration=1.0):
        self.reparent_to(base.aspect2d)

        Sequence(
            Wait(wait),
            self.posInterval(duration, self.pos_appear),
            Func(self.change_status, True)
        ).start()

    def disappear(self, wait=0.5, duration=1.0):
        Sequence(
            Wait(wait),
            self.posInterval(duration, self.pos_disappear),
            Func(self.detach_node),
            Func(self.change_status, False)
        ).start()


class Caption:

    def __init__(self):
        self.display_pos = Point3(0, 0, 0.8)
        self.font = base.loader.load_font('font/Candaral.ttf')

    def show(self, text, scale=0.2, wait=1.0, duration=1.0):
        text_nd = TextNode('caption')
        text_nd.set_text(text)
        text_nd.set_font(self.font)
        text_nd.set_text_scale(scale)
        text_nd.set_align(TextNode.ACenter)

        text_nd.set_text_color(BASE_TEXT_COLOR)
        text_np = base.aspect2d.attach_new_node(text_nd)
        text_np.set_transparency(TransparencyAttrib.M_alpha)

        end, tip = text_np.get_tight_bounds()
        size = tip - end
        pos = self.display_pos - Vec3(0, 0, size.z / 2)
        text_np.set_pos(pos)

        Sequence(
            text_np.colorScaleInterval(duration, 1, 0, blendType='easeInOut'),
            text_np.colorScaleInterval(duration, 0, 1, blendType='easeInOut'),
            Func(text_np.remove_node),
        ).start()