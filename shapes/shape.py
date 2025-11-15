import FreeCAD as App
from datetime import datetime

from .context import Context

class Shape:
    @staticmethod
    def _create_object(label):
        App.activeDocument().addObject('PartDesign::Body', label)
        return Context.get_object(label)

    @staticmethod
    def _create_sketch(sketch_label, parent_object, plane_label):
        parent_object.newObject('Sketcher::SketchObject', sketch_label)
        sketch = Context.get_object(sketch_label)
        plane = Context.get_object(plane_label)
        sketch.AttachmentSupport = (plane,[''])
        sketch.MapMode = 'FlatFace'
        return sketch

    @staticmethod
    def _create_pad(pad_label, parent_obj, sketch, z):
        parent_obj.newObject('PartDesign::Pad', pad_label)
        pad = Context.get_object(pad_label)
        pad.Profile = (sketch, ['',])
        pad.Length = z
        # App.ActiveDocument.recompute()
        pad.ReferenceAxis = (sketch,['N_Axis'])
        pad.Midplane = 1
        return pad

    @staticmethod
    def _teardown_if_needed(label, created_children=None):
        """
        Check if we're in teardown mode and remove object if so.
        Implements proper dependency handling: children are removed first,
        and children not created by the script are preserved (moved out).

        Args:
            label (str): The main object label to remove
            created_children (list, optional): List of child labels that were created by the script.
                                              These will be removed in reverse order.
                                              Children not in this list will be moved out of the parent.
                                              If None, only the main object will be removed.

        Returns:
            bool: True if in teardown mode (caller should return None),
                  False if not in teardown mode (caller should proceed normally)
        """
        if not globals().get('TEARDOWN_MODE', False):
            return False

        # We are in teardown mode
        obj = Context.get_object(label)
        if obj is None:
            return True  # Object doesn't exist, nothing to remove

        # If no children specified, just remove the main object
        if created_children is None:
            Context.remove_object(label)
            return True

        # Get all children of the object
        if hasattr(obj, 'Group'):
            all_children = list(obj.Group)
        else:
            all_children = []

        created_children_set = set(created_children)

        # Move out children not created by script (preserve them)
        for child in all_children:
            if child.Label not in created_children_set:
                # This child was not created by the script, remove from parent to preserve it
                obj.removeObject(child)

        # Remove children that were created by script (in reverse order for proper dependency handling)
        for child_label in reversed(created_children):
            Context.remove_object(child_label)

        # Finally remove the main object
        Context.remove_object(label)

        return True

    @staticmethod
    def _get_or_recreate_body(label, expected_children):
        """
        Get existing Body or prepare for recreation.
        Handles common logic for checking existing objects and their children.

        Args:
            label: The label of the Body
            expected_children: List of tuples (child_label, expected_type_id)
                              e.g., [('box_box', 'PartDesign::AdditiveBox')]

        Returns:
            (existing_obj, children_dict) where:
            - existing_obj is the Body if it should be updated, None if should be recreated
            - children_dict maps child_label to child object (only when existing_obj is not None)

        Raises:
            ValueError: If a child exists but belongs to a different parent
        """
        existing_obj = Context.get_object(label)

        if existing_obj is not None:
            # Check if the existing object is the document itself
            if existing_obj == App.ActiveDocument:
                # Don't move the document to trash, just continue creation
                return None, {}

            # Check the type of the existing object
            if existing_obj.TypeId != 'PartDesign::Body':
                # Not a Body, move to trash and create new
                Shape._move_to_trash_bin(existing_obj)
                return None, {}

            # It's a Body, check if it has the expected children
            children = {}
            for child_label, expected_type in expected_children:
                child = Context.get_object(child_label)

                # Check for parent conflicts first
                if child is not None and child.getParent() != existing_obj:
                    other_parent = child.getParent()
                    other_parent_label = other_parent.Label if other_parent else "None"
                    raise ValueError(f"Creating object with conflicting label: '{child_label}' already exists with different parent '{other_parent_label}'")

                # Check if child exists and has correct type
                if child is None or child.TypeId != expected_type:
                    # Child is missing or wrong type, need to recreate
                    Shape._move_to_trash_bin(existing_obj)
                    return None, {}

                children[child_label] = child

            # All children exist with correct types and parents
            return existing_obj, children

        return None, {}

    @staticmethod
    def _update_attachment_and_offset(obj, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll):
        """
        Update attachment plane, offset, and rotation for an object.

        Args:
            obj: The object to update
            plane_label: The label of the plane to attach to
            x_offset, y_offset, z_offset: Position offsets
            yaw, pitch, roll: Rotation angles

        Returns:
            bool: True if changes were made (recompute needed), False otherwise
        """
        needs_recompute = False

        # Update attachment plane
        plane_obj = Context.get_object(plane_label)
        current_plane = obj.AttachmentSupport[0][0] if obj.AttachmentSupport else None
        if current_plane != plane_obj:
            obj.AttachmentSupport = plane_obj
            obj.MapMode = 'FlatFace'
            needs_recompute = True

        # Update offset and rotation
        new_offset = App.Placement(App.Vector(x_offset, y_offset, z_offset), App.Rotation(yaw, pitch, roll))
        if obj.AttachmentOffset != new_offset:
            obj.AttachmentOffset = new_offset
            needs_recompute = True

        return needs_recompute

    @staticmethod
    def _move_to_trash_bin(obj):
        """
        Move an existing object to a trash_bin folder instead of deleting it.
        Creates the trash_bin folder if it doesn't exist.
        Renames the object with a timestamp to avoid name conflicts.

        Args:
            obj: The object to move to trash_bin
        """
        # Get or create trash_bin folder
        trash_bin = Context.get_object('trash_bin')
        if trash_bin is None:
            App.ActiveDocument.addObject('App::DocumentObjectGroup', 'trash_bin')
            trash_bin = Context.get_object('trash_bin')

        # Generate new name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_label = f"{obj.Label}_{timestamp}"

        # Rename the object
        obj.Label = new_label

        # Move to trash_bin folder
        trash_bin.addObject(obj)

        print(f'Moved object to trash_bin: {new_label}')