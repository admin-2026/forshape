
import FreeCAD as App
import Part
import Sketcher

from shape import Shape

# import cylinder
# from importlib import reload
# reload(cylinder)
# cylinder.Cylinder.create_cylinder('c1', 'XY_Plane', 5, 2)

class Cylinder(Shape):

    @staticmethod
    def _draw_circle_sketch(sketch, r):
        geoList = []
        geoList.append(Part.Circle(App.Vector(0.0, 0.0, 0.0), App.Vector(0.0, 0.0, 1.0), 1))
        sketch.addGeometry(geoList,False)
        del geoList

        constraintList = []
        sketch.addConstraint(Sketcher.Constraint('Coincident', 0, 3, -1, 1))
        sketch.addConstraint(Sketcher.Constraint('Radius',0,r))

    @staticmethod
    def create_cylinder(label, plane_label, r, height):
        obj = Shape._create_object(label)

        sketch_label = label+'_sketch'
        sketch = Shape._create_sketch(sketch_label, obj, plane_label)
        Cylinder._draw_circle_sketch(sketch, r)

        pad_label = label+'_pad'
        pad = Shape._create_pad(pad_label, obj, sketch, height)

        sketch.Visibility = False
        App.ActiveDocument.recompute()
