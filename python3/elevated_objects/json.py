#!/usr/bin/env python3

from __future__ import annotations
import json
import typing
from typing import Dict, List, Any, Set, Optional, Type, TypeVar, Union, Callable

from .serializable import Serializable, Visitor
from .registry import Registry
from .builder import Builder

T = TypeVar('T', bound=Serializable)

class JsonWriter(Visitor[T]):
    """
    Visitor that serializes a Serializable object to JSON.
    
    The JsonWriter traverses the object structure and builds a JSON representation
    that can be later deserialized by JsonReader. It handles circular references
    and object identity preservation.
    """
    
    def __init__(self, obj: T, refs: Optional[Dict[str, Dict[Union[str, int], Serializable]]] = None):
        """
        Initialize the JSON writer with the object to serialize.
        
        Args:
            obj: The object to serialize
            refs: Optional dictionary to track serialized objects by class and id
        """
        self.obj = obj
        self.json: Any = None
        self.refs = refs if refs is not None else {}
        self.is_ref: Optional[bool] = None
    
    def begin(self, obj: T, parent_prop_name: Optional[str] = None) -> None:
        """
        Begin visiting an object and set up its JSON representation.
        
        Args:
            obj: The object being visited
            parent_prop_name: Optional name of the property in the parent object
        """
        self.json = {}
        
        class_spec = obj.get_class_spec()
        if class_spec not in self.refs:
            self.refs[class_spec] = {}
        
        self.json['__class__'] = class_spec
        
        # Generate object ID using identity properties
        id_writer = IdWriter()
        obj.visit(id_writer, identity_only=True)
        object_id = id_writer.get_id()
        
        if object_id:
            self.is_ref = object_id in self.refs[class_spec]
            if not self.is_ref:
                self.refs[class_spec][object_id] = obj
            self.json['__id__'] = object_id
        else:
            self.is_ref = False
        
        self.json['__is_ref__'] = self.is_ref
    
    def end(self, obj: T) -> None:
        """
        End visiting an object.
        
        Args:
            obj: The object being visited
        """
        pass
    
    def owner(self, target: T, owner_prop_name: str) -> None:
        """
        Visit the owner relationship.
        
        Args:
            target: The target object
            owner_prop_name: The property name in the owner that references this object
        """
        pass
    
    def verbatim(
        self,
        data_type: type,
        target: Serializable,
        get_value: Callable[[Serializable], Any],
        set_value: Callable[[Serializable, Any], None],
        get_prop_names: Callable[[], Set[str]]
    ) -> None:
        """
        Write a verbatim value with custom getter/setter.
        
        Args:
            data_type: The type of the data being visited
            target: The object containing the property
            get_value: A function to get the property value
            set_value: A function to set the property value
            get_prop_names: A function to get the names of all properties
        """
        if self.is_ref:
            return
        
        value = get_value(target)
        self.json = to_json(value)
    
    def primitive(
        self,
        data_type: type,
        target: Serializable,
        prop_name: str,
        from_string: Optional[Callable[[str], Any]] = None
    ) -> None:
        """
        Write a primitive property (int, float, str, etc.).
        
        Args:
            data_type: The type of the primitive data
            target: The object containing the property
            prop_name: The name of the property
            from_string: Optional function to convert from string to the data type
        """
        if self.is_ref:
            return
        
        value = getattr(target, prop_name, None)
        if value is not None:
            self.json[prop_name] = to_json(value)
    
    def property(
        self,
        prop_type: type,
        target: Serializable,
        prop_name: str,
        element_builder_type: Optional[Type[Builder]] = None,
        key_type: Optional[type] = None
    ) -> None:
        """
        Write a complex property (object, list, dictionary, etc.).
        
        Args:
            prop_type: The type of the property (e.g., list, dict, Serializable)
            target: The object containing the property
            prop_name: The name of the property
            element_builder_type: Optional builder type for elements
            key_type: Optional type for dictionary keys
        """
        if self.is_ref:
            return
        
        value = getattr(target, prop_name, None)
        if value is None:
            self.json[prop_name] = None
            return
        
        # Handle different property types
        if isinstance(value, list) or isinstance(value, tuple):
            # Array property
            array_json = []
            for item in value:
                if item is None:
                    array_json.append(None)
                elif isinstance(item, Serializable):
                    writer = JsonWriter(item, self.refs)
                    item.visit(writer)
                    array_json.append(writer.json)
                else:
                    array_json.append(to_json(item))
            self.json[prop_name] = array_json
            
        elif isinstance(value, dict):
            # Map property
            map_json = {}
            for key, item in value.items():
                str_key = str(key)  # Convert key to string for JSON
                if item is None:
                    map_json[str_key] = None
                elif isinstance(item, Serializable):
                    writer = JsonWriter(item, self.refs)
                    item.visit(writer)
                    map_json[str_key] = writer.json
                else:
                    map_json[str_key] = to_json(item)
            self.json[prop_name] = map_json
            
        elif isinstance(value, Serializable):
            # Scalar property
            writer = JsonWriter(value, self.refs)
            value.visit(writer)
            self.json[prop_name] = writer.json
            
        else:
            # Handle other types
            self.json[prop_name] = to_json(value)
    
    def write(self) -> Any:
        """
        Complete the JSON serialization process.
        
        Returns:
            The JSON representation of the object
        """
        if self.json is not None:
            return self.json
        
        self.obj.visit(self)
        return self.json


