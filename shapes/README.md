# FreeCAD Shape Generation Library

A Python library for programmatically creating and manipulating 3D shapes in FreeCAD. This library provides a clean API for generating parametric shapes, performing boolean operations, transformations, and exporting to various file formats.

## API Versioning

The shapes library supports versioning to maintain backward compatibility as the API evolves.

### Importing Specific Versions

**Recommended:** Always use versioned imports to ensure your scripts remain stable as the library evolves.

```python
# Recommended: Import from a specific version
from shapes.v1 import AdditiveBox, Boolean

# Alternative: Import the latest version (default) - may break when library updates
from shapes import AdditiveBox, Boolean
```

### Mixing Versions in the Same Script

Different versions can be mixed in the same script:

```python
from shapes.v1 import AdditiveBox as BoxV1
from shapes import AdditiveBox as BoxLatest

# Use v1 API
BoxV1.create_box('box_v1', x_size=10, y_size=10, z_size=5)

# Use latest API
BoxLatest.create_box('box_latest', x_size=20, y_size=20, z_size=10)
```

### Available Versions

- `shapes.v1` - Initial version (current stable API)
- `shapes` - Always points to the latest version

### Version Compatibility

When new versions are released:
- Old versions remain available via `shapes.vN` imports
- The main `shapes` import always provides the latest API
- Versioned imports guarantee stability for existing scripts

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
  from shapes.v1 import AdditiveCylinder
  # Basic cylinder
  AdditiveCylinder.create_cylinder('c1', 'XY_Plane', 5, 10)
  # Cylinder with offset and rotation
  AdditiveCylinder.create_cylinder('c2', 'XY_Plane', 5, 10, x_offset=10, z_offset=5, yaw=45)
  ```

### 3. AdditiveSphere
Location: `additive_sphere.py:9`

Creates spherical shapes using FreeCAD's PartDesign AdditiveSphere feature with support for attachment offsets.

The sphere is created centered at the XY plane center. Supports full 360-degree spheres by default.

**Public Methods:**

`AdditiveSphere.create_sphere(label, radius, x_offset=0, y_offset=0, z_offset=0)`
- **Parameters:**
  - `label` (str): Name/label for the sphere object
  - `radius` (float): Radius of the sphere in mm
  - `x_offset` (float, optional): X-axis offset from attachment plane (default: 0)
  - `y_offset` (float, optional): Y-axis offset from attachment plane (default: 0)
  - `z_offset` (float, optional): Z-axis offset from attachment plane (default: 0)
- **Example:**
  ```python
  from shapes.v1 import AdditiveSphere
  # Basic sphere
  AdditiveSphere.create_sphere('s1', 5)
  # Sphere with offset
  AdditiveSphere.create_sphere('s2', 5, x_offset=10, y_offset=10, z_offset=5)
  ```

### 4. AdditivePrism
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
  from shapes.v1 import AdditivePrism
  # Hexagonal prism
  AdditivePrism.create_prism('hex1', 'XY_Plane', 6, 5, 10)
  # Triangle with offset and rotation
  AdditivePrism.create_prism('tri1', 'XY_Plane', 3, 8, 15, x_offset=20, yaw=30)
  # Octagon
  AdditivePrism.create_prism('oct1', 'XY_Plane', 8, 6, 12)
  ```

### 5. AdditiveBox
Location: `additive_box.py:11`

Creates rectangular box shapes using FreeCAD's PartDesign AdditiveBox feature with support for attachment offsets and rotation.

The box is created from the global coordinate origin, extending in the positive X, Y, and Z directions.

**Public Methods:**

`AdditiveBox.create_box(label, x_size, y_size, z_size, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0)`
- **Description:** Creates a box on the XY plane. x_size, y_size, z_size map directly to length, width, height.
- **Parameters:**
  - `label` (str): Name/label for the box object
  - `x_size` (float): X-axis dimension in mm
  - `y_size` (float): Y-axis dimension in mm
  - `z_size` (float): Z-axis dimension in mm
  - `x_offset` (float, optional): X-axis offset from attachment plane (default: 0)
  - `y_offset` (float, optional): Y-axis offset from attachment plane (default: 0)
  - `z_offset` (float, optional): Z-axis offset from attachment plane (default: 0)
  - `yaw` (float, optional): Rotation around Z-axis in degrees (default: 0)
  - `pitch` (float, optional): Rotation around Y-axis in degrees (default: 0)
  - `roll` (float, optional): Rotation around X-axis in degrees (default: 0)
- **Example:**
  ```python
  from shapes.v1 import AdditiveBox
  # Basic box: 10mm x 20mm x 5mm
  AdditiveBox.create_box('b1', x_size=10, y_size=20, z_size=5)
  # Box with offset and rotation
  AdditiveBox.create_box('b2', x_size=10, y_size=20, z_size=5, x_offset=15, y_offset=10, pitch=30)
  ```

