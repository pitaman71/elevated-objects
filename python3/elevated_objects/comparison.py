#!/usr/bin/env python3

from __future__ import annotations
import typing
import enum
import sys

from code_instruments.task import function, method, Tally
from . import construction
from . import serializable
from . import traversal

PropType = typing.TypeVar('PropType', bound=serializable.Serializable)

#logger=lambda x: sys.stdout.write(x+"\n")
logger=None

class Result(enum.Enum):
    Unknown = None
    Less = -1
    Equal = 0
    Greater = 1

class DefaultComparator(traversal.Visitor):
    a: serializable.Serializable
    b: serializable.Serializable    
    result: Result
    
    def __init__(self, a: serializable.Serializable, b: serializable.Serializable):
        self.a = a
        self.b = b
        self.result = Result.Unknown

    @method(logger=logger)
    def begin(self, obj: serializable.ExpectedType, parent_prop_name: str = None) -> Result:
        self.result = Result.Equal
        return self.result

    @method(logger=logger)
    def end(self, obj: serializable.ExpectedType) -> Result:
        return self.result

    @method(logger=logger)
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

    @method(logger=logger)
    def primitive(self, data_type: typing.Type, target: serializable.Serializable, prop_name: str, fromString: typing.Callable[ [str], PropType ] = None) -> Result:
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

    @method(logger=logger)
    def compare_elements(self, a_prop: serializable.Serializable, b_prop: serializable.Serializable):
        if a_prop.get_global_id() is None and b_prop.get_global_id() is None:
            sub = DefaultComparator(a_prop, b_prop)
            a_prop.marshal(sub)
            if sub.result != Result.Equal:
                self.result = sub.result
        elif a_prop.get_global_id() < b_prop.get_global_id():
            self.result = Result.Less
        elif a_prop.get_global_id() > b_prop.get_global_id():
            self.result = Result.Greater

    @method(logger=logger)
    def scalar(self, element_builder: construction.Factory, target: serializable.Serializable, prop_name: str) -> Result:
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
        else:
            self.compare_elements(a_prop, b_prop)
        if self.result == Result.Unknown:
            self.result = Result.Equal
        return self.result

    @method(logger=logger)
    def array(self, element_builder: construction.Factory, target: serializable.Serializable, prop_name: str) -> Result:
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
        a_len = len(getattr(self.a, prop_name))
        b_len = len(getattr(self.b, prop_name))
        if a_len < b_len:
            self.result = Result.Less
        if a_len > b_len:
            self.result = Result.Greater
        for index in range(0, a_len):
            if self.result == Result.Unknown:
                self.compare_elements(getattr(self.a, prop_name)[index], getattr(self.b, prop_name)[index])
        if self.result == Result.Unknown:
            self.result = Result.Equal
        return self.result

    @method(logger=logger)
    def map(self, key_type: typing.Type, element_builder: construction.Factory, target: serializable.Serializable, prop_name: str) -> Result:
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
        a_keys = set([ key for key in a_prop.keys() ])
        b_keys = set([ key for key in b_prop.keys() ])
        if a_keys < b_keys:
            self.result = Result.Less
        elif a_keys > b_keys:
            self.result = Result.Greater
        for key in a_keys:
            if self.result == Result.Unknown:
                self.compare_elements(getattr(self.a, prop_name)[key], getattr(self.b, prop_name)[key])
        if self.result == Result.Unknown:
            self.result = Result.Equal
            
        return self.result

@function(logger=logger)
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
