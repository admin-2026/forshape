import FreeCAD as App
import os

from context import Context

class Export:
    @staticmethod
    def export(object_or_label, file_path, file_type=None):
        """
        Export an object to a file.

        Args:
            object_or_label: The object or its label to export
            file_path: The full path where the file should be saved
            file_type: Optional file type ('step', 'stl', 'iges', 'obj', etc.)
                      If not specified, it will be inferred from file_path extension
        """
        obj = Context.get_object(object_or_label)
        if obj is None:
            print(f'Object not found')
            return

        # Determine file type from extension if not specified
        if file_type is None:
            _, ext = os.path.splitext(file_path)
            file_type = ext.lstrip('.').lower()
        else:
            file_type = file_type.lower()

        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        try:
            # Export based on file type
            if file_type in ['step', 'stp']:
                import Import
                Import.export([obj], file_path)
                print(f'Exported {obj.Label} to {file_path} as STEP')

            elif file_type == 'stl':
                import Mesh
                # Create mesh from object shape
                mesh = Mesh.Mesh()
                mesh.addFacets(obj.Shape.tessellate(0.1))
                mesh.write(file_path)
                print(f'Exported {obj.Label} to {file_path} as STL')

            elif file_type in ['iges', 'igs']:
                import Import
                Import.export([obj], file_path)
                print(f'Exported {obj.Label} to {file_path} as IGES')

            elif file_type == 'obj':
                import Mesh
                mesh = Mesh.Mesh()
                mesh.addFacets(obj.Shape.tessellate(0.1))
                mesh.write(file_path, 'OBJ')
                print(f'Exported {obj.Label} to {file_path} as OBJ')

            elif file_type == 'brep':
                obj.Shape.exportBrep(file_path)
                print(f'Exported {obj.Label} to {file_path} as BREP')

            else:
                print(f'Unsupported file type: {file_type}')
                print(f'Supported types: step, stp, stl, iges, igs, obj, brep')
                return

        except Exception as e:
            print(f'Error exporting object: {str(e)}')
            return