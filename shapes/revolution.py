import FreeCAD as App

from .context import Context
from .exceptions import ShapeException
from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.revolution;
# reload(shapes.revolution); from shapes.revolution import Revolution
# Revolution.create_revolution('rev1', 'my_sketch', 360)


class Revolution(Shape):
    @staticmethod
    def create_revolution(label, sketch_label, angle=360):
        """
        Create a body with a revolution from an existing sketch.

        Args:
            label (str): Name/label for the revolution object (Body)
            sketch_label (str): Label of the existing sketch to revolve
            angle (float): Revolution angle in degrees (default: 360 for full revolution)

        Returns:
            The created or updated Body object
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode (sketch is preserved, only revolution is removed)
        if Shape._teardown_if_needed(label, created_children=[label + "_revolution"]):
            return None

        # Check for existing object and get children if they exist
        revolution_label = label + "_revolution"
        existing_obj, children = Shape._get_or_recreate_body(label, [(revolution_label, "PartDesign::Revolution")])

        if existing_obj is not None:
            # Revolution exists, update its properties
            existing_revolution = children[revolution_label]
            needs_recompute = False

            # Update angle
            new_angle = f"{angle} °"
            if str(existing_revolution.Angle) != new_angle:
                existing_revolution.Angle = new_angle
                needs_recompute = True

            # Update sketch reference
            sketch = Context.get_object(sketch_label)
            if sketch is None:
                raise ShapeException(
                    f"Revolution '{label}' failed: Sketch '{sketch_label}' not found. "
                    f"Please check that the sketch exists before creating a revolution."
                )

            current_sketch = existing_revolution.Profile[0] if existing_revolution.Profile else None
            if current_sketch != sketch:
                existing_revolution.Profile = (sketch, [""])
                needs_recompute = True

            # Ensure reference axis is set
            if existing_revolution.ReferenceAxis != (sketch, ["V_Axis"]):
                existing_revolution.ReferenceAxis = (sketch, ["V_Axis"])
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
                f"Revolution '{label}' failed: Sketch '{sketch_label}' not found. "
                f"Please check that the sketch exists before creating a revolution."
            )
        sketch.Visibility = False

        # Create revolution
        obj.newObject("PartDesign::Revolution", revolution_label)
        revolution = Context.get_object(revolution_label)
        revolution.Profile = (sketch, [""])
        revolution.Angle = f"{angle} °"
        revolution.ReferenceAxis = (sketch, ["V_Axis"])

        App.ActiveDocument.recompute()

        return obj
