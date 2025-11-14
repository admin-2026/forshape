
import FreeCAD as App
import re

# from shapes.context import Context
# from importlib import reload
# reload(context)
# Context.print_object('b3')
# Context.print_document()
# Context.remove_object('b3')

class Context:
    _epsilon = 0.01  # Default epsilon for fillet operations (mm)

    @classmethod
    def get_epsilon(cls):
        """
        Get the epsilon value used for fillet operations.
        FreeCAD cannot create fillets that touch each other, so epsilon is subtracted
        to prevent adjacent fillets from overlapping.

        Returns:
            float: The current epsilon value in mm
        """
        return cls._epsilon

    @classmethod
    def set_epsilon(cls, value):
        """
        Set the epsilon value used for fillet operations.

        Args:
            value (float): The epsilon value in mm (must be positive)
        """
        if value <= 0:
            raise ValueError("Epsilon must be a positive value")
        cls._epsilon = value

    @staticmethod
    def print_object(obj_or_label, indent=0, verbose=False):
        obj = Context.get_object(obj_or_label)
        prefix = '  ' * indent
        type_id = obj.TypeId
        if type_id == 'Sketcher::SketchObject':
            if verbose:
                print(f'{prefix}{obj.Label}')
                print(f'{prefix}  Type: SketchObject')
            return
        if type_id == 'PartDesign::Pad':
            if verbose:
                print(f'{prefix}{obj.Label}')
                print(f'{prefix}  Type: Pad')
            return
        if type_id == 'PartDesign::Boolean':
            if verbose:
                print(f'{prefix}{obj.Label}')
                # obj.Type returns the operation name as a string
                operation = obj.Type if hasattr(obj, 'Type') else 'Unknown'
                print(f'{prefix}  Type: Boolean')
                print(f'{prefix}  Operation: {operation}')
                # Print secondary operands recursively
                if hasattr(obj, 'Group') and obj.Group:
                    print(f'{prefix}  Operands:')
                    for operand in obj.Group:
                        Context.print_object(operand, indent + 2, verbose)
            return
        if type_id == 'PartDesign::AdditiveBox':
            if verbose:
                print(f'{prefix}{obj.Label}')
                print(f'{prefix}  Type: AdditiveBox')
                print(f'{prefix}  Dimensions: Length={obj.Length}, Width={obj.Width}, Height={obj.Height}')
                attachment = [item[0].Label for item in obj.AttachmentSupport] if obj.AttachmentSupport else None
                print(f'{prefix}  Attachment: {attachment}')
                print(f'{prefix}  Attachment Offset: {obj.AttachmentOffset}')
            return
        if type_id == 'PartDesign::AdditiveCylinder':
            if verbose:
                print(f'{prefix}{obj.Label}')
                print(f'{prefix}  Type: AdditiveCylinder')
                print(f'{prefix}  Dimensions: Radius={obj.Radius}, Height={obj.Height}')
                attachment = [item[0].Label for item in obj.AttachmentSupport] if obj.AttachmentSupport else None
                print(f'{prefix}  Attachment: {attachment}')
                print(f'{prefix}  Attachment Offset: {obj.AttachmentOffset}')
            return
        if type_id == 'PartDesign::Body':
            print(f'{prefix}{obj.Label}')
            print(f'{prefix}  Type: Body')
            if verbose:
                for child in obj.Group:
                    Context.print_object(child, indent + 1, verbose)
            return
        if type_id == 'App::DocumentObjectGroup':
            print(f'{prefix}{obj.Label}')
            print(f'{prefix}  Type: DocumentObjectGroup')
            for child in obj.Group:
                Context.print_object(child, indent + 1, verbose)
            return
        if type_id == 'App::Document':
            print(f'{prefix}{obj.Label}')
            print(f'{prefix}  Type: Document')
            for child in obj.Objects:
                # only print top level object
                if child.getParent() is None:
                    Context.print_object(child, indent + 1, verbose)
            return
        if verbose:
            print(f'{prefix}  Unsupported object type: {type_id}')

    @staticmethod
    def get_object(obj_or_label):
        # If already an object, return it directly
        if not isinstance(obj_or_label, str):
            return obj_or_label
        # Otherwise, treat as label and retrieve object
        # Try to get by internal name first
        obj = App.ActiveDocument.getObject(obj_or_label)
        if obj is not None:
            return obj
        # If not found, try to get by label
        objects = App.ActiveDocument.getObjectsByLabel(obj_or_label)
        if objects:
            return objects[0]
        return None

    @staticmethod
    def find_objects_by_regex(pattern):
        """
        Scans all objects in the active document to find objects whose label, name, or label2 matches the regex pattern.

        Args:
            pattern: A regex pattern string to match against object attributes

        Returns:
            A list of tuples (matched_string, field_name) where:
            - matched_string: The actual string value that matched the pattern
            - field_name: The name of the field that matched ('Label', 'Name', or 'Label2')
        """
        regex = re.compile(pattern)
        matches = []

        for obj in App.ActiveDocument.Objects:
            # Check Label
            if hasattr(obj, 'Label') and regex.search(obj.Label):
                matches.append((obj.Label, 'Label'))

            # Check Name (internal name)
            if hasattr(obj, 'Name') and regex.search(obj.Name):
                matches.append((obj.Name, 'Name'))

            # Check Label2 (if it exists)
            if hasattr(obj, 'Label2') and obj.Label2 and regex.search(obj.Label2):
                matches.append((obj.Label2, 'Label2'))

        return matches

    @staticmethod
    def print_document(verbose=False):
        Context.print_object(App.ActiveDocument, verbose=verbose)

    @staticmethod
    def remove_object(obj_or_label):
        obj = Context.get_object(obj_or_label)
        if obj is None:
            print(f'object not found')
            return
        type_id = obj.TypeId
        print(f'Removing object: {obj.Label} (Type: {type_id})')
        if type_id == 'Sketcher::SketchObject':
            App.ActiveDocument.removeObject(obj.Name)
            App.ActiveDocument.recompute()
            return
        if type_id == 'PartDesign::Pad':
            parent = obj.getParent()
            parent.removeObject(obj)
            App.ActiveDocument.removeObject(obj.Name)
            App.ActiveDocument.recompute()
            return
        if type_id == 'PartDesign::Boolean':
            parent = obj.getParent()
            parent.removeObject(obj)
            App.ActiveDocument.removeObject(obj.Name)
            App.ActiveDocument.recompute()
            return
        if type_id == 'PartDesign::Body':
            obj.removeObjectsFromDocument()
            App.ActiveDocument.removeObject(obj.Name)
            App.ActiveDocument.recompute()
            return
        if type_id == 'App::Document':
            print('cannot remove document')
            return
        print(f'Unsupported object type: {type_id}')

    @staticmethod
    def rename_object(obj_or_label, new_label):
        """
        Rename an object by changing its Label property.

        Args:
            obj_or_label: The object or label/name to identify the object to rename
            new_label: The new label for the object

        Returns:
            None
        """
        obj = Context.get_object(obj_or_label)
        if obj is None:
            print(f'object not found: {obj_or_label}')
            return
        if obj.TypeId == 'App::Document':
            print('cannot rename document')
            return
        old_label = obj.Label
        obj.Label = new_label
        App.ActiveDocument.recompute()
        print(f'Renamed object: "{old_label}" -> "{new_label}"')
