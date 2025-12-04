import FreeCAD as App

from .shape import Shape
from .context import Context

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.additive_box;
# reload(shapes.additive_box); from shapes.additive_box import AdditiveBox
# AdditiveBox.create_box('addbox', 'XY_Plane', 2, 4, 10)
# AdditiveBox.create_slot('slot', 'XY_Plane', 2, 4, 1, 0.5)

class AdditiveBox(Shape):
    @staticmethod
    def _calculate_center_based_rotation_offset(length, width, height, x_offset, y_offset, z_offset, yaw, pitch, roll):
        """
        Calculate adjusted offset for center-based rotation.

        By default, FreeCAD rotates boxes around their origin (left-bottom corner).
        This function calculates the offset adjustment needed to rotate around the center instead.

        Args:
            length, width, height: Box dimensions
            x_offset, y_offset, z_offset: User-specified position offsets
            yaw, pitch, roll: Rotation angles

        Returns:
            tuple: (adjusted_x_offset, adjusted_y_offset, adjusted_z_offset)
        """
        # Box center is at (length/2, width/2, height/2) from its origin
        center = App.Vector(length / 2, width / 2, height / 2)
        rotation = App.Rotation(yaw, pitch, roll)

        # Calculate displacement needed to rotate around center instead of corner
        # When rotating around center: rotate the center point and find how much it moved
        rotated_center = rotation.multVec(center)
        displacement = center - rotated_center

        # Adjust the offset to account for center-based rotation
        return (
            x_offset + displacement.x,
            y_offset + displacement.y,
            z_offset + displacement.z
        )

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
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=[label + '_box']):
            return None

        # Calculate center-based rotation offset
        adjusted_x_offset, adjusted_y_offset, adjusted_z_offset = AdditiveBox._calculate_center_based_rotation_offset(
            length, width, height, x_offset, y_offset, z_offset, yaw, pitch, roll
        )

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

            # Update attachment, offset, and rotation with adjusted offset
            if Shape._update_attachment_and_offset(existing_box, plane_label, adjusted_x_offset, adjusted_y_offset, adjusted_z_offset, yaw, pitch, roll):
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

        Shape._update_attachment_and_offset(box, plane_label, adjusted_x_offset, adjusted_y_offset, adjusted_z_offset, yaw, pitch, roll)
        App.ActiveDocument.recompute()

        return obj

    @staticmethod
    def create_slot(label, plane_label, length, width, height, radius, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Determine expected children based on radius
        slot_label = label + '_slot'
        fillet_label = label + '_fillet'

        if radius == 0:
            # No fillet needed, just create a box
            created_children = [slot_label]
            expected_children = [(slot_label, 'PartDesign::AdditiveBox')]
        else:
            # Need both slot and fillet
            created_children = [slot_label, fillet_label]
            expected_children = [
                (slot_label, 'PartDesign::AdditiveBox'),
                (fillet_label, 'PartDesign::Fillet')
            ]

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=created_children):
            return None

        # Calculate center-based rotation offset
        adjusted_x_offset, adjusted_y_offset, adjusted_z_offset = AdditiveBox._calculate_center_based_rotation_offset(
            length, width, height, x_offset, y_offset, z_offset, yaw, pitch, roll
        )

        # Check for existing object and get children if they exist
        existing_obj, children = Shape._get_or_recreate_body(label, expected_children)

        if existing_obj is not None:
            # Children exist, update their properties
            existing_slot = children[slot_label]
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

            # Update attachment, offset, and rotation with adjusted offset
            if Shape._update_attachment_and_offset(existing_slot, plane_label, adjusted_x_offset, adjusted_y_offset, adjusted_z_offset, yaw, pitch, roll):
                needs_recompute = True

            # Update fillet if it exists (radius > 0)
            if radius > 0:
                existing_fillet = children[fillet_label]
                new_radius = AdditiveBox._calculate_fillet_radius_with_epsilon(radius, width, length)

                if existing_fillet.Radius != new_radius:
                    existing_fillet.Radius = new_radius
                    needs_recompute = True

                # Ensure slot is hidden when fillet exists
                if existing_slot.Visibility != False:
                    existing_slot.Visibility = False
                    needs_recompute = True
            else:
                # No fillet, ensure slot is visible
                if existing_slot.Visibility != True:
                    existing_slot.Visibility = True
                    needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        App.ActiveDocument.addObject('PartDesign::AdditiveBox', slot_label)
        slot = Context.get_object(slot_label)
        obj.addObject(slot)
        slot.Length=f'{length} mm'
        slot.Width=f'{width} mm'
        slot.Height=f'{height} mm'

        Shape._update_attachment_and_offset(slot, plane_label, adjusted_x_offset, adjusted_y_offset, adjusted_z_offset, yaw, pitch, roll)
        App.ActiveDocument.recompute()

        # Only create fillet if radius > 0
        if radius > 0:
            obj.newObject('PartDesign::Fillet', fillet_label)
            fillet = Context.get_object(fillet_label)
            fillet.Base = (slot,['Edge1','Edge3','Edge5','Edge7',])
            # Subtract epsilon only when diameter equals width or length to prevent adjacent fillets from touching
            fillet.Radius = AdditiveBox._calculate_fillet_radius_with_epsilon(radius, width, length)

            slot.Visibility = False
            App.ActiveDocument.recompute()
        else:
            # No fillet, keep slot visible
            slot.Visibility = True

        return obj

    @staticmethod
    def create_round_side_box(label, plane_label, length, width, height, radius1, radius3, radius5, radius7, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):
        """
        Creates a box with individually rounded side edges.

        Args:
            label: Name/label for the box object
            plane_label: Plane to attach to (e.g., 'XY_Plane')
            length: Length dimension in mm
            width: Width dimension in mm
            height: Height dimension in mm
            radius1: Fillet radius for Edge1 in mm (0 for no fillet)
            radius3: Fillet radius for Edge3 in mm (0 for no fillet)
            radius5: Fillet radius for Edge5 in mm (0 for no fillet)
            radius7: Fillet radius for Edge7 in mm (0 for no fillet)
            x_offset, y_offset, z_offset: Position offsets
            yaw, pitch, roll: Rotation angles

        Returns:
            The created/updated object
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Determine expected children based on radiuses
        box_label = label + '_box'
        fillet1_label = label + '_fillet1'
        fillet3_label = label + '_fillet3'
        fillet5_label = label + '_fillet5'
        fillet7_label = label + '_fillet7'

        created_children = [box_label]
        expected_children = [(box_label, 'PartDesign::AdditiveBox')]

        # Track which fillets we need
        fillet_config = {
            'Edge1': (radius1, fillet1_label),
            'Edge3': (radius3, fillet3_label),
            'Edge5': (radius5, fillet5_label),
            'Edge7': (radius7, fillet7_label)
        }

        for edge, (radius, fillet_label) in fillet_config.items():
            if radius > 0:
                created_children.append(fillet_label)
                expected_children.append((fillet_label, 'PartDesign::Fillet'))

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=created_children):
            return None

        # Calculate center-based rotation offset
        adjusted_x_offset, adjusted_y_offset, adjusted_z_offset = AdditiveBox._calculate_center_based_rotation_offset(
            length, width, height, x_offset, y_offset, z_offset, yaw, pitch, roll
        )

        # Check for existing object and get children if they exist
        existing_obj, children = Shape._get_or_recreate_body(label, expected_children)

        if existing_obj is not None:
            # Children exist, update their properties
            existing_box = children[box_label]
            needs_recompute = False

            # Update box dimensions
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

            # Update attachment, offset, and rotation with adjusted offset
            if Shape._update_attachment_and_offset(existing_box, plane_label, adjusted_x_offset, adjusted_y_offset, adjusted_z_offset, yaw, pitch, roll):
                needs_recompute = True

            # Update each fillet if it exists
            for edge, (radius, fillet_label) in fillet_config.items():
                if radius > 0 and fillet_label in children:
                    existing_fillet = children[fillet_label]
                    new_radius = AdditiveBox._calculate_fillet_radius_with_epsilon(radius, width, length)

                    if existing_fillet.Radius != new_radius:
                        existing_fillet.Radius = new_radius
                        needs_recompute = True

            # Handle box visibility - hide if any fillet exists
            should_hide = any(radius > 0 for radius, _ in fillet_config.values())
            if existing_box.Visibility != (not should_hide):
                existing_box.Visibility = not should_hide
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        App.ActiveDocument.addObject('PartDesign::AdditiveBox', box_label)
        box = Context.get_object(box_label)
        obj.addObject(box)
        box.Length = f'{length} mm'
        box.Width = f'{width} mm'
        box.Height = f'{height} mm'

        Shape._update_attachment_and_offset(box, plane_label, adjusted_x_offset, adjusted_y_offset, adjusted_z_offset, yaw, pitch, roll)
        App.ActiveDocument.recompute()

        # Create fillets for edges with radius > 0
        last_feature = box
        has_fillets = False

        for edge, (radius, fillet_label) in fillet_config.items():
            if radius > 0:
                obj.newObject('PartDesign::Fillet', fillet_label)
                fillet = Context.get_object(fillet_label)
                fillet.Base = (last_feature, [edge])
                fillet.Radius = AdditiveBox._calculate_fillet_radius_with_epsilon(radius, width, length)
                last_feature = fillet
                has_fillets = True
                App.ActiveDocument.recompute()

        # Hide the box if we created any fillets
        if has_fillets:
            box.Visibility = False
        else:
            box.Visibility = True

        return obj