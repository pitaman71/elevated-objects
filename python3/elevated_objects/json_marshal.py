#!/usr/bin/env python3

from __future__ import annotations
import typing
import json
import sys

from code_instruments.task import method

from . import construction
from . import serializable
from . import traversal

ExpectedType = typing.TypeVar('ExpectedType', bound=serializable.Serializable)

RefTable = typing.Dict[ typing.Union[int, str], typing.Dict[ int, serializable.Serializable ] ]

#logger=lambda x: sys.stdout.write(x+"\n")
logger=None

class Reader(traversal.Visitor[ExpectedType]):
    factory: construction.Factory[ExpectedType]
    json: typing.Any
    obj: typing.Union[ExpectedType, None]
    refs: RefTable
    is_ref: bool

    # Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    def __init__(self, factory: construction.Factory[ExpectedType], json: typing.Any, refs: RefTable):
        self.json = json
        self.obj = None
        self.factory = factory
        self.refs = refs if refs else dict()
        self.is_ref = False

    def jsonPreview(self) -> str:
        return json.dumps(self.json)[0:80]

    def begin(self, obj: ExpectedType):
        # Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next
        if self.obj is None:
            self.obj = obj

        class_name = self.factory.get_class_spec()
        if class_name not in self.refs:
            self.refs[class_name] = dict()

        by_id = self.refs[class_name]
        if type(self.json) == dict:
            if '__id__' in self.json:
                if self.json['__id__'] in by_id:
                    self.obj = typing.cast(ExpectedType, by_id[self.json['__id__']])
                    self.is_ref = True
                else:
                    by_id[self.json['__id__']] = self.obj

    def end(self, obj:ExpectedType):
        # Must be called at the end of any marshal method. Tells this object that we are done visiting the body of that object
        pass

    def owner(self, target: ExpectedType, owner_prop_name: str):
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

    def scalar(self, element_builder: construction.Factory, target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)
        if self.json is None:
            setattr(target, prop_name, None)
        elif prop_name in self.json:
            item = self.json[prop_name]
            if item is None:
                setattr(target, prop_name, None)
            else:
                reader = Reader(element_builder, self.json[prop_name], self.refs)
                reader.read()
                if reader.obj is not None:
                    setattr(target, prop_name, reader.obj)

    def array(self, element_builder: construction.Factory, target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name
        # Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if self.json is None:
            raise RuntimeError('No JSON here')
        elif prop_name in self.json:
            prop_value = self.json[prop_name]
            new_value = []
            for item in prop_value:
                if item is None:
                    new_value.append(None)
                else:
                    reader = Reader(element_builder, item, self.refs)
                    reader.read()
                    new_value.append(reader.obj)
            setattr(target, prop_name, new_value)

    def map(self, key_type: typing.Type, element_builder: construction.Factory, target: serializable.Serializable, prop_name: str) -> None:
        if self.json is None:
            raise RuntimeError('No JSON here')
        elif prop_name in self.json:
            prop_value = self.json[prop_name]
            new_value = {}
            for key, value in prop_value.items():
                if value is None:
                    new_value[key] = None
                else:
                    reader = Reader(element_builder, value, self.refs)
                    reader.read()
                    new_value[key] = reader.obj
            setattr(target, prop_name, new_value)

    def read(self):
        if type(self.json) == dict and '__class__' in self.json:
            class_spec = self.json['__class__'] 
        else:
            class_spec = self.factory.get_class_spec()
        if self.json is None:
            self.obj = None
        else:
            new_object = self.factory.make(class_spec)
            new_object.marshal(self)
            self.obj = typing.cast(ExpectedType, new_object)
            return new_object

class Writer(traversal.Visitor[ExpectedType]):
    builder: construction.Factory[ExpectedType]
    obj:ExpectedType
    json: typing.Any
    refs: RefTable
    is_ref: typing.Union[bool, None]

    # Reads in-memory representation from semi-self-describing JSON by introspecting objects using their marshal method
    def __init__(self, factory: construction.Factory[ExpectedType], obj: ExpectedType, refs: RefTable):
        self.factory = factory
        self.obj = obj
        self.json = None
        self.refs = refs if refs is not None else dict()
        self.is_ref = None

    @method(logger=logger)
    def begin(self, obj: ExpectedType):
        # Must be called at the start of any marshal method. Tells this object that we are visiting the body of that object next"""
        self.json = {}
        
        class_name = obj.__factory__.get_class_spec() if obj.__factory__ else self.factory.get_class_spec()
        if class_name not in self.refs:
            self.refs[class_name] = {}

        self.json['__class__'] = class_name
        if class_name is None:
            raise RuntimeError(f"Cannot get class spec for {type(obj)}")

        object_id = obj.get_global_id()
        if object_id is not None:
            self.is_ref = object_id in self.refs[class_name]
            if not self.is_ref:
                self.refs[class_name][object_id] = obj
        elif obj in self.refs[class_name].values():
            object_id = list(self.refs[class_name].values()).index(obj)
            self.is_ref = True
        else:
            self.is_ref = False
            object_id = len(self.refs[class_name])
            self.refs[class_name][object_id] = obj

        self.json['__id__'] = object_id
        self.json['__is_ref__'] = self.is_ref

    @method(logger=logger)
    def end(self, obj: ExpectedType):
        # Must be called at the end of any marshal method. Tells this object that we are done visiting the body of that object
        pass

    def owner(self, target: ExpectedType, owner_prop_name: str):
        pass

    @method(logger=logger)
    def verbatim(self,
        data_type: typing.Type, 
        target: serializable.Serializable, 
        get_value: typing.Callable [ [serializable.Serializable], typing.Any ],
        set_value: typing.Callable [ [serializable.Serializable, typing.Any ], None],
        get_prop_names: typing.Callable [ [], typing.Set[str] ]
    ):
        self.json = get_value(target)

    @method(logger=logger)
    def primitive(self, data_type: typing.Type, target: typing.Any, prop_name: str, fromString: typing.Callable[ [str], typing.Any] = None):
        if getattr(target, prop_name) is not None and not self.is_ref:
            self.json[prop_name] = getattr(target, prop_name)

    @method(logger=logger)
    def scalar(self, element_builder: construction.Factory[serializable.Serializable], target: typing.Any, prop_name: str):
        # For the in-memory object currently being read from JSON, read the value of attribute :attr_name from JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)
        # For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name.
        # Expect that the attribute value is probably not a reference to a shared object (though it may be)

        if self.is_ref: return

        if hasattr(target,prop_name):
            item = getattr(target,prop_name)
            if item is None:
                self.json[prop_name] = None
            else:
                writer = Writer(element_builder, item, self.refs)
                writer.write()
                self.json[prop_name] = writer.json

    @method(logger=logger)
    def array(self, element_builder: construction.Factory[serializable.Serializable], target: typing.Any, prop_name: str):
        # For the in-memory object currently being written to JSON, write the value of attribute :attr_name to JSON propery attr_name
        # Expect that the attribute value is probably a reference to a shared object (though it may not be)

        if self.is_ref: return

        if getattr(target,prop_name) is not None:
            prop_value = []
            for item in getattr(target,prop_name):
                if item is None:
                    prop_value.append(None)
                else:
                    writer = Writer(element_builder, item, self.refs)
                    writer.write()
                    prop_value.append(writer.json)
            self.json[prop_name] = prop_value

    @method(logger=logger)
    def map(self, key_type: typing.Type, element_builder: construction.Factory[serializable.Serializable], target: typing.Any, prop_name: str) -> None:
        if self.is_ref: return

        if getattr(target,prop_name) is not None:
            self.json[prop_name] = {}
            for key, value in getattr(target,prop_name).items():
                writer = Writer(element_builder, value, self.refs)
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

def to_json(factories: construction.Factories, obj: typing.Any, path: typing.List[typing.Any]):
    use_path = path or []
    if isinstance(obj, serializable.Serializable):
        writer = Writer(factories.get_builder_of(obj), {})
        writer.write()
        return writer.json
    elif type(obj) in (list,tuple):
        result = [ to_json(factories, obj[index], use_path + [ index ]) for index in range(len(obj)) ]
        return result
    elif type(obj) in (dict,):
        result = {}
        for prop_name, value in obj.items():
            result[prop_name] = to_json(factories, obj[prop_name], use_path + [ prop_name ])
        return result
    else:
        return obj

def from_json(factories: construction.Factories, json: typing.Any):
    if type(json) == dict and '__class__' in json and factories.has_class(json['__class__']):
        reader = Reader(factories.get_builder(json['__class__']), json, {})
        reader.read()
        return reader.obj
    elif type(json) in (list,tuple):
        return [ from_json(factories, item) for item in json ]
    elif type(json) == dict:
        result = {}
        for prop_name, value in json.items():
            result[prop_name] = from_json(factories, json[prop_name])
            return result
    else:
        return json

def to_string(factories: construction.Factories, obj:typing.Any) -> str:
    return json.dumps(to_json(factories, obj, []))

def from_string(factories: construction.Factories, text: str):
    return from_json(factories, json.loads(text))
