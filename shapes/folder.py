import FreeCAD as App

from .shape import Shape
from .context import Context

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.folder;
# reload(shapes.folder); from shapes.folder import Folder
# Folder.create_folder('my_folder')
# Folder.add_to_folder('my_folder', 'object_label')

class Folder(Shape):
    @staticmethod
    def create_folder(label):
        """
        Create a DocumentObjectGroup (folder) in the active document.

        Args:
            label: The label for the folder

        Returns:
            The folder object, or None if in teardown mode
        """
        # Handle teardown mode
        if Shape._teardown_if_needed(label):
            return None

        # Check if folder already exists
        existing_folder = Context.get_object(label)

        if existing_folder is not None:
            # Check if it's already a folder
            if existing_folder.TypeId == 'App::DocumentObjectGroup':
                return existing_folder
            else:
                # Not a folder, move to trash and create new
                Shape._move_to_trash_bin(existing_folder)

        # Create new folder
        App.ActiveDocument.addObject('App::DocumentObjectGroup', label)
        folder = Context.get_object(label)

        return folder

    @staticmethod
    def add_to_folder(folder_label, obj_or_label_or_list):
        """
        Add one or more objects to a folder.

        Args:
            folder_label: The label of the folder to add the object(s) to
            obj_or_label_or_list: The object, label, or list of objects/labels to add

        Returns:
            True if all operations successful, False if any failed
        """
        # Handle list of objects
        if isinstance(obj_or_label_or_list, list):
            all_successful = True
            for item in obj_or_label_or_list:
                if not Folder.add_to_folder(folder_label, item):
                    all_successful = False
            return all_successful

        # Handle single object
        folder = Context.get_object(folder_label)
        if folder is None:
            print(f'Folder not found: {folder_label}')
            return False

        if folder.TypeId != 'App::DocumentObjectGroup':
            print(f'Object is not a folder: {folder_label} (Type: {folder.TypeId})')
            return False

        obj = Context.get_object(obj_or_label_or_list)
        if obj is None:
            print(f'Object not found: {obj_or_label_or_list}')
            return False

        # Get the root parent if it exists, otherwise use the object itself
        root_parent = Context.get_root_parent(obj)
        obj_to_add = root_parent if root_parent is not None else obj

        # Check if object is already in the folder
        if obj_to_add in folder.Group:
            print(f'Object "{obj_to_add.Label}" is already in folder "{folder_label}"')
            return True

        # Add object to folder
        folder.addObject(obj_to_add)
        print(f'Added "{obj_to_add.Label}" to folder "{folder_label}"')

        return True
