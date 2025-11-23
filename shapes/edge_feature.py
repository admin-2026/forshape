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
    def add_chamfer(label, object_label, edges, size):
        """
        Add a chamfer feature to selected edges of an existing object.

        Args:
            label (str): Name/label for the chamfer feature
            object_label (str): Label of the existing object to add chamfer to
            edges (list): List of edge labels (e.g., ['Edge1', 'Edge2', 'Edge3'])
            size (float): Chamfer size in mm

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

                # Update size
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
        chamfer.Size = size
        App.ActiveDocument.recompute()

        return chamfer

    @staticmethod
    def add_draft(label, object_label, faces, angle, neutral_plane):
        """
        Add a draft feature to selected faces of an existing object.

        Args:
            label (str): Name/label for the draft feature
            object_label (str): Label of the existing object to add draft to
            faces (list): List of face labels (e.g., ['Face1', 'Face2', 'Face3'])
            angle (float): Draft angle in degrees
            neutral_plane (str): Neutral plane label (e.g., 'XY_Plane')

        Returns:
            The draft object
        """
        # Handle quick rebuild mode
        quick_rebuild_obj = Shape._quick_rebuild_if_possible(label, 'PartDesign::Draft')
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
            # Get the last feature in the body to apply draft to
            if not body.Group:
                raise ValueError(f"Body '{object_label}' has no features to draft")
            base_feature = body.Group[-1]
        else:
            # Object is a feature, get its parent body
            body = Context.get_first_body_parent(parent_obj)
            if body is None or body.TypeId != 'PartDesign::Body':
                raise ValueError(f"Object '{object_label}' is not part of a Body")
            base_feature = parent_obj

        # Get neutral plane
        plane = Context.get_object(neutral_plane)
        if plane is None:
            raise ValueError(f"Neutral plane not found: '{neutral_plane}'")

        # Check if draft already exists
        existing_draft = Context.get_object(label)

        if existing_draft is not None:
            # Check parent
            if Context.get_first_body_parent(existing_draft) != body:
                other_parent = Context.get_first_body_parent(existing_draft)
                other_parent_label = other_parent.Label if other_parent else "None"
                raise ValueError(f"Creating object with conflicting label: '{label}' already exists with different parent '{other_parent_label}'")

            # Update existing draft
            if existing_draft.TypeId != 'PartDesign::Draft':
                Shape._move_to_trash_bin(existing_draft)
            else:
                needs_recompute = False

                # Update base and faces
                new_base = (base_feature, faces)
                if existing_draft.Base != new_base:
                    existing_draft.Base = new_base
                    needs_recompute = True

                # Update angle
                new_angle = f'{angle} deg'
                if str(existing_draft.Angle) != new_angle:
                    existing_draft.Angle = new_angle
                    needs_recompute = True

                # Update neutral plane
                if existing_draft.NeutralPlane != plane:
                    existing_draft.NeutralPlane = plane
                    needs_recompute = True

                if needs_recompute:
                    App.ActiveDocument.recompute()

                return existing_draft

        # Create new draft
        body.newObject('PartDesign::Draft', label)
        draft = Context.get_object(label)
        draft.Base = (base_feature, faces)
        draft.Angle = f'{angle} deg'
        draft.NeutralPlane = plane
        App.ActiveDocument.recompute()

        return draft