class JsonReader(Visitor[T]):
    """
    Visitor that deserializes a JSON representation back to a Serializable object.
    
    The JsonReader reconstructs the object structure from JSON, handling circular
    references and preserving object identity.
    """
    
    def __init__(self, json_data: Any, refs: Optional[Dict[str, Dict[Union[str, int], Serializable]]] = None):
        """
        Initialize the JSON reader with the JSON data to deserialize.
        
        Args:
            json_data: The JSON data to deserialize
            refs: Optional dictionary to track deserialized objects by class and id
        """
        self.json = json_data
        self.obj: Optional[T] = None
        self.refs = refs if refs is not None else {}
        self.is_ref = False
    
    def begin(self, obj: T, parent_prop_name: Optional[str] = None) -> None:
        """
        Begin visiting an object and populate it from the JSON representation.
        
        Args:
            obj: The object being visited
            parent_prop_name: Optional name of the property in the parent object
        """
        if self.obj is None:
            self.obj = obj
        
        if not isinstance(self.json, dict):
            return
        
        class_spec = obj.get_class_spec()
        if class_spec not in self.refs:
            self.refs[class_spec] = {}
        
        by_id = self.refs[class_spec]
        if '__id__' in self.json:
            obj_id = self.json['__id__']
            if obj_id in by_id:
                self.obj = typing.cast(T, by_id[obj_id])
                self.is_ref = True
            else:
                by_id[obj_id] = obj
    
    def end(self, obj: T) -> None:
        """
        End visiting an object.
        
        Args:
            obj: The object being visited
        """
        pass
    
    def owner(self, target: T, owner_prop_name: str) -> None:
        """
        Visit the owner relationship.
        
        Args:
            target: The target object
            owner_prop_name: The property name in the owner that references this object
        """
        pass
    
    def verbatim(
        self,
        data_type: type,
        target: Serializable,
        get_value: Callable[[Serializable], Any],
        set_value: Callable[[Serializable, Any], None],
        get_prop_names: Callable[[], Set[str]]
    ) -> None:
        """
        Read a verbatim value with custom getter/setter.
        
        Args:
            data_type: The type of the data being visited
            target: The object containing the property
            get_value: A function to get the property value
            set_value: A function to set the property value
            get_prop_names: A function to get the names of all properties
        """
        if self.is_ref:
            return
        
        set_value(target, from_json(self.json))
    
    def primitive(
        self,
        data_type: type,
        target: Serializable,
        prop_name: str,
        from_string: Optional[Callable[[str], Any]] = None
    ) -> None:
        """
        Read a primitive property (int, float, str, etc.).
        
        Args:
            data_type: The type of the primitive data
            target: The object containing the property
            prop_name: The name of the property
            from_string: Optional function to convert from string to the data type
        """
        if self.is_ref:
            return
        
        if not isinstance(self.json, dict) or prop_name not in self.json:
            return
        
        value = self.json[prop_name]
        if value is None:
            setattr(target, prop_name, None)
            return
        
        if isinstance(value, str) and from_string is not None:
            try:
                typed_value = from_string(value)
            except Exception:
                typed_value = value
        else:
            typed_value = value
        
        setattr(target, prop_name, typed_value)
    
    def property(
        self,
        prop_type: type,
        target: Serializable,
        prop_name: str,
        element_builder_type: Optional[Type[Builder]] = None,
        key_type: Optional[type] = None
    ) -> None:
        """
        Read a complex property (object, list, dictionary, etc.).
        
        Args:
            prop_type: The type of the property (e.g., list, dict, Serializable)
            target: The object containing the property
            prop_name: The name of the property
            element_builder_type: Optional builder type for elements
            key_type: Optional type for dictionary keys
        """
        if self.is_ref:
            return
        
        if not isinstance(self.json, dict) or prop_name not in self.json:
            return
        
        json_value = self.json[prop_name]
        if json_value is None:
            setattr(target, prop_name, None)
            return
        
        # Determine property type from hints
        if prop_type == list or prop_type == tuple or (
            isinstance(json_value, list)):
            # Array property
            if not isinstance(json_value, list):
                return
            
            result = []
            for item in json_value:
                if item is None:
                    result.append(None)
                    continue
                
                if isinstance(item, dict) and '__class__' in item and Registry.has_builder(item['__class__']):
                    reader = JsonReader(item, self.refs)
                    builder = Registry.create_builder(item['__class__'])
                    builder.visit(reader)
                    result.append(builder.done())
                else:
                    result.append(from_json(item))
            
            setattr(target, prop_name, result)
            
        elif prop_type == dict or (
            isinstance(json_value, dict) and not (
                '__class__' in json_value and Registry.has_builder(json_value['__class__'])
            )):
            # Map property
            if not isinstance(json_value, dict):
                return
            
            result = {}
            for key, item in json_value.items():
                # Convert key to appropriate type if needed
                if key_type == int:
                    try:
                        typed_key = int(key)
                    except ValueError:
                        typed_key = key
                elif key_type == float:
                    try:
                        typed_key = float(key)
                    except ValueError:
                        typed_key = key
                else:
                    typed_key = key
                
                if item is None:
                    result[typed_key] = None
                    continue
                
                if isinstance(item, dict) and '__class__' in item and Registry.has_builder(item['__class__']):
                    reader = JsonReader(item, self.refs)
                    builder = Registry.create_builder(item['__class__'])
                    builder.visit(reader)
                    result[typed_key] = builder.done()
                else:
                    result[typed_key] = from_json(item)
            
            setattr(target, prop_name, result)
            
        else:
            # Scalar property (assuming it's a Serializable object)
            if not isinstance(json_value, dict) or '__class__' not in json_value:
                setattr(target, prop_name, from_json(json_value))
                return
            
            class_spec = json_value['__class__']
            if Registry.has_builder(class_spec):
                reader = JsonReader(json_value, self.refs)
                builder = Registry.create_builder(class_spec)
                builder.visit(reader)
                setattr(target, prop_name, builder.done())
    
    def read(self) -> Optional[T]:
        """
        Complete the JSON deserialization process.
        
        Returns:
            The deserialized object, or None if deserialization failed
        """
        if self.json is None:
            return None
        
        if not isinstance(self.json, dict):
            return None
        
        class_spec = self.json.get('__class__', None)
        if not class_spec or not Registry.has_builder(class_spec):
            return None
        
        builder = Registry.create_builder(class_spec)
        builder.visit(self)
        return typing.cast(T, builder.done())


