# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
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
from .utils import ClassAttribute

_is_extendable_class_defined = False
_registry_build_mode = False
if TYPE_CHECKING:
    from .registry import ExtendableClassesRegistry


class ExtendableClassDef:
    name: str
    base_names: Set[str]
    namespace: Dict[str, Any]
    original_name: str
    others_bases: List[Any]
    hierarchy: List["ExtendableClassDef"]

    def __init__(
        self, original_name: str, bases: List[Any], namespace: Dict[str, Any]
    ) -> None:
        self.namespace = namespace
        self.name = namespace["__xreg_name__"].value
        self.original_name = original_name
        self.others_bases = bases
        self.base_names = set(namespace["__xreg_base_names__"].value or [])
        self.hierarchy = [self]

    def add_child(self, cls_def: "ExtendableClassDef") -> None:
        self.hierarchy.append(cls_def)
        self.base_names.update(cls_def.base_names)

    @property
    def is_mixed_bases(self) -> bool:
        return {self.name} != self.base_names

    def __repr__(self) -> str:
        return (
            f"ExtendableClassDef {self.name} "
            f"{self.namespace['__module__']}.{self.namespace['__qualname__']}"
        )


_extendable_class_defs_by_module: OrderedDict[
    str, List[ExtendableClassDef]
] = collections.OrderedDict()


def __register__(module: str, cls_def: ExtendableClassDef) -> None:
    global _extendable_class_defs_by_module
    if module not in _extendable_class_defs_by_module:
        _extendable_class_defs_by_module[module] = []
    _extendable_class_defs_by_module[module].append(cls_def)


class ExtendableMeta(ABCMeta):
    @no_type_check
    def __new__(cls, clsname, bases, namespace, extends=None, **kwargs):
        """create a expected class and a fragment class that will be assembled at the
        end of registry load process to build the final class."""
        new_namespace = namespace
        if _is_extendable_class_defined and "_is_aggregated_class" not in namespace:
            registry_name = ".".join(
                (namespace["__module__"], namespace["__qualname__"])
            )
            if extends:
                # if we extend another Extendable, the registry name must
                # be the one from the extended Extendable
                if not issubclass(extends, Extendable):
                    raise TypeError(
                        f"Extendable class {registry_name} extends an non "
                        f"extendable class {extends.__name__} "
                    )
                registry_name = getattr(extends, "__xreg_name__", None)
            registry_base_names = [
                b.__xreg_name__
                for b in bases
                if issubclass(b, Extendable) and b != Extendable
            ]
            namespace.update(
                {
                    "__xreg_name__": ClassAttribute("__xreg_name__", registry_name),
                    "__xreg_base_names__": ClassAttribute(
                        "__xreg_base_names__", registry_base_names
                    ),
                }
            )
            # for the original class, we wrap the class methods to forward
            # the call to the aggregated one at runtime
            new_namespace = cls._wrap_class_methods(namespace)
        # We build the Origial class
        new_cls = super().__new__(
            cls, name=clsname, bases=bases, namespace=new_namespace, **kwargs
        )
        if _is_extendable_class_defined and not _registry_build_mode:
            # we are into the loading process of original Extendable
            # For each defined Extendable class, we keep a copy of the class
            # definition. This copy will be used to create the aggregated class
            other_bases = [Extendable] + [
                b for b in bases if not (issubclass(b, Extendable))
            ]
            namespace.update({"_original_cls": new_cls})
            __register__(
                namespace["__module__"],
                ExtendableClassDef(
                    original_name=clsname, bases=tuple(other_bases), namespace=namespace
                ),
            )
        return new_cls

    @classmethod
    def _wrap_class_methods(cls, namespace: Dict[str, Any]) -> Dict[str, Any]:
        new_namespace = {}
        for key, value in namespace.items():
            if isinstance(value, classmethod):
                func = value.__func__

                @no_type_check
                def new_method(
                    cls, *args, _method_name=None, _initial_func=None, **kwargs
                ):
                    # ensure that arggs and kwargs are conform to the
                    # initial signature
                    inspect.signature(_initial_func).bind(cls, *args, **kwargs)
                    return getattr(cls._get_assembled_cls(), _method_name)(
                        *args, **kwargs
                    )

                new_method_def = functools.partial(
                    new_method, _method_name=key, _initial_func=func
                )
                # preserve signature for IDE
                functools.update_wrapper(new_method_def, func)
                new_namespace[key] = classmethod(new_method_def)
            else:
                new_namespace[key] = value
        return new_namespace

    def __subclasscheck__(cls, subclass: Any) -> bool:  # noqa: B902
        """Implement issubclass(sub, cls)."""
        if hasattr(subclass, "_original_cls"):
            return cls.__subclasscheck__(subclass._original_cls)
        return isinstance(subclass, type) and super().__subclasscheck__(subclass)


class Extendable(metaclass=ExtendableMeta):
    __xreg_base_names__: List[str]
    __xreg_name__: str

    @no_type_check
    def __new__(cls, *args, **kwargs) -> "Extendable":
        if getattr(cls, "_is_aggregated_class", False):
            return super().__new__(cls)
        return cls._get_assembled_cls()(*args, **kwargs)

    @classmethod
    def _get_assembled_cls(
        cls, registry: Optional["ExtendableClassesRegistry"] = None
    ) -> Type["Extendable"]:
        if getattr(cls, "_is_aggregated_class", False):
            return cls
        registry = registry if registry else extendable_registry.get()
        return registry[cls.__xreg_name__]


_is_extendable_class_defined = True
