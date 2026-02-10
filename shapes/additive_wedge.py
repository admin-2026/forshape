import FreeCAD as App

from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);
# from shapes.additive_wedge import AdditiveWedge
#
# # Rectangular box (no tapering) - xmax=10, ymax=5, zmax=3
# AdditiveWedge.create_wedge('box', 'XY_Plane', xmax=10, ymax=5, zmax=3)
#
# # Tapered wedge - base 10x3, top 5x2, height 5
# AdditiveWedge.create_wedge('tapered', 'XY_Plane', xmax=10, ymax=5, zmax=3, x2max=5, z2max=2)
#
# # Pyramid-like shape - base 10x10, top tapers to point (0x0), height 8
# AdditiveWedge.create_wedge('pyramid', 'XY_Plane', xmax=10, ymax=8, zmax=10, x2max=0, z2max=0)
#
# # Asymmetric wedge - offset base from origin
# AdditiveWedge.create_wedge('asymmetric', 'XY_Plane', xmin=2, xmax=12, ymax=5, zmin=1, zmax=4)
#
# # Slanted wedge - top face offset from center
# AdditiveWedge.create_wedge('slanted', 'XY_Plane', xmax=10, ymax=6, zmax=10, x2min=3, x2max=7, z2min=2, z2max=8)
#
# # Wedge with position offset and rotation
# AdditiveWedge.create_wedge('transformed', 'XY_Plane', xmax=8, ymax=4, zmax=6, x_offset=5, y_offset=3, yaw=45)
#
# # Trapezoidal prism - full control over all bounds
# AdditiveWedge.create_wedge('trapezoid', 'XY_Plane', xmin=0, xmax=10, ymin=0, ymax=5, zmin=0, zmax=8, x2min=2, x2max=8, z2min=1, z2max=7)


class AdditiveWedge(Shape):
    @staticmethod
    def create_wedge(
        label,
        plane_label,
        xmin=0,
        xmax=None,
        ymin=0,
        ymax=None,
        zmin=0,
        zmax=None,
        x2min=None,
        x2max=None,
        z2min=None,
        z2max=None,
        x_offset=0,
        y_offset=0,
        z_offset=0,
        yaw=0,
        pitch=0,
        roll=0,
    ):
        from .context import Context

        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label, created_children=[label + "_wedge"]):
            return None

        # Check for existing object and get children if they exist
        wedge_label = label + "_wedge"
        existing_obj, children = Shape._get_or_recreate_body(label, [(wedge_label, "PartDesign::AdditiveWedge")])

        if existing_obj is not None:
            # AdditiveWedge exists, update its properties
            existing_wedge = children[wedge_label]
            needs_recompute = False

            # Update dimensions
            new_xmin = f"{xmin} mm"
            new_xmax = f"{xmax} mm"
            new_ymin = f"{ymin} mm"
            new_ymax = f"{ymax} mm"
            new_zmin = f"{zmin} mm"
            new_zmax = f"{zmax} mm"
            new_x2min = f"{x2min} mm"
            new_x2max = f"{x2max} mm"
            new_z2min = f"{z2min} mm"
            new_z2max = f"{z2max} mm"

            if str(existing_wedge.Xmin) != new_xmin:
                existing_wedge.Xmin = new_xmin
                needs_recompute = True
            if str(existing_wedge.Xmax) != new_xmax:
                existing_wedge.Xmax = new_xmax
                needs_recompute = True
            if str(existing_wedge.Ymin) != new_ymin:
                existing_wedge.Ymin = new_ymin
                needs_recompute = True
            if str(existing_wedge.Ymax) != new_ymax:
                existing_wedge.Ymax = new_ymax
                needs_recompute = True
            if str(existing_wedge.Zmin) != new_zmin:
                existing_wedge.Zmin = new_zmin
                needs_recompute = True
            if str(existing_wedge.Zmax) != new_zmax:
                existing_wedge.Zmax = new_zmax
                needs_recompute = True
            if str(existing_wedge.X2min) != new_x2min:
                existing_wedge.X2min = new_x2min
                needs_recompute = True
            if str(existing_wedge.X2max) != new_x2max:
                existing_wedge.X2max = new_x2max
                needs_recompute = True
            if str(existing_wedge.Z2min) != new_z2min:
                existing_wedge.Z2min = new_z2min
                needs_recompute = True
            if str(existing_wedge.Z2max) != new_z2max:
                existing_wedge.Z2max = new_z2max
                needs_recompute = True

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(
                existing_wedge, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll
            ):
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        wedge_label = label + "_wedge"
        App.ActiveDocument.addObject("PartDesign::AdditiveWedge", wedge_label)
        wedge = Context.get_object(wedge_label)
        obj.addObject(wedge)

        # Set wedge dimensions
        wedge.Xmin = f"{xmin} mm"
        wedge.Xmax = f"{xmax} mm"
        wedge.Ymin = f"{ymin} mm"
        wedge.Ymax = f"{ymax} mm"
        wedge.Zmin = f"{zmin} mm"
        wedge.Zmax = f"{zmax} mm"
        wedge.X2min = f"{x2min} mm"
        wedge.X2max = f"{x2max} mm"
        wedge.Z2min = f"{z2min} mm"
        wedge.Z2max = f"{z2max} mm"

        Shape._update_attachment_and_offset(wedge, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll)
        App.ActiveDocument.recompute()

        return obj
