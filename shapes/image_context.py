import FreeCAD as App
import FreeCADGui as Gui
import os
from enum import Enum

from .context import Context

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.image_context

# reload(shapes.image_context); from shapes.image_context import Perspective, ImageContext;
# ImageContext.capture("top_shell.png", target="top_shell")


class Perspective(Enum):
    """Predefined camera perspectives for screenshots."""
    FRONT = "front"
    BACK = "back"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    ISOMETRIC = "isometric"


class ImageContext:
    """
    Simplified screenshot API for FreeCAD 3D views.

    Main method:
        capture(path, target=None, perspective="isometric")

    Examples:
        # Capture entire scene from isometric view
        ImageContext.capture("output.png")

        # Capture from front view
        ImageContext.capture("front.png", perspective="front")

        # Capture specific object
        ImageContext.capture("box.png", target="MyBox")

        # Capture with multiple perspectives
        ImageContext.capture("model.png", perspectives=["front", "top", "isometric"])
    """

    @staticmethod
    def _get_view():
        """Get the active 3D view."""
        try:
            return Gui.ActiveDocument.ActiveView
        except AttributeError:
            print("Error: No active document or view available")
            return None

    @staticmethod
    def _apply_perspective(view, perspective_str):
        """Apply a perspective to the view."""
        p = perspective_str.lower()

        if p == "front":
            view.viewFront()
        elif p == "back":
            view.viewRear()
        elif p == "top":
            view.viewTop()
        elif p == "bottom":
            view.viewBottom()
        elif p == "left":
            view.viewLeft()
        elif p == "right":
            view.viewRight()
        elif p == "isometric":
            view.viewIsometric()
        else:
            print(f"Unknown perspective '{perspective_str}'. Using current view.")
            print("Available: front, back, top, bottom, left, right, isometric")

    @staticmethod
    def capture(path, target=None, perspective="isometric", perspectives=None):
        """
        Capture a screenshot of the 3D view.

        Args:
            path: File path to save screenshot (e.g., "output.png")
                 For multiple perspectives, use "{}" placeholder (e.g., "model_{}.png")
            target: Optional object name/label to focus on. If None, captures entire scene
            perspective: View angle - "front", "back", "top", "bottom", "left", "right", "isometric"
                        Default: "isometric"
            perspectives: Optional list of perspectives for multiple captures
                         If provided, ignores 'perspective' parameter
                         Example: ["front", "top", "isometric"]

        Returns:
            str or dict: File path if single capture, dict of {perspective: path} if multiple

        Examples:
            ImageContext.capture("box.png")
            ImageContext.capture("box.png", target="MyBox", perspective="front")
            ImageContext.capture("model_{}.png", perspectives=["front", "top"])
        """
        view = ImageContext._get_view()
        if view is None:
            return None

        # Handle multiple perspectives
        if perspectives is not None:
            results = {}
            for persp in perspectives:
                # Generate path for this perspective
                if '{}' in path:
                    file_path = path.format(persp)
                else:
                    base, ext = os.path.splitext(path)
                    file_path = f"{base}_{persp}{ext}"

                # Capture single perspective
                result = ImageContext.capture(file_path, target=target, perspective=persp)
                if result:
                    results[persp] = result

            return results

        # Single capture
        # Set perspective
        ImageContext._apply_perspective(view, perspective)

        # Focus on target object if specified
        if target is not None:
            obj = Context.get_object(target)
            if obj is None:
                print(f'Object not found: {target}')
                return None

            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(obj)
            view.fitAll()
        else:
            view.fitAll()

        # Ensure directory exists
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Save screenshot
        try:
            view.saveImage(path, 1920, 1080, 'Current')
            msg = f'Screenshot saved: {path}'
            if target:
                msg += f' (object: {target})'
            print(msg)

            # Clear selection if we selected an object
            if target is not None:
                Gui.Selection.clearSelection()

            return path
        except Exception as e:
            print(f'Error: {str(e)}')
            if target is not None:
                Gui.Selection.clearSelection()
            return None

    @staticmethod
    def set_view(perspective="isometric"):
        """
        Set the camera view without taking a screenshot.

        Args:
            perspective: View angle - "front", "back", "top", "bottom", "left", "right", "isometric"
        """
        view = ImageContext._get_view()
        if view is None:
            return

        ImageContext._apply_perspective(view, perspective)
        view.fitAll()

    @staticmethod
    def fit():
        """Fit all objects in the current view."""
        view = ImageContext._get_view()
        if view is not None:
            view.fitAll()
