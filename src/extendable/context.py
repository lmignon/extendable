# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

# define context vars to hold the extendable registry

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .registry import ExtendableClassesRegistry

extendable_registry: ContextVar["ExtendableClassesRegistry"] = ContextVar(
    "extendable_registry"
)
