#!/usr/bin/env python3

from __future__ import annotations
import typing
import json
from . import serializable
from . import json_marshal

class Factory:
    spec_to_builder: typing.Dict[ str, serializable.Builder ]
    class_id_to_spec: typing.Dict[ int, str ]

    def __init__(self):
        self.spec_to_builder = {}
        self.class_id_to_spec = {}

    def add_builders(self, prefix: typing.List[str], builders: typing.Dict[str, serializable.Builder]):
        for suffix, builder in builders.items():
            class_spec = '.'.join(prefix + suffix.split('.'))
            if(class_spec in self.spec_to_builder):
                raise RuntimeError(f"Duplicate definition of class_spec {class_spec}")
            tmp = builder()
            self.spec_to_builder[class_spec] = builder
            self.class_id_to_spec[id(tmp.__class__)] = class_spec

    def get_class_spec(self, obj: serializable.Serializable) -> str:
        class_spec = self.class_id_to_spec.get(id(obj.__class__))
        if class_spec is None:
            raise RuntimeError(f'No class_spec for {obj.__class__.__qualname__}')
        return class_spec

    def has_class(self, class_spec: typing.Union[str, None]) -> bool:
        return class_spec is not None and class_spec in self.spec_to_builder

    def instantiate(self, class_spec:str) -> serializable.Serializable:
        return self.spec_to_builder[class_spec]()

    def to_string(self, obj:serializable.Serializable) -> str:
        return json.dumps(self.to_json(obj, []))

    def from_string(self, text: str):
        return self.from_json(json.loads(text))

    def to_json(self, obj, path: typing.List[typing.Any]):
        use_path = path or []
        if isinstance(obj, serializable.Serializable):
            writer = json_marshal.Writer(obj, self, {})
            writer.write()
            return writer.json
        elif type(obj) in (list,tuple):
            result = [ self.to_json(obj[index], use_path + [ index ]) for index in range(len(obj)) ]
            return result
        elif type(obj) in (dict,):
            result = {}
            for prop_name, value in obj.items():
                result[prop_name] = self.to_json(obj[prop_name], use_path + [ prop_name ])
            return result
        else:
            return obj

    def from_json(self, json: typing.Any):
        if self.has_class(json['__class__']):
            builder = self.spec_to_builder[json['__class__']]()
            reader = json_marshal.Reader(json, self, {})
            reader.read()
            return reader.obj
        elif type(json) in (list,tuple):
            return [ self.from_json(item) for item in json ]
        elif type(json) in (dict,):
            result = {}
            for prop_name, value in json.items():
                result[prop_name] = self.from_json(json[prop_name])
                return result
        else:
            return json
