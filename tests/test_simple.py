from typing import Union

import pytest

from extendable import context, models, registry


@pytest.fixture
def test_registry() -> registry.ExtendableClassesRegistry:
    reg = registry.ExtendableClassesRegistry()
    try:
        token = context.extendable_registry.set(reg)
        yield reg
    finally:
        context.extendable_registry.reset(token)


def test_simple_extends(test_registry):
    class A(models.Extendable):
        prop_a: int = 1

        def sum(self) -> int:
            return self.prop_a

        @classmethod
        def cls_sum(cls) -> int:
            return 2

    class B(A, extends=A):
        prop_b: int = 2

        def sum(self) -> int:
            s = super()
            return s.sum() + self.prop_b

        @classmethod
        def cls_sum(cls) -> int:
            return super().cls_sum() + 3

    test_registry.init_registry()

    result: Union[A, B] = A()
    assert isinstance(result, A)
    assert isinstance(result, B)
    assert result.prop_b == 2
    assert result.prop_a == 1
    assert result.sum() == 3
    assert A.cls_sum() == 5


def test_composite_extends(test_registry):
    class Coordinate(models.Extendable):
        lat = 0.1
        lng = 10.1

    class Name(models.Extendable):
        name: str = "name"

    class Location(Coordinate, Name):
        pass

    class NameExtended(Name, extends=Name):
        alias: str = "alias"

    class NameExtended2(NameExtended, extends=Name):
        pass

    test_registry.init_registry()

    loc = Location()
    assert loc.alias == "alias"
    assert loc.lat == 0.1
    assert isinstance(loc, Name)
    assert isinstance(loc, Coordinate)
    assert isinstance(loc, NameExtended)
    assert isinstance(loc, NameExtended2)


def test_composite_extends_mro(test_registry):
    class A(models.Extendable):
        def test(self):
            return "A"

    class B(models.Extendable):
        def test(self):
            return "B"

    class AB(A, B):
        pass

    class BA(B, A):
        pass

    test_registry.init_registry()

    ab = AB()
    assert ab.test() == "A"

    ba = BA()
    assert ba.test() == "B"


def test_extended_composite_mro(test_registry):
    class A(models.Extendable):
        def test(self):
            return "A"

    class B(models.Extendable):
        def test(self):
            return "B"

    class C(models.Extendable):
        def test(self):
            return "C"

    class AB(A, B):
        pass

    class ABExt(C, extends=AB):
        pass

    test_registry.init_registry()

    obj = ABExt()
    assert obj.test() == "C"
