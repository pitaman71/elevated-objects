#!/usr/bin/env python3

from __future__ import annotations
import typing
import enum

from parts_bin.task import function_task
from . import serializable

class Result(enum.Enum):
    Unknown = None
    Less = -1
    Equal = 0
    Greater = 1

class DefaultComparator(serializable.Visitor):
    a: serializable.Serializable
    b: serializable.Serializable    
    result: Result
    
    def __init__(self, a: serializable.Serializable, b: serializable.Serializable):
        self.a = a
        self.b = b
        self.result = Result.Unknown

    @function_task(logMethod=True)
    def begin(self, obj: serializable.ExpectedType, parent_prop_name: str = None) -> Result:
        self.result = Result.Equal
        return self.result

    @function_task(logMethod=True)
    def end(self, obj: serializable.ExpectedType) -> Result:
        return self.result

    @function_task(logMethod=True)
    def verbatim(self, data_type: typing.Type, target: serializable.Serializable, prop_name: str) -> Result:
        return self.primitive(data_type, target, prop_name)

    @function_task(logMethod=True)
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

    def scalar(self, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        pass

    def array(self, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        pass

    def map(self, key_type: typing.Type, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        pass

@function_task(logMethod=True)
def cmp(a: serializable.Serializable, b: serializable.Serializable):
    if a.__class__.__qualname__ < b.__class__.__qualname__: return -1
    if a.__class__.__qualname__ > b.__class__.__qualname__: return 1

    if(hasattr(a, '__cmp__')):
        return getattr(a, '__cmp__')(b)

    comparator = DefaultComparator(a, b)
    a.marshal(comparator)
    if comparator.result == Result.Less:
        return -1
    elif comparator.result == Result.Equal:
        return 0
    elif comparator.result == Result.Greater:
        return 1
    raise RuntimeError('Objects cannot be compared')
