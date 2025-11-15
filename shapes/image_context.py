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
    Screenshot API for FreeCAD 3D views.

    Auto-saves screenshots to configured images folder with timestamp.
    Naming: {target}_{perspective}_{timestamp}.png
    Example: MyBox_front_20240115_143022.png

    Designed for providing vision feedback to LLM - captures and returns
    images that the LLM can see and analyze.

    Usage:
        # Create instance with images directory
        image_ctx = ImageContext(images_dir="/path/to/history/images")

        # Capture screenshots
        image_ctx.capture()  # -> scene_isometric_20240115_143022.png
        image_ctx.capture(target="MyBox")  # -> MyBox_isometric_20240115_143022.png
        image_ctx.capture(perspective="front")  # -> scene_front_20240115_143022.png
        image_ctx.capture(target="MyBox", perspective="top")  # -> MyBox_top_20240115_143022.png
    """

    def __init__(self, images_dir):
        """
        Initialize ImageContext with images directory.

        Args:
            images_dir: Path to the directory where screenshots will be saved
        """
        self.images_dir = images_dir

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

    def capture(self, path=None, target=None, perspective="isometric", perspectives=None):
        """
        Capture a screenshot of the 3D view.

        Args:
            path: Optional file path to save screenshot. If None, auto-generates with timestamp
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
            image_ctx.capture()  # Auto-generates path with timestamp
            image_ctx.capture(target="MyBox", perspective="front")
            image_ctx.capture(perspectives=["front", "top"])
        """
        from datetime import datetime

        view = ImageContext._get_view()
        if view is None:
            return None

        # Auto-generate path if not provided
        if path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # Include milliseconds

            # Generate filename: target_perspective_timestamp
            if target:
                filename = f"{target}_{perspective}_{timestamp}.png"
            else:
                filename = f"scene_{perspective}_{timestamp}.png"

            path = os.path.join(self.images_dir, filename)

        # Handle multiple perspectives
        if perspectives is not None:
            results = {}
            for persp in perspectives:
                # Generate path for this perspective
                if path and '{}' in path:
                    file_path = path.format(persp)
                else:
                    # Auto-generate individual paths: target_perspective_timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]

                    if target:
                        filename = f"{target}_{persp}_{timestamp}.png"
                    else:
                        filename = f"scene_{persp}_{timestamp}.png"

                    file_path = os.path.join(self.images_dir, filename)

                # Capture single perspective
                result = self.capture(file_path, target=target, perspective=persp)
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
