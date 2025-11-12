import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_cylinder import AdditiveCylinder
# AdditiveCylinder.create_cylinder('addcylinder', 'XY_Plane', 2, 10)

class AdditiveCylinder(Shape):
    @staticmethod
    def create_cylinder(label, plane_label, radius, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):
        from .context import Context

        # Try to get existing object with the same label
        existing_obj = Context.get_object(label)

        if existing_obj is not None:
            # Check the type of the existing object
            if existing_obj.TypeId != 'PartDesign::Body':
                # Not a Body, remove it and create new
                Context.remove_object(existing_obj)
                existing_obj = None
            else:
                # It's a Body, check if it has an AdditiveCylinder child
                cylinder_label = label + '_cylinder'
                existing_cylinder = Context.get_object(cylinder_label)

                if existing_cylinder is None or existing_cylinder.TypeId != 'PartDesign::AdditiveCylinder':
                    # Body exists but no AdditiveCylinder child, remove and recreate
                    Context.remove_object(existing_obj)
                    existing_obj = None
                else:
                    # AdditiveCylinder exists, update its properties
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

                    # Update attachment plan
                    plane_obj = Context.get_object(plane_label)
                    current_plane = existing_cylinder.AttachmentSupport[0][0] if existing_cylinder.AttachmentSupport else None
                    if current_plane != plane_obj:
                        existing_cylinder.AttachmentSupport = plane_obj
                        existing_cylinder.MapMode = 'FlatFace'
                        needs_recompute = True

                    # Update offset and rotation
                    new_offset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
                    if existing_cylinder.AttachmentOffset != new_offset:
                        existing_cylinder.AttachmentOffset = new_offset
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

        cylinder.AttachmentSupport = Context.get_object(plane_label)
        cylinder.MapMode = 'FlatFace'
        cylinder.AttachmentOffset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
        App.ActiveDocument.recompute()

        return obj
