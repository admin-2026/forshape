import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_box import AdditiveBox
# AdditiveBox.create_box('addbox', 'XY_Plane', 2, 4, 10)

class AdditiveBox(Shape):
    @staticmethod
    def create_box(label, plane_label, length, width, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):
        obj = Shape._create_object(label)

        box_label = label+'_box'
        App.ActiveDocument.addObject('PartDesign::AdditiveBox', box_label)
        box = App.ActiveDocument.getObject(box_label)
        obj.addObject(box)
        box.Length=f'{length} mm'
        box.Width=f'{width} mm'
        box.Height=f'{height} mm'

        box.AttachmentSupport = App.ActiveDocument.getObject(plane_label)
        box.AttachmentOffset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
        App.ActiveDocument.recompute()
