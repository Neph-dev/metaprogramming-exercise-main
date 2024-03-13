from unittest import TestCase
import unittest
from textwrap import dedent
from dataclasses import dataclass
from typing import Callable, Any, Dict


@dataclass
class Field:
    """
    Defines a field with a label and preconditions
    """
    label: str
    precondition: Callable[[Any], bool] = None

    def __set_name__(self, owner, name):
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        raise AttributeError("Read-only field")

# Record and supporting classes here


class RecordMeta(type):
    def __new__(mcs, name, bases, namespace):
        fields = {
            key: value for key, value in namespace.items() if isinstance(value, Field)
        }
        new_namespace = {**namespace, "_fields": fields}

        def __init__(self, **kwargs):
            cls_fields = {
                name: attr for cls in self.__class__.mro() for name, attr in getattr(cls, "_fields", {}).items()
            }
            annotations = {
                name: attr for cls in self.__class__.mro() for name, attr in getattr(cls, "__annotations__", {}).items()
            }

            if set(kwargs) != set(cls_fields):
                raise TypeError("Argument don't match the declared fields")

            for field_name, field_value in kwargs.items():
                field = cls_fields[field_name]

                if not isinstance(field_value, annotations[field_name]):
                    raise TypeError(f"Incorrect type for field '{field_name}'")

                if field.precondition and not field.precondition(field_value):
                    raise TypeError(
                        f"Precondition for field '{field_name}' failed")

                setattr(self, f"_{field_name}", field_value)

        new_namespace["__init__"] = __init__

        def __str__(self):
            field_strings = []

            for field_name, field in self._fields.items():
                value = getattr(self, field_name)

                field_strings.append(
                    f"  # {field.label}\n  {field_name}={value!r}\n")

            return f"{self.__class__.__name__}(\n" + "".join(field_strings) + ")"

        new_namespace["__str__"] = __str__

        return super().__new__(mcs, name, bases, new_namespace)


class Record(metaclass=RecordMeta):
    pass

# Usage of Record


class Person(Record):
    """
    A simple person record
    """
    name: str = Field(label="The name")
    age: int = Field(label="The person's age",
                     precondition=lambda x: 0 <= x <= 150)
    income: float = Field(label="The person's income",
                          precondition=lambda x: 0 <= x)


class Named(Record):
    """
    A base class for things with names
    """
    name: str = Field(label="The name")


class Animal(Named):
    """
    An animal
    """
    habitat: str = Field(label="The habitat", precondition=lambda x: x in [
                         "air", "land", "water"])
    weight: float = Field(label="The animals weight (kg)",
                          precondition=lambda x: 0 <= x)


class Dog(Animal):
    """
    A type of animal
    """
    bark: str = Field(label="Sound of bark")

# Tests


class RecordTests(TestCase):
    def test_creation(self):
        Person(name="JAMES", age=110, income=24000.0)
        with self.assertRaises(TypeError):
            Person(name="JAMES", age=160, income=24000.0)
        with self.assertRaises(TypeError):
            Person(name="JAMES")
        with self.assertRaises(TypeError):
            Person(name="JAMES", age=-1, income=24000.0)
        with self.assertRaises(TypeError):
            Person(name="JAMES", age="150", income=24000.0)
        with self.assertRaises(TypeError):
            Person(name="JAMES", age="150", wealth=24000.0)

    def test_properties(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        self.assertEqual(james.age, 34)
        with self.assertRaises(AttributeError):
            james.age = 32

    def test_str(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        correct = dedent("""
        Person(
          # The name
          name='JAMES'
          # The person's age
          age=34
          # The person's income
          income=24000.0
        )
        """).strip()
        self.assertEqual(str(james), correct)

    def test_dog(self):
        mike = Dog(name="mike", habitat="land", weight=50., bark="ARF")
        self.assertEqual(mike.weight, 50)


if __name__ == '__main__':
    unittest.main()
