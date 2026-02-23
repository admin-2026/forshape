import FreeCAD as App

from .context import Context
from .exceptions import ShapeException
from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.helix;
# reload(shapes.helix); from shapes.helix import Helix
# Helix.create_helix('helix1', 'my_sketch', 5, 30)


class Helix(Shape):
    @staticmethod
    def create_helix(label, sketch_label, pitch, height):
        """
        Create a body with an additive helix from an existing sketch.

        Args:
            label (str): Name/label for the helix object (Body)
            sketch_label (str): Label of the existing sketch to helix
            pitch (float): Pitch (distance per turn) in mm
            height (float): Total height of the helix in mm

        Returns:
            The created or updated Body object
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode (sketch is preserved, only helix is removed)
        if Shape._teardown_if_needed(label, created_children=[label + "_helix"]):
            return None

        # Check for existing object and get children if they exist
        helix_label = label + "_helix"
        existing_obj, children = Shape._get_or_recreate_body(label, [(helix_label, "PartDesign::AdditiveHelix")])

        if existing_obj is not None:
            # Helix exists, update its properties
            existing_helix = children[helix_label]
            needs_recompute = False

            # Update pitch
            new_pitch = f"{pitch} mm"
            if str(existing_helix.Pitch) != new_pitch:
                existing_helix.Pitch = new_pitch
                needs_recompute = True

            # Update height
            new_height = f"{height} mm"
            if str(existing_helix.Height) != new_height:
                existing_helix.Height = new_height
                needs_recompute = True

            # Update sketch reference
            sketch = Context.get_object(sketch_label)
            if sketch is None:
                raise ShapeException(
                    f"Helix '{label}' failed: Sketch '{sketch_label}' not found. "
                    f"Please check that the sketch exists before creating a helix."
                )

            current_sketch = existing_helix.Profile[0] if existing_helix.Profile else None
            if current_sketch != sketch:
                existing_helix.Profile = (sketch, [""])
                needs_recompute = True

            # Ensure reference axis is set
            if existing_helix.ReferenceAxis != (sketch, ["V_Axis"]):
                existing_helix.ReferenceAxis = (sketch, ["V_Axis"])
                needs_recompute = True

            # Ensure sketch is hidden
            if sketch.Visibility:
                sketch.Visibility = False
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        # Get the sketch
        sketch = Context.get_object(sketch_label)
        if sketch is None:
            raise ShapeException(
                f"Helix '{label}' failed: Sketch '{sketch_label}' not found. "
                f"Please check that the sketch exists before creating a helix."
            )
        sketch.Visibility = False

        # Create helix
        obj.newObject("PartDesign::AdditiveHelix", helix_label)
        helix = Context.get_object(helix_label)
        helix.Profile = (sketch, [""])
        helix.Pitch = f"{pitch} mm"
        helix.Height = f"{height} mm"
        helix.ReferenceAxis = (sketch, ["V_Axis"])

        App.ActiveDocument.recompute()

        return obj
