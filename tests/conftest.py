import collections
import sys

import pytest

from extendable import context, main, registry


@pytest.fixture
def test_registry() -> registry.ExtendableClassesRegistry:
    reg = registry.ExtendableClassesRegistry()
    initial_class_defs = main._extendable_class_defs_by_module
    try:
        main._extendable_class_defs_by_module = collections.OrderedDict()
        token = context.extendable_registry.set(reg)
        yield reg
    finally:
        main._extendable_class_defs_by_module = initial_class_defs
        context.extendable_registry.reset(token)


@pytest.fixture
def sys_modules_cleanup() -> None:
    keys = [k for k in sys.modules.keys() if k.startswith("tests.mod_")]
    for k in keys:
        del sys.modules[k]
    try:
        yield
    finally:
        keys = [k for k in sys.modules.keys() if k.startswith("tests.mod_")]
        for k in keys:
            del sys.modules[k]
