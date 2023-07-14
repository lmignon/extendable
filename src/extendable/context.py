# define context vars to hold the extendable registry

from contextvars import ContextVar
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .registry import ExtendableClassesRegistry

extendable_registry: ContextVar[Optional["ExtendableClassesRegistry"]] = ContextVar(
    "extendable_registry", default=None
)
