import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_cylinder import AdditiveCylinder
# AdditiveCylinder.create_cylinder('addcylinder', 'XY_Plane', 2, 10)

class AdditiveCylinder(Shape):
    @staticmethod
    def create_cylinder(label, plane_label, radius, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):
        from .context import Context

        # Handle quick rebuild mode
        quick_rebuild_obj = Shape._quick_rebuild_if_possible(label)
        if quick_rebuild_obj is not None:
            return quick_rebuild_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=[label + '_cylinder']):
            return None

        # Check for existing object and get children if they exist
        cylinder_label = label + '_cylinder'
        existing_obj, children = Shape._get_or_recreate_body(label, [
            (cylinder_label, 'PartDesign::AdditiveCylinder')
        ])

        if existing_obj is not None:
            # AdditiveCylinder exists, update its properties
            existing_cylinder = children[cylinder_label]
            needs_recompute = False

            # Update dimensions
            new_radius = f'{radius} mm'
            new_height = f'{height} mm'

            if str(existing_cylinder.Radius) != new_radius:
                existing_cylinder.Radius = new_radius
                needs_recompute = True
            if str(existing_cylinder.Height) != new_height:
                existing_cylinder.Height = new_height
                needs_recompute = True

            # Update angle properties
            if str(existing_cylinder.Angle) != '360.00 °':
                existing_cylinder.Angle = '360.00 °'
                needs_recompute = True
            if str(existing_cylinder.FirstAngle) != '0.00 °':
                existing_cylinder.FirstAngle = '0.00 °'
                needs_recompute = True
            if str(existing_cylinder.SecondAngle) != '0.00 °':
                existing_cylinder.SecondAngle = '0.00 °'
                needs_recompute = True

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(existing_cylinder, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll):
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        cylinder_label = label+'_cylinder'
        App.ActiveDocument.addObject('PartDesign::AdditiveCylinder', cylinder_label)
        cylinder = Context.get_object(cylinder_label)
        obj.addObject(cylinder)
        cylinder.Radius=f'{radius} mm'
        cylinder.Height=f'{height} mm'
        cylinder.Angle='360.00 °'
        cylinder.FirstAngle='0.00 °'
        cylinder.SecondAngle='0.00 °'

        Shape._update_attachment_and_offset(cylinder, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll)
        App.ActiveDocument.recompute()

        return obj
