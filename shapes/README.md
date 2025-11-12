# FreeCAD Shape Generation Library

A Python library for programmatically creating and manipulating 3D shapes in FreeCAD. This library provides a clean API for generating parametric shapes, performing boolean operations, transformations, and exporting to various file formats.

## Classes Overview

### 1. Shape (Base Class)
Location: `shape.py:3`

Base class providing core functionality for creating FreeCAD objects, sketches, and pads.

### 2. AdditiveCylinder
Location: `additive_cylinder.py:9`

Creates cylindrical shapes using FreeCAD's PartDesign AdditiveCylinder feature with support for attachment offsets and rotation.

The cylinder is created at the given plane center. The height is extruded in the positive normal direction of the plane.

**Public Methods:**

`AdditiveCylinder.create_cylinder(label, plane_label, radius, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0)`
- **Parameters:**
  - `label` (str): Name/label for the cylinder object
  - `plane_label` (str): Plane to attach to (e.g., 'XY_Plane', 'XZ_Plane', 'YZ_Plane')
  - `radius` (float): Radius of the cylinder in mm
  - `height` (float): Height/length of the cylinder in mm
  - `x_offset` (float, optional): X-axis offset from attachment plane (default: 0)
  - `y_offset` (float, optional): Y-axis offset from attachment plane (default: 0)
  - `z_offset` (float, optional): Z-axis offset from attachment plane (default: 0)
  - `yaw` (float, optional): Rotation around Z-axis in degrees (default: 0)
  - `pitch` (float, optional): Rotation around Y-axis in degrees (default: 0)
  - `roll` (float, optional): Rotation around X-axis in degrees (default: 0)
- **Example:**
  ```python
  from shapes.additive_cylinder import AdditiveCylinder
  # Basic cylinder
  AdditiveCylinder.create_cylinder('c1', 'XY_Plane', 5, 10)
  # Cylinder with offset and rotation
  AdditiveCylinder.create_cylinder('c2', 'XY_Plane', 5, 10, x_offset=10, z_offset=5, yaw=45)
  ```

### 3. AdditiveBox
Location: `additive_box.py:9`

Creates rectangular box shapes using FreeCAD's PartDesign AdditiveBox feature with support for attachment offsets and rotation.

The box is created with the bottom left corner on the plane origin. The height is extruded in the positive normal direction of the plane.

**Public Methods:**

`AdditiveBox.create_box(label, plane_label, length, width, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0)`
- **Parameters:**
  - `label` (str): Name/label for the box object
  - `plane_label` (str): Plane to attach to (e.g., 'XY_Plane')
  - `length` (float): Length dimension in mm
  - `width` (float): Width dimension in mm
  - `height` (float): Height dimension in mm
  - `x_offset` (float, optional): X-axis offset from attachment plane (default: 0)
  - `y_offset` (float, optional): Y-axis offset from attachment plane (default: 0)
  - `z_offset` (float, optional): Z-axis offset from attachment plane (default: 0)
  - `yaw` (float, optional): Rotation around Z-axis in degrees (default: 0)
  - `pitch` (float, optional): Rotation around Y-axis in degrees (default: 0)
  - `roll` (float, optional): Rotation around X-axis in degrees (default: 0)
- **Example:**
  ```python
  from shapes.additive_box import AdditiveBox
  # Basic box
  AdditiveBox.create_box('b1', 'XY_Plane', 10, 20, 5)
  # Box with offset and rotation
  AdditiveBox.create_box('b2', 'XY_Plane', 10, 20, 5, x_offset=15, y_offset=10, pitch=30)
  ```

### 4. Boolean
Location: `boolean.py:9`

Performs boolean operations between shapes (union, difference, intersection).

**Public Methods:**

`Boolean.fuse(fuse_label, primary, secondary)`
- **Description:** Union operation - combines shapes
- **Parameters:**
  - `fuse_label` (str): Label for the resulting fused object
  - `primary` (str or object): Primary object or its label
  - `secondary` (str, object, or list): Secondary object(s) to fuse with
- **Example:**
  ```python
  from shapes.boolean import Boolean
  Boolean.fuse('fused', 'box1', 'box2')
  ```

