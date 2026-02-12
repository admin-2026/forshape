import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_ellipsoid import AdditiveEllipsoid
# AdditiveEllipsoid.create_ellipsoid('addellipsoid', 5, 3, 2)


class AdditiveEllipsoid(Shape):
    @staticmethod
    def create_ellipsoid(label, radius_x, radius_y, radius_z, x_offset=0, y_offset=0, z_offset=0):
        from .context import Context

        # Default values for internal use
        plane_label = "XY_Plane"
        z_rotation = 0
        y_rotation = 0
        x_rotation = 0

        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=[label + "_ellipsoid"]):
            return None

        # Check for existing object and get children if they exist
        ellipsoid_label = label + "_ellipsoid"
        existing_obj, children = Shape._get_or_recreate_body(
            label, [(ellipsoid_label, "PartDesign::AdditiveEllipsoid")]
        )

        if existing_obj is not None:
            # AdditiveEllipsoid exists, update its properties
            existing_ellipsoid = children[ellipsoid_label]
            needs_recompute = False

            # Update dimensions
            new_radius_x = f"{radius_x} mm"
            new_radius_y = f"{radius_y} mm"
            new_radius_z = f"{radius_z} mm"

            if str(existing_ellipsoid.Radius1) != new_radius_x:
                existing_ellipsoid.Radius1 = new_radius_x
                needs_recompute = True
            if str(existing_ellipsoid.Radius2) != new_radius_y:
                existing_ellipsoid.Radius2 = new_radius_y
                needs_recompute = True
            if str(existing_ellipsoid.Radius3) != new_radius_z:
                existing_ellipsoid.Radius3 = new_radius_z
                needs_recompute = True

            # Update angle properties
            if str(existing_ellipsoid.Angle1) != "-90.00 °":
                existing_ellipsoid.Angle1 = "-90.00 °"
                needs_recompute = True
            if str(existing_ellipsoid.Angle2) != "90.00 °":
                existing_ellipsoid.Angle2 = "90.00 °"
                needs_recompute = True
            if str(existing_ellipsoid.Angle3) != "360.00 °":
                existing_ellipsoid.Angle3 = "360.00 °"
                needs_recompute = True

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(
                existing_ellipsoid, plane_label, x_offset, y_offset, z_offset, z_rotation, y_rotation, x_rotation
            ):
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        ellipsoid_label = label + "_ellipsoid"
        App.ActiveDocument.addObject("PartDesign::AdditiveEllipsoid", ellipsoid_label)
        ellipsoid = Context.get_object(ellipsoid_label)
        obj.addObject(ellipsoid)
        ellipsoid.Radius1 = f"{radius_x} mm"
        ellipsoid.Radius2 = f"{radius_y} mm"
        ellipsoid.Radius3 = f"{radius_z} mm"
        ellipsoid.Angle1 = "-90.00 °"
        ellipsoid.Angle2 = "90.00 °"
        ellipsoid.Angle3 = "360.00 °"

        Shape._update_attachment_and_offset(
            ellipsoid, plane_label, x_offset, y_offset, z_offset, z_rotation, y_rotation, x_rotation
        )
        App.ActiveDocument.recompute()

        return obj
