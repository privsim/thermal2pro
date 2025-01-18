"""Mode management system for Thermal2Pro application."""
from enum import Enum, auto

class AppMode(Enum):
    """Available application modes."""
    LIVE_VIEW = auto()
    PHOTO = auto()
    VIDEO = auto()
    GALLERY = auto()

from .base_mode import BaseMode
from .live_view_mode import LiveViewMode

__all__ = [
    'AppMode',
    'BaseMode',
    'LiveViewMode',
]