`Boolean.cut(cut_label, primary, secondary)`
- **Description:** Difference operation - subtracts secondary from primary
- **Parameters:**
  - `cut_label` (str): Label for the resulting cut object
  - `primary` (str or object): Object to cut from
  - `secondary` (str, object, or list): Object(s) to subtract
- **Example:**
  ```python
  Boolean.cut('cut_result', 'box1', 'cylinder1')
  ```

`Boolean.common(common_label, primary, secondary)`
- **Description:** Intersection operation - keeps only overlapping volume
- **Parameters:**
  - `common_label` (str): Label for the resulting common object
  - `primary` (str or object): First object
  - `secondary` (str, object, or list): Second object(s)
- **Example:**
  ```python
  Boolean.common('intersection', 'box1', 'cylinder1')
  ```

### 5. Transform
Location: `transform.py:5`

Provides spatial transformation operations for objects.

**Public Methods:**

`Transform.translate_to(object_or_label, x, y, z)`
- **Description:** Moves object to absolute position
- **Parameters:**
  - `object_or_label` (str or object): Object or its label to transform
  - `x` (float): X coordinate
  - `y` (float): Y coordinate
  - `z` (float): Z coordinate
- **Example:**
  ```python
  from shapes.transform import Transform
  Transform.translate_to('box1', 10, 20, 5)
  ```

`Transform.rotate_to(object_or_label, x, y, z, degree)`
- **Description:** Rotates object around an axis
- **Parameters:**
  - `object_or_label` (str or object): Object or its label to rotate
  - `x` (float): X component of rotation axis
  - `y` (float): Y component of rotation axis
  - `z` (float): Z component of rotation axis
  - `degree` (float): Rotation angle in degrees
- **Example:**
  ```python
  Transform.rotate_to('cylinder1', 0, 1, 0, 45)
  ```

### 6. Export
Location: `export.py:6`

Exports FreeCAD objects to various file formats.

**Public Methods:**

`Export.export(object_or_label, file_path, file_type=None)`
- **Description:** Exports object to file
- **Parameters:**
  - `object_or_label` (str or object): Object or label to export
  - `file_path` (str): Full path for output file
  - `file_type` (str, optional): File format ('step', 'stl', 'iges', 'obj', 'brep')
    - If not specified, inferred from file extension
- **Supported formats:**
  - STEP (.step, .stp) - Standard exchange format
  - STL (.stl) - Triangulated mesh
  - IGES (.iges, .igs) - CAD exchange format
  - OBJ (.obj) - Wavefront 3D object
  - BREP (.brep) - Boundary representation
- **Example:**
  ```python
  from shapes.export import Export
  Export.export('box1', 'C:/output/mybox.step')
  Export.export('cylinder1', 'C:/output/cylinder.stl', 'stl')
  ```

## Complete Usage Example

```python
import FreeCAD as App
from shapes.additive_box import AdditiveBox
from shapes.additive_cylinder import AdditiveCylinder
from shapes.boolean import Boolean
from shapes.transform import Transform
from shapes.export import Export
from shapes.context import Context

# Create a box with offset
AdditiveBox.create_box('main_box', 'XY_Plane', 20, 20, 10)

# Create a cylinder with offset to position it
AdditiveCylinder.create_cylinder('hole', 'XY_Plane', 5, 15, x_offset=10, y_offset=10)

# Cut the cylinder from the box
Boolean.cut('box_with_hole', 'main_box', 'hole')

# Export the result
Export.export('box_with_hole', 'box_with_hole.step')
```

## Important Notes

1. **Plane Labels:** Common plane labels in FreeCAD are:
   - `'XY_Plane'` - Horizontal plane
   - `'XZ_Plane'` - Vertical plane (front)
   - `'YZ_Plane'` - Vertical plane (side)

2. **Object Labels:** All object labels must be unique within the document

3. **Recompute:** Most operations automatically call `App.ActiveDocument.recompute()` to update the 3D view

4. **Units:** All dimensions are in FreeCAD's default units (typically millimeters)

5. **Sketch Visibility:** Sketches are automatically hidden after pad creation for cleaner visualization

## Tips for LLM Usage

- Use descriptive labels for objects to make them easy to reference later
- Boolean operations can accept single objects or lists of objects for the secondary parameter
- Transform operations use absolute positioning (not relative)
- Export automatically creates directories if they don't exist
- When performing multiple operations, consider the order: create shapes, transform them, then apply boolean operations