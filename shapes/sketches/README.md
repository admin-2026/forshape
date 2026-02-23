# shapes.sketches — 2D Primitives

## Rules
- All parameters are keyword-only.
- All methods return a `Part.Face` on the XY plane (z=0).
- `rotation` is in degrees, counter-clockwise, default `0`.
- Import: `from shapes.sketches import Primitives2D`

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

## Examples

```python
from shapes.sketches import Primitives2D

Primitives2D.make_polygon(points=[(0,0),(10,0),(5,8)])
Primitives2D.make_polygon(points=[(0,0),(10,0),(5,8)], rotation=90)

Primitives2D.make_rect(x=0, y=0, w=20, h=10)
Primitives2D.make_rect(x=0, y=0, w=20, h=10, rotation=45)

Primitives2D.make_circle(cx=0, cy=0, r=5)

Primitives2D.make_ellipse(cx=0, cy=0, r1=10, r2=4)
Primitives2D.make_ellipse(cx=0, cy=0, r1=10, r2=4, rotation=60)
```