### 6. Pad
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
  from shapes.v1 import Pad
  # Assuming 'my_sketch' already exists in the document
  Pad.create_pad('extruded_shape', 'my_sketch', 15)
  # Update existing pad with new height
  Pad.create_pad('extruded_shape', 'my_sketch', 20)
  ```

### 7. EdgeFeature
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
  from shapes.v1 import EdgeFeature, AdditiveBox
  # Create a box
  AdditiveBox.create_box('box1', 'XY_Plane', x_size=10, y_size=10, z_size=10)
  # Add fillet to specific edges
  EdgeFeature.add_fillet('fillet1', 'box1', ['Edge1', 'Edge2', 'Edge3'], 2)
  ```

`EdgeFeature.add_chamfer(label, object_label, edges, size, angle=None)`
- **Description:** Adds a chamfer (beveled edge) to selected edges of an existing object. Supports both "Equal distance" (default) and "Distance and Angle" chamfer types.
- **Parameters:**
  - `label` (str): Name/label for the chamfer feature
  - `object_label` (str): Label of the existing object to add chamfer to
  - `edges` (list): List of edge labels (e.g., ['Edge1', 'Edge2'])
  - `size` (float): Chamfer size/distance in mm
  - `angle` (float, optional): Chamfer angle in degrees.
- **Example:**
  ```python
  # Equal distance chamfer (default)
  EdgeFeature.add_chamfer('chamfer1', 'box1', ['Edge5', 'Edge6'], 1.5)

  # Distance and angle chamfer (45 degree angle)
  EdgeFeature.add_chamfer('chamfer2', 'box1', ['Edge9', 'Edge10'], 2.0, angle=45)

  # Distance and angle chamfer (60 degree angle)
  EdgeFeature.add_chamfer('chamfer3', 'box1', ['Edge11'], 1.0, angle=60)
  ```

### 8. Boolean
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
  from shapes.v1 import Boolean
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

### 9. Transform
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
  from shapes.v1 import Transform
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

### 10. Export
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
  from shapes.v1 import Export
  Export.export('box1', 'C:/output/mybox.step')
  Export.export('cylinder1', 'C:/output/cylinder.stl', 'stl')
  ```

### 11. Folder
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
  from shapes.v1 import Folder
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

### 12. Clone
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
  from shapes.v1 import Clone, AdditiveBox

  # Create original object
  AdditiveBox.create_box('original', 'XY_Plane', x_size=10, y_size=10, z_size=10)

  # Create a clone at the origin (default offset and rotation)
  Clone.create_clone('clone1', 'original')

  # Create a clone with custom offset (translated 20mm in X direction)
  Clone.create_clone('clone2', 'original', offset=(20, 0, 0))

  # Create a clone with offset and rotation (rotated 45 degrees around Z axis)
  Clone.create_clone('clone3', 'original', offset=(40, 0, 0), rotation=(0, 0, 45))

  # Update existing clone (idempotent)
  Clone.create_clone('clone1', 'original', offset=(10, 10, 0))
  ```

### 13. Copy
Location: `copy.py:9`

Creates a Body object with an independent geometric copy of another object. Unlike Clone which creates a parametric reference, Copy creates an independent copy that doesn't change when the original is modified.

**Public Methods:**

`Copy.create_copy(label, base_obj_or_label, offset=(0, 0, 0), rotation=(0, 0, 0))`
- **Description:** Creates a new Body containing a SimpleCopy feature that is an independent copy of an existing object
- **Parameters:**
  - `label` (str): Name/label for the Body containing the copy
  - `base_obj_or_label` (str or object): The object or label to copy
  - `offset` (tuple, optional): Tuple of (x, y, z) offset values. Defaults to (0, 0, 0)
  - `rotation` (tuple, optional): Tuple of (yaw, pitch, roll) rotation values in degrees. Defaults to (0, 0, 0)
- **Returns:** The Body object containing the copy, or None if in teardown mode
- **Key Differences from Clone:**
  - **Clone:** Creates a parametric reference that updates when the original changes
  - **Copy:** Creates an independent geometric copy that doesn't update with the original
- **Example:**
  ```python
  from shapes.v1 import Copy, AdditiveBox

  # Create original object
  AdditiveBox.create_box('original', 'XY_Plane', x_size=10, y_size=10, z_size=10)

  # Create an independent copy at the origin
  Copy.create_copy('copy1', 'original')

  # Create a copy with custom offset (translated 20mm in X direction)
  Copy.create_copy('copy2', 'original', offset=(20, 0, 0))

  # Create a copy with offset and rotation (rotated 45 degrees around Z axis)
  Copy.create_copy('copy3', 'original', offset=(40, 0, 0), rotation=(0, 0, 45))

  # Update existing copy (idempotent)
  Copy.create_copy('copy1', 'original', offset=(10, 10, 0))
  ```

