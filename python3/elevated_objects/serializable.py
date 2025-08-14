#!/usr/bin/env python3

from __future__ import annotations
from typing import Protocol, TypeVar, Optional, Any, Union, Generic

T = TypeVar('T', bound='Serializable')

class Visitor(Protocol, Generic[T]):
    """
    Protocol defining the visitor interface for traversing serializable objects.
    
    The visitor pattern allows for operations to be performed on an object structure
    without modifying the classes of the objects on which it operates. This is useful
    for operations like serialization, validation, and data transformation.
    """
    
    def begin(self, obj: T, parent_prop_name: Optional[str] = None) -> None:
        """
        Begin visiting an object. Called at the start of traversal.
        
        Args:
            obj: The object being visited
            parent_prop_name: Optional name of the property in the parent object
        """
        ...
    
    def end(self, obj: T) -> None:
        """
        End visiting an object. Called at the end of traversal.
        
        Args:
            obj: The object being visited
        """
        ...
    
    def owner(self, target: T, owner_prop_name: str) -> None:
        """
        Visit the owner relationship.
        
        Args:
            target: The target object
            owner_prop_name: The property name in the owner that references this object
        """
        ...
    
    def verbatim(
        self, 
        data_type: type, 
        target: 'Serializable', 
        get_value: callable[[Serializable], Any],
        set_value: callable[[Serializable, Any], None],
        get_prop_names: callable[[], set[str]]
    ) -> None:
        """
        Visit a verbatim value with custom getter/setter.
        
        This method allows for custom handling of properties that don't fit
        the standard property access pattern.
        
        Args:
            data_type: The type of the data being visited
            target: The object containing the property
            get_value: A function to get the property value
            set_value: A function to set the property value
            get_prop_names: A function to get the names of all properties
        """
        ...
    
    def primitive(
        self, 
        data_type: type, 
        target: 'Serializable', 
        prop_name: str, 
        from_string: Optional[callable[[str], Any]] = None
    ) -> None:
        """
        Visit a primitive property (int, float, str, etc.).
        
        Args:
            data_type: The type of the primitive data
            target: The object containing the property
            prop_name: The name of the property
            from_string: Optional function to convert from string to the data type
        """
        ...
    
    def property(
        self, 
        prop_type: type, 
        target: 'Serializable', 
        prop_name: str,
        element_builder_type: Optional[type] = None,
        key_type: Optional[type] = None
    ) -> None:
        """
        Visit a complex property (object, list, dictionary, etc.).
        
        This method handles scalar, array, and map properties based on the type
        of the property.
        
        Args:
            prop_type: The type of the property (e.g., list, dict, Serializable)
            target: The object containing the property
            prop_name: The name of the property
            element_builder_type: Optional builder type for elements (needed for Serializable elements)
            key_type: Optional type for dictionary keys (only needed for dictionaries)
        """
        ...


class Serializable(Protocol):
    """
    Protocol defining the interface for serializable objects.
    
    Serializable objects can:
    1. Visit themselves with a visitor pattern
    2. Report their class specification
    
    This protocol should be implemented by any class that needs to be
    serialized, compared, or otherwise introspected by the elevated_objects
    framework.
    """
    
    def visit(self, visitor: Visitor[Any], identity_only: bool = False) -> None:
        """
        Accept a visitor to traverse this object's structure.
        
        This method should call the appropriate visitor methods for each
        property of the object, allowing the visitor to process the object
        structure without modifying the object classes.
        
        Args:
            visitor: The visitor to accept
            identity_only: If True, only visit properties that participate in the 
                          object's identity/address. If False (default), visit all properties.
        """
        ...
    
    def get_class_spec(self) -> str:
        """
        Get the class specification string for this object.
        
        This string should uniquely identify the class, and should be consistent
        across different runs of the program and different environments.
        
        Returns:
            A string that uniquely identifies this class
        """
        ...