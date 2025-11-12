import FreeCAD as App

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