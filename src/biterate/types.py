"""Types for Bits class."""
from typing import Dict, Iterable, Literal, Union

ValidBit = Union[bool, Literal[1, 0, "1", "0", b"1", b"0"]]
DirtyBits = Union[Iterable, Dict[str, int]]
