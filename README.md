[![CI](https://github.com/lmignon/extendable/actions/workflows/ci.yml/badge.svg)](https://github.com/lmignon/extendable/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/lmignon/extendable/branch/master/graph/badge.svg?token=LXD34T420H)](https://codecov.io/gh/lmignon/extendable)
# Extendable

## About

Extendable is a module that aims to provide a way to define extensible python
classes. It is designed to provide developers with a convenient and flexible way
to extend the functionality of their Python applications. By leveraging the "extendable"
library, developers can easily create modular and customizable components that
can be added or modified without modifying the core codebase. This library utilizes
Python's object-oriented programming features and provides a simple and intuitive
interface for extending and customizing applications. It aims to enhance code
reusability, maintainability, and overall development efficiency. It implements
the extension by inheritance and composition pattern. It's inspired by the way
odoo implements its models. Others patterns can be used to make your code pluggable
and this library doesn't replace them.

## Quick start

Let's define a first python class.

```python
from extendable import ExtendableMeta

class Person(metaclass=ExtendableMeta):

    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return self.name

```

Someone using the module where the class is defined would need to extend the
person definition with a firstname field.

```python
from extendable import ExtendableMeta

class PersonExt(Person, extends=Person):
    def __init__(self, name: str):
        super().__init__(name)
        self._firstname = None

    @property
    def firstname(self) -> str:
        return self._firstname

    @firstname.setter
    def firstname(self, value:str) -> None:
        self._firstname = value

    def __repr__(self) -> str:
        res = super().__repr__()
        return f"{res}, {self.firstname or ''}"
```
At this time we have defined that `PersonExt` extends the initial definition
of `Person`. To finalyse the process, we need to instruct the runtime that
all our class declarations are done by building the final class definitions and
making it available into the current execution context.

```python
from extendable import context, registry

_registry = registry.ExtendableClassesRegistry()
context.extendable_registry.set(_registry)
_registry.init_registry()

```

Once it's done the `Person` and `PersonExt` classes can be used interchangeably
into your code since both represent the same class...

```python
p = Person("Mignon")
p.firstname = "Laurent"
print (p)
#> Mignon, Laurent
```

> :warning: This way of extending a predefined behaviour must be used carefully and in
> accordance with the [Liskov substitution principle](https://en.wikipedia.org/wiki/Liskov_substitution_principle)
> It doesn't replace others design patterns that can be used to make your code pluggable.

## How it works

 Behind the scenes, the "extendable" library utilizes several key concepts and
 mechanisms to enable its functionality. Overall, the "extendable" library leverages
 metaclasses, registry initialization, and dynamic loading to provide a flexible
 and modular approach to extending Python classes. By utilizing these mechanisms,
 developers can easily enhance the functionality of their applications without
 the need for extensive modifications to the core codebase.

### Metaclasses

The metaclass do 2 things.

* It collects the definitions of the declared class and gathers information about
  its attributes, methods, and other characteristics. These definitions are stored
  in a global registry by module. This registry is a map of module name to a list
  of class definitions.
* This information is then used to build a class object that acts as a proxy or
  blueprint for the actual concrete class that will be created later when the registry
  is initialized based on the aggregated definition of all the classes declared
  to extend the initial class...

### Registry initialization

The registry initialization is the process that build the final class definition.
To make your blueprint class work, you need to initialize the registry. This is
done by calling the `init_registry` method of the registry object. This method
will build the final class definition by aggregating all the definitions of the
classes declared to extend the initial class through a class hierarchy. The
order of the classes in the hierarchy is important. This order is by default
the order in which the classes are loaded by the python interpreter. For advanced
usage, you can change this order or even the list of definitions used to build the
final class definition. This is done by calling the `init_registry` method with
the list of modules[^1] to load as argument.

[^1]: When you specify a module into the list of modules to load, the wildcart
      character `*` is allowed at the end of the module name to load all the
      submodules of the module. Otherwise, only the module itself is loaded.

```python
from extendable import registry

_registry = registry.ExtendableClassesRegistry()
_registry.init_registry(["module1", "module2.*"])
```

Once the registry is initialized, it must be made available into the current
execution context so the blueprint class can use it. To do so you must set the
registry into the `extendable_registry` context variable. This is done by
calling the `set` method of the `extendable_registry` context variable.

```python
from extendable import context, registry

_registry = registry.ExtendableClassesRegistry()
context.extendable_registry.set(_registry)
_registry.init_registry()
```

### Dynamic loading

All of this is made possible by the dynamic loading capabilities of Python.
The concept of dynamic loading in Python refers to the ability to load and execute
code at runtime, rather than during the initial compilation or execution phase.
It allows developers to dynamically import and use modules, classes, functions
or variables based on certain conditions or user input. The dynamic loading
can also be applied at class instantiation time. This is the mechanism used by
the "extendable" library to instantiate the final class definition when you call
the constructor of the blueprint class. This is done by implementing the
`__call__` method into the metaclass to return the final class definition instead
of the blueprint class itself. The same applies to pretend that the blueprint
class is the final class definition through the implementation of the `__subclasscheck__`
method into the metaclass.

## Development

To run tests, use `tox`. You will get a test coverage report in `htmlcov/index.html`.
An easy way to install tox is `pipx install tox`.

This project uses pre-commit to enforce linting (among which black for code formating,
isort for sorting imports, and mypy for type checking).

To make sure linters run locally on each of your commits, install pre-commit
(`pipx install pre-commit` is recommended), and run `pre-commit install` in your
local clone of the extendable repository.

To release:

 * run ``bumpversion patch|minor|major` --list`
 * Check the `new_version` value returned by the previous command
 * run `towncrier build`.
 * Inspect and commit the updated HISTORY.rst.
 * `git tag {new_version} ; git push --tags`.

## Contributing

All kind of contributions are welcome.
