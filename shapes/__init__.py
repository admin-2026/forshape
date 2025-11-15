"""
FreeCAD shape generation and manipulation.

This package contains classes and utilities for creating and manipulating
3D shapes using FreeCAD.
"""

from .shape import Shape
from .additive_box import AdditiveBox
from .additive_cylinder import AdditiveCylinder
from .pad import Pad
from .context import Context
from .boolean import Boolean
from .transform import Transform
from .export import Export

__all__ = [
    'Shape',
    'AdditiveBox',
    'AdditiveCylinder',
    'Pad',
    'Context',
    'Boolean',
    'Transform',
    'Export',
]
