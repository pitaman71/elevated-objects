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
from . import visitor

class Primitives(serializable.Cloneable):
    prop_int: typing.Union[ int, None ]
    prop_float: typing.Union[ float, None ]
    prop_string: typing.Union[ str, None ]

    @classmethod
    def Builder(cls):
        return construction.Builder(lambda: Primitives())

    def __init__(self):
        self.prop_int = None
        self.prop_float = None
        self.prop_string = None

    def clone(self, *initializers: object) -> serializable.Serializable:
        result = Primitives()
        initializer = json_marshal.Initializer(*initializers)
        result.marshal(initializer)
        return result

    def marshal(self, visitor: visitor.Visitor):
        visitor.begin(self)
        visitor.primitive(int, self, 'prop_int')
        visitor.primitive(float, self, 'prop_float')
        visitor.primitive(str, self, 'prop_string')
        visitor.end(self)

DataType = typing.TypeVar('DataType', int, float, str)

class Verbatim(serializable.Cloneable):
    data_type: typing.Type
    prop: typing.Union[ int, float, str, None]

    @classmethod
    def Builder(cls, data_type: typing.Type):
        return construction.Builder(lambda: Verbatim(data_type))

    def __init__(self, data_type: typing.Type):
        self.data_type = data_type
        self.prop = None

    def clone(self, *initializers: object) -> serializable.Serializable:
        result = Verbatim(self.data_type)
        initializer = json_marshal.Initializer(*initializers)
        result.marshal(initializer)
        return result

    def marshal(self, visitor: visitor.Visitor):
        visitor.begin(self)
        visitor.verbatim(
            self.data_type, 
            self,
            lambda target: getattr(target, 'prop'), 
            lambda target, new_value: setattr(target, 'prop', new_value),
            lambda: {'prop'}
        )
        visitor.end(self)

class Scalar(serializable.Cloneable):
    prop_primitives: typing.Union[Primitives, None]
    prop_verbatim: typing.Union[Verbatim, None]

    @classmethod
    def Builder(cls):
        construction.Builder(lambda: Scalar())

    def __init__(self):
        self.prop_primitives = None

    def clone(self, *initializers: object) -> serializable.Serializable:
        result = self.__class__()
        initializer = json_marshal.Initializer(*initializers)
        result.marshal(initializer)
        return result

    def marshal(self, visitor: visitor.Visitor):
        visitor.begin(self)
        visitor.scalar(Primitives.Builder(), self, 'prop_primitives')
        visitor.end(self)

factory = construction.Factory()

class TestPrimitives(unittest.TestCase, serializable.Serializable):
    dirty: bool
    blank: typing.Union[Primitives, None]
    mutation_count: int
    mutations: typing.List[Primitives]

    @classmethod
    def Builder(cls):
        return construction.Builder(lambda: TestPrimitives())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dirty = False
        self.blank = None
        self.mutation_count = 50
        self.mutations = []

    def randomize(self):
        self.blank = Primitives()
        last = self.blank
        mutator = configuration.Mutator(factory)
        for index in range(self.mutation_count):
            st_mutator = configuration.SymbolTableMutator(mutator, {
                'a': last
            })
            st_mutator.done()
            last = typing.cast(Primitives, st_mutator.after['a'])
            self.mutations.append(last)

    def marshal(self, visitor: visitor.Visitor):
        visitor.begin(self)
        visitor.scalar(Primitives.Builder(), self, 'blank')
        visitor.primitive(int, self, 'mutation_count')
        visitor.array(Primitives.Builder(), self, 'mutations')
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

    @classmethod
    def Builder(cls, data_type: typing.Type):
        return construction.Builder(lambda: GenericTestVerbatim(data_type))

    def __init__(self, data_type: typing.Type):
        self.data_type = data_type
        self.dirty = False
        self.blank = None
        self.mutation_count = 5
        self.mutations = []

    def randomize(self):
        self.blank = Verbatim(self.data_type)
        last = self.blank
        mutator = configuration.Mutator(factory)
        for index in range(self.mutation_count):
            st_mutator = configuration.SymbolTableMutator(mutator, {
                'a': last
            })
            st_mutator.done()
            last = typing.cast(Verbatim, st_mutator.after['a'])
            self.mutations.append(last)

    def marshal(self, visitor: visitor.Visitor):
        visitor.begin(self)
        visitor.scalar(Verbatim.Builder(self.data_type), self, 'blank')
        visitor.primitive(int, self, 'mutation_count')
        visitor.array(Verbatim.Builder(self.data_type), self, 'mutations')
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

class TestScalar(unittest.TestCase, serializable.Serializable):
    dirty: bool
    blank: typing.Union[Scalar, None]
    mutation_count: int
    mutations: typing.List[Scalar]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dirty = False
        self.blank = None
        self.mutation_count = 50
        self.mutations = []

    def randomize(self):
        self.blank = Scalar()
        last = self.blank
        mutator = configuration.Mutator(factory)
        for index in range(self.mutation_count):
            st_mutator = configuration.SymbolTableMutator(mutator, {
                'a': last
            })
            st_mutator.done()
            last = typing.cast(Scalar, st_mutator.after['a'])
            self.mutations.append(last)

    def marshal(self, visitor: visitor.Visitor):
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
        return 'test_serializable.TestScalar.json'

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

factory.add_value_makers(['test_serializable'], {
    'Verbatim.int': lambda: Verbatim(int),
    'Verbatim.float': lambda: Verbatim(float),
    'Verbatim.str': lambda: Verbatim(str),
    'Primitives': lambda: Primitives(),
    'Scalar': lambda: Scalar(),
    'TestPrimitives': lambda: TestPrimitives(),
    'GenericTestVerbatim.int': lambda: GenericTestVerbatim(int),
    'GenericTestVerbatim.float': lambda: GenericTestVerbatim(float),
    'GenericTestVerbatim.str': lambda: GenericTestVerbatim(str),
    #'TestScalar': lambda: TestScalar()
})

if __name__ == '__main__':
    unittest.main()
