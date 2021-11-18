"""Exceptions."""
from typing import Any


class SubscriptError(Exception):
    """Raised when an object is accessed by a subscript of an unsupported type."""

    def __init__(self, subbing_class: Any, subscript: Any, message="unsupported subscript"):
        """Create the Exception and save the classes involved."""
        self.class_name = type(subbing_class).__name__
        self.subscript_class_name = type(subscript).__name__
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        """Display error message."""
        return f"{self.message}, '{self.class_name}' does not support '{self.subscript_class_name}' subscripts"
