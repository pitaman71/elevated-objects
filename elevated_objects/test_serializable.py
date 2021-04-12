import unittest
import datetime
import json
import os
import typing

from . import comparison
from . import configuration
from . import construction
from . import serializable
from . import json_marshal

class Record(serializable.Cloneable):
    prop_int: typing.Union[ int, None]
    prop_float: typing.Union[float, None]
    prop_string: typing.Union[str, None]
    #prop_datetime: typing.Union[datetime.datetime, None]

    def __init__(self):
        self.prop_int = None
        self.prop_float = None
        self.prop_string = None
        #self.prop_datetime = None

    def clone(self, *initializers: object) -> serializable.Serializable:
        result = Record()
        initializer = json_marshal.Initializer(*initializers)
        result.marshal(initializer)
        return result

    def marshal(self, visitor: serializable.Visitor):
        visitor.begin(self)
        visitor.primitive(int, self, 'prop_int')
        visitor.primitive(float, self, 'prop_float')
        visitor.primitive(str, self, 'prop_string')
        #visitor.primitive(datetime.datetime, self, 'prop_datetime')
        visitor.end(self)

factory = construction.Factory()

class TestAll(unittest.TestCase, serializable.Serializable):
    dirty: bool
    blank: typing.Union[Record, None]
    mutation_count: int
    mutations: typing.List[Record]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dirty = False
        self.blank = None
        self.mutation_count = 50
        self.mutations = []

    def randomize(self):
        self.blank = Record()
        last = self.blank
        for index in range(self.mutation_count):
            mutator = configuration.Mutator(factory, {
                'a': last
            })
            mutator.done()
            last = typing.cast(Record, mutator.after['a'])
            self.mutations.append(last)

    def marshal(self, visitor: serializable.Visitor):
        visitor.begin(self)
        visitor.scalar(Record, self, 'blank')
        visitor.primitive(int, self, 'mutation_count')
        visitor.array(Record, self, 'mutations')
        visitor.end(self)

    def test_mutate_compare(self):
        for index in range(self.mutation_count):
            self.assertTrue(comparison.cmp(self.mutations[index], self.mutations[index]) == 0)
            if index == 0:
                self.assertTrue(comparison.cmp(typing.cast(Record, self.blank), self.mutations[index]) != 0)
            else:
                self.assertTrue(comparison.cmp(self.mutations[index-1], self.mutations[index]) != 0)

    def get_static_pattern_path(self):
        return 'test_serializable.TestAll.json'

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

factory.add_builders([], {
    'test_serializable.Record': lambda: Record(),
    'test_serializable.TestAll': lambda: TestAll()
})

if __name__ == '__main__':
    unittest.main()
