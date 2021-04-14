#!/usr/bin/env python3

from __future__ import annotations
import datetime
import random
import sys
import typing
import functools
import multidict

from . import construction
from . import serializable
from . import json_marshal
from . import visitor

from parts_bin.task import function_task
from lorem_text import lorem

ExpectedType = typing.TypeVar('ExpectedType', bound=serializable.Serializable)
PropType = typing.TypeVar('PropType', bound=serializable.Serializable)

class PropertyCollector(visitor.Visitor[ExpectedType]):
    prop_names: typing.Set[str]

    def __init__(self):
        self.prop_names = set()

    def begin(self, obj: ExpectedType, parent_prop_name: str = None) -> None:
        pass

    def end(self, obj: ExpectedType) -> None:
        pass

    def verbatim(self, 
        data_type: typing.Type, 
        target: serializable.Serializable, 
        get_value: typing.Callable [ [serializable.Serializable], typing.Any ],
        set_value: typing.Callable [ [serializable.Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ) -> None:
        self.prop_names = self.prop_names.union(get_prop_names())

    def primitive(self, data_type: typing.Type, target: serializable.Serializable, prop_name: str, fromString: typing.Callable[ [str], PropType ] = None) -> None:
        self.prop_names.add(prop_name)

    def scalar(self, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> None:
        self.prop_names.add(prop_name)
        pass

    def array(self, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> None:
        #self.prop_names.add(prop_name)
        pass

    def map(self, key_type: typing.Type, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> None:
        #self.prop_names.add(prop_name)
        pass

ElementType = typing.TypeVar('ElementType', bound=serializable.Serializable)
class ScalarMutator(typing.Generic[ElementType]):
    mutator: Mutator
    element_type: construction.Builder
    before: ElementType | None
    after: ElementType | None
    weights: typing.Dict[ str, float ]

    def __init__(self, 
        mutator: Mutator,
        element_type: construction.Builder, 
        before: ElementType | None
    ):
        self.mutator = mutator
        self.element_type = element_type
        self.before = before
        self.after = None

        self.weights = {
            'make': 1.0,
            'pick': 1.0,
            'modify': 1.0,
            'clear': 1.0
        }

    def __call__(self) -> ElementType | None:
        class_spec = self.mutator.factory.get_class_spec(self.element_type.make())
        if self.before is None:
            self.weights['clear'] = 0.0
            self.weights['modify'] = 0.0
        if not self.mutator.can_pick(class_spec):
            self.weights['pick'] = 0.0

        total = functools.reduce(
            lambda total, kind: self.weights[kind] + total,
            self.weights.keys(), 
            0.0
        )

        if total == 0.0:
            raise RuntimeError(f"No randomization strategy is available")
        
        class Iterator:
            selected: str | None
            remainder: float

            def __init__(self, selected: str | None, remainder: float):
                self.selected = selected
                self.remainder = remainder

            def next(self, weight: float):
                return Iterator(self.selected, self.remainder - weight)

        kind_selector = functools.reduce(
            lambda iterator, kind: Iterator(kind, 0.0) if self.weights[kind] > iterator.remainder else iterator.next(self.weights[kind]),
            self.weights.keys(),
            Iterator(None, random.uniform(0.0,total))
        )
        if kind_selector.selected == 'make':
            made = self.mutator.make(class_spec)
            self.after = typing.cast(ElementType, self.mutator.element(made))
        elif kind_selector.selected == 'pick':
            if not self.mutator.can_pick(class_spec):
                raise RuntimeError('No samples from which to pick')
            self.after = typing.cast(ElementType, self.mutator.pick(class_spec))
        elif kind_selector.selected == 'modify':
            if self.before is None:
                raise RuntimeError('Logic error')
            self.after = typing.cast(ElementType, self.mutator.element(self.before))
        elif kind_selector.selected == 'clear':
            self.after = None
        return self.after

class PropertyMutator(visitor.Visitor):
    mutator: Mutator
    prop_name: str
    count: int

    def __init__(self, mutator: Mutator, prop_name: str):
        self.mutator = mutator
        self.prop_name = prop_name
        self.count = 0

    def begin(self, obj: serializable.ExpectedType, parent_prop_name: str = None) -> None:
        self.count = 0

    def end(self, obj: serializable.ExpectedType) -> None:
        pass

    def verbatim(self,
        data_type: typing.Type, 
        target: serializable.Serializable, 
        get_value: typing.Callable [ [serializable.Serializable], typing.Any ],
        set_value: typing.Callable [ [serializable.Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ) -> None:
        self.count += 1
        if data_type == int:
            before = get_value(target)
            after = get_value(target)
            while before == after:
                gen = random.choice([ 
                    lambda: random.randint(0,1),
                    lambda: random.randint(-1,1),
                    lambda: random.randint(0,10),
                    lambda: random.randint(-10,10),
                    lambda: random.random()
                ])
                after = gen()
            set_value(target, after)
        elif data_type == float:
            before = get_value(target)
            after = get_value(target)
            while before == after:
                gen = random.choice([ 
                    lambda: random.uniform(0,1),
                    lambda: random.uniform(-1,1),
                    lambda: random.uniform(0,10),
                    lambda: random.uniform(-10,10),
                    lambda: random.uniform(sys.float_info.min, sys.float_info.max)
                ])
                after = gen()
            set_value(target, after)
        elif data_type == datetime.datetime:
            before = get_value(target)
            after = get_value(target)
            while before == after:
                basis = datetime.datetime.now() if before is None else random.choice([before, datetime.datetime.now()])
                delta_generators = [
                    lambda: -1,
                    lambda: 1,
                    lambda: random.randint(-7,-1),
                    lambda: random.randint(1,7),
                    lambda: random.randint(-27,-1),
                    lambda: random.randint(1,27),
                    lambda: random.choice([27, 28, 29, 30, 31, 52, 60]),
                    lambda: random.choice([-27, -28, -29, -30, -31, 52, -60]),
                    lambda: random.choice([100, 1000, 10000])
                ]
                delta = random.choice(delta_generators)
                gen = random.choice([ 
                    lambda: basis + datetime.timedelta(seconds=delta()),
                    lambda: basis + datetime.timedelta(minutes=delta()),
                    lambda: basis + datetime.timedelta(hours=delta()),
                    lambda: basis + datetime.timedelta(days=delta()),
                    lambda: basis + datetime.timedelta(weeks=delta())
                ])
                after = gen()
            set_value(target, after)
        elif data_type == str:
            before = get_value(target)
            after = get_value(target)
            while before == after:
                after = lorem.sentence()
            set_value(target, after)
        else:
            raise RuntimeError(f"Unable to mutate property of type {data_type}")

    def primitive(self, data_type: typing.Type, target: serializable.Serializable, prop_name: str, fromString: typing.Callable[ [str], PropType ] = None) -> None:
        if prop_name != self.prop_name:
            return

        return self.verbatim(data_type, target, 
            lambda target: getattr(target, prop_name),
            lambda target, new_value: setattr(target, prop_name, new_value),
            lambda: set(prop_name,)
        )

    def scalar(self, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> None:
        if prop_name != self.prop_name:
            return
        self.count += 1
        element_class_spec = self.mutator.factory.get_class_spec(element_builder.make())
        mutator = ScalarMutator(self.mutator,
            element_builder,
            getattr(target, prop_name)
        )
        setattr(target, prop_name, mutator())

    def array(self, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> None:
        raise RuntimeError('Unsupported Method')

    def map(self, key_type: typing.Type, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> None:
        raise RuntimeError('Unsupported Method')

class ElementWeights:
    nullify: float
    spawn: float
    select: float
    mutate: float

SymbolTable = typing.Dict[ str, serializable.Serializable ]
class SymbolTableMutator:
    mutator: Mutator
    before: SymbolTable
    after: typing.Union[SymbolTable, None]

    def __init__(self, 
        mutator: Mutator,
        before: SymbolTable
    ):
        self.mutator = mutator
        self.pool = multidict.MultiDict()
        self.before = before
        self.after = None

    @function_task(logMethod=True)
    def done(self) -> typing.Tuple[SymbolTable, typing.Union[SymbolTable, None] ]:
        self.after = dict(self.before)

        # choose a symbol to mutate
        chosen_symbol_name = random.choice(list(self.after.keys()))

        self.after[chosen_symbol_name] = self.mutator.element(self.before[chosen_symbol_name])
        return (self.before, self.after)

class Mutator:
    factory: construction.Factory
    pool: multidict.MultiDict[serializable.Serializable]

    def __init__(self, 
        factory: construction.Factory
    ):
        self.factory = factory
        self.pool = multidict.MultiDict()

    def make(self, class_spec: str) -> serializable.Serializable:
        return self.factory.make(class_spec)

    def can_pick(self, class_spec: str) -> bool:
        return class_spec in self.pool

    def pick(self, class_spec: str) -> serializable.Serializable:
        return random.choice(self.pool.getall(class_spec))

    def element(self, before: serializable.Serializable) -> serializable.Serializable:
        class_spec = self.factory.get_class_spec(before)
        after = self.factory.make(class_spec)
        self.pool.add(class_spec, after)
        after.marshal(json_marshal.Initializer(before))

        # choose a property to mutate
        prop_name_collector = PropertyCollector()
        after.marshal(prop_name_collector)
        chosen_prop_name = random.choice(list(prop_name_collector.prop_names))

        # mutate that one property
        prop_mutator = PropertyMutator(self, chosen_prop_name)
        after.marshal(prop_mutator)
        if prop_mutator.count == 0:
            raise RuntimeError(f"Failed to mutate property {class_spec}.{chosen_prop_name}")
        return after
