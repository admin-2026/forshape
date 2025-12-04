import FreeCAD as App

from .shape import Shape
from .context import Context

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.copy;
# reload(shapes.copy); from shapes.copy import Copy
# Copy.create_copy('my_copy', 'slider_tab_base')

class Copy(Shape):
    @staticmethod
    def create_copy(label, base_obj_or_label, offset=(0, 0, 0), rotation=(0, 0, 0)):
        """
        Create a Body object with a SimpleCopy feature that copies another object.

        Args:
            label: The label for the new Body containing the copy
            base_obj_or_label: The object or label to copy
            offset: Tuple of (x, y, z) offset values. Defaults to (0, 0, 0).
            rotation: Tuple of (yaw, pitch, roll) rotation values in degrees. Defaults to (0, 0, 0).

        Returns:
            The Body object containing the copy, or None if in teardown mode
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        copy_label = label + '_copy'
        if Shape._teardown_if_needed(label, created_children=[copy_label]):
            return None

        # Get the base object
        base_obj = Context.get_object(base_obj_or_label)
        if base_obj is None:
            print(f'Base object not found: {base_obj_or_label}')
            return None

        # Check for existing object and get children if they exist
        existing_obj, children = Shape._get_or_recreate_body(label, [
            (copy_label, 'Part::SimpleCopy')
        ])

        if existing_obj is not None:
            # Copy exists, update its properties
            existing_copy = children[copy_label]
            needs_recompute = False

            # For SimpleCopy, we need to recreate if the source changed
            # SimpleCopy doesn't have a BaseFeature property, it copies the shape at creation
            # So we'll check if we need to update the shape
            if hasattr(existing_copy, 'Source'):
                if existing_copy.Source != base_obj:
                    # Source changed, need to recreate the copy
                    existing_copy.Source = base_obj
                    needs_recompute = True

            # Create placement from offset and rotation
            target_placement = App.Placement(
                App.Vector(offset[0], offset[1], offset[2]),
                App.Rotation(rotation[0], rotation[1], rotation[2])
            )
            if existing_copy.Placement != target_placement:
                existing_copy.Placement = target_placement
                needs_recompute = True

            # Ensure the copy is the Body's Tip
            if existing_obj.Tip != existing_copy:
                existing_obj.Tip = existing_copy
                needs_recompute = True

            # Ensure the copy is in the Body's Group
            if existing_copy not in existing_obj.Group:
                existing_obj.Group = [existing_copy]
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new Body object
        obj = Shape._create_object(label)

        # Create SimpleCopy
        App.ActiveDocument.addObject('Part::SimpleCopy', copy_label)
        copy = Context.get_object(copy_label)

        # Add Copy to Body's Group
        obj.Group = [copy]

        # Set Body's Tip to the Copy
        obj.Tip = copy

        # Get the shape from the base object and copy it
        if hasattr(base_obj, 'Shape'):
            copy.Shape = base_obj.Shape.copy()
        elif hasattr(base_obj, 'Tip') and hasattr(base_obj.Tip, 'Shape'):
            # If base_obj is a Body, use its Tip's shape
            copy.Shape = base_obj.Tip.Shape.copy()

        # Set Placement from offset and rotation
        copy.Placement = App.Placement(
            App.Vector(offset[0], offset[1], offset[2]),
            App.Rotation(rotation[0], rotation[1], rotation[2])
        )

        App.ActiveDocument.recompute()

        return obj
