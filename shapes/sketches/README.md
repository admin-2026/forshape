# shapes.sketches — 2D Primitives & Boolean Operations

## Rules
- All parameters are keyword-only.
- All `Primitives2D` methods return a `Part.Face` on the XY plane (z=0).
- All `Boolean2D` methods return a `Part.Shape`.
- `rotation` is in degrees, counter-clockwise, default `0`.


## API

### `Primitives2D.make_polygon(*, points, rotation=0)`
- `points`: list of `(x, y)` tuples — open list, closing vertex added automatically.
- Rotation pivot: centroid of `points`.

### `Primitives2D.make_rect(*, x, y, w, h, rotation=0)`
- `x, y`: bottom-left corner. `w, h`: width and height.
- Rotation pivot: rectangle centre `(x + w/2, y + h/2)`.

### `Primitives2D.make_circle(*, cx, cy, r, rotation=0)`
- `cx, cy`: centre. `r`: radius.
- `rotation` has no effect (circle is rotationally symmetric); accepted for consistency.

### `Primitives2D.make_ellipse(*, cx, cy, r1, r2, rotation=0)`
- `cx, cy`: centre. `r1, r2`: radii — swapped automatically if `r1 < r2`.
- Rotation pivot: centre `(cx, cy)`.

---

## `Boolean2D`

Performs boolean operations on two `Part.Face` objects. All methods are static.

### `Boolean2D.union(face_a, face_b)`
Returns the union of `face_a` and `face_b`.

### `Boolean2D.intersection(face_a, face_b)`
Returns the area common to both faces.

### `Boolean2D.difference(face_a, face_b)`
Returns `face_a` with `face_b` subtracted.

---

---

## `FaceToSketch`

Converts a `Part.Face` to a `Sketcher::SketchObject` by iterating its edges.

Autoconstraints applied automatically:
- **Coincident** — shared vertices between edges
- **Horizontal** — line segments where `dy < tol`
- **Vertical** — line segments where `dx < tol`

Supported curve types: `Part.Line`, `Part.Circle` (full circle and arc), `Part.BSplineCurve`.

### `FaceToSketch.convert(face, name, tol=1e-6)`
- `face`: `Part.Face` to convert.
- `name`: Name for the new sketch object.
- `tol`: Tolerance for coincident/degenerate checks (default `1e-6`).
- Uses `App.ActiveDocument` internally.
- Returns: `Sketcher::SketchObject`

---

## Examples

```python
from shapes.sketches.v0 import Primitives2D, Boolean2D, FaceToSketch

Primitives2D.make_polygon(points=[(0,0),(10,0),(5,8)])
Primitives2D.make_polygon(points=[(0,0),(10,0),(5,8)], rotation=90)

Primitives2D.make_rect(x=0, y=0, w=20, h=10)
Primitives2D.make_rect(x=0, y=0, w=20, h=10, rotation=45)

Primitives2D.make_circle(cx=0, cy=0, r=5)

Primitives2D.make_ellipse(cx=0, cy=0, r1=10, r2=4)
Primitives2D.make_ellipse(cx=0, cy=0, r1=10, r2=4, rotation=60)

a = Primitives2D.make_rect(x=0, y=0, w=20, h=20)
b = Primitives2D.make_circle(cx=10, cy=10, r=8)

Boolean2D.union(a, b)
Boolean2D.intersection(a, b)
Boolean2D.difference(a, b)

face = Primitives2D.make_rect(x=0, y=0, w=20, h=10)
sketch = FaceToSketch.convert(face, "MySketch")

sketch = FaceToSketch.convert(face, "MySketch", tol=1e-5)
```
