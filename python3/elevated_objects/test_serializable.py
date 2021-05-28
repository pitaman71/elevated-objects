#!/usr/bin/env python3

import unittest
import json
import os
import typing
import abc

from . import comparison
from . import configuration
from . import construction
from . import serializable
from . import json_marshal
from . import traversal

class Property(serializable.Serializable):
    @classmethod
    def Factory(cls, class_spec: str = 'test_serializable.Property'):
        return construction.factories.register(class_spec, lambda: construction.Factory.abstract(class_spec))

class Primitives(Property):
    prop_int: typing.Union[ int, None ]
    prop_float: typing.Union[ float, None ]
    prop_string: typing.Union[ str, None ]

    @classmethod
    def Factory(cls, class_spec: str = 'test_serializable.Primitives'):
        return construction.factories.register(class_spec, lambda: construction.Factory.derived(class_spec, lambda: cls(), [ Property.Factory() ]))

    def __init__(self):
        self.prop_int = None
        self.prop_float = None
        self.prop_string = None

    def get_class_spec(self): return 'test_serializable.Primitives'

    def marshal(self, visitor: traversal.Visitor):
        visitor.begin(self)
        visitor.primitive(int, self, 'prop_int')
        visitor.primitive(float, self, 'prop_float')
        visitor.primitive(str, self, 'prop_string')
        visitor.end(self)

DataType = typing.TypeVar('DataType', int, float, str)

class Verbatim(Property):
    data_type: typing.Type
    prop: typing.Union[ int, float, str, None]

    @classmethod
    def Factory(cls, data_type: typing.Type, class_spec: str = None):
        if class_spec is None:
            class_spec = f"test_serializable.Verbatim.{str(data_type)}"
        return construction.factories.register(class_spec, lambda: construction.Factory.derived(class_spec, lambda: cls(data_type), [ Property.Factory() ]))

    def __init__(self, data_type: typing.Type):
        self.data_type = data_type
        self.prop = None

    def get_class_spec(self): return f"test_serializable.Verbatim.{str(self.data_type)}"

    def marshal(self, visitor: traversal.Visitor):
        visitor.begin(self)
        visitor.verbatim(
            self.data_type, 
            self,
            lambda target: getattr(target, 'prop'), 
            lambda target, new_value: setattr(target, 'prop', new_value),
            lambda: {'prop'}
        )
        visitor.end(self)

class Scalar(Property):
    prop_primitives: typing.Union[Primitives, None]
    prop_array: typing.Union[typing.List, None]
    prop_map: typing.Union[typing.Dict, None]

    @classmethod
    def Factory(cls, class_spec: str = 'test_serializable.Scalar'):
        return construction.factories.register(class_spec, lambda: construction.Factory.derived(class_spec, lambda: cls(), [ Property.Factory() ]))

    def __init__(self):
        self.prop_primitives = None
        self.prop_array = []
        self.prop_map = {}

    def get_class_spec(self): return f"test_serializable.Scalar"

    def marshal(self, visitor: traversal.Visitor):
        visitor.begin(self)
        visitor.scalar(Primitives.Factory(), self, 'prop_primitives')
        visitor.array(Property.Factory(), self, 'prop_array')
        visitor.map(str, Property.Factory(), self, 'prop_map')
        visitor.end(self)

