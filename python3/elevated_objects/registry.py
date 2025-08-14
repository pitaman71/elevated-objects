#!/usr/bin/env python3

from __future__ import annotations
from typing import Dict, Type, List, Optional, Any, TypeVar, Generic, Set, ClassVar

# Type variable for the built object
T = TypeVar('T')

# Forward reference to Builder
class Builder:
    pass

class Registry:
    """
    Central registry for locating Builder classes by serializable class name.
    
    This registry provides:
    1. Builder class registration by class specification
    2. Builder class lookup by class specification
    3. Builder instance creation
    4. Version validation (future functionality)
    
    The Registry serves as a central point of access for all Builder classes,
    allowing for discovery and instantiation without knowing specific builder classes.
    """
    
    # Class variable to store registered builders
    _builders: ClassVar[Dict[str, Type[Builder]]] = {}
    
    @classmethod
    def register(cls, class_spec: str, builder_class: Type[Builder]) -> None:
        """
        Register a builder class for a given class specification.
        
        Args:
            class_spec: A string that uniquely identifies a serializable class
            builder_class: The builder class for that serializable class
        """
        cls._builders[class_spec] = builder_class
    
    @classmethod
    def get_builder_class(cls, class_spec: str) -> Type[Builder]:
        """
        Get the builder class for the specified class.
        
        Args:
            class_spec: A string that uniquely identifies a serializable class
            
        Returns:
            The builder class for that serializable class
            
        Raises:
            ValueError: If no builder is registered for the class specification
        """
        if class_spec not in cls._builders:
            raise ValueError(f"No builder registered for {class_spec}")
        return cls._builders[class_spec]
    
    @classmethod
    def create_builder(cls, class_spec: str, instance: Optional[Any] = None) -> Builder:
        """
        Create a builder instance for the specified class.
        
        Args:
            class_spec: A string that uniquely identifies a serializable class
            instance: An optional existing instance to modify
            
        Returns:
            A builder instance for the specified class
            
        Raises:
            ValueError: If no builder is registered for the class specification
        """
        builder_class = cls.get_builder_class(class_spec)
        return builder_class(instance)
    
    @classmethod
    def has_builder(cls, class_spec: str) -> bool:
        """
        Check if a builder is registered for the specified class.
        
        Args:
            class_spec: A string that uniquely identifies a serializable class
            
        Returns:
            True if a builder is registered, False otherwise
        """
        return class_spec in cls._builders
    
    @classmethod
    def get_registered_classes(cls) -> List[str]:
        """
        Get a list of all registered class specifications.
        
        Returns:
            A list of class specification strings
        """
        return list(cls._builders.keys())
    
    @classmethod
    def validate_version(cls, class_spec: str, version: str) -> bool:
        """
        Validate if the specified version of a class is supported.
        
        Args:
            class_spec: A string that uniquely identifies a serializable class
            version: The version string to validate
            
        Returns:
            True if the version is supported, False otherwise
            
        Note:
            This is a placeholder for future functionality
        """
        # Future functionality for version validation
        return True