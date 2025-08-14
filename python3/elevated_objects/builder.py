#!/usr/bin/env python3

from __future__ import annotations
from typing import TypeVar, Generic, Optional, Any, Type

from .serializable import Serializable, Visitor

# Type variable for the built object
T = TypeVar('T')

class Builder(Generic[T]):
    """
    Base class for builders of serializable objects.
    
    The Builder pattern provides:
    1. Instance creation or modification
    2. Fluent API for property configuration
    3. Visitor pattern support
    
    Each Serializable class should have a corresponding Builder class
    that handles the creation and modification of instances.
    """
    
    def __init__(self, instance: Optional[T] = None):
        """
        Initialize the builder, optionally with an existing instance to modify.
        
        Args:
            instance: An existing instance to modify in-place. If None, a new instance will be created.
        """
        self._instance = instance or self._create_default_instance()
    
    def _create_default_instance(self) -> T:
        """
        Create a default instance of the target class.
        
        This method must be implemented by subclasses to provide a fresh instance
        of the appropriate type when no existing instance is provided.
        
        Returns:
            A new instance of the target class with default values
            
        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError("Subclasses must implement _create_default_instance")
    
    def visit(self, visitor: Visitor, identity_only: bool = False) -> Builder[T]:
        """
        Accept a visitor to process this builder's instance.
        
        This method delegates to the visit method of the instance being built,
        allowing the visitor to process the object structure.
        
        Args:
            visitor: The visitor to accept
            identity_only: If True, only visit properties that participate in the 
                         object's identity/address. If False (default), visit all properties.
            
        Returns:
            Self for method chaining
            
        Raises:
            AttributeError: If the instance does not implement the visit method
        """
        if hasattr(self._instance, 'visit'):
            self._instance.visit(visitor, identity_only)
        else:
            raise AttributeError(f"Instance of type {type(self._instance)} does not implement 'visit'")
        return self
    
    def done(self) -> T:
        """
        Complete the building process and return the built object.
        
        This method finalizes any pending operations and returns the 
        fully configured instance.
        
        Returns:
            The fully configured instance
        """
        return self._instance
    
    @staticmethod
    def register(class_spec: str):
        """
        Decorator to register a builder class with the Registry.
        
        Args:
            class_spec: The class specification string for the built class
            
        Returns:
            A decorator function that registers the builder class
            
        Example:
            @Builder.register("app.models.Person")
            class PersonBuilder(Builder[Person]):
                pass
        """
        def decorator(builder_class: Type[Builder]):
            from .registry import Registry
            Registry.register(class_spec, builder_class)
            return builder_class
        return decorator