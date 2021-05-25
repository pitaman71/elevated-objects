#!/usr/bin/env python3

from __future__ import annotations
import typing
import functools

from . import serializable
from . import traversal

ExpectedType = typing.TypeVar('ExpectedType', bound=serializable.Serializable)
PropType = typing.TypeVar('PropType', bound=serializable.Serializable)

class Factory:
    spec_to_builder: typing.Dict[ str, Builder ]

    def __init__(self):
        self.spec_to_builder = {}

    def add_builders(self, builders: typing.List[ Builder ]):
        for builder in builders:
            class_spec = builder.get_class_spec()
            if(class_spec in self.spec_to_builder):
                raise RuntimeError(f"Duplicate definition of class_spec {class_spec}")
            self.spec_to_builder[class_spec] = builder

    def has_class(self, class_spec: typing.Union[str, None]) -> bool:
        return class_spec is not None and class_spec in self.spec_to_builder

    def get_builder(self, class_spec: str):
        return self.spec_to_builder[class_spec]

    def make(self, class_spec:str) -> serializable.Serializable:
        return self.spec_to_builder[class_spec].make()

class Initializer(traversal.Visitor[ExpectedType]):
    builder: Builder[ExpectedType]
    initializers: typing.List[typing.Any]
    obj: ExpectedType

    def begin(self, obj: ExpectedType, parent_prop_name: str = None):
        self.obj = obj

    def end(self, obj: ExpectedType):
        pass

    def owner(self, target: ExpectedType, ownerPropName: str):
        pass

    def __init__(self, builder: Builder[ExpectedType], *initializers):
        self.builder = builder
        self.initializers = list(initializers)

    def clone(self, *initializers: object) -> serializable.Serializable:
        result = self.builder.make()
        initializer = Initializer(self.builder, *initializers)
        result.marshal(initializer)
        return result

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
            return setattr(target, prop_name, self.clone(*new_values))

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
                element_values = [ getattr(initializer, prop_name)[index] for initializer in has_property if len(getattr(initializer, prop_name)) > index ]
                if len(element_values) == 0:
                    new_element_value = None
                elif len(element_values) == 1:
                    new_element_value = element_values[0]
                else:
                    new_element_value = self.clone(*element_values)
                new_array_value.append(new_element_value)
            setattr(target, prop_name, new_array_value)

    def map(self, key_type: typing.Type, element_builder: Builder, target, prop_name: str):
        has_property = [
            initializer for initializer in self.initializers if hasattr(initializer, prop_name)
        ]

        all_keys = set()
        for initializer in has_property:
            all_keys.update(getattr(initializer, prop_name).keys())
        new_value = {}
        for key in all_keys:
            element_values = [ getattr(initializer, prop_name)[key] for initializer in has_property if prop_name in getattr(initializer, prop_name) ]
            if len(element_values) == 0:
                new_element_value = None
            elif len(element_values) == 1:
                new_element_value = element_values[0]
            else:
                new_element_value = self.clone(*element_values)
            new_value[key] = new_element_value
        setattr(target, prop_name, new_value)

    def init(self, target: serializable.Serializable):
        target.marshal(self)

class Builder(typing.Generic[ExpectedType]):
    factory: Factory
    class_spec: any
    allocator: typing.Callable[ [], ExpectedType ]
    when_done: typing.Callable = lambda x: x
    built: ExpectedType = None

    def __init__(self, factory: Factory, class_spec: any, allocator: typing.Callable[ [], ExpectedType ], when_done: typing.Callable = lambda x: x, built: ExpectedType = None):
        self.factory = factory
        self.class_spec = class_spec
        self.allocator = allocator
        self.when_done = when_done
        self.built = built or allocator()

    def get_class_spec(self):
        return self.class_spec

    def get_peer(self, class_spec: str):
        return self.factory.get_builder(class_spec)

    def make(self):
        self.built = self.allocator()
        return self.built

    def done(self, finisher: typing.Callable [ [ ExpectedType ], serializable.Serializable] = lambda x:x) -> serializable.Serializable:
        result = self.built
        self.built = None
        return finisher(self.when_done(result))
