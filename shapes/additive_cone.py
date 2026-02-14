import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_cone import AdditiveCone
# AdditiveCone.create_cone('addcone', 5, 0, 10)


class AdditiveCone(Shape):
    @staticmethod
    def create_cone(
        label,
        base_radius,
        top_radius,
        height,
        x_offset=0,
        y_offset=0,
        z_offset=0,
        z_rotation=0,
        y_rotation=0,
        x_rotation=0,
    ):
        plane_label = "XY_Plane"
        from .context import Context

        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=[label + "_cone"]):
            return None

        # Check for existing object and get children if they exist
        cone_label = label + "_cone"
        existing_obj, children = Shape._get_or_recreate_body(label, [(cone_label, "PartDesign::AdditiveCone")])

        if existing_obj is not None:
            # AdditiveCone exists, update its properties
            existing_cone = children[cone_label]
            needs_recompute = False

            # Update dimensions
            new_base_radius = f"{base_radius} mm"
            new_top_radius = f"{top_radius} mm"
            new_height = f"{height} mm"

            if str(existing_cone.Radius1) != new_base_radius:
                existing_cone.Radius1 = new_base_radius
                needs_recompute = True
            if str(existing_cone.Radius2) != new_top_radius:
                existing_cone.Radius2 = new_top_radius
                needs_recompute = True
            if str(existing_cone.Height) != new_height:
                existing_cone.Height = new_height
                needs_recompute = True

            # Update angle properties
            if str(existing_cone.Angle) != "360.00 °":
                existing_cone.Angle = "360.00 °"
                needs_recompute = True

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(
                existing_cone, plane_label, x_offset, y_offset, z_offset, z_rotation, y_rotation, x_rotation
            ):
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        cone_label = label + "_cone"
        App.ActiveDocument.addObject("PartDesign::AdditiveCone", cone_label)
        cone = Context.get_object(cone_label)
        obj.addObject(cone)
        cone.Radius1 = f"{base_radius} mm"
        cone.Radius2 = f"{top_radius} mm"
        cone.Height = f"{height} mm"
        cone.Angle = "360.00 °"

        Shape._update_attachment_and_offset(
            cone, plane_label, x_offset, y_offset, z_offset, z_rotation, y_rotation, x_rotation
        )
        App.ActiveDocument.recompute()

        return obj
