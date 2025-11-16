"""
Drawable image label widget for annotating images.
"""

from PySide2.QtWidgets import QLabel
from PySide2.QtCore import Qt, QPoint
from PySide2.QtGui import QColor, QPixmap, QPainter, QPen


class DrawableImageLabel(QLabel):
    """A QLabel that allows drawing on the displayed image."""

    def __init__(self, parent=None):
        """Initialize the drawable image label."""
        super().__init__(parent)
        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = QColor(255, 0, 0)  # Red by default
        self.pen_width = 3
        self.image = None
        self.drawing_layer = None
        self.setMouseTracking(False)

    def set_image(self, pixmap):
        """Set the image to display and create a drawing layer."""
        self.image = pixmap.copy()
        self.drawing_layer = QPixmap(pixmap.size())
        self.drawing_layer.fill(Qt.transparent)
        self.update_display()

    def update_display(self):
        """Update the display by compositing the image and drawing layer."""
        if self.image is None:
            return

        # Composite the original image with the drawing layer
        result = self.image.copy()
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self.drawing_layer)
        painter.end()

        self.setPixmap(result)

    def set_pen_color(self, color):
        """Set the pen color for drawing."""
        self.pen_color = color

    def set_pen_width(self, width):
        """Set the pen width for drawing."""
        self.pen_width = width

    def clear_drawings(self):
        """Clear all drawings."""
        if self.drawing_layer:
            self.drawing_layer.fill(Qt.transparent)
            self.update_display()

    def get_annotated_image(self):
        """Get the final image with annotations."""
        if self.image is None:
            return None

        result = self.image.copy()
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self.drawing_layer)
        painter.end()
        return result

    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton and self.drawing_layer:
            self.drawing = True
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move event - draw on the image."""
        if self.drawing and event.buttons() & Qt.LeftButton and self.drawing_layer:
            painter = QPainter(self.drawing_layer)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            painter.end()

            self.last_point = event.pos()
            self.update_display()

    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.LeftButton:
            self.drawing = False
