import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_sphere import AdditiveSphere
# AdditiveSphere.create_sphere('addsphere', 5)


class AdditiveSphere(Shape):
    @staticmethod
    def create_sphere(label, radius, x_offset=0, y_offset=0, z_offset=0):
        from .context import Context

        # Default values for internal use
        plane_label = "XY_Plane"
        yaw = 0
        pitch = 0
        roll = 0

        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=[label + "_sphere"]):
            return None

        # Check for existing object and get children if they exist
        sphere_label = label + "_sphere"
        existing_obj, children = Shape._get_or_recreate_body(label, [(sphere_label, "PartDesign::AdditiveSphere")])

        if existing_obj is not None:
            # AdditiveSphere exists, update its properties
            existing_sphere = children[sphere_label]
            needs_recompute = False

            # Update dimensions
            new_radius = f"{radius} mm"

            if str(existing_sphere.Radius) != new_radius:
                existing_sphere.Radius = new_radius
                needs_recompute = True

            # Update angle properties
            if str(existing_sphere.Angle1) != "-90.00 °":
                existing_sphere.Angle1 = "-90.00 °"
                needs_recompute = True
            if str(existing_sphere.Angle2) != "90.00 °":
                existing_sphere.Angle2 = "90.00 °"
                needs_recompute = True
            if str(existing_sphere.Angle3) != "360.00 °":
                existing_sphere.Angle3 = "360.00 °"
                needs_recompute = True

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(
                existing_sphere, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll
            ):
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        sphere_label = label + "_sphere"
        App.ActiveDocument.addObject("PartDesign::AdditiveSphere", sphere_label)
        sphere = Context.get_object(sphere_label)
        obj.addObject(sphere)
        sphere.Radius = f"{radius} mm"
        sphere.Angle1 = "-90.00 °"
        sphere.Angle2 = "90.00 °"
        sphere.Angle3 = "360.00 °"

        Shape._update_attachment_and_offset(sphere, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll)
        App.ActiveDocument.recompute()

        return obj
