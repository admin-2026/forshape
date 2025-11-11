import FreeCAD as App

class Shape:
    @staticmethod
    def _create_object(label):
        App.activeDocument().addObject('PartDesign::Body', label)
        return App.ActiveDocument.getObject(label)

    @staticmethod
    def _create_sketch(sketch_label, parent_object, plane_label):
        parent_object.newObject('Sketcher::SketchObject', sketch_label)
        sketch = App.ActiveDocument.getObject(sketch_label)
        plane = App.activeDocument().getObject(plane_label)
        sketch.AttachmentSupport = (plane,[''])
        sketch.MapMode = 'FlatFace'
        return sketch

    @staticmethod
    def _create_pad(pad_label, parent_obj, sketch, z):
        parent_obj.newObject('PartDesign::Pad', pad_label)
        pad = App.ActiveDocument.getObject(pad_label)
        pad.Profile = (sketch, ['',])
        pad.Length = z
        # App.ActiveDocument.recompute()
        pad.ReferenceAxis = (sketch,['N_Axis'])
        return pad