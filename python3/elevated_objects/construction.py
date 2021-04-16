#!/usr/bin/env python3

from __future__ import annotations
import typing
import functools

from . import serializable
from . import visitor

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

class Initializer(visitor.Visitor[visitor.ExpectedType]):
    initializers: typing.List[typing.Any]
    obj: visitor.ExpectedType

    def begin(self, obj: visitor.ExpectedType, parent_prop_name: str = None):
        self.obj = obj

    def end(self, obj: visitor.ExpectedType):
        pass

    def __init__(self, *initializers):
        self.initializers = list(initializers)

    def verbatim(self,
        data_type: typing.Type, 
        target: serializable.Serializable, 
        get_value: typing.Callable [ [serializable.Serializable], typing.Any ],
        set_value: typing.Callable [ [serializable.Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ) -> None:
        new_value = functools.reduce(
            lambda result, initializer: result if initializer is None else get_value(initializer),
            self.initializers,
            None)
        if new_value is not None:
            set_value(target, new_value)

    def primitive(self, data_type: typing.Type, target, prop_name: str, fromString: typing.Callable[ [str], typing.Any] = None):
        new_value = functools.reduce(
            lambda result, initializer: getattr(initializer, prop_name) or result,
            self.initializers,
            None)
        if new_value is not None:
            if isinstance(new_value, str) and fromString is not None:
                typed_value = fromString(new_value)
            else: 
                typed_value = new_value
            setattr(target, prop_name, typed_value)

    def scalar(self, element_builder: Builder, target, prop_name: str):
        new_values = [
            getattr(initializer, prop_name) for initializer in self.initializers if hasattr(initializer, prop_name)
        ]
        if len(new_values) == 1:
            return setattr(target, prop_name, new_values[0])
        elif len(new_values) > 1:
            return setattr(target, prop_name, element_builder.clone(*new_values))

    def array(self, element_builder: Builder, target, prop_name: str):
        has_property = [
            initializer for initializer in self.initializers if hasattr(initializer, prop_name)
        ]
        max_length = functools.reduce(
            lambda result, initializer:
                max(len(getattr(initializer, prop_name)), result),
            has_property, 0)

        if max_length > 0:
            new_array_value = []
            for index in range(max_length):
                element_values = [ getattr(initializer, prop_name)[index] for initializer in has_property if getattr(initializer, prop_name) is not None and len(getattr(initializer, prop_name)) > index ]
                if len(element_values) == 0:
                    new_element_value = None
                elif len(element_values) == 1:
                    new_element_value = element_values[0]
                else:
                    new_element_value = element_builder.clone(*element_values)
                new_array_value.append(new_element_value)
            setattr(target, prop_name, new_array_value)

    def init(self, target: serializable.Serializable):
        target.marshal(self)

class Builder(typing.Generic[serializable.ExpectedType]):
    make_value: typing.Callable[ [], serializable.ExpectedType ]

    def __init__(self, make_value: typing.Callable[ [], serializable.ExpectedType ]):
        self.make_value = make_value

    def make(self):
        result = self.make_value()
        return result

    def clone(self, *initializers: object) -> serializable.Serializable:
        result = self.make_value()
        initializer = Initializer(*initializers)
        result.marshal(initializer)
        return result
