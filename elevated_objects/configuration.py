#!/usr/bin/env python3

from __future__ import annotations
import datetime
import random
import sys
import typing

from . import construction
from . import serializable
from parts_bin.task import function_task
from lorem_text import lorem

ExpectedType = typing.TypeVar('ExpectedType', bound=serializable.Serializable)
PropType = typing.TypeVar('PropType', bound=serializable.Serializable)

class PropertyCollector(serializable.Visitor[ExpectedType]):
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

    def scalar(self, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        #self.prop_names.add(prop_name)
        pass

    def array(self, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        #self.prop_names.add(prop_name)
        pass

    def map(self, key_type: typing.Type, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        #self.prop_names.add(prop_name)
        pass

class PropertyMutator(serializable.Visitor):
    prop_name: str

    def __init__(self, prop_name: str):
        self.prop_name = prop_name

    def begin(self, obj: serializable.ExpectedType, parent_prop_name: str = None) -> None:
        pass

    def end(self, obj: serializable.ExpectedType) -> None:
        pass

    def verbatim(self,
        data_type: typing.Type, 
        target: serializable.Serializable, 
        get_value: typing.Callable [ [serializable.Serializable], typing.Any ],
        set_value: typing.Callable [ [serializable.Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ) -> None:
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

    def primitive(self, data_type: typing.Type, target: serializable.Serializable, prop_name: str, fromString: typing.Callable[ [str], PropType ] = None) -> None:
        if prop_name != self.prop_name:
            return

        return self.verbatim(data_type, target, 
            lambda target: getattr(target, prop_name),
            lambda target, new_value: setattr(target, prop_name, new_value),
            lambda: set(prop_name,)
        )

    def scalar(self, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        raise RuntimeError('Unsupported Method')

    def array(self, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        raise RuntimeError('Unsupported Method')

    def map(self, key_type: typing.Type, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        raise RuntimeError('Unsupported Method')

class ElementWeights:
    nullify: float
    spawn: float
    select: float
    mutate: float

SymbolTable = typing.Dict[ str, serializable.Cloneable ]
class Mutator:
    factory: construction.Factory
    before: SymbolTable
    after: typing.Union[SymbolTable, None]

    def __init__(self, 
        factory: construction.Factory,
        before: SymbolTable
    ):
        self.factory = factory
        self.before = before
        self.after = None

    @function_task(logMethod=True)
    def done(self) -> typing.Tuple[SymbolTable, typing.Union[SymbolTable, None] ]:
        self.after = dict(self.before)

        # choose a symbol to mutate
        chosen_symbol = random.choice(list(self.after.keys()))

        self.mutate_symbol(chosen_symbol)
        return (self.before, self.after)

    def mutate_symbol(self, chosen_symbol_name: str):
        chosen_symbol = self.after[chosen_symbol_name]
        chosen_symbol = chosen_symbol.clone(chosen_symbol)
        self.after[chosen_symbol_name] = chosen_symbol

        # choose a property to mutate
        prop_name_collector = PropertyCollector()
        chosen_symbol.marshal(prop_name_collector)
        chosen_prop_name = random.choice(list(prop_name_collector.prop_names))

        # mutate that one property
        prop_mutator = PropertyMutator(chosen_prop_name)
        chosen_symbol.marshal(prop_mutator)

        