[![CI](https://github.com/lmignon/extendable/actions/workflows/ci.yml/badge.svg)](https://github.com/lmignon/extendable/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/lmignon/extendable/branch/master/graph/badge.svg?token=LXD34T420H)](https://codecov.io/gh/lmignon/extendable)
# Extendable

Extendable is a module that aims to provide a way to define extensible python
classes. This module was born out of the need to find a way to allow the
definition of modules whose behaviour can be extended by other modules by
extending the initial definition of classes at runtime.

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
accordance with the [Liskov substitution principle](https://en.wikipedia.org/wiki/Liskov_substitution_principle)
It doesn't replace others design patterns that can be used to make your code pluggable.
