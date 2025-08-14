#!/usr/bin/env python3

"""
Elevated Objects: A framework for introspectable object types.

This framework provides tools for creating classes that can:
- Accurately initialize themselves
- Marshal themselves to/from JSON and other formats
- Support introspection and traversal
- Enable comparison and validation

The core components are:
- Serializable: Protocol for introspectable objects
- Builder: Pattern for creating and modifying objects
- Registry: Central location for finding builders
- Visitor: Pattern for traversing object structures
"""

from .serializable import Serializable, Visitor
from .builder import Builder
from .registry import Registry

__all__ = [
    'Serializable',
    'Visitor',
    'Builder',
    'Registry'
]