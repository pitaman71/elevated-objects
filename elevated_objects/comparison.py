#!/usr/bin/env python3

from __future__ import annotations
import typing
import enum

from parts_bin.task import function_task
from . import construction
from . import serializable
from . import visitor

class Result(enum.Enum):
    Unknown = None
    Less = -1
    Equal = 0
    Greater = 1

class DefaultComparator(visitor.Visitor):
    a: serializable.Serializable
    b: serializable.Serializable    
    result: Result
    
    def __init__(self, a: serializable.Serializable, b: serializable.Serializable):
        self.a = a
        self.b = b
        self.result = Result.Unknown

    @function_task()
    def begin(self, obj: serializable.ExpectedType, parent_prop_name: str = None) -> Result:
        self.result = Result.Equal
        return self.result

    @function_task()
    def end(self, obj: serializable.ExpectedType) -> Result:
        return self.result

    @function_task()
    def verbatim(self, 
        data_type: typing.Type, 
        target: serializable.Serializable, 
        get_value: typing.Callable [ [serializable.Serializable], typing.Any ],
        set_value: typing.Callable [ [serializable.Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ) -> Result:
        if self.result != Result.Equal:
            return self.result
        a_prop = get_value(self.a)
        b_prop = get_value(self.b)
        if not a_prop is None and b_prop is None:
            self.result = Result.Less
        elif a_prop is None and not b_prop is None:
            self.result = Result.Greater
        elif a_prop is None and b_prop is None:
            pass
        elif a_prop < b_prop:
            self.result = Result.Less
        elif a_prop > b_prop:
            self.result = Result.Greater
        return self.result

    @function_task()
    def primitive(self, data_type: typing.Type, target: serializable.Serializable, prop_name: str, fromString: typing.Callable[ [str], serializable.PropType ] = None) -> Result:
        if self.result != Result.Equal:
            return self.result
        a_has_prop = hasattr(self.a, prop_name)
        b_has_prop = hasattr(self.b, prop_name)
        if not a_has_prop and not b_has_prop:
            return self.result
        if not a_has_prop and b_has_prop:
            self.result = Result.Less
        if a_has_prop and not b_has_prop:
            self.result = Result.Greater
        a_prop = getattr(self.a, prop_name)
        b_prop = getattr(self.b, prop_name)
        if not a_prop is None and b_prop is None:
            self.result = Result.Less
        elif a_prop is None and not b_prop is None:
            self.result = Result.Greater
        elif a_prop is None and b_prop is None:
            pass
        elif a_prop < b_prop:
            self.result = Result.Less
        elif a_prop > b_prop:
            self.result = Result.Greater
        return self.result

    def scalar(self, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> Result:
        if self.result != Result.Equal:
            return self.result
        a_has_prop = hasattr(self.a, prop_name)
        b_has_prop = hasattr(self.b, prop_name)
        if not a_has_prop and not b_has_prop:
            return self.result
        if not a_has_prop and b_has_prop:
            self.result = Result.Less
        if a_has_prop and not b_has_prop:
            self.result = Result.Greater
        a_prop = getattr(self.a, prop_name)
        b_prop = getattr(self.b, prop_name)
        if not a_prop is None and b_prop is None:
            self.result = Result.Less
        elif a_prop is None and not b_prop is None:
            self.result = Result.Greater
        elif a_prop is None and b_prop is None:
            pass
        elif id(a_prop) < id(b_prop):
            self.result = Result.Less
        elif id(a_prop) > id(b_prop):
            self.result = Result.Greater
        return self.result

    def array(self, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> Result:
        if self.result != Result.Equal:
            return self.result
        a_has_prop = hasattr(self.a, prop_name)
        b_has_prop = hasattr(self.b, prop_name)
        if not a_has_prop and not b_has_prop:
            return self.result
        if not a_has_prop and b_has_prop:
            self.result = Result.Less
        if a_has_prop and not b_has_prop:
            self.result = Result.Greater
        a_prop = [ id(item) for item in getattr(self.a, prop_name) ]
        b_prop = [ id(item) for item in getattr(self.b, prop_name) ]
        if a_prop < b_prop:
            self.result = Result.Less
        elif a_prop > b_prop:
            self.result = Result.Greater
        return self.result

    def map(self, key_type: typing.Type, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> Result:
        if self.result != Result.Equal:
            return self.result
        a_has_prop = hasattr(self.a, prop_name)
        b_has_prop = hasattr(self.b, prop_name)
        if not a_has_prop and not b_has_prop:
            return self.result
        if not a_has_prop and b_has_prop:
            self.result = Result.Less
        if a_has_prop and not b_has_prop:
            self.result = Result.Greater
        a_prop = getattr(self.a, prop_name)
        b_prop = getattr(self.b, prop_name)
        if list(a_prop.keys()) < list(b_prop.keys()):
            self.result = Result.Less
        elif list(a_prop.keys()) > list(b_prop.keys()):
            self.result = Result.Greater
        a_values = [ a_prop[key] for key in a_prop.keys() ]
        b_values = [ b_prop[key] for key in b_prop.keys() ]
        if a_values < b_values:
            self.result = Result.Less
        elif a_values > b_values:
            self.result = Result.Greater
        return self.result

@function_task(logMethod=True)
def cmp(a: serializable.Serializable, b: serializable.Serializable):
    if a.__class__.__qualname__ < b.__class__.__qualname__: return -1
    if a.__class__.__qualname__ > b.__class__.__qualname__: return 1

    if(hasattr(a, '__cmp__')):
        return getattr(a, '__cmp__')(b)

    if a is None and b is not None:
        return -1
    elif a is not None and b is None:
        return 1
    elif a is None and b is None:
        return 0

    comparator = DefaultComparator(a, b)
    a.marshal(comparator)
    if comparator.result == Result.Less:
        return -1
    elif comparator.result == Result.Equal:
        return 0
    elif comparator.result == Result.Greater:
        return 1
    raise RuntimeError('Objects cannot be compared')
