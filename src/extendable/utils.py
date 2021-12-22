from collections import OrderedDict
from typing import Generic, Iterator, MutableSet, Optional, Tuple, TypeVar

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
