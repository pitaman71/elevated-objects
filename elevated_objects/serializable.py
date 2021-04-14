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
    pass

