import FreeCAD as App

from context import Context

class Transform:
    @staticmethod
    def translate_to(object_or_label, x, y, z):
        """Translate an object to a specific position (x, y, z)"""
        obj = Context.get_object(object_or_label)
        if obj is None:
            print(f'Object not found')
            return

        # Set the object's placement base to the new position
        obj.Placement.Base = App.Vector(x, y, z)
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

        # Apply the rotation to the object's placement
        obj.Placement.Rotation = rotation
        App.ActiveDocument.recompute()