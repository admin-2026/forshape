"""
FreeCAD shape generation and manipulation.

This package contains classes and utilities for creating and manipulating
3D shapes using FreeCAD.

Versioning:
    The shapes package supports versioning. Import from specific versions:

        from shapes.v1 import AdditiveBox as BoxV1
        from shapes import AdditiveBox  # Latest version

    You can mix different versions in the same script:

        from shapes.v1 import AdditiveBox as BoxV1
        from shapes.v2 import AdditiveBox as BoxV2  # When v2 exists
"""

from .additive_box import AdditiveBox
from .additive_cone import AdditiveCone
from .additive_cylinder import AdditiveCylinder
from .additive_ellipsoid import AdditiveEllipsoid
from .additive_prism import AdditivePrism
from .additive_sphere import AdditiveSphere
from .additive_torus import AdditiveTorus
from .boolean import Boolean
from .clone import Clone
from .context import Context
from .copy import Copy
from .edge_feature import EdgeFeature
from .exceptions import ShapeException
from .export import Export
from .folder import Folder
from .image_context import ImageContext, Perspective
from .import_geometry import ImportGeometry
from .pad import Pad
from .shape import Shape
from .transform import Transform

__all__ = [
    "Shape",
    "AdditiveBox",
    "AdditiveCone",
    "AdditiveCylinder",
    "AdditiveEllipsoid",
    "AdditivePrism",
    "AdditiveSphere",
    "AdditiveTorus",
    "Pad",
    "EdgeFeature",
    "ShapeException",
    "Context",
    "Boolean",
    "Transform",
    "Export",
    "ImportGeometry",
    "ImageContext",
    "Perspective",
    "Folder",
    "Clone",
    "Copy",
]

__version__ = "1.0.0"
