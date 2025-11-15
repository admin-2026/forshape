"""
FreeCAD shape generation and manipulation.

This package contains classes and utilities for creating and manipulating
3D shapes using FreeCAD.
"""

from .shape import Shape
from .additive_box import AdditiveBox
from .additive_cylinder import AdditiveCylinder
from .additive_prism import AdditivePrism
from .pad import Pad
from .edge_feature import EdgeFeature
from .context import Context
from .boolean import Boolean
from .transform import Transform
from .export import Export

__all__ = [
    'Shape',
    'AdditiveBox',
    'AdditiveCylinder',
    'AdditivePrism',
    'Pad',
    'EdgeFeature',
    'Context',
    'Boolean',
    'Transform',
    'Export',
]
