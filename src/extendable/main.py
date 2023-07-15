import collections
import functools
import inspect
import sys
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Type, no_type_check

if sys.version_info >= (3, 7):
    from typing import OrderedDict
else:
    from typing_extensions import OrderedDict

from abc import ABCMeta

from .context import extendable_registry
from .exceptions import RegistryNotInitializedError

_registry_build_mode = False
if TYPE_CHECKING:
    from .registry import ExtendableClassesRegistry

    AnyClassMethod = classmethod[Any, Any, Any]


class ExtendableClassDef:
    name: str
    base_names: List[str]
    namespace: Dict[str, Any]
    original_name: str
    others_bases: List[Any]
    hierarchy: List["ExtendableClassDef"]
    metaclass: "ExtendableMeta"
    original_cls: Type["ExtendableMeta"]
    kwargs: Dict[str, Any]

    def __init__(
        self,
        original_name: str,
        bases: List[Any],
        namespace: Dict[str, Any],
        metaclass: "ExtendableMeta",
        kwargs: Dict[str, Any],
    ) -> None:
        self.namespace = namespace
        self.name = namespace["__xreg_name__"]
        self.original_name = original_name
        self.others_bases = bases
        self.base_names = namespace["__xreg_base_names__"] or []
        self.hierarchy = [self]
        self.metaclass = metaclass
        self.kwargs = kwargs

    def add_child(self, cls_def: "ExtendableClassDef") -> None:
        self.hierarchy.append(cls_def)
        for name in cls_def.base_names:
            if name not in self.base_names:
                self.base_names.append(name)

    @property
    def is_mixed_bases(self) -> bool:
        return {self.name} != set(self.base_names)

    def __repr__(self) -> str:
        return (
            f"ExtendableClassDef {self.name} "
            f"{self.namespace['__module__']}.{self.namespace['__qualname__']}"
        )

    def clone(self) -> "ExtendableClassDef":
        """Clone the class definition, but not the class itself nor the information
        about the hierarchy.

        This is used to allow to recompute the registry from scratch by
        starting from the original class definition. This definition is
        then modified by the build process to define the class
        hierarchy.
        """
        clone = ExtendableClassDef(
            self.original_name,
            self.others_bases,
            self.namespace,
            self.metaclass,
            self.kwargs,
        )
        clone.original_cls = self.original_cls
        return clone


_extendable_class_defs_by_module: OrderedDict[
    str, List[ExtendableClassDef]
] = collections.OrderedDict()


def __register_class_def__(module: str, cls_def: ExtendableClassDef) -> None:
    global _extendable_class_defs_by_module
    if module not in _extendable_class_defs_by_module:
        _extendable_class_defs_by_module[module] = []
    _extendable_class_defs_by_module[module].append(cls_def)


