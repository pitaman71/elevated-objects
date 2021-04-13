import unittest
import datetime
import json
import os
import typing
import abc

from . import comparison
from . import configuration
from . import construction
from . import serializable
from . import json_marshal

class Primitives(serializable.Cloneable):
    prop_int: typing.Union[ int, None]
    prop_float: typing.Union[float, None]
    prop_string: typing.Union[str, None]

    def __init__(self):
        self.prop_int = None
        self.prop_float = None
        self.prop_string = None

    def clone(self, *initializers: object) -> serializable.Serializable:
        result = Primitives()
        initializer = json_marshal.Initializer(*initializers)
        result.marshal(initializer)
        return result

    def marshal(self, visitor: serializable.Visitor):
        visitor.begin(self)
        visitor.primitive(int, self, 'prop_int')
        visitor.primitive(float, self, 'prop_float')
        visitor.primitive(str, self, 'prop_string')
        visitor.end(self)

DataType = typing.TypeVar('DataType', int, float, str)

class Verbatim(serializable.Cloneable):
    data_type: typing.Type
    prop: typing.Union[ int, float, str, None]

    def __init__(self, data_type: typing.Type):
        self.data_type = data_type
        self.prop = None

    def clone(self, *initializers: object) -> serializable.Serializable:
        result = Verbatim(self.data_type)
        initializer = json_marshal.Initializer(*initializers)
        result.marshal(initializer)
        return result

    def marshal(self, visitor: serializable.Visitor):
        visitor.begin(self)
        visitor.verbatim(
            self.data_type, 
            self,
            lambda target: getattr(target, 'prop'), 
            lambda target, new_value: setattr(target, 'prop', new_value),
            lambda: {'prop'}
        )
        visitor.end(self)

factory = construction.Factory()

class TestPrimitives(unittest.TestCase, serializable.Serializable):
    dirty: bool
    blank: typing.Union[Primitives, None]
    mutation_count: int
    mutations: typing.List[Primitives]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dirty = False
        self.blank = None
        self.mutation_count = 50
        self.mutations = []

    def randomize(self):
        self.blank = Primitives()
        last = self.blank
        for index in range(self.mutation_count):
            mutator = configuration.Mutator(factory, {
                'a': last
            })
            mutator.done()
            last = typing.cast(Primitives, mutator.after['a'])
            self.mutations.append(last)

    def marshal(self, visitor: serializable.Visitor):
        visitor.begin(self)
        visitor.scalar(Primitives, self, 'blank')
        visitor.primitive(int, self, 'mutation_count')
        visitor.array(Primitives, self, 'mutations')
        visitor.end(self)

    def test_mutate_compare(self):
        for index in range(self.mutation_count):
            self.assertTrue(comparison.cmp(self.mutations[index], self.mutations[index]) == 0)
            if index == 0:
                self.assertTrue(comparison.cmp(typing.cast(Primitives, self.blank), self.mutations[index]) != 0)
            else:
                self.assertTrue(comparison.cmp(self.mutations[index-1], self.mutations[index]) != 0, f"Expected difference was not detected while comparing {index-1} vs. {index} in {self.get_static_pattern_path()}")

    def get_static_pattern_path(self):
        return 'test_serializable.TestPrimitives.json'

    def setUp(self):
        if self.blank is not None:
            self.dirty = False
        elif(os.path.exists(self.get_static_pattern_path())):
            self.dirty = False
            with open(self.get_static_pattern_path(), 'rt') as fp:
                obj = json.load(fp)
                reader = json_marshal.Reader(obj, factory, {})
                self.marshal(reader)
        else:
            self.dirty = True
            self.randomize()

    def tearDown(self):
        if self.dirty:
            with open(self.get_static_pattern_path(), 'wt') as fp:
                writer = json_marshal.Writer(self, factory, {})
                writer.write()
                json.dump(writer.json, fp, indent=2)

class GenericTestVerbatim(serializable.Serializable):
    data_type: typing.Type
    dirty: bool
    blank: typing.Union[Verbatim, None]
    mutation_count: int
    mutations: typing.List[Verbatim]

    def __init__(self, data_type: typing.Type):
        self.data_type = data_type
        self.dirty = False
        self.blank = None
        self.mutation_count = 5
        self.mutations = []

    def randomize(self):
        self.blank = Verbatim(self.data_type)
        last = self.blank
        for index in range(self.mutation_count):
            mutator = configuration.Mutator(factory, {
                'a': last
            })
            mutator.done()
            last = typing.cast(Verbatim, mutator.after['a'])
            self.mutations.append(last)

    def marshal(self, visitor: serializable.Visitor):
        visitor.begin(self)
        visitor.scalar(Verbatim, self, 'blank')
        visitor.primitive(int, self, 'mutation_count')
        visitor.array(Verbatim, self, 'mutations')
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
                reader = json_marshal.Reader(obj, factory, {})
                self.marshal(reader)
        else:
            self.dirty = True
            self.randomize()

    def tearDown(self, static_pattern_path: str):
        if self.dirty:
            with open(static_pattern_path, 'wt') as fp:
                writer = json_marshal.Writer(self, factory, {})
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

factory.add_builders([], {
    'test_serializable.Verbatim.int': lambda: Verbatim(int),
    'test_serializable.Verbatim.float': lambda: Verbatim(float),
    'test_serializable.Verbatim.str': lambda: Verbatim(str),
    'test_serializable.Primitives': lambda: Primitives(),
    'test_serializable.TestPrimitives': lambda: TestPrimitives(),
    'test_serializable.GenericTestVerbatim.int': lambda: GenericTestVerbatim(int),
    'test_serializable.GenericTestVerbatim.float': lambda: GenericTestVerbatim(float),
    'test_serializable.GenericTestVerbatim.str': lambda: GenericTestVerbatim(str)
})

if __name__ == '__main__':
    unittest.main()
