import FreeCAD as App

from .context import Context
from .shape import Shape

# from importlib import reload
# reload(boolean)
# boolean.Boolean.cut('c', 'b3', 'b4')

class Boolean:

    @staticmethod
    def _create_boolean(label, primary, secondary, boolean_type):
        """
        Helper function to create a boolean operation.

        Args:
            label: Label for the boolean object
            primary: Primary object
            secondary: Secondary object(s) - can be a single object or a list
            boolean_type: 0 for fuse, 1 for cut, 2 for common
        """
        primary = Context.get_object(primary)

        # Traverse up the parent chain to find a PartDesign::Body
        if primary is not None:
            visited = set()  # Track visited objects to detect cycles
            current = primary

            while current is not None and current.TypeId != 'PartDesign::Body':
                # Check for cycles
                obj_id = id(current)
                if obj_id in visited:
                    # Cycle detected, break out
                    break
                visited.add(obj_id)

                # Move to parent
                parent = current.getParent()
                if parent is None:
                    break
                current = parent

            # Use the found Body if we found one, otherwise keep original
            if current is not None and current.TypeId == 'PartDesign::Body':
                primary = current

        # Handle secondary as either a list or a single object
        if isinstance(secondary, list):
            secondary_objects = [Context.get_object(obj) for obj in secondary]
        else:
            secondary_objects = [Context.get_object(secondary)]

        # Try to get existing boolean object with the same label
        existing_boolean = Context.get_object(label)

        if existing_boolean is not None:
            # Check the type of the existing object
            if existing_boolean.TypeId != 'PartDesign::Boolean':
                # Not a Boolean, remove it and create new
                Context.remove_object(existing_boolean)
                existing_boolean = None
            else:
                # Check if the parent is the same as the primary object
                # Handle case where Parents might be empty (e.g., parent was removed)
                if not existing_boolean.Parents or len(existing_boolean.Parents) == 0:
                    # No parent, remove and recreate
                    Context.remove_object(existing_boolean)
                    existing_boolean = None
                else:
                    existing_parent = existing_boolean.Parents[0][0]
                    if existing_parent != primary:
                        # Different parent, remove and recreate
                        Context.remove_object(existing_boolean)
                        existing_boolean = None
                    else:
                        # Boolean exists with correct parent, update its properties
                        needs_recompute = False

                        # Update boolean type
                        if existing_boolean.Type != boolean_type:
                            existing_boolean.Type = boolean_type
                            needs_recompute = True

                        # Update secondary objects
                        current_objects = existing_boolean.Group
                        if current_objects != secondary_objects:
                            existing_boolean.setObjects(secondary_objects)
                            needs_recompute = True

                        if needs_recompute:
                            App.ActiveDocument.recompute()

                        return

        # Create new boolean object if it doesn't exist
        ### Begin command PartDesign_Boolean
        primary.newObject('PartDesign::Boolean', label)
        boolean_obj = Context.get_object(label)
        ### End command PartDesign_Boolean

        boolean_obj.setObjects(secondary_objects)
        boolean_obj.Type = boolean_type
        App.ActiveDocument.recompute()

    @staticmethod
    def fuse(fuse_label, primary, secondary):
        # Handle teardown mode
        if Shape._teardown_if_needed(fuse_label):
            return None
        Boolean._create_boolean(fuse_label, primary, secondary, 0)

    @staticmethod
    def common(common_label, primary, secondary):
        # Handle teardown mode
        if Shape._teardown_if_needed(common_label):
            return None
        Boolean._create_boolean(common_label, primary, secondary, 2)

    @staticmethod
    def cut(cut_label, primary, secondary):
        # Handle teardown mode
        if Shape._teardown_if_needed(cut_label):
            return None
        Boolean._create_boolean(cut_label, primary, secondary, 1)
