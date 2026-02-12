import FreeCAD as App

from .context import Context
from .exceptions import ShapeException
from .shape import Shape

# from importlib import reload
# reload(boolean)
# boolean.Boolean.cut('c', 'b3', 'b4')


class Boolean:
    BOOLEAN_TYPE_NAMES = {0: "Fuse", 1: "Cut", 2: "Common"}

    @staticmethod
    def _raise_if_boolean_error(label, boolean_obj, boolean_type, primary_label, secondary_labels):
        """
        Check if the boolean object has errors and raise an appropriate error.
        Must be called after App.ActiveDocument.recompute().
        """
        if hasattr(boolean_obj, "getStatusString"):
            status = boolean_obj.getStatusString()
            if status != "Valid":
                type_name = Boolean.BOOLEAN_TYPE_NAMES.get(boolean_type, str(boolean_type))
                secondary_str = ", ".join(f"'{s}'" for s in secondary_labels)
                raise ShapeException(
                    f"Boolean {type_name} '{label}' failed: {status}. "
                    f"Primary: '{primary_label}', Secondary: [{secondary_str}]."
                )

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
        primary_label = primary
        primary = Context.get_object(primary)
        if primary is None:
            raise ShapeException(
                f"Boolean '{label}' failed: Primary object '{primary_label}' not found. "
                f"Please check that the object exists."
            )

        # Traverse up the parent chain to find a PartDesign::Body
        body_parent = Context.get_first_body_parent(primary)
        if body_parent is None:
            raise ShapeException(
                f"Boolean '{label}' failed: Primary object '{primary_label}' is not part of a Body. "
                f"Boolean operations require the primary object to be in a PartDesign Body."
            )
        primary = body_parent

        # Handle secondary as either a list or a single object
        secondary_labels = secondary if isinstance(secondary, list) else [secondary]
        secondary_objects = []
        for sec_label in secondary_labels:
            sec_obj = Context.get_object(sec_label)
            if sec_obj is None:
                raise ShapeException(
                    f"Boolean '{label}' failed: Secondary object '{sec_label}' not found. "
                    f"Please check that all secondary objects exist."
                )
            body_parent = Context.get_first_body_parent(sec_obj)
            if body_parent is None:
                raise ShapeException(
                    f"Boolean '{label}' failed: Secondary object '{sec_label}' is not part of a Body. "
                    f"Boolean operations require the secondary object to be in a PartDesign Body."
                )
            secondary_objects.append(body_parent)

        # Try to get existing boolean object with the same label
        existing_boolean = Context.get_object(label)

        if existing_boolean is not None:
            # Check the type of the existing object
            if existing_boolean.TypeId != "PartDesign::Boolean":
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
                            Boolean._raise_if_boolean_error(
                                label, existing_boolean, boolean_type, primary_label, secondary_labels
                            )

                        return

        # Create new boolean object if it doesn't exist
        ### Begin command PartDesign_Boolean
        primary.newObject("PartDesign::Boolean", label)
        boolean_obj = Context.get_object(label)
        ### End command PartDesign_Boolean

        boolean_obj.setObjects(secondary_objects)
        boolean_obj.Type = boolean_type
        App.ActiveDocument.recompute()
        Boolean._raise_if_boolean_error(label, boolean_obj, boolean_type, primary_label, secondary_labels)

    @staticmethod
    def fuse(fuse_label, primary, secondary):
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(fuse_label, "PartDesign::Boolean")
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(fuse_label):
            return None
        Boolean._create_boolean(fuse_label, primary, secondary, 0)

    @staticmethod
    def common(common_label, primary, secondary):
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(common_label, "PartDesign::Boolean")
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(common_label):
            return None
        Boolean._create_boolean(common_label, primary, secondary, 2)

    @staticmethod
    def cut(cut_label, primary, secondary):
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(cut_label, "PartDesign::Boolean")
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(cut_label):
            return None
        Boolean._create_boolean(cut_label, primary, secondary, 1)
