import FreeCAD as App

from .context import Context
from .exceptions import ShapeException
from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.loft;
# reload(shapes.loft); from shapes.loft import Loft
# Loft.create_loft('loft1', ['sketch_bottom', 'sketch_top'])


class Loft(Shape):
    @staticmethod
    def create_loft(label, sketch_labels):
        """
        Create a body with an additive loft through existing sketches.

        Args:
            label (str): Name/label for the loft object (Body)
            sketch_labels (list): Ordered list of sketch labels to loft through

        Returns:
            The created or updated Body object
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode (sketches are preserved, only loft is removed)
        if Shape._teardown_if_needed(label, created_children=[label + "_loft"]):
            return None

        # Check for existing object and get children if they exist
        loft_label = label + "_loft"
        existing_obj, children = Shape._get_or_recreate_body(label, [(loft_label, "PartDesign::AdditiveLoft")])

        if existing_obj is not None:
            # Loft exists, update its properties
            existing_loft = children[loft_label]
            needs_recompute = False

            # Resolve sketches
            sketches = _resolve_sketches(label, sketch_labels)

            # Update sections
            if list(existing_loft.Sections) != sketches:
                existing_loft.Sections = sketches
                needs_recompute = True

            # Hide all sketches
            for sketch in sketches:
                if sketch.Visibility:
                    sketch.Visibility = False
                    needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        # Resolve and hide sketches
        sketches = _resolve_sketches(label, sketch_labels)
        for sketch in sketches:
            sketch.Visibility = False

        # Create loft
        obj.newObject("PartDesign::AdditiveLoft", loft_label)
        loft = Context.get_object(loft_label)
        loft.Sections = sketches

        App.ActiveDocument.recompute()

        return obj


def _resolve_sketches(label, sketch_labels):
    sketches = []
    for sketch_label in sketch_labels:
        sketch = Context.get_object(sketch_label)
        if sketch is None:
            raise ShapeException(
                f"Loft '{label}' failed: Sketch '{sketch_label}' not found. "
                f"Please check that the sketch exists before creating a loft."
            )
        sketches.append(sketch)
    return sketches
