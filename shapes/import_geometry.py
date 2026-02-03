import os

import FreeCAD as App

from .context import Context
from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from shapes.import_geometry import ImportGeometry
# from importlib import reload; import shapes.import_geometry; reload(shapes.import_geometry)
# ImportGeometry.import_geometry("./artifacts/pcb.wrl")


class ImportGeometry(Shape):
    @staticmethod
    def import_geometry(file_path, label=None, file_type=None):
        """
        Import 3D geometry from a file into the FreeCAD document.
        Idempotent: if an object with the label already exists, returns it without re-importing.

        Args:
            file_path: The full path to the file to import
            label: Optional label for the imported object(s)
                  If not specified, will use the filename without extension
            file_type: Optional file type ('step', 'stl', 'iges', 'obj', 'brep', etc.)
                      If not specified, it will be inferred from file_path extension

        Returns:
            The imported object(s) or None if import failed
        """
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        # Determine file type from extension if not specified
        if file_type is None:
            _, ext = os.path.splitext(file_path)
            file_type = ext.lstrip(".").lower()
        else:
            file_type = file_type.lower()

        # Generate label from filename if not specified
        if label is None:
            filename = os.path.basename(file_path)
            label, _ = os.path.splitext(filename)

        # Check if object with this label already exists
        existing_obj = Context.get_object(label)
        if existing_obj is not None:
            print(f'Object "{label}" already exists, returning existing object')
            return existing_obj

        try:
            # Import based on file type
            if file_type in ["step", "stp"]:
                import Import

                Import.insert(file_path, App.ActiveDocument.Name)
                print(f"Imported {file_path} as STEP")
                # Get the imported objects (they are added to the document)
                imported_objs = ImportGeometry._get_recently_added_objects(label)
                return imported_objs

            elif file_type == "stl":
                import Mesh

                mesh = Mesh.Mesh(file_path)
                mesh_obj = App.ActiveDocument.addObject("Mesh::Feature", label)
                mesh_obj.Mesh = mesh
                App.ActiveDocument.recompute()
                print(f"Imported {file_path} as STL")
                return mesh_obj

            elif file_type in ["iges", "igs"]:
                import Import

                Import.insert(file_path, App.ActiveDocument.Name)
                print(f"Imported {file_path} as IGES")
                imported_objs = ImportGeometry._get_recently_added_objects(label)
                return imported_objs

            elif file_type == "obj":
                import Mesh

                mesh = Mesh.Mesh(file_path)
                mesh_obj = App.ActiveDocument.addObject("Mesh::Feature", label)
                mesh_obj.Mesh = mesh
                App.ActiveDocument.recompute()
                print(f"Imported {file_path} as OBJ")
                return mesh_obj

            elif file_type == "brep":
                import Part

                shape = Part.Shape()
                shape.read(file_path)
                part_obj = App.ActiveDocument.addObject("Part::Feature", label)
                part_obj.Shape = shape
                App.ActiveDocument.recompute()
                print(f"Imported {file_path} as BREP")
                return part_obj

            elif file_type in ["wrl", "vrml"]:
                # Create a VRML object
                vrml_obj = App.ActiveDocument.addObject("App::VRMLObject", label)
                vrml_obj.VrmlFile = file_path
                vrml_obj.Label = label
                App.ActiveDocument.recompute()
                print(f"Imported {file_path} as VRML/WRL")
                return vrml_obj

            else:
                print(f"Unsupported file type: {file_type}")
                print("Supported types: step, stp, stl, iges, igs, obj, brep, wrl, vrml")
                return None

        except Exception as e:
            print(f"Error importing file: {str(e)}")
            return None

    @staticmethod
    def _get_recently_added_objects(base_label):
        """
        Helper method to get recently added objects after import.
        Some import formats (like STEP, IGES) may add multiple objects.

        Args:
            base_label: Base label to look for in recently added objects

        Returns:
            List of imported objects or the single object if only one was added
        """
        # This is a simple implementation that returns all objects
        # In a more sophisticated version, you could track objects before/after import
        all_objects = App.ActiveDocument.Objects

        # Try to find objects that match the base label or were recently added
        # For now, just return the last added object
        if all_objects:
            return all_objects[-1]
        return None

    @staticmethod
    def import_as_body(file_path, label=None, file_type=None):
        """
        Import 3D geometry and convert it to a PartDesign::Body if possible.
        This is useful for integrating imported geometry with the PartDesign workflow.
        Idempotent: if the Body and geometry already exist, returns the existing Body.

        Args:
            file_path: The full path to the file to import
            label: Optional label for the Body object (will have '_imported' suffix)
                  If not specified, will use the filename without extension
            file_type: Optional file type ('step', 'stl', 'iges', 'obj', 'brep', etc.)
                      If not specified, it will be inferred from file_path extension

        Returns:
            The Body object containing the imported geometry, or None if import failed
        """
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None

        # Generate label from filename if not specified
        if label is None:
            filename = os.path.basename(file_path)
            label, _ = os.path.splitext(filename)

        # Determine file type from extension if not specified
        if file_type is None:
            _, ext = os.path.splitext(file_path)
            file_type = ext.lstrip(".").lower()
        else:
            file_type = file_type.lower()

        # Determine expected child type based on file type
        if file_type in ["stl", "obj"]:
            expected_type = "Mesh::Feature"
        elif file_type == "brep":
            expected_type = "Part::Feature"
        elif file_type in ["step", "stp", "iges", "igs"]:
            # STEP/IGES can create various Part types, we'll be flexible
            expected_type = "Part::"  # Prefix match
        elif file_type in ["wrl", "vrml"]:
            expected_type = "App::VRMLObject"
        else:
            print(f"Unsupported file type: {file_type}")
            return None

        body_label = label + "_imported"
        geometry_label = label + "_geometry"

        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(body_label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode
        if Shape._teardown_if_needed(body_label, created_children=[geometry_label]):
            return None

        # Check for existing Body and geometry
        existing_body = Context.get_object(body_label)
        existing_geometry = Context.get_object(geometry_label)

        if existing_body is not None and existing_geometry is not None:
            # Check if existing_body is actually a Body
            if existing_body.TypeId == "PartDesign::Body":
                # Check if the geometry type matches expectations
                type_matches = existing_geometry.TypeId == expected_type or (
                    expected_type.endswith("::") and existing_geometry.TypeId.startswith(expected_type)
                )

                if type_matches:
                    # Verify the geometry is a child of the body
                    if hasattr(existing_body, "Group") and existing_geometry in existing_body.Group:
                        print(f'Body "{body_label}" with geometry already exists, returning existing object')
                        return existing_body
                    # Geometry exists but not in body, add it
                    elif hasattr(existing_geometry, "Shape"):
                        existing_body.addObject(existing_geometry)
                        App.ActiveDocument.recompute()
                        print(f'Added existing geometry to Body "{body_label}"')
                        return existing_body

        # If we get here, we need to import the geometry
        # First, import or get the geometry object
        imported_obj = ImportGeometry.import_geometry(file_path, geometry_label, file_type)

        if imported_obj is None:
            return None

        try:
            # For mesh objects (STL, OBJ) and VRML objects, we can't add to Body
            if not (hasattr(imported_obj, "Shape") and imported_obj.TypeId.startswith("Part::")):
                print(f'Imported object type "{imported_obj.TypeId}" cannot be added to Body, returning as-is')
                # If we created a body earlier, remove it
                if existing_body is not None:
                    Shape._move_to_trash_bin(existing_body)
                return imported_obj

            # Create or reuse Body
            if existing_body is not None and existing_body.TypeId == "PartDesign::Body":
                body = existing_body
            else:
                # Remove existing object if it's not a Body
                if existing_body is not None:
                    Shape._move_to_trash_bin(existing_body)
                # Create new Body
                body = Shape._create_object(body_label)

            # Add the imported object to the body if not already added
            if hasattr(body, "Group") and imported_obj not in body.Group:
                body.addObject(imported_obj)

            App.ActiveDocument.recompute()
            print(f'Created Body "{body_label}" with imported geometry')
            return body

        except Exception as e:
            print(f"Error creating Body from imported geometry: {str(e)}")
            return imported_obj
