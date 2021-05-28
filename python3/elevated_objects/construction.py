#!/usr/bin/env python3

from __future__ import annotations
import typing
import functools

from . import serializable
from . import traversal

DoneType = typing.TypeVar('DoneType')
ExpectedType = typing.TypeVar('ExpectedType', bound=serializable.Serializable)

class Initializer(traversal.Visitor[ExpectedType]):
    factory: Factory[ExpectedType]
    initializers: typing.List[typing.Any]
    obj: ExpectedType

    def begin(self, obj: ExpectedType):
        self.obj = obj

    def end(self, obj: ExpectedType):
        pass

    def owner(self, target: ExpectedType, ownerPropName: str):
        pass

    def __init__(self, factory: Factory[ExpectedType], *initializers):
        self.factory = factory
        self.initializers = list(initializers)

    def clone(self, *initializers: object) -> serializable.Serializable:
        result = self.factory.make()
        initializer = Initializer(self.factory, *initializers)
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

    def scalar(self, element_factory: Factory, target, prop_name: str):
        new_values = [
            getattr(initializer, prop_name) for initializer in self.initializers if hasattr(initializer, prop_name)
        ]
        if len(new_values) == 1:
            return setattr(target, prop_name, new_values[0])
        elif len(new_values) > 1:
            return setattr(target, prop_name, element_factory.clone(*new_values))

    def array(self, element_factory: Factory, target, prop_name: str):
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
                    new_element_value = element_factory.clone(*element_values)
                new_array_value.append(new_element_value)
            setattr(target, prop_name, new_array_value)

    def map(self, key_type: typing.Type, element_factory: Factory, target, prop_name: str):
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
                new_element_value = element_factory.clone(*element_values)
            new_value[key] = new_element_value
        setattr(target, prop_name, new_value)

    def init(self, target: serializable.Serializable):
        target.marshal(self)

class Factory(typing.Generic[ExpectedType]):
    pass

Allocator = typing.Callable[ [ Factory[ExpectedType] ], ExpectedType ]

class Factory(typing.Generic[ExpectedType]):
    class_spec: str
    allocators: Allocator[ExpectedType]

    @classmethod
    def abstract(cls, class_spec: str):
        result = Factory(class_spec)
        return result

    @classmethod
    def concrete(cls, class_spec: str, allocator: Allocator[ExpectedType]):
        result = Factory(class_spec)
        result.allocators = { class_spec: allocator }
        return result

    @classmethod
    def derived(cls, class_spec: str, 
        allocator: Allocator[ExpectedType],
        parent_factories: typing.List[ Factory ]
    ):
        result = Factory(class_spec)
        result.allocators = { class_spec: allocator }
        for parent_factory in parent_factories:
            parent_factory.allocators.update(result.allocators)
        return result

    def __init__(self, class_spec: str):
        self.allocators = {}
        self.class_spec = class_spec

    def get_class_spec(self):
        return self.class_spec
        
    def make(self, class_spec: str):
        if class_spec is None:
            class_spec = self.class_spec

        if class_spec not in self.allocators:
            raise RuntimeError(f"Object of type {class_spec} is not compatible with {self.allocators.keys()}")

        result = self.allocators[class_spec]()
        result.__factory__ = self
        return result

class Factories:
    spec_to_builder: typing.Dict[ str, Factory ]

    def __init__(self):
        self.spec_to_builder = {}

    def register(self, class_spec: str, factory_maker: typing.Callable[ [], Factory ]):
        if(class_spec not in self.spec_to_builder):
            self.spec_to_builder[class_spec] = factory_maker()
        return self.spec_to_builder[class_spec]

    def has_class(self, class_spec: typing.Union[str, None]) -> bool:
        return class_spec is not None and class_spec in self.spec_to_builder

    def get_builder(self, class_spec: str) -> Factory:
        return self.spec_to_builder[class_spec]

    def get_builder_of(self, obj: serializable.Serializable) -> Factory:
        return obj.__class.__.Factory()

    def make(self, class_spec:str) -> serializable.Serializable:
        return self.spec_to_builder[class_spec].make()

factories = Factories()

class Builder(typing.Generic[ExpectedType, DoneType]):
    factory: Factory[ExpectedType]
    when_done: typing.Callable[ [ ExpectedType ], DoneType ] = lambda x: x
    built: ExpectedType

    def __init__(self, factory: Factory[ExpectedType], when_done: typing.Callable[ [ ExpectedType ], DoneType ] = lambda x: x, built: ExpectedType = None):
        self.factory = factory
        self.when_done = when_done
        self.built = built or factory.make()

    def get_class_spec(self):
        return self.factory.class_spec
        
    def done(self, finisher: typing.Callable [ [ ExpectedType ], ExpectedType] = lambda x:x) -> DoneType:
        return self.when_done(finisher(self.built))

