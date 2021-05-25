#!/usr/bin/env python3

from __future__ import annotations
import abc
import typing

from . import serializable
from . import construction

ExpectedType = typing.TypeVar('ExpectedType', bound=serializable.Serializable)
PropType = typing.TypeVar('PropType')

class Visitor(serializable.Visitor[ExpectedType]): 
    @abc.abstractmethod
    def begin(self, obj: ExpectedType) -> None:
        pass

    @abc.abstractmethod
    def end(self, obj: ExpectedType) -> None:
        pass

    @abc.abstractmethod
    def owner(self, target: ExpectedType, owner_prop_name: str):
        pass

    @abc.abstractmethod
    def verbatim(self,
        data_type: typing.Type, 
        target: serializable.Serializable, 
        get_value: typing.Callable [ [serializable.Serializable], typing.Any ],
        set_value: typing.Callable [ [serializable.Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ) -> None:
        pass

    @abc.abstractmethod
    def primitive(self, data_type: typing.Type, target: serializable.Serializable, prop_name: str, fromString: typing.Callable[ [str], PropType ] = None) -> None:
        pass

    @abc.abstractmethod
    def scalar(self, element_builder: construction.Factory, target: serializable.Serializable, prop_name: str) -> None:
        pass

    @abc.abstractmethod
    def array(self, element_builder: construction.Factory, target: serializable.Serializable, prop_name: str) -> None:
        pass

    @abc.abstractmethod
    def map(self, key_type: typing.Type, element_builder: construction.Factory, target: serializable.Serializable, prop_name: str) -> None:
        pass
