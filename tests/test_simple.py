from typing import Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from extendable import ExtendableMeta


def test_simple_extends(test_registry):
    class A(metaclass=ExtendableMeta):
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
    assert isinstance(result.__class__, ExtendableMeta)


def test_simple_extends_with_boolean(test_registry):
    class A(metaclass=ExtendableMeta):
        prop_a: int = 1

        def sum(self) -> int:
            return self.prop_a

        @classmethod
        def cls_sum(cls) -> int:
            return 2

    class B(A, extends=True):
        prop_b: int = 2

        def sum(self) -> int:
            s = super()
            return s.sum() + self.prop_b

        @classmethod
        def cls_sum(cls) -> int:
            return super().cls_sum() + 3

    class C(A, extends=True):
        prop_c: int = 3

        def sum(self) -> int:
            s = super()
            return s.sum() + self.prop_c

        @classmethod
        def cls_sum(cls) -> int:
            return super().cls_sum() + 4

    test_registry.init_registry()

    result: Union[A, B, C] = A()
    assert isinstance(result, A)
    assert isinstance(result, B)
    assert isinstance(result, C)
    assert result.prop_c == 3
    assert result.prop_b == 2
    assert result.prop_a == 1
    assert result.sum() == 6
    assert A.cls_sum() == 9
    assert isinstance(result.__class__, ExtendableMeta)


def test_simple_extends_same_class(test_registry):
    class A(metaclass=ExtendableMeta):
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

    class C(A, extends=A):
        prop_c: int = 3

        def sum(self) -> int:
            s = super()
            return s.sum() + self.prop_c

        @classmethod
        def cls_sum(cls) -> int:
            return super().cls_sum() + 4

    test_registry.init_registry()

    result: Union[A, B, C] = A()
    assert isinstance(result, A)
    assert isinstance(result, B)
    assert isinstance(result, C)
    assert result.prop_c == 3
    assert result.prop_b == 2
    assert result.prop_a == 1
    assert result.sum() == 6
    assert A.cls_sum() == 9
    assert isinstance(result.__class__, ExtendableMeta)


def test_extends_new_model(test_registry):
    class A(metaclass=ExtendableMeta):
        value: int = 2

        def method(self):
            return self.value

    class B(A):  # no extends, I want two different models here
        value2: int = 3

        def method(self):
            return super().method() + self.value2

    # we extend A after the definition of B
    class AExt(A, extends=A):
        def method(self):
            return super().method() + 1

    test_registry.init_registry()
    # The result should take into account AExt
    assert B().method() == 6


def test_composite_extends(test_registry):
    class Coordinate(metaclass=ExtendableMeta):
        lat = 0.1
        lng = 10.1

    class Name(metaclass=ExtendableMeta):
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
    class A(metaclass=ExtendableMeta):
        def test(self):
            return "A"

    class B(metaclass=ExtendableMeta):
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
    class A(metaclass=ExtendableMeta):
        def test(self):
            return "A"

    class B(metaclass=ExtendableMeta):
        def test(self):
            return "B"

    class C(metaclass=ExtendableMeta):
        def test(self):
            return "C"

    class AB(A, B):
        pass

    class ABExt(C, extends=AB):
        pass

    test_registry.init_registry()

    obj = ABExt()
    assert obj.test() == "C"


def test_issubclass(test_registry):
    """In this test we check that issublass is lenient when used with GenericAlias."""

    class A(metaclass=ExtendableMeta):
        pass

    test_registry.init_registry()

    assert not issubclass(Literal["test"], A)
    assert not issubclass(Literal, A)


def test_meta_subclass():
    class MyMeta(ExtendableMeta):
        pass

    class MyExt(metaclass=MyMeta):
        pass

    assert MyMeta._is_extendable(MyExt)


def test_mixin_inheritance(test_registry):
    class BaseMixin(metaclass=ExtendableMeta):
        def test(self):
            return "base"

    class MixinA(BaseMixin):
        def test_a(self):
            return "A"

    class MixinB(BaseMixin):
        def test_b(self):
            return "B"

    class ExtendedB(MixinB, extends=True):
        def test_b(self):
            res = super().test_b()
            return res + " extended"

    class Mixin(MixinA, MixinB, extends=MixinB):
        pass

    test_registry.init_registry()

    obj = Mixin()
    assert obj.test() == "base"
    assert obj.test_a() == "A"
    assert obj.test_b() == "B extended"


def test_issubclass_multi_level(test_registry):
    class A(metaclass=ExtendableMeta):
        pass

    class B(A):
        pass

    class C(B):
        pass

    test_registry.init_registry()

    assert issubclass(C, B)
    assert issubclass(C().__class__, B)
    assert issubclass(C().__class__, B().__class__)
    assert issubclass(C, B().__class__)
    assert issubclass(C, A)
    assert issubclass(C().__class__, A)
    assert issubclass(C, A().__class__)
    assert issubclass(C().__class__, A().__class__)
    assert issubclass(B, A)
    assert issubclass(B().__class__, A)
    assert issubclass(B().__class__, A().__class__)
    assert issubclass(B, A().__class__)


def test_isinstance_multi_level(test_registry):
    class A(metaclass=ExtendableMeta):
        pass

    class B(A):
        pass

    class C(B):
        pass

    test_registry.init_registry()

    assert isinstance(C(), B)
    assert isinstance(C(), B().__class__)
    assert isinstance(C(), A)
    assert isinstance(C(), A().__class__)
    assert isinstance(B(), A)
    assert isinstance(B(), A().__class__)


def test_isinstance_no_extend(test_registry):
    # in this test our class are not extended
    # we chech that the isinstance works as expected
    # when we have no extends by the classes
    # are extendable by default
    class A(metaclass=ExtendableMeta):
        pass

    class B(A):
        pass

    test_registry.init_registry()

    assert isinstance(A(), A)
    assert isinstance(B(), A)
    assert isinstance(B(), B)
    assert isinstance(B(), A().__class__)
    assert isinstance(B(), B().__class__)
