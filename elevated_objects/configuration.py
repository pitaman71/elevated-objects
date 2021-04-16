#!/usr/bin/env python3

from __future__ import annotations
import datetime
import random
import sys
import typing
import functools
import multidict

from . import construction
from . import json_marshal
from . import serializable
from . import source_code
from . import visitor

from parts_bin.task import function_task
from lorem_text import lorem
    
ExpectedType = typing.TypeVar('ExpectedType', bound=serializable.Serializable)
PropType = typing.TypeVar('PropType', bound=serializable.Serializable)

def weighted_random(keys: typing.List[str], get_weight: typing.Callable[ [str], float]):
        total = functools.reduce(
            lambda total, kind: get_weight(kind) + total,
            keys, 
            0.0
        )
        if total == 0.0:
            return None
        
        class Iterator:
            selected: str | None
            remainder: float

            def __init__(self, selected: str | None, remainder: float):
                self.selected = selected
                self.remainder = remainder

            def next(self, weight: float):
                return Iterator(self.selected, self.remainder - weight)

        iterator = functools.reduce(
            lambda iterator, kind: Iterator(iterator.selected or kind, 0.0) if get_weight(kind) > iterator.remainder else iterator.next(get_weight(kind)),
            keys,
            Iterator(None, random.uniform(0.0,total))
        )
        return iterator.selected

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
        self.prop_names.add(prop_name)
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
        if self.before is not None:
            with Ancestor(self.mutator, self.before):
                return self.go()
        else:
            return self.go()

    def go(self) -> ElementType | None:
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

        chosen_kind = weighted_random(
            list(self.weights.keys()),
            lambda key: self.weights[key]
        )
        print(f"DEBUG: weights are {self.weights} when mutating {json_marshal.to_string(self.mutator.factory,self.before)} with strategy {chosen_kind}")

        if chosen_kind is None:
            raise RuntimeError(f"No randomization strategy is available")            
        
        if chosen_kind == 'make':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            with self.mutator.make(class_spec) as ancestor1:
                with self.mutator.modify(ancestor1.target) as ancestor2:
                    self.after = typing.cast(ElementType, ancestor2.target)
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'pick':
            if not self.mutator.can_pick(class_spec):
                raise RuntimeError('No samples from which to pick')
            location = source_code.Line()
            self.mutator.push_strategy(location)
            with self.mutator.pick(class_spec) as ancestor:
                self.after = typing.cast(ElementType, ancestor.target)

            self.mutator.pop_strategy(location)
        elif chosen_kind == 'modify':
            if self.before is None:
                raise RuntimeError('Logic error')
            location = source_code.Line()
            self.mutator.push_strategy(location)
            with self.mutator.modify(self.before) as ancestor:
                self.after = typing.cast(ElementType, ancestor.target)
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'clear':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            self.after = None
            self.mutator.pop_strategy(location)
        else:
            raise RuntimeError(f"Invalid mutation strategy {chosen_kind}")
        return self.after