def to_json(obj: Any, path: Optional[List[Any]] = None) -> Any:
    """
    Convert a Python object to a JSON-serializable representation.
    
    Args:
        obj: The object to convert
        path: Optional path to the object in the object graph (for debugging)
        
    Returns:
        A JSON-serializable representation of the object
    """
    use_path = path or []
    
    if isinstance(obj, Serializable):
        writer = JsonWriter(obj)
        obj.visit(writer)
        return writer.json
    elif isinstance(obj, (list, tuple)):
        return [to_json(item, use_path + [i]) for i, item in enumerate(obj)]
    elif isinstance(obj, set):
        return {
            '__native__': 'Set',
            '__values__': [to_json(item, use_path + [i]) for i, item in enumerate(obj)]
        }
    elif isinstance(obj, dict):
        result = {'__native__': 'Dict'}
        for key, value in obj.items():
            result[str(key)] = to_json(value, use_path + [key])
        return result
    elif isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    else:
        # For other types, convert to string representation
        return str(obj)


def from_json(json_data: Any) -> Any:
    """
    Convert a JSON-serializable representation back to a Python object.
    
    Args:
        json_data: The JSON data to convert
        
    Returns:
        The reconstructed Python object
    """
    if json_data is None:
        return None
    
    if isinstance(json_data, dict):
        if '__class__' in json_data and Registry.has_builder(json_data['__class__']):
            reader = JsonReader(json_data)
            return reader.read()
        elif '__native__' in json_data:
            native_type = json_data['__native__']
            if native_type == 'Set':
                return set(from_json(json_data['__values__']))
            elif native_type == 'Dict':
                result = {}
                for key, value in json_data.items():
                    if key not in ('__native__',):
                        result[key] = from_json(value)
                return result
        
        # Regular dictionary
        return {key: from_json(value) for key, value in json_data.items()}
    elif isinstance(json_data, list):
        return [from_json(item) for item in json_data]
    else:
        # Primitive types
        return json_data


def serialize(obj: Serializable) -> str:
    """
    Serialize a Serializable object to a JSON string.
    
    Args:
        obj: The object to serialize
        
    Returns:
        A JSON string representation of the object
    """
    return json.dumps(to_json(obj))


def deserialize(json_str: str, class_spec: Optional[str] = None) -> Optional[Serializable]:
    """
    Deserialize a JSON string to a Serializable object.
    
    Args:
        json_str: The JSON string to deserialize
        class_spec: Optional class specification to override the one in the JSON
        
    Returns:
        The deserialized object, or None if deserialization failed
    """
    json_data = json.loads(json_str)
    
    if class_spec:
        if isinstance(json_data, dict):
            json_data['__class__'] = class_spec
        else:
            return None
    
    return from_json(json_data)