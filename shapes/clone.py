import FreeCAD as App

from .shape import Shape
from .context import Context

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.clone;
# reload(shapes.clone); from shapes.clone import Clone
# Clone.create_clone('my_clone', 'slider_tab_base')

class Clone(Shape):
    @staticmethod
    def create_clone(label, base_obj_or_label, offset=(0, 0, 0), rotation=(0, 0, 0)):
        """
        Create a Body object with a Clone feature that references another object.

        Args:
            label: The label for the new Body containing the clone
            base_obj_or_label: The object or label to clone
            offset: Tuple of (x, y, z) offset values. Defaults to (0, 0, 0).
            rotation: Tuple of (yaw, pitch, roll) rotation values in degrees. Defaults to (0, 0, 0).

        Returns:
            The Body object containing the clone, or None if in teardown mode
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        clone_label = label + '_clone'
        if Shape._teardown_if_needed(label, created_children=[clone_label]):
            return None

        # Get the base object
        base_obj = Context.get_object(base_obj_or_label)
        if base_obj is None:
            print(f'Base object not found: {base_obj_or_label}')
            return None

        # Check for existing object and get children if they exist
        existing_obj, children = Shape._get_or_recreate_body(label, [
            (clone_label, 'PartDesign::FeatureBase')
        ])

        if existing_obj is not None:
            # Clone exists, update its properties
            existing_clone = children[clone_label]
            needs_recompute = False

            # Update BaseFeature if it changed
            if existing_clone.BaseFeature != base_obj:
                existing_clone.BaseFeature = base_obj
                needs_recompute = True

            # Create placement from offset and rotation
            target_placement = App.Placement(
                App.Vector(offset[0], offset[1], offset[2]),
                App.Rotation(rotation[0], rotation[1], rotation[2])
            )
            if existing_clone.Placement != target_placement:
                existing_clone.Placement = target_placement
                needs_recompute = True

            # Ensure the clone is the Body's Tip
            if existing_obj.Tip != existing_clone:
                existing_obj.Tip = existing_clone
                needs_recompute = True

            # Ensure the clone is in the Body's Group
            if existing_clone not in existing_obj.Group:
                existing_obj.Group = [existing_clone]
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new Body object
        obj = Shape._create_object(label)

        # Create Clone (PartDesign::FeatureBase)
        App.ActiveDocument.addObject('PartDesign::FeatureBase', clone_label)
        clone = Context.get_object(clone_label)

        # Add Clone to Body's Group
        obj.Group = [clone]

        # Set Body's Tip to the Clone
        obj.Tip = clone

        # Set Clone's BaseFeature to the original object
        clone.BaseFeature = base_obj

        # Set Placement from offset and rotation
        clone.Placement = App.Placement(
            App.Vector(offset[0], offset[1], offset[2]),
            App.Rotation(rotation[0], rotation[1], rotation[2])
        )

        App.ActiveDocument.recompute()

        return obj
