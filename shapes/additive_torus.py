import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_torus import AdditiveTorus
# AdditiveTorus.create_torus('addtorus', 'XY_Plane', 10, 2)


class AdditiveTorus(Shape):
    @staticmethod
    def create_torus(
        label,
        plane_label,
        ring_radius,
        tube_radius,
        x_offset=0,
        y_offset=0,
        z_offset=0,
        z_rotation=0,
        y_rotation=0,
        x_rotation=0,
    ):
        from .context import Context

        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=[label + "_torus"]):
            return None

        # Check for existing object and get children if they exist
        torus_label = label + "_torus"
        existing_obj, children = Shape._get_or_recreate_body(label, [(torus_label, "PartDesign::AdditiveTorus")])

        if existing_obj is not None:
            # AdditiveTorus exists, update its properties
            existing_torus = children[torus_label]
            needs_recompute = False

            # Update dimensions
            new_ring_radius = f"{ring_radius} mm"
            new_tube_radius = f"{tube_radius} mm"

            if str(existing_torus.Radius1) != new_ring_radius:
                existing_torus.Radius1 = new_ring_radius
                needs_recompute = True
            if str(existing_torus.Radius2) != new_tube_radius:
                existing_torus.Radius2 = new_tube_radius
                needs_recompute = True

            # Update angle properties
            if str(existing_torus.Angle1) != "-180.00 °":
                existing_torus.Angle1 = "-180.00 °"
                needs_recompute = True
            if str(existing_torus.Angle2) != "180.00 °":
                existing_torus.Angle2 = "180.00 °"
                needs_recompute = True
            if str(existing_torus.Angle3) != "360.00 °":
                existing_torus.Angle3 = "360.00 °"
                needs_recompute = True

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(
                existing_torus, plane_label, x_offset, y_offset, z_offset, z_rotation, y_rotation, x_rotation
            ):
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        torus_label = label + "_torus"
        App.ActiveDocument.addObject("PartDesign::AdditiveTorus", torus_label)
        torus = Context.get_object(torus_label)
        obj.addObject(torus)
        torus.Radius1 = f"{ring_radius} mm"
        torus.Radius2 = f"{tube_radius} mm"
        torus.Angle1 = "-180.00 °"
        torus.Angle2 = "180.00 °"
        torus.Angle3 = "360.00 °"

        Shape._update_attachment_and_offset(
            torus, plane_label, x_offset, y_offset, z_offset, z_rotation, y_rotation, x_rotation
        )
        App.ActiveDocument.recompute()

        return obj
