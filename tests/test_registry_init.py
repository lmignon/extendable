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


def test_built_classes_repr(test_registry, sys_modules_cleanup):
    """The classes built by the registry keep the name of the original class but their
    representation shows their level into the hierarchy and the class definition they
    come from."""
    from tests.mod_base.base import Base  # NOQA isort:skip
    import tests.mod_ext1  # NOQA isort:skip
    import tests.mod_ext2  # NOQA isort:skip

    test_registry.init_registry()
    mro = type(Base()).__mro__
    assert [cls.__qualname__ for cls in mro[:3]] == ["Base", "Base", "Base"]
    assert [repr(cls) for cls in mro[:3]] == [
        "<class 'tests.mod_ext2.base.Base' #2 (tests.mod_ext2.base.ExtBase)>",
        "<class 'tests.mod_ext1.base.Base' #1 (tests.mod_ext1.base.ExtBase)>",
        "<class 'tests.mod_base.base.Base' #0>",
    ]
    # the original classes keep the default representation
    assert repr(Base) == "<class 'tests.mod_base.base.Base'>"


def _assert_built_on_final_mixin(registry: ExtendableClassesRegistry) -> None:
    final_b = registry["tests.mod_mixin.b.B"]
    final_m = registry["tests.mod_mixin.m.M"]
    # the class is built on the final class of its mixin, including its extension
    assert final_m in final_b.__mro__
    assert final_b().ext()


def test_class_loaded_before_its_mixin(test_registry, sys_modules_cleanup, mocker):
    """A class waiting for its mixin is built once, on the final mixin."""
    import tests.mod_mixin.b  # NOQA isort:skip
    import tests.mod_mixin.mext  # NOQA isort:skip

    spy = mocker.spy(test_registry, "build_extendable_class")
    test_registry.init_registry(
        [
            "tests.mod_mixin.a",
            "tests.mod_mixin.b",
            "tests.mod_mixin.m",
            "tests.mod_mixin.mext",
        ]
    )
    # A, M (with its extension) and B are each built once
    assert spy.call_count == 3
    _assert_built_on_final_mixin(test_registry)


def test_mixin_extended_by_a_new_init(test_registry, sys_modules_cleanup):
    """When an extension of a mixin is loaded by a new initialization of the
    registry, the classes using the mixin are rebuilt."""
    import tests.mod_mixin.b  # NOQA isort:skip
    import tests.mod_mixin.mext  # NOQA isort:skip

    test_registry.init_registry(
        ["tests.mod_mixin.a", "tests.mod_mixin.m", "tests.mod_mixin.b"]
    )
    test_registry.init_registry(["tests.mod_mixin.mext"])
    _assert_built_on_final_mixin(test_registry)
