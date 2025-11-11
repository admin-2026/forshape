"""
FreeCAD shape generation and manipulation.

This package contains classes and utilities for creating and manipulating
3D shapes using FreeCAD.
"""

from .shape import Shape
from .box import Box
from .cylinder import Cylinder
from .context import Context
from .boolean import Boolean
from .transform import Transform
from .export import Export

__all__ = [
    'Shape',
    'Box',
    'Cylinder',
    'Context',
    'Boolean',
    'Transform',
    'Export',
]
