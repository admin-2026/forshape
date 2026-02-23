"""
Version 1 of the shapes API.

This module exports the v1 API for backward compatibility.
Users can import specific versions and mix them in scripts:

    from shapes.v1 import AdditiveBox as AdditiveBoxV1
    from shapes import AdditiveBox  # Latest version
"""

from ..additive_box import AdditiveBox
from ..additive_cone import AdditiveCone
from ..additive_cylinder import AdditiveCylinder
from ..additive_ellipsoid import AdditiveEllipsoid
from ..additive_prism import AdditivePrism
from ..additive_sphere import AdditiveSphere
from ..additive_torus import AdditiveTorus
from ..additive_wedge import AdditiveWedge
from ..appearance import Appearance
from ..boolean import Boolean
from ..clone import Clone
from ..context import Context
from ..copy import Copy
from ..edge_feature import EdgeFeature
from ..export import Export
from ..folder import Folder
from ..helix import Helix
from ..image_context import ImageContext, Perspective
from ..import_geometry import ImportGeometry
from ..loft import Loft
from ..pad import Pad
from ..pipe import Pipe
from ..revolution import Revolution
from ..shape import Shape
from ..transform import Transform

__all__ = [
    "Appearance",
    "Shape",
    "AdditiveBox",
    "AdditiveCone",
    "AdditiveCylinder",
    "AdditiveEllipsoid",
    "AdditivePrism",
    "AdditiveSphere",
    "AdditiveTorus",
    "AdditiveWedge",
    "Helix",
    "Loft",
    "Pad",
    "Pipe",
    "Revolution",
    "EdgeFeature",
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

__version__ = "1.5.0"
