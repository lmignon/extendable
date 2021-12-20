from collections import OrderedDict
from typing import Any, Generic, Iterator, MutableSet, Optional, Tuple, Type, TypeVar


class ClassAttribute:
    """Hide class attribute from its instances."""

    __slots__ = (
        "name",
        "value",
    )

    def __init__(self, name: str, value: Any) -> None:
        self.name = name
        self.value = value

    def __get__(self, instance: Any, owner: Type[Any]) -> Any:
        if instance is None:
            return self.value
        raise AttributeError(
            f"{self.name!r} attribute of {owner.__name__!r} is class-only"
        )


T = TypeVar("T")


class OrderedSet(MutableSet[T], Generic[T]):
    """A set collection that remembers the elements first insertion order."""

    __slots__ = ["_map"]

    def __init__(self, elems: Optional[Tuple[T]] = None) -> None:
        self._map: OrderedDict[T, None] = OrderedDict(
            (elem, None) for elem in elems or []
        )

    def __contains__(self, elem: object) -> bool:
        return elem in self._map

    def __iter__(self) -> Iterator[T]:
        return iter(self._map)

    def __len__(self) -> int:
        return len(self._map)

    def add(self, elem: T) -> None:
        self._map[elem] = None

    def discard(self, elem: T) -> None:
        self._map.pop(elem, None)


class LastOrderedSet(OrderedSet[T], Generic[T]):
    """A set collection that remembers the elements last insertion order."""

    def add(self, elem: T) -> None:
        OrderedSet.discard(self, elem)
        OrderedSet.add(self, elem)
