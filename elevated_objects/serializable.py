#!/usr/bin/env python3

from __future__ import annotations
import abc
import typing

class Serializable(abc.ABC):
    @abc.abstractmethod
    def marshal(self, visitor: Visitor) -> None:
        pass

class Cloneable(Serializable):
    @abc.abstractmethod
    def clone(self, *initializers: object) -> Cloneable:
        pass

ExpectedType = typing.TypeVar('ExpectedType', bound=Serializable)
PropType = typing.TypeVar('PropType')

class Visitor(typing.Generic[ExpectedType]): 
    @abc.abstractmethod
    def begin(self, obj: ExpectedType, parent_prop_name: str = None) -> None:
        pass

    @abc.abstractmethod
    def end(self, obj: ExpectedType) -> None:
        pass

    @abc.abstractmethod
    def verbatim(self,
        data_type: typing.Type, 
        target: Serializable, 
        get_value: typing.Callable [ [Serializable], typing.Any ],
        set_value: typing.Callable [ [Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ) -> None:
        pass

    @abc.abstractmethod
    def primitive(self, data_type: typing.Type, target: Serializable, prop_name: str, fromString: typing.Callable[ [str], PropType ] = None) -> None:
        pass

    @abc.abstractmethod
    def scalar(self, element_type: typing.Type, target: Serializable, prop_name: str) -> None:
        pass

    @abc.abstractmethod
    def array(self, element_type: typing.Type, target: Serializable, prop_name: str) -> None:
        pass

    @abc.abstractmethod
    def map(self, key_type: typing.Type, element_type: typing.Type, target: Serializable, prop_name: str) -> None:
        pass

Builder = typing.Callable[ [], Serializable ]

class Property(typing.Generic[PropType]):
    prop_name: str
    value: typing.Union[PropType, None]
    set_value: typing.Callable[ [PropType], None ]

    def object_has_prop(self, other):
        return hasattr(other, self.prop_name)

    def object_get_prop(self, other):
        return getattr(other, self.prop_name)

class Primitive(Property[PropType]):
    data_type: typing.Type
    value: PropType

    def __init__(self, data_type: typing.Type, target, prop_name: str):
        self.prop_name = prop_name
        self.value = getattr(target, prop_name)
        self.target = target

    def set_value(self, value: PropType):
        setattr(self.target, self.prop_name, value)

class Scalar(Property[ExpectedType]):
    element_type: typing.Type
    value: typing.Union[ ExpectedType, None ]

    def __init__(self, element_type: typing.Type, target, prop_name: str):
        self.prop_name = prop_name
        self.value = getattr(target, prop_name)
        self.target = target

    def set_value(self, value: ExpectedType):
        setattr(self.target, self.prop_name, value)

class ArrayProp(Property[ExpectedType]):
    element_type: typing.Type
    value: typing.Union[ ExpectedType, None ]

    def __init__(self, element_type: typing.Type, target, prop_name: str):
        self.prop_name = prop_name
        self.value = getattr(target, prop_name)
        self.target = target

    def set_value(self, value: ExpectedType):
        setattr(self.target, self.prop_name, value)

class MapProp(Property[ExpectedType]):
    element_type: typing.Type
    value: typing.Union[ ExpectedType, None ]

    def __init__(self, element_type: typing.Type, target, prop_name: str):
        self.prop_name = prop_name
        self.value = getattr(target, prop_name)
        self.target = target

    def set_value(self, value: ExpectedType):
        setattr(self.target, self.prop_name, value)

