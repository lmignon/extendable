# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Set, Type, cast

from . import models
from .utils import ClassAttribute, LastOrderedSet


class ExtendableClassesRegistry:
    """Store all the extendableClasses and allow to retrieve them by name.

    The key is the ``cls.__module__ + "." + cls.__qualname__`` of the
    extendable classes.

    The :attr:`ready` attribute must be set to ``True`` when all the extendable classes
    are loaded.
    """

    def __init__(self) -> None:
        self._extendable_classes: Dict[str, Type[models.Extendable]] = {}
        self._loaded_modules: Set[str] = set()
        self.ready: bool = False
        self._extendable_class_defs: Dict[str, models.ExtendableClassDef] = {}

    def __getitem__(self, key: str) -> Type[models.Extendable]:
        return self._extendable_classes[key]

    def __setitem__(self, key: str, value: Type[models.Extendable]) -> None:
        self._extendable_classes[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._extendable_classes

    def get(self, key: str, default: Any = ...) -> Type[models.Extendable]:
        return self._extendable_classes.get(key, default)

    def __iter__(self) -> Iterator[str]:
        return self._extendable_classes.__iter__()

    def load_extendable_classes(self, module: str) -> None:
        if module in self._loaded_modules:
            return
        for cls_def in models._extendable_class_defs_by_module.get(module, []):
            self.load_extendable_class_def(cls_def)
        self._loaded_modules.add(module)

    def load_extendable_class_def(self, cls_def: models.ExtendableClassDef) -> None:
        parents = cls_def.base_names
        if cls_def.name in self and not parents:
            raise TypeError(
                f"extendable {cls_def.name} (in class def {cls_def}) already exists."
            )
        class_def = self._extendable_class_defs.get(cls_def.name)
        if not class_def:
            self._extendable_class_defs[cls_def.name] = cls_def
        else:
            class_def.add_child(cls_def)

    def build_extendable_classes(self) -> None:
        """, We iterate over all the class definitions and build the final hierarchy."""
        # we first check that all bases are defined
        for class_def in self._extendable_class_defs.values():
            for base in class_def.base_names:
                if base not in self._extendable_class_defs:
                    raise TypeError(
                        f"extendable class '{class_def.name}' inherits from"
                        f"undefined base '{base}'"
                    )
        to_build = self._extendable_class_defs.items()
        while to_build:
            remaining = []
            for name, class_def in self._extendable_class_defs.items():
                if not class_def.is_mixed_bases:
                    self.build_extendable_class(class_def)
                    continue
                # Generate only class with all the bases into the registry
                all_in_registry = True
                for base in class_def.base_names:
                    if base == name:
                        continue
                    if base not in self:
                        all_in_registry = False
                        break
                if all_in_registry:
                    self.build_extendable_class(class_def)
                    continue
                remaining.append((name, class_def))
            to_build = remaining  # type: ignore

    def build_extendable_class(
        self, class_def: models.ExtendableClassDef
    ) -> Type[models.Extendable]:
        """Build the class hierarchy from the first one to the last one into the
        hierachy definition."""
        name = class_def.name
        for idx, cls_def in enumerate(class_def.hierarchy):
            # retrieve extendable_parent
            # determine all the classes the component should inherit from
            bases = LastOrderedSet[Type[models.Extendable]]()
            for base_name in cls_def.base_names:
                if base_name not in self:
                    if idx != 0 or base_name != cls_def.name:
                        raise TypeError(
                            f"Pydnatic class '{name}' extends an non-existing "
                            f"extendable class '{base_name}'."
                        )
                else:
                    parent_class = self[base_name]
                    bases.add(parent_class)
            for other_base in class_def.others_bases:
                bases.add(other_base)
            simple_name = name.split(".")[-1]
            uniq_class_name = f"{simple_name}{idx}"
            namespace = cls_def.namespace
            namespace.update(
                {
                    "__qualname__": uniq_class_name,
                    "_is_aggregated_class": ClassAttribute(
                        "_is_aggregated_class", True
                    ),
                }
            )
            extendableClass = type(simple_name, tuple(bases), namespace)
            base = cast(Type[models.Extendable], extendableClass)
            self[name] = base
        return base

    @contextmanager
    def build_mode(self) -> Iterator[None]:
        models._registry_build_mode = True
        try:
            yield
        finally:
            models._registry_build_mode = False

    def init_registry(self, module_matchings: Optional[List[str]] = None) -> None:
        """Build the extendable classes by aggregating the classes declared in the given
        module matching list in the same order as the list one. IOW, the mro into the
        aggregated classes will be the inverse one of the given module list. If no
        module list given, build the aggregated classes for all the modules loaded by
        the metaclass in the same order as the loading process.

        The module list accept wildcard expression as last character
        """
        module_matchings = module_matchings if module_matchings else ["*"]
        with self.build_mode(), ModuleIndex() as idx:
            for match in module_matchings:
                for module in idx.get_modules(match):
                    self.load_extendable_classes(module)
            self.build_extendable_classes()
        self.ready = True


class ModuleIndex:
    def __enter__(self) -> "ModuleIndex":
        self._conn = sqlite3.connect(":memory:")
        self.__init_modules_index__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._conn:
            self._conn.close()

    def __init_modules_index__(self) -> None:
        """Create an SQL table used to get the a list of module from a matching
        expression using wildcard character.

        Thanks to the idx column we always return the list of module
        into the same order as the initial loading order
        """
        self._conn.execute(
            """
            CREATE TABLE modules (
                name TEXT not null PRIMARY KEY,
                idx INTEGER not null
            )
        """
        )
        records = (
            (m, idx)
            for idx, m in enumerate(models._extendable_class_defs_by_module.keys())
        )
        self._conn.executemany("INSERT INTO modules VALUES (?, ?)", records)

    def get_modules(self, module_matching: str) -> List[str]:
        query = "SELECT name from modules where name like ? order by idx ASC"
        result = self._conn.execute(query, [module_matching.replace("*", "%")])
        return [r[0] for r in result.fetchall()]