#!/usr/bin/env python3

from __future__ import annotations
import typing
import functools
import json

from . import construction
from . import serializable
from . import visitor

ExpectedType = typing.TypeVar('ExpectedType', bound=serializable.Serializable)

RefTable = typing.Dict[ str, typing.Dict[ int, serializable.Serializable ] ]
class Reader(visitor.Visitor[ExpectedType]):
    json: typing.Any
    obj: typing.Union[ExpectedType, None]
    factory: construction.Factory
    refs: RefTable
    is_ref: bool

    # Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    def __init__(self, json: typing.Any, factory: construction.Factory, refs: RefTable):
        self.json = json
        self.obj = None
        self.factory = factory
        self.refs = refs if refs else dict()
        self.is_ref = False

    def jsonPreview(self) -> str:
        return json.dumps(self.json)[0:80]

    def begin(self, obj: ExpectedType, parent_prop_name: str = None):
        # Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next
        if self.obj is None:
            self.obj = obj

        class_name = self.factory.get_class_spec(self.obj)
        if class_name not in self.refs:
            self.refs[class_name] = dict()

        by_id = self.refs[class_name]
        if type(self.json) == dict and '__id__' in self.json:
            if self.json['__id__'] in by_id:
                self.obj = typing.cast(ExpectedType, by_id[self.json['__id__']])
                self.is_ref = True
            else:
                by_id[self.json['__id__']] = self.obj

    def end(self, obj:ExpectedType):
        # Must be called at the end of any marshal method. Tells this object that we are done visiting the body of that object
        pass

    def verbatim(self,
        data_type: typing.Type, 
        target: serializable.Serializable, 
        get_value: typing.Callable [ [serializable.Serializable], typing.Any ],
        set_value: typing.Callable [ [serializable.Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)

        set_value(target, self.json)

    def primitive(self, data_type: typing.Type, target: typing.Any, prop_name: str, fromString: typing.Callable[ [str], typing.Any] = None):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)

        if self.json is None:
            raise RuntimeError('No JSON here')
        elif prop_name in self.json:
            new_value = fromString(self.json[prop_name]) if type(self.json[prop_name]) == str and  fromString is not None else self.json[prop_name]
            setattr(target, prop_name, new_value)

    def scalar(self, element_builder: construction.Builder, target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)
        if self.json is None:
            setattr(target, prop_name, None)
        elif prop_name in self.json:
            reader = Reader(self.json[prop_name], self.factory, self.refs)
            reader.read(element_builder)
            if reader.obj is not None:
                setattr(target, prop_name, reader.obj)

    def array(self, element_type: typing.Type, target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        # Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if self.json is None:
            raise RuntimeError('No JSON here')
        elif prop_name in self.json:
            prop_value = self.json[prop_name]
            new_value = []
            for item in prop_value:
                reader = Reader(item, self.factory, self.refs)
                reader.read(element_type)
                new_value.append(reader.obj)
            setattr(target, prop_name, new_value)

    def map(self, key_type: typing.Type, element_type: typing.Type, target: serializable.Serializable, prop_name: str) -> None:
        if self.json is None:
            raise RuntimeError('No JSON here')
        elif prop_name in self.json:
            prop_value = self.json[prop_name]
            new_value = {}
            for key, value in self.json[prop_name].items():
                reader = Reader(value, self.factory, self.refs)
                reader.read(element_type)
                new_value[key] = reader.obj
            setattr(target, prop_name, new_value)

    def read(self, element_builder: typing.Union[construction.Builder, None] = None):
        if type(self.json) == dict and '__class__' in self.json:
            class_spec = self.json['__class__'] 
        elif element_builder is not None:
            class_spec = self.factory.get_class_spec(element_builder.make())
        else:
            class_spec = None
        if self.json is None:
            self.obj = None
        elif class_spec is not None and self.factory.has_class(class_spec):
            new_object = self.factory.make(class_spec)
            new_object.marshal(self)
            self.obj = typing.cast(ExpectedType, new_object)
            return new_object
        else:
            raise RuntimeError(f"Cannot construct object by reading JSON: {self.jsonPreview()}")

class Writer(visitor.Visitor[ExpectedType]):
    obj:ExpectedType
    json: typing.Any
    factory: construction.Factory
    refs: RefTable
    is_ref: bool

    # Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    def __init__(self, obj: ExpectedType, factory: construction.Factory, refs: RefTable):
        self.obj = obj
        self.json = None
        self.factory = factory
        self.refs = refs if refs is not None else dict()
        self.is_ref = None

    def begin(self, obj: ExpectedType, parent_prop_name: str = None):
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

    def verbatim(self,
        data_type: typing.Type, 
        target: serializable.Serializable, 
        get_value: typing.Callable [ [serializable.Serializable], typing.Any ],
        set_value: typing.Callable [ [serializable.Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ):
        self.json = get_value(target)

    def primitive(self, data_type: typing.Type, target: typing.Any, prop_name: str, fromString: typing.Callable[ [str], typing.Any] = None):
        if getattr(target, prop_name) is not None and not self.is_ref:
            self.json[prop_name] = getattr(target, prop_name)

    def scalar(self, element_builder: construction.Builder, target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)
        # For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)

        if self.is_ref: return

        if getattr(target,prop_name) is not None and not self.is_ref:
            writer = Writer(getattr(target,prop_name), self.factory, self.refs)
            writer.write()
            self.json[prop_name] = writer.json

    def array(self, element_builder: construction.Builder, target: typing.Any, prop_name: str):
        # For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        # Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if self.is_ref: return

        if getattr(target,prop_name) is not None and not self.is_ref:
            self.json[prop_name] = []
            for item in getattr(target,prop_name):
                writer = Writer(item, self.factory, self.refs)
                writer.write()
                self.json[prop_name].append(writer.json)

    def map(self, key_type: typing.Type, element_builder: construction.Builder, target: typing.Any, prop_name: str) -> None:
        if self.is_ref: return

        if getattr(target,prop_name) is not None and not self.is_ref:
            self.json[prop_name] = {}
            for key, value in getattr(target,prop_name).items():
                writer = Writer(value, self.factory, self.refs)
                writer.write()
                self.json[prop_name][key] = writer.json

    def write(self):
        if self.json is not None:
            pass
        elif isinstance(self.obj, serializable.Serializable):
            self.obj.marshal(self)
        else:
            self.json = self.obj

        return self.json

def to_json(factory: construction.Factory, obj, path: typing.List[typing.Any]):
    use_path = path or []
    if isinstance(obj, serializable.Serializable):
        writer = Writer(obj, factory, {})
        writer.write()
        return writer.json
    elif type(obj) in (list,tuple):
        result = [ to_json(factory, obj[index], use_path + [ index ]) for index in range(len(obj)) ]
        return result
    elif type(obj) in (dict,):
        result = {}
        for prop_name, value in obj.items():
            result[prop_name] = to_json(factory, obj[prop_name], use_path + [ prop_name ])
        return result
    else:
        return obj

def from_json(factory: construction.Factory, json: typing.Any):
    if type(json) == dict and '__class__' in json and factory.has_class(json['__class__']):
        reader = Reader(json, factory, {})
        reader.read()
        return reader.obj
    elif type(json) in (list,tuple):
        return [ from_json(factory, item) for item in json ]
    elif type(json) == dict:
        result = {}
        for prop_name, value in json.items():
            result[prop_name] = from_json(factory, json[prop_name])
            return result
    else:
        return json

def to_string(factory: construction.Factory, obj:serializable.Serializable) -> str:
    return json.dumps(to_json(factory, obj, []))

def from_string(factory: construction.Factory, text: str):
    return from_json(factory, json.loads(text))