class ExtendableMeta(ABCMeta):
    __xreg_base_names__: List[str]
    __xreg_name__: str
    __xreg_all_base_names__: Set[str]
    _is_aggregated_class: bool
    _original_cls: "ExtendableMeta"

    @no_type_check
    def __new__(metacls, name, bases, namespace, extends=None, **kwargs):
        """create the expected class and collect the class definition that will be used
        at the end of registry load process to build the final class."""
        class_def = None
        if isinstance(extends, bool) and extends:
            extends = bases[0]
        if not _registry_build_mode:
            namespace = metacls._prepare_namespace(
                name=name, bases=bases, namespace=namespace, extends=extends, **kwargs
            )
            class_def = metacls._collect_class_def(
                name=name, bases=bases, namespace=namespace, extends=extends, **kwargs
            )
            # for the original class, we wrap the class methods to forward
            # the call to the aggregated one at runtime
            namespace = metacls._wrap_class_methods(namespace)
        # We build the Origial class
        new_cls = metacls._build_original_class(
            name=name, bases=bases, namespace=namespace, **kwargs
        )
        if not _registry_build_mode and class_def:
            class_def.original_cls = new_cls
        return new_cls

    @no_type_check
    @classmethod
    def _prepare_namespace(metacls, name, bases, namespace, extends=None, **kwargs):
        registry_name = ".".join(
            (namespace["__module__"], namespace.get("__qualname__", name))
        )
        if extends:
            # if we extend another Extendable, the registry name must
            # be the one from the extended Extendable
            if not metacls._is_extendable(extends):
                raise TypeError(
                    f"Extendable class {registry_name} extends an non "
                    f"extendable class {extends.__name__} "
                )
            registry_name = getattr(extends, "__xreg_name__", None)
        registry_base_names = [
            b.__xreg_name__ for b in bases if metacls._is_extendable(b)
        ]
        namespace.update(
            {
                "__xreg_name__": registry_name,
                "__xreg_base_names__": registry_base_names,
                "_is_aggregated_class": False,
            }
        )
        return namespace

    @no_type_check
    @classmethod
    def _collect_class_def(metacls, name, bases, namespace, extends=None, **kwargs):
        # we are into the loading process of original Extendable
        # For each defined Extendable class, we keep a copy of the class
        # definition. This copy will be used to create the aggregated class
        other_bases = [b for b in bases if not metacls._is_extendable(b)]
        cls_def = ExtendableClassDef(
            original_name=name,
            bases=tuple(other_bases),
            namespace=namespace.copy(),
            metaclass=metacls,
            kwargs=kwargs,
        )
        __register_class_def__(
            namespace["__module__"],
            cls_def,
        )
        return cls_def

    @no_type_check
    @classmethod
    def _build_original_class(metacls, name, bases, namespace, **kwargs):
        """Build the original class.

        By default we call super.__new__. This method could be overriden
        if you need to create a new type mixin ExtendableMeta with
        another type. In such a case, the new type should only override
        this method to call the __new__ method on the other type.
        """
        return super().__new__(metacls, name, bases, namespace, **kwargs)

    @classmethod
    def _wrap_class_methods(metacls, namespace: Dict[str, Any]) -> Dict[str, Any]:
        """Wrap classmethods defined into the namespace to delegate the call to the
        final class."""
        new_namespace: Dict[str, Any] = {}
        for key, value in namespace.items():
            if isinstance(value, classmethod):
                new_namespace[key] = metacls._wrap_class_method(value, key)
            else:
                new_namespace[key] = value
        return new_namespace

    @classmethod
    def _is_extendable(metacls, cls: Type[Any]) -> bool:
        return issubclass(type(cls), ExtendableMeta)

    @classmethod
    def _wrap_class_method(
        metacls, method: "AnyClassMethod", method_name: str
    ) -> "AnyClassMethod":
        """Wrap a class method to delegate the call to the final class.

        In addition to preserve the signature and the docstring, this
        method will also preserve the validation of args and kwargs
        against the signature of the initial method at method call.
        """
        func = method.__func__

        @no_type_check
        def new_method(cls, *args, _method_name=None, _initial_func=None, **kwargs):
            # ensure that args and kwargs are conform to the
            # initial signature
            inspect.signature(_initial_func).bind(cls, *args, **kwargs)
            try:
                return getattr(cls._get_assembled_cls(), _method_name)(*args, **kwargs)
            except (RegistryNotInitializedError, KeyError):
                return _initial_func(cls, *args, **kwargs)

        new_method_def = functools.partial(
            new_method, _method_name=method_name, _initial_func=func
        )
        # preserve signature for IDE
        functools.update_wrapper(new_method_def, func)
        return classmethod(new_method_def)

    @no_type_check
    def __call__(cls, *args, **kwargs) -> "ExtendableMeta":
        """Create the aggregated class in place of the original class definition.

        This method called at instance creation. The resulted instance
        will be an instance of the aggregated class not an instance of
        the original class definition since this definition could have
        been extended.
        """
        if cls._is_aggregated_class:
            return super().__call__(*args, **kwargs)
        return cls._get_assembled_cls()(*args, **kwargs)

    ###############################################################
    # concrete methods provided to the final class by the metaclass
    ###############################################################

    def __subclasscheck__(cls, subclass: Any) -> bool:  # noqa: B902
        """Implement issubclass(sub, cls)."""
        if hasattr(subclass, "__xreg_all_base_names__"):
            return cls.__xreg_name__ in subclass.__xreg_all_base_names__
        return isinstance(subclass, type) and super().__subclasscheck__(subclass)

    def _get_assembled_cls(
        cls, registry: Optional["ExtendableClassesRegistry"] = None
    ) -> "ExtendableMeta":
        """An helper method to get the final class (the aggregated one) for the current
        class."""
        registry = registry if registry else extendable_registry.get()
        if not registry:
            raise RegistryNotInitializedError(
                "Extendable classes registry is not initialized"
            )
        return registry[cls.__xreg_name__]