class TestPrimitives(unittest.TestCase, serializable.Serializable):
    dirty: bool
    blank: typing.Union[Primitives, None]
    mutation_count: int
    mutations: typing.List[Primitives]

    @classmethod
    def Factory(cls, class_spec: str = 'test_serializable.TestPrimitives'):
        return construction.factories.register(class_spec, lambda: construction.Factory.concrete(class_spec, lambda: cls()))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dirty = False
        self.blank = None
        self.mutation_count = 50
        self.mutations = []

    def randomize(self):
        self.blank = Primitives()
        last = self.blank
        mutator = configuration.Mutator()
        for index in range(self.mutation_count):
            mutator.push_strategy(f"TestPrimitives.{index}")
            st_mutator = configuration.SymbolTableMutator(mutator, {
                'a': last
            })
            st_mutator()
            last = typing.cast(Primitives, st_mutator.after['a'])
            print(f"DEBUG: append {last}")
            self.mutations.append(last)
            mutator.pop_strategy(f"TestPrimitives.{index}")

    def get_class_spec(self): return f"test_serializable.TestPrimitives"

    def marshal(self, visitor: traversal.Visitor):
        visitor.begin(self)
        visitor.scalar(Primitives.Factory(), self, 'blank')
        visitor.primitive(int, self, 'mutation_count')
        visitor.array(Primitives.Factory(), self, 'mutations')
        visitor.end(self)

    def test_mutate_compare(self):
        for index in range(self.mutation_count):
            self.assertTrue(comparison.cmp(self.mutations[index], self.mutations[index]) == 0)
            if index == 0:
                self.assertTrue(comparison.cmp(typing.cast(Primitives, self.blank), self.mutations[index]) != 0)
            else:
                self.assertTrue(comparison.cmp(self.mutations[index-1], self.mutations[index]) != 0, f"Expected difference was not detected while comparing {self.mutations[index-1]} vs. {self.mutations[index]} in {self.get_static_pattern_path()}")

    def get_static_pattern_path(self):
        return 'test_serializable.TestPrimitives.json'

    def setUp(self):
        if self.blank is not None:
            self.dirty = False
        elif(os.path.exists(self.get_static_pattern_path())):
            self.dirty = False
            with open(self.get_static_pattern_path(), 'rt') as fp:
                obj = json.load(fp)
                reader = json_marshal.Reader(self.Factory(), obj, {})
                self.marshal(reader)
        else:
            self.dirty = True
            self.randomize()

    def tearDown(self):
        if self.dirty:
            with open(self.get_static_pattern_path(), 'wt') as fp:
                writer = json_marshal.Writer(self.Factory(), self, {})
                writer.write()
                json.dump(writer.json, fp, indent=2)

class GenericTestVerbatim(serializable.Serializable):
    data_type: typing.Type
    dirty: bool
    blank: typing.Union[Verbatim, None]
    mutation_count: int
    mutations: typing.List[Verbatim]

    @classmethod
    def Factory(cls, data_type: typing.Type, class_spec: str = None):
        if class_spec is None:
            class_spec = f"test_serializable.GenericTestVerbatim.{str(data_type)}"
        return construction.factories.register(class_spec, lambda: construction.Factory.concrete(class_spec, lambda: cls(data_type)))

    def __init__(self, data_type: typing.Type):
        self.data_type = data_type
        self.dirty = False
        self.blank = None
        self.mutation_count = 5
        self.mutations = []

    def randomize(self):
        self.blank = Verbatim(self.data_type)
        last = self.blank
        mutator = configuration.Mutator()
        for index in range(self.mutation_count):
            st_mutator = configuration.SymbolTableMutator(mutator, {
                'a': last
            })
            st_mutator()
            last = typing.cast(Verbatim, st_mutator.after['a'])
            self.mutations.append(last)

    def get_class_spec(self): return f"test_serializable.GenericTestVerbatim.{str(self.data_type)}"

    def marshal(self, visitor: traversal.Visitor):
        visitor.begin(self)
        visitor.scalar(Verbatim.Factory(self.data_type), self, 'blank')
        visitor.primitive(int, self, 'mutation_count')
        visitor.array(Verbatim.Factory(self.data_type), self, 'mutations')
        visitor.end(self)

    def test_mutate_compare(self, test_case: unittest.TestCase, static_pattern_path: str):
        for index in range(self.mutation_count):
            test_case.assertTrue(comparison.cmp(self.mutations[index], self.mutations[index]) == 0)
            if index == 0:
                test_case.assertTrue(comparison.cmp(typing.cast(Verbatim, self.blank), self.mutations[index]) != 0, f"Expected difference was not detected while comparing <blank> vs. {index} in {static_pattern_path}")
            else:
                test_case.assertTrue(comparison.cmp(self.mutations[index-1], self.mutations[index]) != 0, f"Expected difference was not detected while comparing {index-1} vs. {index} in {static_pattern_path}")

    def setUp(self, static_pattern_path: str):
        if self.blank is not None:
            self.dirty = False
        elif(os.path.exists(static_pattern_path)):
            self.dirty = False
            with open(static_pattern_path, 'rt') as fp:
                obj = json.load(fp)
                reader = json_marshal.Reader(self.Factory(construction.factories, self.data_type), obj, {})
                self.marshal(reader)
        else:
            self.dirty = True
            self.randomize()

    def tearDown(self, static_pattern_path: str):
        if self.dirty:
            with open(static_pattern_path, 'wt') as fp:
                writer = json_marshal.Writer(self.Factory(construction.factories, self.data_type), self, {})
                writer.write()
                json.dump(writer.json, fp, indent=2)

