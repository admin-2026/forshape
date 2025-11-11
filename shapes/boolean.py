import FreeCAD as App

from .context import Context

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

        ### Begin command PartDesign_Boolean
        primary.newObject('PartDesign::Boolean', label)
        boolean_obj = App.ActiveDocument.getObject(label)
        ### End command PartDesign_Boolean

        # Handle secondary as either a list or a single object
        if isinstance(secondary, list):
            secondary_objects = [Context.get_object(obj) for obj in secondary]
        else:
            secondary_objects = [Context.get_object(secondary)]

        boolean_obj.setObjects(secondary_objects)
        boolean_obj.Type = boolean_type
        App.ActiveDocument.recompute()

    @staticmethod
    def fuse(fuse_label, primary, secondary):
        Boolean._create_boolean(fuse_label, primary, secondary, 0)

    @staticmethod
    def common(common_label, primary, secondary):
        Boolean._create_boolean(common_label, primary, secondary, 2)

    @staticmethod
    def cut(cut_label, primary, secondary):
        Boolean._create_boolean(cut_label, primary, secondary, 1)
