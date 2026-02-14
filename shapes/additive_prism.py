import FreeCAD as App

from .context import Context
from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.additive_prism;
# from shapes.additive_prism import AdditivePrism
# AdditivePrism.create_prism('hexprism', 6, 5, 10)


class AdditivePrism(Shape):
    @staticmethod
    def create_prism(
        label,
        polygon,
        circumradius,
        height,
        x_offset=0,
        y_offset=0,
        z_offset=0,
        z_rotation=0,
        y_rotation=0,
        x_rotation=0,
    ):
        plane_label = "XY_Plane"
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=[label + "_prism"]):
            return None

        # Check for existing object and get children if they exist
        prism_label = label + "_prism"
        existing_obj, children = Shape._get_or_recreate_body(label, [(prism_label, "PartDesign::AdditivePrism")])

        if existing_obj is not None:
            # AdditivePrism exists, update its properties
            existing_prism = children[prism_label]
            needs_recompute = False

            # Update dimensions
            new_circumradius = f"{circumradius} mm"
            new_height = f"{height} mm"

            if existing_prism.Polygon != polygon:
                existing_prism.Polygon = polygon
                needs_recompute = True
            if str(existing_prism.Circumradius) != new_circumradius:
                existing_prism.Circumradius = new_circumradius
                needs_recompute = True
            if str(existing_prism.Height) != new_height:
                existing_prism.Height = new_height
                needs_recompute = True

            # Update angle properties
            if str(existing_prism.FirstAngle) != "0.00 °":
                existing_prism.FirstAngle = "0.00 °"
                needs_recompute = True
            if str(existing_prism.SecondAngle) != "0.00 °":
                existing_prism.SecondAngle = "0.00 °"
                needs_recompute = True

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(
                existing_prism, plane_label, x_offset, y_offset, z_offset, z_rotation, y_rotation, x_rotation
            ):
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        prism_label = label + "_prism"
        App.ActiveDocument.addObject("PartDesign::AdditivePrism", prism_label)
        prism = Context.get_object(prism_label)
        obj.addObject(prism)
        prism.Polygon = polygon
        prism.Circumradius = f"{circumradius} mm"
        prism.Height = f"{height} mm"
        prism.FirstAngle = "0.00 °"
        prism.SecondAngle = "0.00 °"

        Shape._update_attachment_and_offset(
            prism, plane_label, x_offset, y_offset, z_offset, z_rotation, y_rotation, x_rotation
        )
        App.ActiveDocument.recompute()

        return obj
