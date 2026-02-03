import FreeCAD as App

from .context import Context
from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.pad;
# reload(shapes.pad); from shapes.pad import Pad
# Pad.create_pad('pad1', 'hexagon_sketch', 1)


class Pad(Shape):
    @staticmethod
    def create_pad(label, sketch_label, height):
        """
        Create a body with a pad from an existing sketch.

        Args:
            label (str): Name/label for the pad object (Body)
            sketch_label (str): Label of the existing sketch to pad
            height (float): Extrusion height in mm

        Returns:
            The created or updated Body object
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode (sketch is preserved, only pad is removed)
        if Shape._teardown_if_needed(label, created_children=[label + "_pad"]):
            return None

        # Check for existing object and get children if they exist
        pad_label = label + "_pad"
        existing_obj, children = Shape._get_or_recreate_body(label, [(pad_label, "PartDesign::Pad")])

        if existing_obj is not None:
            # Pad exists, update its properties
            existing_pad = children[pad_label]
            needs_recompute = False

            # Update height
            new_height = f"{height} mm"
            if str(existing_pad.Length) != new_height:
                existing_pad.Length = new_height
                needs_recompute = True

            # Update sketch reference
            sketch = Context.get_object(sketch_label)
            if sketch is None:
                raise ValueError(f"Sketch not found: '{sketch_label}'")

            current_sketch = existing_pad.Profile[0] if existing_pad.Profile else None
            if current_sketch != sketch:
                existing_pad.Profile = (sketch, [""])
                needs_recompute = True

            # Ensure midplane mode is enabled
            if existing_pad.Midplane != 1:
                existing_pad.Midplane = 1
                needs_recompute = True

            # Ensure reference axis is set
            if existing_pad.ReferenceAxis != (sketch, ["N_Axis"]):
                existing_pad.ReferenceAxis = (sketch, ["N_Axis"])
                needs_recompute = True

            # Ensure sketch is hidden
            if sketch.Visibility != False:
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
            raise ValueError(f"Sketch not found: '{sketch_label}'")
        sketch.Visibility = False

        # Create pad
        obj.newObject("PartDesign::Pad", pad_label)
        pad = Context.get_object(pad_label)
        pad.Profile = (sketch, [""])
        pad.Length = f"{height} mm"
        pad.ReferenceAxis = (sketch, ["N_Axis"])
        pad.Midplane = 1

        App.ActiveDocument.recompute()

        return obj
