
import FreeCAD as App

# from importlib import reload
# reload(context)
# context.Context.print_object('b3')
# context.Context.remove_object('b3')

class Context:
    @staticmethod
    def print_object(obj_or_label, indent=0, verbose=False):
        obj = Context.get_object(obj_or_label)
        prefix = '  ' * indent
        print(f'{prefix}{obj.Label}')
        type_id = obj.TypeId
        if type_id == 'Sketcher::SketchObject':
            if verbose:
                print(f'{prefix}  Type: SketchObject')
            return
        if type_id == 'PartDesign::Pad':
            if verbose:
                print(f'{prefix}  Type: Pad')
            return
        if type_id == 'PartDesign::Boolean':
            if verbose:
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
                print(f'{prefix}  Type: AdditiveBox')
                print(f'{prefix}  Dimensions: Length={obj.Length}, Width={obj.Width}, Height={obj.Height}')
                attachment = [item[0].Label for item in obj.AttachmentSupport] if obj.AttachmentSupport else None
                print(f'{prefix}  Attachment: {attachment}')
                print(f'{prefix}  Attachment Offset: {obj.AttachmentOffset}')
            return
        if type_id == 'PartDesign::AdditiveCylinder':
            if verbose:
                print(f'{prefix}  Type: AdditiveCylinder')
                print(f'{prefix}  Dimensions: Radius={obj.Radius}, Height={obj.Height}')
                attachment = [item[0].Label for item in obj.AttachmentSupport] if obj.AttachmentSupport else None
                print(f'{prefix}  Attachment: {attachment}')
                print(f'{prefix}  Attachment Offset: {obj.AttachmentOffset}')
            return
        if type_id == 'PartDesign::Body':
            if verbose:
                print(f'{prefix}  Type: Body')
                for child in obj.Group:
                    Context.print_object(child, indent + 1, verbose)
            return
        if type_id == 'App::DocumentObjectGroup':
            if verbose:
                print(f'{prefix}  Type: DocumentObjectGroup')
            for child in obj.Group:
                Context.print_object(child, indent + 1, verbose)
            return
        if type_id == 'App::Document':
            if verbose:
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
        if obj_or_label == App.ActiveDocument.Label:
            return App.ActiveDocument
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
            App.ActiveDocument.removeObject(obj.Label)
            App.ActiveDocument.recompute()
            return
        if type_id == 'PartDesign::Pad':
            parent = obj.getParent()
            parent.removeObject(obj)
            App.ActiveDocument.removeObject(obj.Label)
            App.ActiveDocument.recompute()
            return
        if type_id == 'PartDesign::Boolean':
            parent = obj.getParent()
            parent.removeObject(obj)
            App.ActiveDocument.removeObject(obj.Label)
            App.ActiveDocument.recompute()
            return
        if type_id == 'PartDesign::Body':
            obj.removeObjectsFromDocument()
            App.ActiveDocument.removeObject(obj.Label)
            App.ActiveDocument.recompute()
            return
        if type_id == 'App::Document':
            print('cannot remove document')
            return
        print(f'Unsupported object type: {type_id}')