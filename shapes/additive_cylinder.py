import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_cylinder import AdditiveCylinder
# AdditiveCylinder.create_cylinder('addcylinder', 'XY_Plane', 2, 10)

class AdditiveCylinder(Shape):
    @staticmethod
    def create_cylinder(label, plane_label, radius, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):
        obj = Shape._create_object(label)

        cylinder_label = label+'_cylinder'
        App.ActiveDocument.addObject('PartDesign::AdditiveCylinder', cylinder_label)
        cylinder = App.ActiveDocument.getObject(cylinder_label)
        obj.addObject(cylinder)
        cylinder.Radius=f'{radius} mm'
        cylinder.Height=f'{height} mm'
        cylinder.Angle='360.00 °'
        cylinder.FirstAngle='0.00 °'
        cylinder.SecondAngle='0.00 °'

        cylinder.AttachmentSupport = App.ActiveDocument.getObject(plane_label)
        cylinder.AttachmentOffset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
        App.ActiveDocument.recompute()
