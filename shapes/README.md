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

### 3. AdditivePrism
Location: `additive_prism.py:9`

Creates regular polygon prism shapes using FreeCAD's PartDesign AdditivePrism feature with support for attachment offsets and rotation.

The prism is created at the given plane center. The height is extruded in the positive normal direction of the plane.

**Public Methods:**

`AdditivePrism.create_prism(label, plane_label, polygon, circumradius, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0)`
- **Parameters:**
  - `label` (str): Name/label for the prism object
  - `plane_label` (str): Plane to attach to (e.g., 'XY_Plane', 'XZ_Plane', 'YZ_Plane')
  - `polygon` (int): Number of sides for the prism (e.g., 3=triangle, 6=hexagon, 8=octagon)
  - `circumradius` (float): Radius of the circumscribed circle in mm
  - `height` (float): Height/length of the prism in mm
  - `x_offset` (float, optional): X-axis offset from attachment plane (default: 0)
  - `y_offset` (float, optional): Y-axis offset from attachment plane (default: 0)
  - `z_offset` (float, optional): Z-axis offset from attachment plane (default: 0)
  - `yaw` (float, optional): Rotation around Z-axis in degrees (default: 0)
  - `pitch` (float, optional): Rotation around Y-axis in degrees (default: 0)
  - `roll` (float, optional): Rotation around X-axis in degrees (default: 0)
- **Example:**
  ```python
  from shapes.additive_prism import AdditivePrism
  # Hexagonal prism
  AdditivePrism.create_prism('hex1', 'XY_Plane', 6, 5, 10)
  # Triangle with offset and rotation
  AdditivePrism.create_prism('tri1', 'XY_Plane', 3, 8, 15, x_offset=20, yaw=30)
  # Octagon
  AdditivePrism.create_prism('oct1', 'XY_Plane', 8, 6, 12)
  ```

### 4. AdditiveBox
Location: `additive_box.py:11`

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

`AdditiveBox.create_slot(label, plane_label, length, width, height, radius, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0)`
- **Description:** Creates a rectangular slot with rounded corners using fillets. Useful for creating elongated holes or slots with smooth edges.
- **Parameters:**
  - `label` (str): Name/label for the slot object
  - `plane_label` (str): Plane to attach to (e.g., 'XY_Plane')
  - `length` (float): Length dimension in mm
  - `width` (float): Width dimension in mm
  - `height` (float): Height dimension in mm
  - `radius` (float): Fillet radius for rounded corners in mm
  - `x_offset` (float, optional): X-axis offset from attachment plane (default: 0)
  - `y_offset` (float, optional): Y-axis offset from attachment plane (default: 0)
  - `z_offset` (float, optional): Z-axis offset from attachment plane (default: 0)
  - `yaw` (float, optional): Rotation around Z-axis in degrees (default: 0)
  - `pitch` (float, optional): Rotation around Y-axis in degrees (default: 0)
  - `roll` (float, optional): Rotation around X-axis in degrees (default: 0)
- **Example:**
  ```python
  from shapes.additive_box import AdditiveBox
  # Basic slot with rounded corners
  AdditiveBox.create_slot('slot1', 'XY_Plane', 20, 10, 5, 2)
  # Fully rounded slot (stadium shape) - diameter equals width
  AdditiveBox.create_slot('slot2', 'XY_Plane', 30, 10, 5, 5, x_offset=25)
  # Slot with offset and rotation
  AdditiveBox.create_slot('slot3', 'XY_Plane', 15, 8, 3, 1.5, x_offset=10, y_offset=15, yaw=45)
  ```

### 5. Pad
Location: `pad.py:10`

Creates a body with a pad feature from an existing sketch. Useful when you have a pre-existing sketch and want to extrude it into a 3D body.

**Public Methods:**

`Pad.create_pad(label, sketch_label, height)`
- **Description:** Creates a body with a pad from an existing sketch. The pad is extruded centered on the sketch plane (midplane mode).
- **Parameters:**
  - `label` (str): Name/label for the body object
  - `sketch_label` (str): Label of the existing sketch to pad
  - `height` (float): Extrusion height in mm
- **Example:**
  ```python
  from shapes.pad import Pad
  # Assuming 'my_sketch' already exists in the document
  Pad.create_pad('extruded_shape', 'my_sketch', 15)
  # Update existing pad with new height
  Pad.create_pad('extruded_shape', 'my_sketch', 20)
  ```

### 6. EdgeFeature
Location: `edge_feature.py:10`

Adds design features (fillets, chamfers, drafts) to edges or faces of existing objects.

**Public Methods:**

`EdgeFeature.add_fillet(label, object_label, edges, radius)`
- **Description:** Adds a fillet (rounded edge) to selected edges of an existing object
- **Parameters:**
  - `label` (str): Name/label for the fillet feature
  - `object_label` (str): Label of the existing object to add fillet to
  - `edges` (list): List of edge labels (e.g., ['Edge1', 'Edge2', 'Edge3'])
  - `radius` (float): Fillet radius in mm
- **Example:**
  ```python
  from shapes.edge_feature import EdgeFeature
  from shapes.additive_box import AdditiveBox
  # Create a box
  AdditiveBox.create_box('box1', 'XY_Plane', 10, 10, 10)
  # Add fillet to specific edges
  EdgeFeature.add_fillet('fillet1', 'box1', ['Edge1', 'Edge2', 'Edge3'], 2)
  ```

