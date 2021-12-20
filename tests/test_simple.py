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


def test_basic_extends(test_registry):
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
