#!/usr/bin/env python3

from typing import List, Dict, Optional, Any
from elevated_objects import Serializable, Visitor, Builder, Registry, serialize, deserialize

class Address(Serializable):
    """Example Address class implementing the Serializable protocol."""
    
    def __init__(self, street: str = "", city: str = "", postal_code: str = ""):
        self.street = street
        self.city = city
        self.postal_code = postal_code
    
    def visit(self, visitor: Visitor, identity_only: bool = False) -> None:
        visitor.begin(self)
        
        # These properties participate in identity
        visitor.primitive(str, self, "street")
        visitor.primitive(str, self, "city")
        visitor.primitive(str, self, "postal_code")
        
        visitor.end(self)
    
    def get_class_spec(self) -> str:
        return "examples.Address"
    
    def __str__(self) -> str:
        return f"{self.street}, {self.city}, {self.postal_code}"


class Person(Serializable):
    """Example Person class implementing the Serializable protocol."""
    
    def __init__(self, name: str = "", age: int = 0, address: Optional[Address] = None, 
                 contacts: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.age = age
        self.address = address
        self.contacts = contacts or []
        self.metadata = metadata or {}
    
    def visit(self, visitor: Visitor, identity_only: bool = False) -> None:
        visitor.begin(self)
        
        # These properties participate in identity
        visitor.primitive(str, self, "name")
        
        # If we only need identity properties, stop here
        if identity_only:
            visitor.end(self)
            return
            
        # These properties don't participate in identity
        visitor.primitive(int, self, "age")
        visitor.property(Address, self, "address", AddressBuilder)
        visitor.property(list, self, "contacts")
        visitor.property(dict, self, "metadata", key_type=str)
        
        visitor.end(self)
    
    def get_class_spec(self) -> str:
        return "examples.Person"
    
    def __str__(self) -> str:
        address_str = str(self.address) if self.address else "No address"
        return f"Person(name='{self.name}', age={self.age}, address={address_str})"


@Builder.register("examples.Address")
class AddressBuilder(Builder[Address]):
    """Builder for Address objects."""
    
    def _create_default_instance(self) -> Address:
        return Address()
    
    def with_street(self, street: str) -> 'AddressBuilder':
        self._instance.street = street
        return self
    
    def with_city(self, city: str) -> 'AddressBuilder':
        self._instance.city = city
        return self
    
    def with_postal_code(self, postal_code: str) -> 'AddressBuilder':
        self._instance.postal_code = postal_code
        return self


@Builder.register("examples.Person")
class PersonBuilder(Builder[Person]):
    """Builder for Person objects."""
    
    def _create_default_instance(self) -> Person:
        return Person()
    
    def with_name(self, name: str) -> 'PersonBuilder':
        self._instance.name = name
        return self
    
    def with_age(self, age: int) -> 'PersonBuilder':
        self._instance.age = age
        return self
    
    def with_address(self, address: Address) -> 'PersonBuilder':
        self._instance.address = address
        return self
    
    def add_contact(self, contact: str) -> 'PersonBuilder':
        self._instance.contacts.append(contact)
        return self
    
    def with_metadata(self, key: str, value: Any) -> 'PersonBuilder':
        self._instance.metadata[key] = value
        return self


def main():
    """Example usage of the Elevated Objects framework."""
    
    # Create an address using its builder
    address = AddressBuilder()\
        .with_street("123 Main St")\
        .with_city("Anytown")\
        .with_postal_code("12345")\
        .done()
    
    # Create a person using its builder
    person = PersonBuilder()\
        .with_name("John Doe")\
        .with_age(30)\
        .with_address(address)\
        .add_contact("john@example.com")\
        .add_contact("555-1234")\
        .with_metadata("created_at", "2023-01-01")\
        .with_metadata("role", "admin")\
        .done()
    
    # Serialize to JSON
    json_str = serialize(person)
    print("Serialized JSON:")
    print(json_str)
    print()
    
    # Deserialize from JSON
    deserialized_person = deserialize(json_str)
    print("Deserialized Person:")
    print(deserialized_person)
    
    # Create another person with the same name (identity property)
    # This should be treated as a reference to the same logical object
    duplicate_person = PersonBuilder()\
        .with_name("John Doe")\
        .with_age(40)  # Different age, but same identity
    
    # Serialize both persons to show reference handling
    persons = [person, duplicate_person.done()]
    json_list = serialize(persons)
    print("\nSerialized list with duplicate person:")
    print(json_list)
    
    # Modify the deserialized person using a builder
    modified_person = PersonBuilder(deserialized_person)\
        .with_age(31)\
        .add_contact("john.doe@example.com")\
        .done()
    
    print("\nModified Person:")
    print(modified_person)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3

from typing import List, Dict, Optional, Any
from elevated_objects import Serializable, Visitor, Builder, Registry, serialize, deserialize

class Address(Serializable):
    """Example Address class implementing the Serializable protocol."""
    
    def __init__(self, street: str = "", city: str = "", postal_code: str = ""):
        self.street = street
        self.city = city
        self.postal_code = postal_code
    
    def visit(self, visitor: Visitor) -> None:
        visitor.begin(self)
        visitor.primitive(str, self, "street")
        visitor.primitive(str, self, "city")
        visitor.primitive(str, self, "postal_code")
        visitor.end(self)
    
    def get_global_id(self) -> Optional[str]:
        return None  # No global ID for this example
    
    def get_class_spec(self) -> str:
        return "examples.Address"
    
    def __str__(self) -> str:
        return f"{self.street}, {self.city}, {self.postal_code}"


class Person(Serializable):
    """Example Person class implementing the Serializable protocol."""
    
    def __init__(self, name: str = "", age: int = 0, address: Optional[Address] = None, 
                 contacts: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.age = age
        self.address = address
        self.contacts = contacts or []
        self.metadata = metadata or {}
    
    def visit(self, visitor: Visitor) -> None:
        visitor.begin(self)
        visitor.primitive(str, self, "name")
        visitor.primitive(int, self, "age")
        
        # Using the new property method for complex types
        visitor.property(Address, self, "address", AddressBuilder)
        visitor.property(list, self, "contacts")
        visitor.property(dict, self, "metadata", key_type=str)
        
        visitor.end(self)
    
    def get_global_id(self) -> Optional[str]:
        return None  # No global ID for this example
    
    def get_class_spec(self) -> str:
        return "examples.Person"
    
    def __str__(self) -> str:
        address_str = str(self.address) if self.address else "No address"
        return f"Person(name='{self.name}', age={self.age}, address={address_str})"


@Builder.register("examples.Address")
class AddressBuilder(Builder[Address]):
    """Builder for Address objects."""
    
    def _create_default_instance(self) -> Address:
        return Address()
    
    def with_street(self, street: str) -> 'AddressBuilder':
        self._instance.street = street
        return self
    
    def with_city(self, city: str) -> 'AddressBuilder':
        self._instance.city = city
        return self
    
    def with_postal_code(self, postal_code: str) -> 'AddressBuilder':
        self._instance.postal_code = postal_code
        return self


@Builder.register("examples.Person")
class PersonBuilder(Builder[Person]):
    """Builder for Person objects."""
    
    def _create_default_instance(self) -> Person:
        return Person()
    
    def with_name(self, name: str) -> 'PersonBuilder':
        self._instance.name = name
        return self
    
    def with_age(self, age: int) -> 'PersonBuilder':
        self._instance.age = age
        return self
    
    def with_address(self, address: Address) -> 'PersonBuilder':
        self._instance.address = address
        return self
    
    def add_contact(self, contact: str) -> 'PersonBuilder':
        self._instance.contacts.append(contact)
        return self
    
    def with_metadata(self, key: str, value: Any) -> 'PersonBuilder':
        self._instance.metadata[key] = value
        return self


def main():
    """Example usage of the Elevated Objects framework."""
    
    # Create an address using its builder
    address = AddressBuilder()\
        .with_street("123 Main St")\
        .with_city("Anytown")\
        .with_postal_code("12345")\
        .done()
    
    # Create a person using its builder
    person = PersonBuilder()\
        .with_name("John Doe")\
        .with_age(30)\
        .with_address(address)\
        .add_contact("john@example.com")\
        .add_contact("555-1234")\
        .with_metadata("created_at", "2023-01-01")\
        .with_metadata("role", "admin")\
        .done()
    
    # Serialize to JSON
    json_str = serialize(person)
    print("Serialized JSON:")
    print(json_str)
    print()
    
    # Deserialize from JSON
    deserialized_person = deserialize(json_str)
    print("Deserialized Person:")
    print(deserialized_person)
    
    # Modify the deserialized person using a builder
    modified_person = PersonBuilder(deserialized_person)\
        .with_age(31)\
        .add_contact("john.doe@example.com")\
        .done()
    
    print("\nModified Person:")
    print(modified_person)


if __name__ == "__main__":
    main()