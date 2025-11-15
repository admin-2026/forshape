import FreeCAD as App

from .shape import Shape
from .context import Context

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.additive_box;
# reload(shapes.additive_box); from shapes.additive_box import AdditiveBox
# AdditiveBox.create_box('addbox', 'XY_Plane', 2, 4, 10)
# AdditiveBox.create_slot('slot', 'XY_Plane', 2, 4, 1, 0.5)

class AdditiveBox(Shape):
    @staticmethod
    def _calculate_fillet_radius_with_epsilon(radius, width, length):
        """
        Calculate fillet radius with epsilon adjustment when needed.
        Epsilon is subtracted when diameter equals width or length to prevent
        adjacent fillets from touching in FreeCAD.

        Args:
            radius: The desired fillet radius
            width: The width of the slot
            length: The length of the slot

        Returns:
            float: The adjusted radius (with epsilon subtracted if needed)
        """
        diameter = 2 * radius
        if diameter == width or diameter == length:
            epsilon = Context.get_epsilon()
            return radius - epsilon
        else:
            return radius

    @staticmethod
    def create_box(label, plane_label, length, width, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):

        # Check for existing object and get children if they exist
        box_label = label + '_box'
        existing_obj, children = Shape._get_or_recreate_body(label, [
            (box_label, 'PartDesign::AdditiveBox')
        ])

        if existing_obj is not None:
            # AdditiveBox exists, update its properties
            existing_box = children[box_label]
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

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(existing_box, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll):
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

        Shape._update_attachment_and_offset(box, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll)
        App.ActiveDocument.recompute()

        return obj

    @staticmethod
    def create_slot(label, plane_label, length, width, height, radius, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):

        # Check for existing object and get children if they exist
        slot_label = label + '_slot'
        fillet_label = label + '_fillet'
        existing_obj, children = Shape._get_or_recreate_body(label, [
            (slot_label, 'PartDesign::AdditiveBox'),
            (fillet_label, 'PartDesign::Fillet')
        ])

        if existing_obj is not None:
            # Both children exist, update their properties
            existing_slot = children[slot_label]
            existing_fillet = children[fillet_label]
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

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(existing_slot, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll):
                needs_recompute = True

            # Update fillet radius with epsilon logic
            new_radius = AdditiveBox._calculate_fillet_radius_with_epsilon(radius, width, length)

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

        Shape._update_attachment_and_offset(slot, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll)
        App.ActiveDocument.recompute()

        fillet_label = label+'_fillet'
        obj.newObject('PartDesign::Fillet', fillet_label)
        fillet = Context.get_object(fillet_label)
        fillet.Base = (slot,['Edge7','Edge5','Edge1','Edge3',])
        # Subtract epsilon only when diameter equals width or length to prevent adjacent fillets from touching
        fillet.Radius = AdditiveBox._calculate_fillet_radius_with_epsilon(radius, width, length)

        slot.Visibility = False
        App.ActiveDocument.recompute()

        return obj