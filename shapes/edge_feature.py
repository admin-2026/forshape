import FreeCAD as App

from .context import Context
from .exceptions import ShapeException
from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.edge_feature;
# reload(shapes.edge_feature); from shapes.edge_feature import EdgeFeature
# EdgeFeature.add_fillet('fillet1', 'b4', ['Edge1', 'Edge2'], 2)


class EdgeFeature(Shape):
    @staticmethod
    def _raise_if_feature_error(label, feature_type, error_message, feature_obj=None):
        """
        Check if the feature object has errors and raise an appropriate error.
        Must be called after App.ActiveDocument.recompute().

        Args:
            label: The feature label
            feature_type: Type of feature ('Fillet' or 'Chamfer')
            error_message: The actionable error message to display
            feature_obj: The feature object to check for errors after recompute (optional)
        """
        # Check if the feature object has errors (FreeCAD sometimes stores errors here instead of raising)
        if hasattr(feature_obj, "getStatusString"):
            original_error = feature_obj.getStatusString()
            if original_error == "Valid":
                return
            if "BRep_API: command not done" in original_error:
                raise ShapeException(
                    f"{feature_type} '{label}' failed: {error_message} Original error: {original_error}"
                )
            else:
                raise ShapeException(f"{feature_type} '{label}' failed: {original_error}.")

    @staticmethod
    def add_fillet(label, object_label, edges, radius):
        """
        Add a fillet feature to selected edges of an existing object.

        Args:
            label (str): Name/label for the fillet feature
            object_label (str): Label of the existing object to add fillet to
            edges (list): List of edge labels (e.g., ['Edge1', 'Edge2', 'Edge3'])
            radius (float): Fillet radius in mm

        Returns:
            The fillet object
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label, "PartDesign::Fillet")
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label):
            return None

        # Get the parent object
        parent_obj = Context.get_object(object_label)
        if parent_obj is None:
            raise ShapeException(
                f"Fillet '{label}' failed: Object '{object_label}' not found. "
                f"Please check that the object exists before adding a fillet."
            )

        # Get the body (parent of the object)
        if parent_obj.TypeId == "PartDesign::Body":
            body = parent_obj
            # Get the last feature in the body to apply fillet to
            if not body.Group:
                raise ShapeException(
                    f"Fillet '{label}' failed: Body '{object_label}' has no features to fillet. "
                    f"Please add a feature (e.g., Pad, Box) to the body before adding a fillet."
                )
            base_feature = body.Group[-1]
        else:
            # Object is a feature, get its parent body
            body = Context.get_first_body_parent(parent_obj)
            if body is None or body.TypeId != "PartDesign::Body":
                raise ShapeException(
                    f"Fillet '{label}' failed: Object '{object_label}' is not part of a Body. "
                    f"Fillet operations require the object to be inside a PartDesign Body."
                )
            base_feature = parent_obj

        # Check if fillet already exists
        existing_fillet = Context.get_object(label)

        if existing_fillet is not None:
            # Check parent
            if Context.get_first_body_parent(existing_fillet) != body:
                other_parent = Context.get_first_body_parent(existing_fillet)
                other_parent_label = other_parent.Label if other_parent else "None"
                raise ShapeException(
                    f"Fillet '{label}' failed: Conflicting label exists with different parent '{other_parent_label}'. "
                    f"Please use a different label or remove the existing fillet."
                )

            # Update existing fillet
            if existing_fillet.TypeId != "PartDesign::Fillet":
                Shape._move_to_trash_bin(existing_fillet)
            else:
                needs_recompute = False

                # Update base and edges
                new_base = (base_feature, edges)
                if existing_fillet.Base != new_base:
                    existing_fillet.Base = new_base
                    needs_recompute = True

                # Update radius
                if existing_fillet.Radius != radius:
                    existing_fillet.Radius = radius
                    needs_recompute = True

                if needs_recompute:
                    App.ActiveDocument.recompute()
                    EdgeFeature._raise_if_feature_error(
                        label,
                        "Fillet",
                        f"The fillet radius ({radius}mm) may be too large for the selected edges. Try a smaller radius or check that the edges exist.",
                        existing_fillet,
                    )

                return existing_fillet

        # Create new fillet
        body.newObject("PartDesign::Fillet", label)
        fillet = Context.get_object(label)
        fillet.Base = (base_feature, edges)
        fillet.Radius = radius
        App.ActiveDocument.recompute()
        EdgeFeature._raise_if_feature_error(
            label,
            "Fillet",
            f"The fillet radius ({radius}mm) may be too large for the selected edges. Try a smaller radius or check that the edges exist.",
            fillet,
        )

        return fillet

    @staticmethod
    def add_chamfer(label, object_label, edges, size, angle=None):
        """
        Add a chamfer feature to selected edges of an existing object.

        Args:
            label (str): Name/label for the chamfer feature
            object_label (str): Label of the existing object to add chamfer to
            edges (list): List of edge labels (e.g., ['Edge1', 'Edge2', 'Edge3'])
            size (float): Chamfer size/distance in mm
            angle (float, optional): Chamfer angle in degrees. If provided, uses "Distance and Angle" chamfer type

        Returns:
            The chamfer object
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label, "PartDesign::Chamfer")
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label):
            return None

        # Get the parent object
        parent_obj = Context.get_object(object_label)
        if parent_obj is None:
            raise ShapeException(
                f"Chamfer '{label}' failed: Object '{object_label}' not found. "
                f"Please check that the object exists before adding a chamfer."
            )

        # Get the body (parent of the object)
        if parent_obj.TypeId == "PartDesign::Body":
            body = parent_obj
            # Get the last feature in the body to apply chamfer to
            if not body.Group:
                raise ShapeException(
                    f"Chamfer '{label}' failed: Body '{object_label}' has no features to chamfer. "
                    f"Please add a feature (e.g., Pad, Box) to the body before adding a chamfer."
                )
            base_feature = body.Group[-1]
        else:
            # Object is a feature, get its parent body
            body = Context.get_first_body_parent(parent_obj)
            if body is None or body.TypeId != "PartDesign::Body":
                raise ShapeException(
                    f"Chamfer '{label}' failed: Object '{object_label}' is not part of a Body. "
                    f"Chamfer operations require the object to be inside a PartDesign Body."
                )
            base_feature = parent_obj

        # Check if chamfer already exists
        existing_chamfer = Context.get_object(label)

        if existing_chamfer is not None:
            # Check parent
            if Context.get_first_body_parent(existing_chamfer) != body:
                other_parent = Context.get_first_body_parent(existing_chamfer)
                other_parent_label = other_parent.Label if other_parent else "None"
                raise ShapeException(
                    f"Chamfer '{label}' failed: Conflicting label exists with different parent '{other_parent_label}'. "
                    f"Please use a different label or remove the existing chamfer."
                )

            # Update existing chamfer
            if existing_chamfer.TypeId != "PartDesign::Chamfer":
                Shape._move_to_trash_bin(existing_chamfer)
            else:
                needs_recompute = False

                # Update base and edges
                new_base = (base_feature, edges)
                if existing_chamfer.Base != new_base:
                    existing_chamfer.Base = new_base
                    needs_recompute = True

                # Update chamfer type and parameters
                if angle is not None:
                    # Distance and Angle mode
                    if existing_chamfer.ChamferType != "Distance and Angle":
                        existing_chamfer.ChamferType = "Distance and Angle"
                        needs_recompute = True

                    if existing_chamfer.Size != size:
                        existing_chamfer.Size = size
                        needs_recompute = True

                    if existing_chamfer.Angle != angle:
                        existing_chamfer.Angle = angle
                        needs_recompute = True
                else:
                    # Equal distance mode (default)
                    if existing_chamfer.ChamferType != "Equal distance":
                        existing_chamfer.ChamferType = "Equal distance"
                        needs_recompute = True

                    if existing_chamfer.Size != size:
                        existing_chamfer.Size = size
                        needs_recompute = True

                if needs_recompute:
                    chamfer_msg = f"The chamfer size ({size}mm) may be too large for the selected edges"
                    if angle is not None:
                        chamfer_msg += f", or the angle ({angle}°) may be invalid"
                    chamfer_msg += ". Try a smaller size or check that the edges exist."
                    App.ActiveDocument.recompute()
                    EdgeFeature._raise_if_feature_error(label, "Chamfer", chamfer_msg, existing_chamfer)

                return existing_chamfer

        # Create new chamfer
        body.newObject("PartDesign::Chamfer", label)
        chamfer = Context.get_object(label)
        chamfer.Base = (base_feature, edges)

        if angle is not None:
            # Distance and Angle mode
            chamfer.ChamferType = "Distance and Angle"
            chamfer.Size = size
            chamfer.Angle = angle
        else:
            # Equal distance mode (default)
            chamfer.ChamferType = "Equal distance"
            chamfer.Size = size

        chamfer_msg = f"The chamfer size ({size}mm) may be too large for the selected edges"
        if angle is not None:
            chamfer_msg += f", or the angle ({angle}°) may be invalid"
        chamfer_msg += ". Try a smaller size or check that the edges exist."
        App.ActiveDocument.recompute()
        EdgeFeature._raise_if_feature_error(label, "Chamfer", chamfer_msg, chamfer)

        return chamfer
