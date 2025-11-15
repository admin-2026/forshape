import FreeCAD as App

from .shape import Shape
from .context import Context

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.additive_prism;
# from shapes.additive_prism import AdditivePrism
# AdditivePrism.create_prism('hexprism', 'XY_Plane', 6, 5, 10)

class AdditivePrism(Shape):
    @staticmethod
    def create_prism(label, plane_label, polygon, circumradius, height, x_offset=0, y_offset=0, z_offset=0, yaw=0, pitch=0, roll=0):
        """
        Create a prism shape using FreeCAD's PartDesign AdditivePrism feature.

        Args:
            label (str): Name/label for the prism object
            plane_label (str): Plane to attach to (e.g., 'XY_Plane')
            polygon (int): Number of sides for the prism
            circumradius (float): Radius of the circumscribed circle in mm
            height (float): Height of the prism in mm
            x_offset (float, optional): X-axis offset from attachment plane (default: 0)
            y_offset (float, optional): Y-axis offset from attachment plane (default: 0)
            z_offset (float, optional): Z-axis offset from attachment plane (default: 0)
            yaw (float, optional): Rotation around Z-axis in degrees (default: 0)
            pitch (float, optional): Rotation around Y-axis in degrees (default: 0)
            roll (float, optional): Rotation around X-axis in degrees (default: 0)

        Returns:
            The created or updated Body object
        """

        # Check for existing object and get children if they exist
        prism_label = label + '_prism'
        existing_obj, children = Shape._get_or_recreate_body(label, [
            (prism_label, 'PartDesign::AdditivePrism')
        ])

        if existing_obj is not None:
            # AdditivePrism exists, update its properties
            existing_prism = children[prism_label]
            needs_recompute = False

            # Update dimensions
            new_circumradius = f'{circumradius} mm'
            new_height = f'{height} mm'

            if existing_prism.Polygon != polygon:
                existing_prism.Polygon = polygon
                needs_recompute = True
            if str(existing_prism.Circumradius) != new_circumradius:
                existing_prism.Circumradius = new_circumradius
                needs_recompute = True
            if str(existing_prism.Height) != new_height:
                existing_prism.Height = new_height
                needs_recompute = True

            # Update angle properties
            if str(existing_prism.FirstAngle) != '0.00 °':
                existing_prism.FirstAngle = '0.00 °'
                needs_recompute = True
            if str(existing_prism.SecondAngle) != '0.00 °':
                existing_prism.SecondAngle = '0.00 °'
                needs_recompute = True

            # Update attachment, offset, and rotation
            if Shape._update_attachment_and_offset(existing_prism, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll):
                needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        prism_label = label+'_prism'
        App.ActiveDocument.addObject('PartDesign::AdditivePrism', prism_label)
        prism = Context.get_object(prism_label)
        obj.addObject(prism)
        prism.Polygon = polygon
        prism.Circumradius = f'{circumradius} mm'
        prism.Height = f'{height} mm'
        prism.FirstAngle = '0.00 °'
        prism.SecondAngle = '0.00 °'

        Shape._update_attachment_and_offset(prism, plane_label, x_offset, y_offset, z_offset, yaw, pitch, roll)
        App.ActiveDocument.recompute()

        return obj