### 14. ImportGeometry
Location: `import_geometry.py:11`

Imports 3D geometry from external files into the FreeCAD document. Supports multiple common 3D file formats and can optionally wrap imported geometry in a PartDesign Body.

**Public Methods:**

`ImportGeometry.import_geometry(file_path, label=None, file_type=None)`
- **Description:** Imports 3D geometry from a file into the FreeCAD document. Automatically detects file type from extension if not specified.
- **Parameters:**
  - `file_path` (str): Full path to the file to import
  - `label` (str, optional): Name/label for the imported object. If not specified, uses the filename without extension
  - `file_type` (str, optional): File format type. If not specified, inferred from file extension
- **Supported file formats:**
  - STEP (.step, .stp) - Standard exchange format
  - STL (.stl) - Triangulated mesh
  - IGES (.iges, .igs) - CAD exchange format
  - OBJ (.obj) - Wavefront 3D object
  - BREP (.brep) - Boundary representation
  - VRML/WRL (.wrl, .vrml) - Virtual Reality Modeling Language
- **Returns:** The imported object(s), or None if import failed
- **Note:** This method is idempotent - if an object with the label already exists, it returns the existing object without re-importing
- **Example:**
  ```python
  from shapes.v1 import ImportGeometry

  # Import STEP file with auto-detected type
  ImportGeometry.import_geometry('C:/models/part.step')

  # Import with custom label
  ImportGeometry.import_geometry('C:/models/bracket.stl', label='my_bracket')

  # Import with explicit file type
  ImportGeometry.import_geometry('C:/models/model.obj', label='imported_obj', file_type='obj')

  # Import VRML file (commonly used for PCB models)
  ImportGeometry.import_geometry('./artifacts/pcb.wrl', label='pcb_model')
  ```

`ImportGeometry.import_as_body(file_path, label=None, file_type=None)`
- **Description:** Imports 3D geometry and wraps it in a PartDesign::Body for integration with PartDesign workflow. The Body will have '_imported' suffix and contains a geometry child with '_geometry' suffix.
- **Parameters:**
  - `file_path` (str): Full path to the file to import
  - `label` (str, optional): Base name for the Body object (actual Body will be named '{label}_imported'). If not specified, uses the filename without extension
  - `file_type` (str, optional): File format type. If not specified, inferred from file extension
- **Returns:** The Body object containing the imported geometry, or the imported object directly if it cannot be added to a Body (e.g., mesh objects)
- **Note:**
  - Mesh objects (STL, OBJ) and VRML objects cannot be added to a Body and will be returned as-is
  - STEP, IGES, and BREP formats work well with PartDesign Bodies
  - This method is idempotent - if the Body and geometry already exist, returns the existing Body
- **Example:**
  ```python
  from shapes.v1 import ImportGeometry

  # Import STEP file as Body (creates 'part_imported' Body with 'part_geometry' child)
  body = ImportGeometry.import_as_body('C:/models/part.step')

  # Import with custom label (creates 'motor_imported' Body with 'motor_geometry' child)
  body = ImportGeometry.import_as_body('C:/models/motor.stp', label='motor')

  # Import BREP as Body
  body = ImportGeometry.import_as_body('C:/models/component.brep', label='component')

  # Import STL (will return mesh object directly, not in Body)
  mesh = ImportGeometry.import_as_body('C:/models/scan.stl', label='scan')
  ```

## Complete Usage Example

```python
from shapes.v1 import AdditiveBox, AdditiveCylinder, Boolean, Folder, Export

# Create a box (20mm x 20mm x 10mm on XY plane)
AdditiveBox.create_box('main_box', 'XY_Plane', x_size=20, y_size=20, z_size=10)

# Create a cylinder with offset to position it
AdditiveCylinder.create_cylinder('hole', 'XY_Plane', 5, 15, x_offset=10, y_offset=10)

# Cut the cylinder from the box
Boolean.cut('box_with_holes', 'main_box', ['hole'])

# Organize objects into a folder
Folder.create_folder('my_project')
Folder.add_to_folder('my_project', ['box_with_holes', 'hole'])

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

6. **Idempotent Operations:** The `create_box`, `create_cylinder`, `create_sphere`, `create_prism`, `create_pad`, `create_clone`, and `create_copy` methods are idempotent - calling them multiple times with the same label will update the existing object instead of creating duplicates

## Tips for LLM Usage

- Use descriptive labels for objects to make them easy to reference later
- Boolean operations can accept single objects or lists of objects for the secondary parameter
- Transform operations use absolute positioning (not relative)
- Export automatically creates directories if they don't exist
- When performing multiple operations, consider the order: create shapes, transform them, then apply boolean operations
- For boxes with rounded edges, use `create_fillet_side_box` with individual edge radii