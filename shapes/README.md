# FreeCAD Shape Generation Library

A Python library for programmatically creating and manipulating 3D shapes in FreeCAD. This library provides a clean API for generating parametric shapes, performing boolean operations, transformations, and exporting to various file formats.

## Classes Overview

### 1. Shape (Base Class)
Location: `shape.py:3`

Base class providing core functionality for creating FreeCAD objects, sketches, and pads.

### 2. Cylinder
Location: `cylinder.py:13`

Creates cylindrical shapes.

**Public Methods:**

`Cylinder.create_cylinder(label, plane_label, r, height)`
- **Parameters:**
  - `label` (str): Name/label for the cylinder object
  - `plane_label` (str): Plane to create on (e.g., 'XY_Plane', 'XZ_Plane', 'YZ_Plane')
  - `r` (float): Radius of the cylinder
  - `height` (float): Height/length of the cylinder
- **Example:**
  ```python
  from cylinder import Cylinder
  Cylinder.create_cylinder('c1', 'XY_Plane', 5, 10)
  ```

### 3. Box
Location: `box.py:14`

Creates rectangular box shapes with optional rounded edges.

**Public Methods:**

`Box.create_box(label, plane_label, x, y, z)`
- **Parameters:**
  - `label` (str): Name/label for the box object
  - `plane_label` (str): Plane to create on (e.g., 'XY_Plane')
  - `x` (float): Width (X dimension)
  - `y` (float): Depth (Y dimension)
  - `z` (float): Height (Z dimension)
- **Example:**
  ```python
  from box import Box
  Box.create_box('b1', 'XY_Plane', 10, 20, 5)
  ```

`Box.create_side_rounded_box(label, plane_label, x, y, z, r)`
- **Parameters:**
  - `label` (str): Name/label for the box object
  - `plane_label` (str): Plane to create on
  - `x` (float): Width (X dimension)
  - `y` (float): Depth (Y dimension)
  - `z` (float): Height (Z dimension)
  - `r` (float): Radius of rounded edges
- **Example:**
  ```python
  from box import Box
  Box.create_side_rounded_box('b2', 'XY_Plane', 10, 20, 5, 2)
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
  from boolean import Boolean
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
  from transform import Transform
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

### 6. Context
Location: `context.py:9`

Utility class for managing and inspecting FreeCAD objects.

**Public Methods:**

`Context.get_object(obj_or_label)`
- **Description:** Retrieves FreeCAD object from label or returns object if already an object
- **Parameters:**
  - `obj_or_label` (str or object): Object label or object itself
- **Returns:** FreeCAD object

`Context.print_object(obj_or_label)`
- **Description:** Prints object hierarchy/structure
- **Parameters:**
  - `obj_or_label` (str or object): Object or label to print

`Context.print_document()`
- **Description:** Prints entire document structure
- **Example:**
  ```python
  from context import Context
  Context.print_document()
  ```

`Context.remove_object(obj_or_label)`
- **Description:** Removes object and its children from the document
- **Parameters:**
  - `obj_or_label` (str or object): Object or label to remove
- **Example:**
  ```python
  Context.remove_object('box1')
  ```

### 7. Export
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
  from export import Export
  Export.export('box1', 'C:/output/mybox.step')
  Export.export('cylinder1', 'C:/output/cylinder.stl', 'stl')
  ```

## Complete Usage Example

```python
import FreeCAD as App
from box import Box
from cylinder import Cylinder
from boolean import Boolean
from transform import Transform
from export import Export
from context import Context

Box.create_box('main_box', 'XY_Plane', 20, 20, 10)

Cylinder.create_cylinder('hole', 'XY_Plane', 5, 15)

Transform.translate_to('hole', 10, 10, -2.5)

Boolean.cut('box_with_hole', 'main_box', 'hole')

Context.print_document()

Export.export('main_box', 'C:/output/box_with_hole.step')
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

6. **Error Handling:** Most methods will print error messages if objects are not found or operations fail

## Tips for LLM Usage

- Always ensure a FreeCAD document is active before using these classes
- Use descriptive labels for objects to make them easy to reference later
- Boolean operations can accept single objects or lists of objects for the secondary parameter
- Transform operations use absolute positioning (not relative)
- Export automatically creates directories if they don't exist
- Use Context.print_document() to inspect the current object hierarchy
- When performing multiple operations, consider the order: create shapes, transform them, then apply boolean operations
