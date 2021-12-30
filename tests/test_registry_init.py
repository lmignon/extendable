"""Test registry loading."""
from extendable.registry import ExtendableClassesRegistry, ExtendableRegistryListener


def test_init_order_1(test_registry, sys_modules_cleanup):
    """By default the order used to build the class hierarchy is the one of the initial
    import order."""
    from tests.mod_base.base import Base  # NOQA isort:skip
    import tests.mod_ext1  # NOQA isort:skip
    import tests.mod_ext2  # NOQA isort:skip

    test_registry.init_registry()
    assert Base().test() == "mod2.mod1.base"


def test_init_order_2(test_registry, sys_modules_cleanup):
    """By default the order used to build the class hierarchy is the one of the initial
    import order."""
    from tests.mod_base.base import Base  # NOQA isort:skip
    import tests.mod_ext2  # NOQA isort:skip
    import tests.mod_ext1  # NOQA isort:skip

    test_registry.init_registry()
    assert Base().test() == "mod1.mod2.base"


def test_init_registry_specific_modules(test_registry, sys_modules_cleanup):
    """Ensure that only specified modules are taken into when loading the registry."""
    from tests.mod_base.base import Base  # NOQA isort:skip
    import tests.mod_ext2  # NOQA isort:skip
    import tests.mod_ext1  # NOQA isort:skip

    test_registry.init_registry(["tests.mod_base.*", "tests.mod_ext1.*"])
    assert Base().test() == "mod1.base"


def test_init_registry_specific_modules_order_1(test_registry, sys_modules_cleanup):
    """Ensure that the import order is taken into accoun the registry is build for a
    list of specific modules."""
    from tests.mod_base.base import Base  # NOQA isort:skip
    import tests.mod_ext2  # NOQA isort:skip
    import tests.mod_ext1  # NOQA isort:skip

    test_registry.init_registry(["tests.mod_*"])
    assert Base().test() == "mod1.mod2.base"


def test_init_registry_specific_modules_order_2(test_registry, sys_modules_cleanup):
    """Ensure that the import order is taken into accoun the registry is build for a
    list of specific modules."""
    from tests.mod_base.base import Base  # NOQA isort:skip
    import tests.mod_ext1  # NOQA isort:skip
    import tests.mod_ext2  # NOQA isort:skip

    test_registry.init_registry(["tests.mod_*"])
    assert Base().test() == "mod2.mod1.base"


def test_init_registry_specific_modules_order_3(test_registry, sys_modules_cleanup):
    """Ensure that the import order is taken into accoun the registry is build for a
    list of specific modules."""
    from tests.mod_base.base import Base  # NOQA isort:skip
    import tests.mod_ext1  # NOQA isort:skip
    import tests.mod_ext2  # NOQA isort:skip

    test_registry.init_registry(
        ["tests.mod_base.*", "tests.mod_ext2.*", "tests.mod_ext1.*"]
    )
    assert Base().test() == "mod1.mod2.base"


def test_init_registry_listener(test_registry, mocker):
    """Check that our listener is called a the end of registry initialisation."""
    from tests.mod_base.base import Base  # NOQA isort:skip
    import tests.mod_ext1  # NOQA isort:skip
    import tests.mod_ext2  # NOQA isort:skip

    test_registry.init_registry()

    class MyLister(ExtendableRegistryListener):
        pass

    listener = MyLister()
    try:
        listeners = ExtendableClassesRegistry.listeners.copy()
        ExtendableClassesRegistry.listeners.append(listener)
        mocker.patch.object(MyLister, "on_registry_initialized")
        test_registry.init_registry()
        listener.on_registry_initialized.assert_called_with(test_registry)
    finally:
        ExtendableClassesRegistry.listeners = listeners
