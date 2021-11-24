"""Constants."""
from typing import Dict, Iterable, Literal, Union

ONES = frozenset({1, "1", b"1", True})
ZEROS = frozenset({0, "0", b"0", False})
PAD = frozenset({"_", " ", ",", "\n", "\r", "\t"})
ValidBit = Union[bool, Literal[1, 0, "1", "0"]]
DirtyBits = Union[Iterable, Dict[str, int]]
