import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_box import AdditiveBox
# AdditiveBox.create_box('addbox', 'XY_Plane', 2, 4, 10)

class AdditiveBox(Shape):
    @staticmethod
    def create_box(label, plane_label, length, width, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):
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
                # It's a Body, check if it has an AdditiveBox child
                box_label = label + '_box'
                existing_box = App.ActiveDocument.getObject(box_label)

                if existing_box is None or existing_box.TypeId != 'PartDesign::AdditiveBox':
                    # Body exists but no AdditiveBox child, remove and recreate
                    Context.remove_object(existing_obj)
                    existing_obj = None
                else:
                    # AdditiveBox exists, update its properties
                    needs_recompute = False

                    # Update dimensions
                    new_length = f'{length} mm'
                    new_width = f'{width} mm'
                    new_height = f'{height} mm'

                    if str(existing_box.Length) != new_length:
                        existing_box.Length = new_length
                        needs_recompute = True
                    if str(existing_box.Width) != new_width:
                        existing_box.Width = new_width
                        needs_recompute = True
                    if str(existing_box.Height) != new_height:
                        existing_box.Height = new_height
                        needs_recompute = True

                    # Update attachment plan
                    plane_obj = App.ActiveDocument.getObject(plane_label)
                    current_plane = existing_box.AttachmentSupport[0][0] if existing_box.AttachmentSupport else None
                    if current_plane != plane_obj:
                        existing_box.AttachmentSupport = plane_obj
                        existing_box.MapMode = 'FlatFace'
                        needs_recompute = True

                    # Update offset and rotation
                    new_offset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
                    if existing_box.AttachmentOffset != new_offset:
                        existing_box.AttachmentOffset = new_offset
                        needs_recompute = True

                    if needs_recompute:
                        App.ActiveDocument.recompute()

                    return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        box_label = label+'_box'
        App.ActiveDocument.addObject('PartDesign::AdditiveBox', box_label)
        box = App.ActiveDocument.getObject(box_label)
        obj.addObject(box)
        box.Length=f'{length} mm'
        box.Width=f'{width} mm'
        box.Height=f'{height} mm'

        box.AttachmentSupport = App.ActiveDocument.getObject(plane_label)
        box.MapMode = 'FlatFace'
        box.AttachmentOffset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
        App.ActiveDocument.recompute()

        return obj