`EdgeFeature.add_chamfer(label, object_label, edges, size)`
- **Description:** Adds a chamfer (beveled edge) to selected edges of an existing object
- **Parameters:**
  - `label` (str): Name/label for the chamfer feature
  - `object_label` (str): Label of the existing object to add chamfer to
  - `edges` (list): List of edge labels (e.g., ['Edge1', 'Edge2'])
  - `size` (float): Chamfer size in mm
- **Example:**
  ```python
  EdgeFeature.add_chamfer('chamfer1', 'box1', ['Edge5', 'Edge6'], 1.5)
  ```

`EdgeFeature.add_draft(label, object_label, faces, angle, neutral_plane)`
- **Description:** Adds a draft (tapered face) to selected faces of an existing object
- **Parameters:**
  - `label` (str): Name/label for the draft feature
  - `object_label` (str): Label of the existing object to add draft to
  - `faces` (list): List of face labels (e.g., ['Face1', 'Face2'])
  - `angle` (float): Draft angle in degrees
  - `neutral_plane` (str): Neutral plane label (e.g., 'XY_Plane')
- **Example:**
  ```python
  EdgeFeature.add_draft('draft1', 'box1', ['Face1', 'Face2'], 5, 'XY_Plane')
  ```

### 7. Boolean
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

### 8. Transform
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

### 9. Export
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

### 10. Folder
Location: `folder.py:9`

Manages folder organization in FreeCAD documents. Creates folders (DocumentObjectGroup) and adds objects to them for better organization.

**Public Methods:**

`Folder.create_folder(label)`
- **Description:** Creates a DocumentObjectGroup (folder) in the active document
- **Parameters:**
  - `label` (str): Name/label for the folder
- **Returns:** The folder object, or None if in teardown mode
- **Example:**
  ```python
  from shapes.folder import Folder
  # Create a folder
  Folder.create_folder('my_parts')
  ```

`Folder.add_to_folder(folder_label, obj_or_label_or_list)`
- **Description:** Adds one or more objects to a folder for organization
- **Parameters:**
  - `folder_label` (str): Label of the folder to add objects to
  - `obj_or_label_or_list` (str, object, or list): Single object/label or list of objects/labels to add
- **Returns:** True if all operations successful, False if any failed
- **Example:**
  ```python
  # Add a single object
  Folder.add_to_folder('my_parts', 'box1')

  # Add multiple objects at once
  Folder.add_to_folder('my_parts', ['box1', 'box2', 'cylinder1', 'prism1'])
  ```

### 11. Clone
Location: `clone.py:9`

Creates a Body object with a Clone feature that references another object. Clones are useful for creating instances of existing objects that maintain a reference to the original, allowing for efficient reuse of geometry with different placements.

**Public Methods:**

`Clone.create_clone(label, base_obj_or_label, offset=(0, 0, 0), rotation=(0, 0, 0))`
- **Description:** Creates a new Body containing a Clone feature that references an existing object
- **Parameters:**
  - `label` (str): Name/label for the Body containing the clone
  - `base_obj_or_label` (str or object): The object or label to clone
  - `offset` (tuple, optional): Tuple of (x, y, z) offset values. Defaults to (0, 0, 0)
  - `rotation` (tuple, optional): Tuple of (yaw, pitch, roll) rotation values in degrees. Defaults to (0, 0, 0)
- **Returns:** The Body object containing the clone, or None if in teardown mode
- **Example:**
  ```python
  from shapes.clone import Clone
  from shapes.additive_box import AdditiveBox

  # Create original object
  AdditiveBox.create_box('original', 'XY_Plane', 10, 10, 10)

  # Create a clone at the origin (default offset and rotation)
  Clone.create_clone('clone1', 'original')

  # Create a clone with custom offset (translated 20mm in X direction)
  Clone.create_clone('clone2', 'original', offset=(20, 0, 0))

  # Create a clone with offset and rotation (rotated 45 degrees around Z axis)
  Clone.create_clone('clone3', 'original', offset=(40, 0, 0), rotation=(0, 0, 45))

  # Update existing clone (idempotent)
  Clone.create_clone('clone1', 'original', offset=(10, 10, 0))
  ```

## Complete Usage Example

```python
from shapes.additive_box import AdditiveBox
from shapes.additive_cylinder import AdditiveCylinder
from shapes.boolean import Boolean
from shapes.folder import Folder
from shapes.export import Export

# Create a box with offset
AdditiveBox.create_box('main_box', 'XY_Plane', 20, 20, 10)

# Create a cylinder with offset to position it
AdditiveCylinder.create_cylinder('hole', 'XY_Plane', 5, 15, x_offset=10, y_offset=10)

# Create a rounded slot (stadium shape)
AdditiveBox.create_slot('slot', 'XY_Plane', 15, 6, 15, 3, x_offset=25)

# Cut the cylinder and slot from the box
Boolean.cut('box_with_holes', 'main_box', ['hole', 'slot'])

# Organize objects into a folder
Folder.create_folder('my_project')
Folder.add_to_folder('my_project', ['box_with_holes', 'hole', 'slot'])

# Export the result
Export.export('box_with_holes', 'box_with_holes.step')
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

6. **Idempotent Operations:** The `create_box`, `create_slot`, `create_cylinder`, `create_prism`, `create_pad`, and `create_clone` methods are idempotent - calling them multiple times with the same label will update the existing object instead of creating duplicates

## Tips for LLM Usage

- Use descriptive labels for objects to make them easy to reference later
- Boolean operations can accept single objects or lists of objects for the secondary parameter
- Transform operations use absolute positioning (not relative)
- Export automatically creates directories if they don't exist
- When performing multiple operations, consider the order: create shapes, transform them, then apply boolean operations
- For elongated holes with rounded ends (stadium/obround shapes), use `create_slot` with radius equal to half the width