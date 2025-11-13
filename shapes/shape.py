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