class ArrayMutator(typing.Generic[ElementType]):
    mutator: Mutator
    element_type: construction.Builder
    before: typing.List[ElementType]
    after: typing.List[ElementType] | None
    weights: typing.Dict[ str, float ]

    def __init__(self, 
        mutator: Mutator,
        element_type: construction.Builder, 
        before: typing.List[ElementType]
    ):
        self.mutator = mutator
        self.element_type = element_type
        self.before = before
        self.after = None

        self.weights = {
            'clear': 1.0,
            'modify': 1.0,
            'make.front': 1.0,
            'make.back': 1.0,
            'make.insert': 1.0,
            'pick.front': 1.0,
            'pick.back': 1.0,
            'pick.insert': 1.0,
            'pop.front': 1.0,
            'pop.back': 1.0,
            'reverse.all': 1.0,
            'reverse.front': 0,
            'reverse.back': 0,
            'reverse.insert': 0,
            'stutter.front': 1.0,
            'stutter.back': 1.0,
            'stutter.insert': 1.0,
            'swap.ends': 1.0,
            'swap.front': 1.0,
            'swap.back': 1.0,
            'swap.insert': 0.0
        }

    def __call__(self) -> typing.List[ElementType] | None:
        class_spec = self.mutator.factory.get_class_spec(self.element_type.make())

        if len(self.before) == 0:
            self.weights['clear'] = 0.0
            self.weights['modify'] = 0.0
            self.weights['pop.front'] = 0.0
            self.weights['pop.back'] = 0.0
            self.weights['stutter.front'] = 0.0
            self.weights['stutter.back'] = 0.0
        if len(self.before) <= 1:
            self.weights['make.insert'] = 0.0
            self.weights['pick.insert'] = 0.0
            self.weights['stutter.insert'] = 0.0
            self.weights['reverse.all'] = 0.0
            self.weights['swap.ends'] = 0.0
            self.weights['swap.front'] = 0.0
            self.weights['swap.back'] = 0.0
            self.weights['swap.insert'] = 0.0
        if len(self.before) <= 2:
            self.weights['reverse.front'] = 0.0
            self.weights['reverse.back'] = 0.0
            self.weights['reverse.insert'] = 0.0
        if not self.mutator.can_pick(class_spec):
            self.weights['pick.front'] = 0.0
            self.weights['pick.back'] = 0.0
            self.weights['pick.insert'] = 0.0

        if len(set(self.before)) < len(self.before):
            self.weights['swap.ends'] = 0.0
            self.weights['swap.front'] = 0.0
            self.weights['swap.back'] = 0.0
            self.weights['swap.insert'] = 0.0
            self.weights['reverse.all'] = 0.0
            self.weights['reverse.front'] = 0.0
            self.weights['reverse.back'] = 0.0
            self.weights['reverse.insert'] = 0.0

        chosen_kind = weighted_random(
            list(self.weights.keys()),
            lambda key: self.weights[key]
        )
        if chosen_kind is None:
            raise RuntimeError(f"No randomization strategy is available")            

        if chosen_kind == 'clear':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            self.after = []
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'modify':
            if len(self.before) == 0:
                raise RuntimeError('Logic error')
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_index = int(random.randint(0, len(self.before) - 1))
            self.after = list(self.before)
            with self.mutator.modify(self.before[chosen_index]) as ancestor:
                self.after[chosen_index] = typing.cast(ElementType, ancestor.target)
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'make.front':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            with self.mutator.make(class_spec) as ancestor1:
                with self.mutator.modify(ancestor1.target) as ancestor2:
                    made = typing.cast(ElementType, ancestor2.target)
            self.after = [made] + self.before
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'make.back':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            with self.mutator.make(class_spec) as ancestor1:
                with self.mutator.modify(ancestor1.target) as ancestor2:
                    made = typing.cast(ElementType, ancestor2.target)
            self.after = self.before + [made]
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'make.insert':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_index = int(random.randint(0, len(self.before) - 2))
            with self.mutator.make(class_spec) as ancestor1:
                with self.mutator.modify(ancestor1.target) as ancestor2:
                    made = typing.cast(ElementType, ancestor2.target)
            self.after = self.before[0:chosen_index] + [made] + self.before[chosen_index:]
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'pick.front':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            with self.mutator.pick(class_spec) as ancestor:
                made = typing.cast(ElementType, ancestor.target)
                self.after = [made] + self.before
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'pick.back':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            with self.mutator.pick(class_spec) as ancestor:
                made = typing.cast(ElementType, ancestor.target)
                self.after = self.before + [made]
                self.mutator.pop_strategy(location)
        elif chosen_kind == 'pick.insert':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_index = int(random.randint(0, len(self.before) - 2))
            with self.mutator.pick(class_spec) as ancestor:
                made = typing.cast(ElementType, ancestor.target)
                self.after = self.before[0:chosen_index] + [made] + self.before[chosen_index:]
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'pop.front':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            self.after = self.before[1:]
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'pop.back':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            self.after = self.before[0:-1]
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'reverse.all':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            segment = list(self.before)
            segment.reverse()
            self.after = segment
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'reverse.front':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_length = int(random.randint(2, len(self.before) - 1))
            segment = self.before[0:chosen_length]
            segment.reverse()
            self.after = segment + self.before[chosen_length:]
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'reverse.back':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_length = int(random.randint(2, len(self.before) - 1))
            total_length = len(self.before)
            segment = self.before[total_length - chosen_length:]
            segment.reverse()
            self.after = self.before[:total_length - chosen_length] + segment
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'reverse.insert':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_index = int(random.randint(1, len(self.before) - 2))
            chosen_length = int(random.randint(2, len(self.before) - chosen_index - 1))
            segment = self.before[chosen_index:chosen_index+chosen_length]
            segment.reverse()
            self.after = self.before[:chosen_index] + segment + self.before[chosen_index+chosen_length:]
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'stutter.front':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_copies = int(random.randint(2,5))
            chosen_length = int(random.randint(1, len(self.before)))
            segment = list(chosen_copies * tuple(self.before[0:chosen_length]))
            self.after = segment + segment + self.before[chosen_length:]
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'stutter.back':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_copies = int(random.randint(2,5))
            chosen_length = int(random.randint(1, len(self.before)))
            total_length = len(self.before)
            segment = list(chosen_copies * tuple(self.before[total_length-chosen_length:]))
            self.after = self.before[total_length-chosen_length:] + segment + segment
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'stutter.insert':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_copies = int(random.randint(2,5))
            chosen_index = int(random.randint(1, len(self.before) - 2))
            chosen_length = int(random.randint(1, len(self.before)))
            segment = list(chosen_copies * tuple(self.before[0:chosen_length]))
            self.after = self.before[:chosen_index] + segment + self.before[chosen_index+chosen_length:]
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'swap.ends':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_length = int(random.randint(1, int(len(self.before)/2)))
            total_length = len(self.before)
            back = self.before[total_length - chosen_length:]
            front = self.before[0:chosen_length]
            middle = self.before[chosen_length:total_length - (2*chosen_length)]
            self.after = back + middle + front
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'swap.front':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_length = int(random.randint(1, int(len(self.before)/2) - 1))
            total_length = len(self.before)
            front = self.before[0:chosen_length]
            rest = self.before[chosen_length:]
            chosen_index = int(random.randint(0, total_length - 2*chosen_length - 1))
            left = rest[0:chosen_index]
            middle = rest[chosen_index:chosen_index+chosen_length]
            right = rest[chosen_index+chosen_length:]
            self.after = middle + left + front + right
            self.mutator.pop_strategy(location)
        elif chosen_kind == 'swap.back':
            location = source_code.Line()
            self.mutator.push_strategy(location)
            chosen_length = int(random.randint(1, int(len(self.before)/2) - 1))
            total_length = len(self.before)
            back = self.before[(total_length - chosen_length):]
            rest = self.before[0:(total_length - chosen_length)]
            chosen_index = int(random.randint(0, total_length - 2*chosen_length - 1))
            left = rest[0:chosen_index]
            middle = rest[chosen_index:chosen_index+chosen_length]
            right = rest[chosen_index+chosen_length:]
            self.after = left + back + right + middle
            self.mutator.pop_strategy(location)
        else:
            raise RuntimeError(f'Unsupported method {chosen_kind}')

        if(self.after is not None and len([ item for item in self.after if item is None])) > 0:
            raise RuntimeError('Array mutator introduced a NULL {location}')
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
            location = source_code.Line()
            self.mutator.push_strategy(location)
            before = get_value(target)
            after = get_value(target)
            while before == after:
                gen = random.choice([ 
                    lambda: int(random.randint(0,1)),
                    lambda: int(random.randint(-1,1)),
                    lambda: int(random.randint(0,10)),
                    lambda: int(random.randint(-10,10)),
                    lambda: int(random.randint(-127,256))
                ])
                after = gen()
            print(f"DEBUG: int value {before} -> {after}")
            set_value(target, after)
            self.mutator.pop_strategy(location)
        elif data_type == float:
            location = source_code.Line()
            self.mutator.push_strategy(location)
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
            print(f"DEBUG: float value {before} -> {after}")
            set_value(target, after)
            self.mutator.pop_strategy(location)
        elif data_type == datetime.datetime:
            location = source_code.Line()
            self.mutator.push_strategy(location)
            before = get_value(target)
            after = get_value(target)
            while before == after:
                basis = datetime.datetime.now() if before is None else random.choice([before, datetime.datetime.now()])
                delta_generators = [
                    lambda: -1,
                    lambda: 1,
                    lambda: int(random.randint(-7,-1)),
                    lambda: int(random.randint(1,7)),
                    lambda: int(random.randint(-27,-1)),
                    lambda: int(random.randint(1,27)),
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
            self.mutator.pop_strategy(location)
        elif data_type == str:
            location = source_code.Line()
            self.mutator.push_strategy(location)
            before = get_value(target)
            after = get_value(target)
            while before == after:
                after = lorem.sentence()
            set_value(target, after)
            self.mutator.pop_strategy(location)
        else:
            raise RuntimeError(f"Unable to mutate property of type {data_type}")

    def primitive(self, data_type: typing.Type, target: serializable.Serializable, prop_name: str, fromString: typing.Callable[ [str], PropType ] = None) -> None:
        if prop_name != self.prop_name:
            return

        location = source_code.Line()
        self.mutator.push_strategy(location)
        result = self.verbatim(data_type, target, 
            lambda target: getattr(target, prop_name),
            lambda target, new_value: setattr(target, prop_name, new_value),
            lambda: set(prop_name,)
        )
        self.mutator.pop_strategy(location)
        return result

    def scalar(self, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> None:
        if prop_name != self.prop_name:
            return
        self.count += 1
        location = source_code.Line()
        self.mutator.push_strategy(location)
        mutator = ScalarMutator(self.mutator,
            element_builder,
            getattr(target, prop_name)
        )
        setattr(target, prop_name, mutator())
        self.mutator.pop_strategy(location)

    def array(self, element_builder: construction.Builder, target: serializable.Serializable, prop_name: str) -> None:
        if prop_name != self.prop_name:
            return
        self.count += 1
        location = source_code.Line()
        self.mutator.push_strategy(location)
        mutator = ArrayMutator(self.mutator,
            element_builder,
            getattr(target, prop_name)
        )
        setattr(target, prop_name, mutator())
        self.mutator.pop_strategy(location)

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
    kind: typing.Union[str, None]

    def __init__(self, 
        mutator: Mutator,
        before: SymbolTable
    ):
        self.mutator = mutator
        self.pool = multidict.MultiDict()
        self.before = before
        self.after = None

    @function_task(logMethod=True)
    def __call__(self)  -> typing.Union[SymbolTable, None]:
        self.after = dict(self.before)

        # choose a symbol to mutate
        chosen_symbol_name = random.choice(list(self.after.keys()))

        return self.symbol(chosen_symbol_name, list(self.after.keys()))

    def symbol(self, chosen_symbol_name: str, keys: typing.List[str])  -> typing.Union[SymbolTable, None]:
        if len(keys) == 0:
            return self.finish(chosen_symbol_name)
        else:
            if not isinstance(self.before[keys[0]], serializable.Serializable):
                raise RuntimeError(f"Expected serializable.Serializable but got {type(self.before[keys[0]])}")
            with Ancestor(self.mutator, self.before[keys[0]]) as ancestor:
                return self.symbol(chosen_symbol_name, keys[1:])

    def finish(self, chosen_symbol_name: str) -> typing.Union[SymbolTable, None]:
        with self.mutator.modify(self.before[chosen_symbol_name]) as ancestor:
            if not isinstance(ancestor.target, serializable.Serializable):
                raise RuntimeError(f"Expected serializable.Serializable but got {type(ancestor.target)}")
            self.after[chosen_symbol_name] = ancestor.target
        return self.after

class Ancestor:
    mutator: Mutator
    target: serializable.Serializable

    def __init__(self, mutator: Mutator, target: serializable.Serializable):
        self.mutator = mutator
        self.target = target

    def __enter__(self):
        print(f"DEBUG: push ancestor {id(self.target)}")
        self.mutator.ancestors.add(self.target)
        return self

    def __exit__(self, type, value, tb):
        print(f"DEBUG: pop ancestor {id(self.target)}")
        self.mutator.ancestors.remove(self.target)

class Mutator:
    factory: construction.Factory
    pool: multidict.MultiDict[serializable.Serializable]
    ancestors: typing.Set[serializable.Serializable]

    def __init__(self, 
        factory: construction.Factory
    ):
        self.factory = factory
        self.pool = multidict.MultiDict()
        self.ancestors = set()

    def push_strategy(self, strategy):
        print(f"PUSH strategy {strategy}")

    def pop_strategy(self, strategy):
        print(f"POP  strategy {strategy}")

    def make(self, class_spec: str) -> Ancestor:
        result = self.factory.make(class_spec)
        return Ancestor(self, result)

    def can_pick(self, class_spec: str) -> bool:
        if class_spec not in self.pool: return False
        return len(self.get_candidates(class_spec)) > 0

    def get_candidates(self, class_spec: str):
        return [ candidate for candidate in self.pool.getall(class_spec) if candidate not in self.ancestors ]

    def pick(self, class_spec: str) -> Ancestor:
        return Ancestor(self, random.choice(self.get_candidates(class_spec)))

    def modify(self, before: serializable.Serializable) -> Ancestor:
        class_spec = self.factory.get_class_spec(before)
        after = self.factory.make(class_spec)
        self.pool.add(class_spec, after)
        after.marshal(construction.Initializer(before))

        # choose a property to mutate
        prop_name_collector = PropertyCollector()
        after.marshal(prop_name_collector)
        chosen_prop_name = random.choice(list(prop_name_collector.prop_names))

        save = getattr(before, chosen_prop_name)

        # mutate that one property
        self.push_strategy(f"Mutating property {class_spec}.{chosen_prop_name}")
        prop_mutator = PropertyMutator(self, chosen_prop_name)
        after.marshal(prop_mutator)
        if prop_mutator.count == 0:
            raise RuntimeError(f"Failed to mutate property {class_spec}.{chosen_prop_name}")
        self.pop_strategy(f"Mutating property {class_spec}.{chosen_prop_name}")
        print(f"DEBUG: {id(before)} property value before = {getattr(before, chosen_prop_name)}")
        print(f"DEBUG: {id(after)} property value after = {getattr(after, chosen_prop_name)}")

        return Ancestor(self, after)
