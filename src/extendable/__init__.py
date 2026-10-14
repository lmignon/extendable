"""A lib to define class extendable at runtime."""

from importlib.metadata import version

# shortcut to main used class
from .main import ExtendableMeta

__version__ = version("extendable")

# declare "public" members
# __all__ doesn't restrict access to others members, but they are at least
# removed from the list of imported members when imported with
# from extendable import *
__all__ = ["registry", "context", "ExtendableMeta"]
