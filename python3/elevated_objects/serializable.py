#!/usr/bin/env python3

from __future__ import annotations
import abc
import typing

class Serializable(abc.ABC):
    __factory__: typing.Any

    @abc.abstractmethod
    def marshal(self, visitor: Visitor) -> None:
        pass

    @abc.abstractmethod
    def get_class_spec(self) -> str:
        pass

    def get_global_id(self) -> str|int|None:
        return id(self)

    def __str__(self) -> str:
        global_id = self.get_global_id()
        if global_id is not None:
            return f"{self.__class__.__qualname__} \"{global_id}\""
        else:
            return f"{self.__class__.__qualname__} @{id(self)}"
            
ExpectedType = typing.TypeVar('ExpectedType', bound=Serializable)
PropType = typing.TypeVar('PropType')

class Visitor(typing.Generic[ExpectedType]):
    pass

