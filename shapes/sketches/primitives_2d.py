import FreeCAD as App
import Part

_Z_AXIS = App.Vector(0, 0, 1)


class Primitives2D:
    @staticmethod
    def make_polygon(*, points, rotation=0):
        """
        Create a planar polygon Part.Face from a list of (x, y) points.
        Rotation is applied around the centroid of the points.

        Args:
            points: List of (x, y) tuples defining the polygon vertices (open list; closing
                    vertex is added automatically).
            rotation: Rotation angle in degrees around the centroid (default 0).

        Returns:
            Part.Face
        """
        vectors = [App.Vector(x, y, 0) for x, y in points]
        vectors.append(vectors[0])  # close
        wire = Part.makePolygon(vectors)
        face = Part.Face(wire)
        if rotation:
            cx = sum(p[0] for p in points) / len(points)
            cy = sum(p[1] for p in points) / len(points)
            face.rotate(App.Vector(cx, cy, 0), _Z_AXIS, rotation)
        return face

    @staticmethod
    def make_rect(*, x, y, w, h, rotation=0):
        """
        Create a planar rectangular Part.Face at (x, y) with size w x h.
        Rotation is applied around the centre of the rectangle.

        Args:
            x, y: Bottom-left corner coordinates.
            w, h: Width and height.
            rotation: Rotation angle in degrees around the rect centre (default 0).

        Returns:
            Part.Face
        """
        wire = Part.makePolygon(
            [
                App.Vector(x, y, 0),
                App.Vector(x + w, y, 0),
                App.Vector(x + w, y + h, 0),
                App.Vector(x, y + h, 0),
                App.Vector(x, y, 0),  # close
            ]
        )
        face = Part.Face(wire)
        if rotation:
            face.rotate(App.Vector(x + w / 2, y + h / 2, 0), _Z_AXIS, rotation)
        return face

    @staticmethod
    def make_circle(*, cx, cy, r, rotation=0):
        """
        Create a planar circular Part.Face centred at (cx, cy) with radius r.

        Args:
            cx, cy: Centre coordinates.
            r: Radius.
            rotation: Rotation angle in degrees (no effect on a circle; included for API
                      consistency, default 0).

        Returns:
            Part.Face
        """
        edge = Part.makeCircle(r, App.Vector(cx, cy, 0))
        wire = Part.Wire(edge)
        return Part.Face(wire)

    @staticmethod
    def make_ellipse(*, cx, cy, r1, r2, rotation=0):
        """
        Create a planar elliptical Part.Face centred at (cx, cy).
        Rotation is applied around the centre.

        Args:
            cx, cy: Centre coordinates.
            r1: First radius (major and minor are sorted automatically).
            r2: Second radius.
            rotation: Rotation angle in degrees around the centre (default 0).

        Returns:
            Part.Face
        """
        if r1 < r2:
            r1, r2 = r2, r1
        edge = Part.makeEllipse(r1, r2, App.Vector(cx, cy, 0))
        wire = Part.Wire(edge)
        face = Part.Face(wire)
        if rotation:
            face.rotate(App.Vector(cx, cy, 0), _Z_AXIS, rotation)
        return face
