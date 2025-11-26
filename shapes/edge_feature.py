import FreeCAD as App

from .shape import Shape
from .context import Context

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.edge_feature;
# reload(shapes.edge_feature); from shapes.edge_feature import EdgeFeature
# EdgeFeature.add_fillet('fillet1', 'b4', ['Edge1', 'Edge2'], 2)

class EdgeFeature(Shape):
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
        # Handle quick rebuild mode
        quick_rebuild_obj = Shape._quick_rebuild_if_possible(label, 'PartDesign::Fillet')
        if quick_rebuild_obj is not None:
            return quick_rebuild_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label):
            return None

        # Get the parent object
        parent_obj = Context.get_object(object_label)
        if parent_obj is None:
            raise ValueError(f"Object not found: '{object_label}'")

        # Get the body (parent of the object)
        if parent_obj.TypeId == 'PartDesign::Body':
            body = parent_obj
            # Get the last feature in the body to apply fillet to
            if not body.Group:
                raise ValueError(f"Body '{object_label}' has no features to fillet")
            base_feature = body.Group[-1]
        else:
            # Object is a feature, get its parent body
            body = Context.get_first_body_parent(parent_obj)
            if body is None or body.TypeId != 'PartDesign::Body':
                raise ValueError(f"Object '{object_label}' is not part of a Body")
            base_feature = parent_obj

        # Check if fillet already exists
        existing_fillet = Context.get_object(label)

        if existing_fillet is not None:
            # Check parent
            if Context.get_first_body_parent(existing_fillet) != body:
                other_parent = Context.get_first_body_parent(existing_fillet)
                other_parent_label = other_parent.Label if other_parent else "None"
                raise ValueError(f"Creating object with conflicting label: '{label}' already exists with different parent '{other_parent_label}'")

            # Update existing fillet
            if existing_fillet.TypeId != 'PartDesign::Fillet':
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

                return existing_fillet

        # Create new fillet
        body.newObject('PartDesign::Fillet', label)
        fillet = Context.get_object(label)
        fillet.Base = (base_feature, edges)
        fillet.Radius = radius
        App.ActiveDocument.recompute()

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
        # Handle quick rebuild mode
        quick_rebuild_obj = Shape._quick_rebuild_if_possible(label, 'PartDesign::Chamfer')
        if quick_rebuild_obj is not None:
            return quick_rebuild_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(label):
            return None

        # Get the parent object
        parent_obj = Context.get_object(object_label)
        if parent_obj is None:
            raise ValueError(f"Object not found: '{object_label}'")

        # Get the body (parent of the object)
        if parent_obj.TypeId == 'PartDesign::Body':
            body = parent_obj
            # Get the last feature in the body to apply chamfer to
            if not body.Group:
                raise ValueError(f"Body '{object_label}' has no features to chamfer")
            base_feature = body.Group[-1]
        else:
            # Object is a feature, get its parent body
            body = Context.get_first_body_parent(parent_obj)
            if body is None or body.TypeId != 'PartDesign::Body':
                raise ValueError(f"Object '{object_label}' is not part of a Body")
            base_feature = parent_obj

        # Check if chamfer already exists
        existing_chamfer = Context.get_object(label)

        if existing_chamfer is not None:
            # Check parent
            if Context.get_first_body_parent(existing_chamfer) != body:
                other_parent = Context.get_first_body_parent(existing_chamfer)
                other_parent_label = other_parent.Label if other_parent else "None"
                raise ValueError(f"Creating object with conflicting label: '{label}' already exists with different parent '{other_parent_label}'")

            # Update existing chamfer
            if existing_chamfer.TypeId != 'PartDesign::Chamfer':
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
                    if existing_chamfer.ChamferType != 'Distance and Angle':
                        existing_chamfer.ChamferType = 'Distance and Angle'
                        needs_recompute = True

                    if existing_chamfer.Size != size:
                        existing_chamfer.Size = size
                        needs_recompute = True

                    if existing_chamfer.Angle != angle:
                        existing_chamfer.Angle = angle
                        needs_recompute = True
                else:
                    # Equal distance mode (default)
                    if existing_chamfer.ChamferType != 'Equal distance':
                        existing_chamfer.ChamferType = 'Equal distance'
                        needs_recompute = True

                    if existing_chamfer.Size != size:
                        existing_chamfer.Size = size
                        needs_recompute = True

                if needs_recompute:
                    App.ActiveDocument.recompute()

                return existing_chamfer

        # Create new chamfer
        body.newObject('PartDesign::Chamfer', label)
        chamfer = Context.get_object(label)
        chamfer.Base = (base_feature, edges)

        if angle is not None:
            # Distance and Angle mode
            chamfer.ChamferType = 'Distance and Angle'
            chamfer.Size = size
            chamfer.Angle = angle
        else:
            # Equal distance mode (default)
            chamfer.ChamferType = 'Equal distance'
            chamfer.Size = size

        App.ActiveDocument.recompute()

        return chamfer
