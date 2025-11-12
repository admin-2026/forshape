import FreeCAD as App

from .context import Context

class Transform:
    @staticmethod
    def translate_to(object_or_label, x, y, z):
        """Translate an object to a specific position (x, y, z)"""
        obj = Context.get_object(object_or_label)
        if obj is None:
            print(f'Object not found')
            return

        # Check if the object is already at the desired position
        new_position = App.Vector(x, y, z)
        if obj.Placement.Base != new_position:
            # Set the object's placement base to the new position
            obj.Placement.Base = new_position
            App.ActiveDocument.recompute()

    @staticmethod
    def rotate_to(object_or_label, x, y, z, degree):
        """Rotate an object around an axis defined by vector (x, y, z) by the given degree"""
        obj = Context.get_object(object_or_label)
        if obj is None:
            print(f'Object not found')
            return

        # Create a rotation around the specified axis
        axis = App.Vector(x, y, z)
        rotation = App.Rotation(axis, degree)

        # Check if the object already has the desired rotation
        if obj.Placement.Rotation != rotation:
            # Apply the rotation to the object's placement
            obj.Placement.Rotation = rotation
            App.ActiveDocument.recompute()