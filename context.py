
import FreeCAD as App

# from importlib import reload
# reload(context)
# context.Context.print_object('b3')
# context.Context.remove_object('b3')

class Context:
    @staticmethod
    def print_object(obj_or_label):
        obj = Context.get_object(obj_or_label)
        print(obj.Label)
        type_id = obj.TypeId
        if type_id == 'Sketcher::SketchObject':
            return
        if type_id == 'PartDesign::Pad':
            return
        if type_id == 'PartDesign::Boolean':
            return
        if type_id == 'PartDesign::Body':
            for child in obj.Group:
                Context.print_object(child)
            return
        if type_id == 'App::Document':
            for child in obj.Objects:
                # only print Body
                if child.TypeId == 'PartDesign::Body':
                    Context.print_object(child)
            return
        print('Unsupported object type')

    @staticmethod
    def get_object(obj_or_label):
        # If already an object, return it directly
        if not isinstance(obj_or_label, str):
            return obj_or_label
        # Otherwise, treat as label and retrieve object
        if obj_or_label == App.ActiveDocument.Label:
            return App.ActiveDocument
        return App.ActiveDocument.getObject(obj_or_label)


    @staticmethod
    def print_document():
        Context.print_object(App.ActiveDocument)

    @staticmethod
    def remove_object(obj_or_label):
        obj = Context.get_object(obj_or_label)
        if obj is None:
            print(f'object not found')
            return
        type_id = obj.TypeId
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
        print('Unsupported object type')