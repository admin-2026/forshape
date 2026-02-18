from .context import Context


class Appearance:
    @staticmethod
    def set_transparency(object_or_label, transparency):
        """Set the transparency of an object (0=opaque, 100=fully transparent)"""
        obj = Context.get_object(object_or_label)
        if obj is None:
            print("Object not found")
            return

        if obj.ViewObject.Transparency != transparency:
            obj.ViewObject.Transparency = transparency