class TestVerbatimInt(unittest.TestCase):
    generic: GenericTestVerbatim = GenericTestVerbatim(int)
    def test_mutate_compare(self): return self.generic.test_mutate_compare(self, self.get_static_pattern_path())
    def setUp(self): return self.generic.setUp(self.get_static_pattern_path())
    def tearDown(self): return self.generic.tearDown(self.get_static_pattern_path())
    def get_static_pattern_path(self):
        return 'test_serializable.TestVerbatimInt.json'

class TestVerbatimFloat(unittest.TestCase):
    generic: GenericTestVerbatim = GenericTestVerbatim(float)
    def test_mutate_compare(self): return self.generic.test_mutate_compare(self, self.get_static_pattern_path())
    def setUp(self): return self.generic.setUp(self.get_static_pattern_path())
    def tearDown(self): return self.generic.tearDown(self.get_static_pattern_path())
    def get_static_pattern_path(self):
        return 'test_serializable.TestVerbatimFloat.json'

class TestVerbatimString(unittest.TestCase):
    generic: GenericTestVerbatim = GenericTestVerbatim(str)
    def test_mutate_compare(self): return self.generic.test_mutate_compare(self, self.get_static_pattern_path())
    def setUp(self): return self.generic.setUp(self.get_static_pattern_path())
    def tearDown(self): return self.generic.tearDown(self.get_static_pattern_path())
    def get_static_pattern_path(self):
        return 'test_serializable.TestVerbatimString.json'

class TestScalar(unittest.TestCase, serializable.Serializable):
    dirty: bool
    blank: typing.Union[Scalar, None]
    mutation_count: int
    mutations: typing.List[Scalar]

    @classmethod
    def Factory(cls, class_spec: str = 'test_serializable.TestScalar'):
        return construction.factories.register(class_spec, lambda: construction.Factory.concrete(class_spec, lambda: cls()))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dirty = False
        self.blank = None
        self.mutation_count = 50
        self.mutations = []

    def randomize(self):
        self.blank = Scalar()
        last = self.blank
        mutator = configuration.Mutator()
        for index in range(self.mutation_count):
            st_mutator = configuration.SymbolTableMutator(mutator, {
                'a': last
            })
            st_mutator()
            last = typing.cast(Scalar, st_mutator.after['a'])
            self.mutations.append(last)

    def get_class_spec(self): return f"test_serializable.TestScalar"

    def marshal(self, visitor: traversal.Visitor):
        visitor.begin(self)
        visitor.scalar(Scalar.Factory(), self, 'blank')
        visitor.primitive(int, self, 'mutation_count')
        visitor.array(Scalar.Factory(), self, 'mutations')
        visitor.end(self)

    def test_mutate_compare(self):
        for index in range(self.mutation_count):
            self.assertTrue(comparison.cmp(self.mutations[index], self.mutations[index]) == 0)
            if index == 0:
                self.assertTrue(comparison.cmp(typing.cast(Scalar, self.blank), self.mutations[index]) != 0, f"Expected difference was not detected while comparing <blank> vs. {index} in {self.get_static_pattern_path()}")
            else:
                self.assertTrue(comparison.cmp(self.mutations[index-1], self.mutations[index]) != 0, f"Expected difference was not detected at {index-1} while comparing {self.mutations[index-1]} vs. {self.mutations[index]} in {self.get_static_pattern_path()}")

    def get_static_pattern_path(self):
        return 'test_serializable.TestScalar.json'

    def setUp(self):
        if self.blank is not None:
            self.dirty = False
        elif(os.path.exists(self.get_static_pattern_path())):
            self.dirty = False
            with open(self.get_static_pattern_path(), 'rt') as fp:
                obj = json.load(fp)
                reader = json_marshal.Reader(self.Factory(), obj, {})
                self.marshal(reader)
            # with open(self.get_static_pattern_path()+".output", 'wt') as fp:
            #     writer = json_marshal.Writer(self.Factory(), self, {})
            #     self.marshal(writer)
            #     json.dump(writer.json, fp, indent=2)

        else:
            self.dirty = True
            self.randomize()

    def tearDown(self):
        if self.dirty:
            with open(self.get_static_pattern_path(), 'wt') as fp:
                writer = json_marshal.Writer( self.Factory(), self, {})
                writer.write()
                json.dump(writer.json, fp, indent=2)

Property.Factory()
Verbatim.Factory(int)
Verbatim.Factory(float)
Verbatim.Factory(str)
Primitives.Factory()
Scalar.Factory()
TestPrimitives.Factory()
GenericTestVerbatim.Factory(int)
GenericTestVerbatim.Factory(float)
GenericTestVerbatim.Factory(str)
TestScalar.Factory()

if __name__ == '__main__':
    unittest.main()
