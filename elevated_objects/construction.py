#!/usr/bin/env python3

from __future__ import annotations
import typing
import json
import random

from . import serializable

class Factory:
    spec_to_builder: typing.Dict[ str, Builder ]
    class_id_to_spec: typing.Dict[ int, str ]

    def __init__(self):
        self.spec_to_builder = {}
        self.class_id_to_spec = {}

    def add_value_makers(self, prefix: typing.List[str], value_makers: typing.Dict[str, typing.Callable[ [], serializable.Serializable ]]):
        for suffix, value_maker in value_makers.items():
            class_spec = '.'.join(prefix + suffix.split('.'))
            if(class_spec in self.spec_to_builder):
                raise RuntimeError(f"Duplicate definition of class_spec {class_spec}")
            tmp = value_maker()
            self.spec_to_builder[class_spec] = Builder(value_maker)
            self.class_id_to_spec[id(tmp.__class__)] = class_spec

    def get_class_spec(self, obj: serializable.Serializable) -> str:
        class_spec = self.class_id_to_spec.get(id(obj.__class__))
        if class_spec is None:
            raise RuntimeError(f'No class_spec for {obj.__class__.__qualname__}')
        return class_spec

    def has_class(self, class_spec: typing.Union[str, None]) -> bool:
        return class_spec is not None and class_spec in self.spec_to_builder

    def make(self, class_spec:str) -> serializable.Serializable:
        return self.spec_to_builder[class_spec].make()

class Builder(typing.Generic[serializable.ExpectedType]):
    make_value: typing.Callable[ [], serializable.ExpectedType ]

    def __init__(self, make_value: typing.Callable[ [], serializable.ExpectedType ]):
        self.make_value = make_value

    def make(self):
        result = self.make_value()
        return result
