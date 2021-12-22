# define context vars to hold the extendable registry

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .registry import ExtendableClassesRegistry

extendable_registry: ContextVar["ExtendableClassesRegistry"] = ContextVar(
    "extendable_registry"
)
