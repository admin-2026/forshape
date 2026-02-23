import math

import FreeCAD as App
import Part
import Sketcher


class FaceToSketch:
    @staticmethod
    def convert(face, name, tol=1e-6):
        """
        Convert a Part.Face to a Sketcher::SketchObject by iterating its edges.

        Autoconstraints applied:
          - Coincident : shared vertices between edges
          - Horizontal : line segments with dy < tol
          - Vertical   : line segments with dx < tol

        Args:
            face: Part.Face to convert.
            name: Name for the new sketch object.
            tol:  Tolerance for coincident/degenerate checks (default 1e-6).

        Returns:
            Sketcher::SketchObject
        """
        sketch = App.ActiveDocument.addObject("Sketcher::SketchObject", name)
        # geo_data: list of (geo_index, start_pt, end_pt, edge_type)
        geo_data = []

        # --- Add geometry ---
        for edge in face.Edges:
            if edge.Length < tol:
                continue  # skip degenerate edges

            curve = edge.Curve
            p1 = edge.valueAt(edge.FirstParameter)
            p2 = edge.valueAt(edge.LastParameter)

            if isinstance(curve, Part.Line):
                idx = sketch.addGeometry(Part.LineSegment(p1, p2))
                geo_data.append((idx, p1, p2, "line"))

            elif isinstance(curve, Part.Circle):
                span = abs(edge.LastParameter - edge.FirstParameter)
                if span < 2 * math.pi - tol:  # arc
                    arc = Part.ArcOfCircle(curve, edge.FirstParameter, edge.LastParameter)
                    idx = sketch.addGeometry(arc)
                    geo_data.append((idx, p1, p2, "arc"))
                else:  # full circle
                    idx = sketch.addGeometry(Part.Circle(curve.Center, curve.Axis, curve.Radius))
                    geo_data.append((idx, None, None, "circle"))

            elif isinstance(curve, Part.BSplineCurve):
                idx = sketch.addGeometry(curve)
                geo_data.append((idx, p1, p2, "bspline"))

        # --- Coincident constraints ---
        # Sketcher point indices: 1 = start, 2 = end
        for i, (gi, sp_i, ep_i, _) in enumerate(geo_data):
            for j, (gj, sp_j, ep_j, _) in enumerate(geo_data):
                if j <= i:
                    continue
                if sp_i is None or sp_j is None:
                    continue
                for pa, pb, pi, pj in [
                    (sp_i, sp_j, 1, 1),
                    (sp_i, ep_j, 1, 2),
                    (ep_i, sp_j, 2, 1),
                    (ep_i, ep_j, 2, 2),
                ]:
                    if pa.distanceToPoint(pb) < tol:
                        sketch.addConstraint(Sketcher.Constraint("Coincident", gi, pi, gj, pj))

        # --- Horizontal / Vertical constraints (lines only) ---
        for idx, p1, p2, edge_type in geo_data:
            if edge_type != "line" or p1 is None:
                continue
            dx = abs(p2.x - p1.x)
            dy = abs(p2.y - p1.y)
            if dy < tol:
                sketch.addConstraint(Sketcher.Constraint("Horizontal", idx))
            elif dx < tol:
                sketch.addConstraint(Sketcher.Constraint("Vertical", idx))

        return sketch
