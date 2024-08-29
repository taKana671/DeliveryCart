# import direct.gui.DirectGuiGlobals as DGG
from direct.gui.DirectFrame import DirectFrame
from direct.gui.DirectLabel import DirectLabel
from direct.gui.DirectButton import DirectButton
from panda3d.core import CardMaker, LColor, Point3
from panda3d.core import NodePath, TextNode
from panda3d.core import TransparencyAttrib


class Frame(DirectFrame):

    def __init__(self):
        super().__init__(
            parent=base.aspect2d,
            frameSize=(-0.65, 0.65, 0.2, -0.2),  # (left, right, bottom, top)
            frameColor=(1, 1, 1, 0.2),
            pos=(0, 0, 0.7)
        )
        self.initialiseoptions(type(self))
        self.set_transparency(TransparencyAttrib.MAlpha)
        self.selected_level = None

        color_high = LColor(0.5, 0.5, 0.5, 1)
        color_normal = LColor(0.66, 0.66, 0.66, 1)
        self.create_label(color_high, 'Select Level')
        self.create_buttons(color_high, color_normal)


    def select_level(self, level):
        self.selected_level = level
        print(self.selected_level, type(level))

    def create_label(self, color, text):
        font = base.loader.load_font('font/Candaral.ttf')

        DirectLabel(
            parent=self,
            text=text,
            pos=Point3(0, 0, 0.08),
            text_fg=color,
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
        return nd

    def create_buttons(self, color_high, color_normal):
        font = base.loader.load_font('font/segoeui.ttf')
        text_pos = Point3(-0.03, 0, -0.03)
        alpha = 0.5

        cm = CardMaker('card')
        cm.set_frame(-0.1, 0.1, -0.06, 0.06)

        for num, x in enumerate([-0.45, -0.15, 0.15, 0.45], start=1):
            btn_normal = NodePath(cm.generate())
            btn_normal.set_transparency(TransparencyAttrib.MAlpha)
            btn_normal.set_color(LColor(1, 1, 1, alpha))
            text_nd = self.get_text_nd(font, str(num), color_normal)
            text_np = btn_normal.attach_new_node(text_nd)
            text_np.set_pos(text_pos)

            btn_high = NodePath(cm.generate())
            btn_high.set_transparency(TransparencyAttrib.MAlpha)
            btn_high.set_color(LColor(1, 1, 1, alpha + 1))
            text_nd = self.get_text_nd(font, str(num), color_high)
            text_np = btn_high.attach_new_node(text_nd)
            text_np.set_pos(text_pos)

            DirectButton(
                parent=self,
                relief=None,
                pressEffect=0,
                pos=Point3(x, 0, -0.08),
                geom=(btn_normal, btn_high, btn_high, btn_normal),
                command=self.select_level,
                extraArgs=[int(num)]
            )