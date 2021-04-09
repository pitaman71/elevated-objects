#!/usr/bin/env python3

from __future__ import annotations
import inspect
import abc
import enum
import typing
import functools
import json

from . import serializable

ExpectedType = typing.TypeVar('ExpectedType', bound=serializable.Serializable)

class Initializer(serializable.Visitor[ExpectedType]):
    initializers: typing.List[typing.Any]
    obj: ExpectedType

    def begin(self, obj: ExpectedType, parent_prop_name: str|None):
        self.obj = obj

    def end(self, obj: ExpectedType):
        pass

    def __init__(self, *initializers: typing.List[typing.Any]):
        self.initializers = list(initializers)

    def verbatim(self, data_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        host = serializable.Primitive(data_type, target, prop_name)
        new_value = functools.reduce(
            lambda result, initializer: initializer or result,
            self.initializers,
            None)
        if new_value is not None:
            host.set_value(new_value)

    def primitive(self, data_type: typing.Type, target, prop_name: str, fromString: typing.Callable[ [str], typing.Any]):
        host = serializable.Primitive(data_type, target, prop_name)
        new_value = functools.reduce(
            lambda result, initializer: initializer[prop_name] or result,
            self.initializers,
            None)
        if new_value is not None:
            typed_value = fromString(new_value) if type(new_value) == str and fromString is not None else new_value
            host.set_value(typed_value)

    def scalar(self, element_type: typing.Type, target, prop_name: str):
        host = serializable.Scalar(element_type, target, prop_name)
        new_values = [
            initializer[prop_name] for initializer in self.initializers if prop_name in initializer
        ]
        if len(new_values) == 1:
            return host.set_value(new_values[0])
        elif len(new_values) > 1:
            return host.set_value(new_values[0].clone(*new_values))

    def array(self, element_type: typing.Type, target, prop_name: str):
        host = serializable.ArrayProp(element_type, target, prop_name)
        has_property = [
            initializer for initializer in self.initializers if prop_name in initializer
        ]
        max_length = functools.reduce(
            lambda result, initializer:
                max(len(initializer[prop_name]), result),
            has_property, 0)

        if max_length > 0:
            new_array_value = []
            for index in range(max_length):
                element_values = [ initializer[index] for initializer in has_property if len(initializer) > index and initializer[index] is not None ]
                new_element_value = element_values[0].clone(*element_values) if len(element_values) > 0 else None
                new_array_value.append(new_element_value)
            host.set_value(new_array_value)

    def init(self, target: serializable.Serializable):
        target.marshal(self)

RefTable = typing.Dict[ str, typing.Dict[ int, serializable.Serializable ] ]
class Reader(serializable.Visitor[ExpectedType]):
    json: typing.Any
    obj: ExpectedType|None
    factory: serializable.Factory
    refs: RefTable
    is_ref: bool

    # Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    def __init__(self, json: typing.Any, factory: serializable.Factory, refs: RefTable):
        self.json = json
        self.factory = factory
        self.refs = refs if refs else dict()
        self.is_ref = False

    def jsonPreview(self) -> str:
        return json.dumps(self.json)[0:80]

    def begin(self, obj: ExpectedType):
        # Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next
        if self.obj is None:
            self.obj = obj

        if '__class__' not in self.json:
            raise RuntimeError(f"Expected __class__ to be present in JSON. Properties included ${self.json.keys()}")

        class_name = self.json['__class__']
        if class_name not in self.refs:
            self.refs[class_name] = dict()

        by_id = self.refs[class_name]
        if '__id__' in self.json:
            if self.json['__id__'] in by_id:
                self.obj = typing.cast(ExpectedType, by_id[self.json['__id__']])
                self.is_ref = True
            else:
                by_id[self.json['__id__']] = self.obj

    def end(self, obj:ExpectedType):
        # Must be called at the end of any marshal method. Tells this object that we are done visiting the body of that object
        pass

    def verbatim(self, data_type: typing.Type, target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)

        host = serializable.Primitive(data_type, target, prop_name)
        if self.json is None:
            raise RuntimeError('No JSON here')
        else:
            host.set_value(self.json)

    def primitive(self, data_type: typing.Type, target: typing.Any, prop_name: str, fromString: typing.Callable[ [str], typing.Any]):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)

        host = serializable.Primitive(data_type, target, prop_name)
        if self.json is None:
            raise RuntimeError('No JSON here')
        elif host.prop_name in self.json:
            new_value = fromString(self.json[prop_name]) if type(self.json[prop_name]) == str and  fromString is not None else self.json[prop_name]
            host.set_value(new_value)

    def scalar(self, element_type: typing.Type, target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)
        host = serializable.Scalar(element_type, target, prop_name)
        if self.json is None:
            raise RuntimeError('No JSON here')
        elif host.prop_name in self.json:
            reader = Reader(self.json[host.prop_name], self.factory, self.refs)
            reader.read()
            if reader.obj is not None:
                host.set_value(reader.obj)

    def array(self, element_type: typing.Type, target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        # Expect that the attribute value is probably a reference to a shared object (though it may not be)

        host = serializable.ArrayProp(element_type, target, prop_name)
        if self.json is None:
            raise RuntimeError('No JSON here')
        elif host.prop_name in self.json:
            prop_value = self.json[host.prop_name]
            new_value = []
            for item in prop_value:
                reader = Reader(item, self.factory, self.refs)
                reader.read()
                new_value.append(reader.obj)
            host.set_value(new_value)

    def map(self, key_type: typing.Type, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        host = serializable.MapProp(element_type, target, prop_name)
        if self.json is None:
            raise RuntimeError('No JSON here')
        elif host.prop_name in self.json:
            prop_value = self.json[host.prop_name]
            new_value = {}
            for key, value in self.json[host.prop_name].items():
                reader = Reader(value, self.factory, self.refs)
                reader.read()
                new_value[key] = reader.obj
            host.set_value(new_value)

    def read(self):
        klass = self.json['__class__']
        if self.factory.has_class(klass):
            new_object = self.factory.instantiate(klass)
            new_object.marshal(self)
            self.obj = typing.cast(ExpectedType, new_object)
            return new_object
        else:
            raise RuntimeError(f"Cannot construct object by reading JSON: {self.jsonPreview()}")

class Writer(serializable.Visitor[ExpectedType]):
    obj:ExpectedType
    json: typing.Any
    factory: serializable.Factory
    refs: RefTable
    is_ref: bool

    # Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    def __init__(self, obj: ExpectedType, factory: serializable.Factory, refs: RefTable):
        self.obj = obj
        self.factory = factory
        self.refs = refs if refs is not None else dict()

    def begin(self, obj: ExpectedType):
        # Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next"""
        self.json = {}
        
        class_name = self.factory.get_class_spec(obj)
        if class_name not in self.refs:
            self.refs[class_name] = {}

        self.json['__class__'] = class_name
        if class_name is None:
            raise RuntimeError(f"Cannot find class name for {type(obj)} with builders {self.factory.spec_to_builder.keys()}")

        if self.is_ref is None:
            if id(obj) in self.refs[class_name]:
                self.is_ref = True
            else:
                self.is_ref = False
                self.refs[class_name][id(obj)] = obj

        self.json['__id__'] = id(obj)
        self.json['__is_ref__'] = self.is_ref

    def end(self, obj: ExpectedType):
        # Must be called at the end of any marshal method. Tells this object that we are done visiting the body of that object
        pass

    def verbatim(self, data_type: typing.Type, target: typing.Any, prop_name: str):
        host = serializable.Primitive(data_type, target, prop_name)
        if host.value is not None and not self.is_ref:
            self.json = host.value

    def primitive(self, data_type: typing.Type, target: typing.Any, prop_name: str, fromString: typing.Callable[ [str], typing.Any]):
        host = serializable.Primitive(data_type, target, prop_name)
        if host.value is not None and not self.is_ref:
            self.json[host.prop_name] = host.value

    def scalar(self, element_type: typing.Type, target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)
        host = serializable.Scalar(element_type, target, prop_name)
        # For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)

        if host.value is not None and not self.is_ref:
            writer = Writer(host.value, self.factory, self.refs)
            writer.write()
            self.json[host.prop_name] = writer.json

    def array(self, element_type: typing.Type, target: typing.Any, prop_name: str):
        # For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        # Expect that the attribute value is probably a reference to a shared object (though it may not be)

        host = serializable.ArrayProp(element_type, target, prop_name)
        if host.value is not None and not self.is_ref:
            self.json[host.prop_name] = []
            for item in host.value:            
                writer = Writer(item, self.factory, self.refs)
                writer.write()
                self.json[host.prop_name].append(writer.json)

    def map(self, key_type: typing.Type, element_type: typing.Type, target: typing.Any, prop_name: str) -> None:
        host = serializable.MapProp(element_type, target, prop_name)
        if host.value is not None and not self.is_ref:
            self.json[host.prop_name] = {}
            for key, value in host.value.items():
                writer = Writer(value, self.factory, self.refs)
                writer.write()
                self.json[host.prop_name][key] = writer.json

    def write(self):
        if self.json is not None:
            pass
        elif isinstance(self.obj, serializable.Serializable):
            self.obj.marshal(self)
        else:
            self.json = self.obj

        return self.json
