import FreeCAD as App

from .shape import Shape
from .context import Context

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.additive_box;
# reload(shapes.additive_box); from shapes.additive_box import AdditiveBox
# AdditiveBox.create_box('addbox', 'XY_Plane', 2, 4, 10)
# AdditiveBox.create_slot('slot', 'XY_Plane', 2, 4, 1, 0.5)

class AdditiveBox(Shape):
    @staticmethod
    def create_box(label, plane_label, length, width, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):

        # Try to get existing object with the same label
        existing_obj = Context.get_object(label)

        if existing_obj is not None:
            # Check if the existing object is the document itself
            if existing_obj == App.ActiveDocument:
                # Don't move the document to trash, just continue creation
                existing_obj = None
            # Check the type of the existing object
            elif existing_obj.TypeId != 'PartDesign::Body':
                # Not a Body, move to trash and create new
                Shape._move_to_trash_bin(existing_obj)
                existing_obj = None
            else:
                # It's a Body, check if it has an AdditiveBox child
                box_label = label + '_box'
                existing_box = Context.get_object(box_label)

                if existing_box is not None and existing_box.getParent() != existing_obj:
                    # Box exists but has wrong parent - label conflict
                    other_parent = existing_box.getParent()
                    other_parent_label = other_parent.Label if other_parent else "None"
                    raise ValueError(f"Creating object with conflicting label: '{box_label}' already exists with different parent '{other_parent_label}'")

                if existing_box is None or existing_box.TypeId != 'PartDesign::AdditiveBox':
                    # Body exists but no AdditiveBox child, move to trash and recreate
                    Shape._move_to_trash_bin(existing_obj)
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
                    plane_obj = Context.get_object(plane_label)
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
        box = Context.get_object(box_label)
        obj.addObject(box)
        box.Length=f'{length} mm'
        box.Width=f'{width} mm'
        box.Height=f'{height} mm'

        box.AttachmentSupport = Context.get_object(plane_label)
        box.MapMode = 'FlatFace'
        box.AttachmentOffset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
        App.ActiveDocument.recompute()

        return obj

    @staticmethod
    def create_slot(label, plane_label, length, width, height, radius, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):

        # Try to get existing object with the same label
        existing_obj = Context.get_object(label)

        if existing_obj is not None:
            # Check if the existing object is the document itself
            if existing_obj == App.ActiveDocument:
                # Don't move the document to trash, just continue creation
                existing_obj = None
            # Check the type of the existing object
            elif existing_obj.TypeId != 'PartDesign::Body':
                # Not a Body, move to trash and create new
                Shape._move_to_trash_bin(existing_obj)
                existing_obj = None
            else:
                # It's a Body, check if it has the expected slot and fillet children
                slot_label = label + '_slot'
                fillet_label = label + '_fillet'
                existing_slot = Context.get_object(slot_label)
                existing_fillet = Context.get_object(fillet_label)

                if existing_slot is not None and existing_slot.getParent() != existing_obj:
                    # Slot exists but has wrong parent - label conflict
                    other_parent = existing_slot.getParent()
                    other_parent_label = other_parent.Label if other_parent else "None"
                    raise ValueError(f"Creating object with conflicting label: '{slot_label}' already exists with different parent '{other_parent_label}'")
                if existing_fillet is not None existing_fillet.getParent() != existing_obj:
                    # Fillet exists but has wrong parent - label conflict
                    other_parent = existing_fillet.getParent()
                    other_parent_label = other_parent.Label if other_parent else "None"
                    raise ValueError(f"Creating object with conflicting label: '{fillet_label}' already exists with different parent '{other_parent_label}'")

                if (existing_slot is None or existing_slot.TypeId != 'PartDesign::AdditiveBox' or
                    existing_fillet is None or existing_fillet.TypeId != 'PartDesign::Fillet'):
                    # Body exists but children are missing or wrong type, move to trash and recreate
                    Shape._move_to_trash_bin(existing_obj)
                    existing_obj = None
                else:
                    # Both children exist, update their properties
                    needs_recompute = False

                    # Update slot dimensions
                    new_length = f'{length} mm'
                    new_width = f'{width} mm'
                    new_height = f'{height} mm'

                    if str(existing_slot.Length) != new_length:
                        existing_slot.Length = new_length
                        needs_recompute = True
                    if str(existing_slot.Width) != new_width:
                        existing_slot.Width = new_width
                        needs_recompute = True
                    if str(existing_slot.Height) != new_height:
                        existing_slot.Height = new_height
                        needs_recompute = True

                    # Update attachment plane
                    plane_obj = Context.get_object(plane_label)
                    current_plane = existing_slot.AttachmentSupport[0][0] if existing_slot.AttachmentSupport else None
                    if current_plane != plane_obj:
                        existing_slot.AttachmentSupport = plane_obj
                        existing_slot.MapMode = 'FlatFace'
                        needs_recompute = True

                    # Update offset and rotation
                    new_offset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
                    if existing_slot.AttachmentOffset != new_offset:
                        existing_slot.AttachmentOffset = new_offset
                        needs_recompute = True

                    # Update fillet radius with epsilon logic
                    diameter = 2 * radius
                    if diameter == width or diameter == length:
                        epsilon = Context.get_epsilon()
                        new_radius = radius - epsilon
                    else:
                        new_radius = radius

                    if existing_fillet.Radius != new_radius:
                        existing_fillet.Radius = new_radius
                        needs_recompute = True

                    # Ensure slot is hidden
                    if existing_slot.Visibility != False:
                        existing_slot.Visibility = False
                        needs_recompute = True

                    if needs_recompute:
                        App.ActiveDocument.recompute()

                    return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        slot_label = label+'_slot'
        App.ActiveDocument.addObject('PartDesign::AdditiveBox', slot_label)
        slot = Context.get_object(slot_label)
        obj.addObject(slot)
        slot.Length=f'{length} mm'
        slot.Width=f'{width} mm'
        slot.Height=f'{height} mm'

        slot.AttachmentSupport = Context.get_object(plane_label)
        slot.MapMode = 'FlatFace'
        slot.AttachmentOffset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
        App.ActiveDocument.recompute()

        fillet_label = label+'_fillet'
        obj.newObject('PartDesign::Fillet', fillet_label)
        fillet = Context.get_object(fillet_label)
        fillet.Base = (slot,['Edge7','Edge5','Edge1','Edge3',])
        # Subtract epsilon only when diameter equals width or length to prevent adjacent fillets from touching
        diameter = 2 * radius
        if diameter == width or diameter == length:
            epsilon = Context.get_epsilon()
            fillet.Radius = radius - epsilon
        else:
            fillet.Radius = radius

        slot.Visibility = False
        App.ActiveDocument.recompute()

        return obj