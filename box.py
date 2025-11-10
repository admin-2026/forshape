# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder);

# from importlib import reload
# reload(box)
# box.Box.create_box('b2', 'XY_Plane', 10, 20, 5)
# box.Box.create_side_rounded_box('b3', 'XY_Plane', 10, 20, 5, 3)

import FreeCAD as App
import Part
import Sketcher


class Box:
    @staticmethod
    def _create_object(label):
        App.activeDocument().addObject('PartDesign::Body', label)
        return App.ActiveDocument.getObject(label)

    @staticmethod
    def _create_rect_sketch(sketch_label, obj, x, y):
        obj.newObject('Sketcher::SketchObject', sketch_label)
        sketch = App.ActiveDocument.getObject(sketch_label)
        plane = App.activeDocument().getObject(plane_label)
        sketch.AttachmentSupport = (plane,[''])
        sketch.MapMode = 'FlatFace'

        geoList = []
        geoList.append(Part.LineSegment(App.Vector(-10.0, -10.0, 0.0),App.Vector(10.0, -10.0, 0.0)))
        geoList.append(Part.LineSegment(App.Vector(10.0, -10.0, 0.0),App.Vector(10.0, 10.0, 0.0)))
        geoList.append(Part.LineSegment(App.Vector(10.0, 10.0, 0.0),App.Vector(-10.0, 10.0, 0.0)))
        geoList.append(Part.LineSegment(App.Vector(-10.0, 10.0, 0.0),App.Vector(-10.0, -10.0, 0.0)))
        sketch.addGeometry(geoList,False)
        del geoList

        constrGeoList = []
        constrGeoList.append(Part.Point(App.Vector(0.0, 0.0, 0.0)))
        sketch.addGeometry(constrGeoList,True)
        del constrGeoList

        constraintList = []
        constraintList.append(Sketcher.Constraint('Coincident', 0, 2, 1, 1))
        constraintList.append(Sketcher.Constraint('Coincident', 1, 2, 2, 1))
        constraintList.append(Sketcher.Constraint('Coincident', 2, 2, 3, 1))
        constraintList.append(Sketcher.Constraint('Coincident', 3, 2, 0, 1))
        constraintList.append(Sketcher.Constraint('Horizontal', 0))
        constraintList.append(Sketcher.Constraint('Horizontal', 2))
        constraintList.append(Sketcher.Constraint('Vertical', 1))
        constraintList.append(Sketcher.Constraint('Vertical', 3))
        constraintList.append(Sketcher.Constraint('Symmetric', 2, 1, 0, 1, 4, 1))
        sketch.addConstraint(constraintList)
        del constraintList

        sketch.addConstraint(Sketcher.Constraint('Coincident', 4, 1, -1, 1))
        sketch.addConstraint(Sketcher.Constraint('DistanceX',2,2,2,1,x))
        sketch.addConstraint(Sketcher.Constraint('DistanceY',1,1,1,2,y))
        return sketch

    @staticmethod
    def _create_pad(pad_label, obj, sketch, z):
        obj.newObject('PartDesign::Pad', pad_label)
        pad = App.ActiveDocument.getObject(pad_label)
        pad.Profile = (sketch, ['',])
        pad.Length = z
        # App.ActiveDocument.recompute()
        pad.ReferenceAxis = (sketch,['N_Axis'])
        return pad
    
    @staticmethod
    def _create_rounded_rect_sketch(sketch_label, obj, x, y, r):
        obj.newObject('Sketcher::SketchObject', sketch_label)
        sketch = App.ActiveDocument.getObject(sketch_label)

        geoList = []
        geoList.append(Part.LineSegment(App.Vector(9.0, -5.0, 0.0),App.Vector(9.0, 5.0, 0.0)))
        geoList.append(Part.LineSegment(App.Vector(1.0, 13.0, 0.0),App.Vector(-1.0, 13.0, 0.0)))
        geoList.append(Part.LineSegment(App.Vector(-9.0, 5.0, 0.0),App.Vector(-9.0, -5.0, 0.0)))
        geoList.append(Part.LineSegment(App.Vector(-1.0, -13.0, 0.0),App.Vector(1.0, -13.0, 0.0)))
        geoList.append(Part.ArcOfCircle(Part.Circle(App.Vector(1.0, -5.0, 0.0), App.Vector(0.0, 0.0, 1.0), 7.0), 4.0, 6.0))
        geoList.append(Part.ArcOfCircle(Part.Circle(App.Vector(1.0, 5.0, 0.0), App.Vector(0.0, 0.0, 1.0), 7.0), 0.0, 1.0))
        geoList.append(Part.ArcOfCircle(Part.Circle(App.Vector(-1.0, 5.0, 0.0), App.Vector(0.0, 0.0, 1.0), 7.0), 1.0, 3.0))
        geoList.append(Part.ArcOfCircle(Part.Circle(App.Vector(-1.0, -5.0, 0.0), App.Vector(0.0, 0.0, 1.0), 7.0), 3.0, 4.0))
        sketch.addGeometry(geoList,False)
        del geoList
        
        constrGeoList = []
        constrGeoList.append(Part.Point(App.Vector(-9.0, 13.0, 0.0)))
        constrGeoList.append(Part.Point(App.Vector(0.0, 0.0, 0.0)))
        sketch.addGeometry(constrGeoList,True)
        del constrGeoList
        
        constraintList = []
        constraintList.append(Sketcher.Constraint('Tangent', 0, 1, 4, 2))
        constraintList.append(Sketcher.Constraint('Tangent', 0, 2, 5, 1))
        constraintList.append(Sketcher.Constraint('Tangent', 1, 1, 5, 2))
        constraintList.append(Sketcher.Constraint('Tangent', 1, 2, 6, 1))
        constraintList.append(Sketcher.Constraint('Tangent', 2, 1, 6, 2))
        constraintList.append(Sketcher.Constraint('Tangent', 2, 2, 7, 1))
        constraintList.append(Sketcher.Constraint('Tangent', 3, 1, 7, 2))
        constraintList.append(Sketcher.Constraint('Tangent', 3, 2, 4, 1))
        constraintList.append(Sketcher.Constraint('Vertical', 0))
        constraintList.append(Sketcher.Constraint('Vertical', 2))
        constraintList.append(Sketcher.Constraint('Horizontal', 1))
        constraintList.append(Sketcher.Constraint('Horizontal', 3))
        constraintList.append(Sketcher.Constraint('Equal', 4, 5))
        constraintList.append(Sketcher.Constraint('Equal', 5, 6))
        constraintList.append(Sketcher.Constraint('Equal', 6, 7))
        constraintList.append(Sketcher.Constraint('Symmetric', 2, 1, 0, 1, 9, 1))
        constraintList.append(Sketcher.Constraint('PointOnObject', 8, 1, 1))
        constraintList.append(Sketcher.Constraint('PointOnObject', 8, 1, 2))
        sketch.addConstraint(constraintList)
        del constraintList

        sketch.addConstraint(Sketcher.Constraint('Coincident', 9, 1, -1, 1))

        #
        sketch.addConstraint(Sketcher.Constraint('DistanceX',1,2,1,1,x))
        sketch.addConstraint(Sketcher.Constraint('DistanceY',2,2,2,1,y))
        sketch.addConstraint(Sketcher.Constraint('Radius',6,r))

        return sketch

    @staticmethod
    def create_box(label, plane_label, x, y, z):
        obj = Box._create_object(label)

        sketch_label = label+'_sketch'
        sketch = Box._create_sketch(sketch_label, obj, x, y)

        pad_label = label+'_pad'
        pad = Box._create_pad(pad_label, obj, sketch, z)

        sketch.Visibility = False
        App.ActiveDocument.recompute()

    @staticmethod
    def create_side_rounded_box(label, plane_label, x, y, z, r):
        obj = Box._create_object(label)

        sketch_label = label+'_sketch'
        sketch = Box._create_rounded_rect_sketch(sketch_label, obj, x, y, r)

        pad_label = label+'_pad'
        pad = Box._create_pad(pad_label, obj, sketch, z)

        sketch.Visibility = False
        App.ActiveDocument.recompute()
