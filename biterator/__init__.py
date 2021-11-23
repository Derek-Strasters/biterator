"""
Bit manipulation tools.

The primary tools available are the `biterator()` function:
 * Attempt to parse any iterable for bit-like values.
And the `Bits()` class:
 * Holds bit values which can be iterated over and supports all bitwise operators.
"""
from biterator.biterators import (
    bin_str_to_bits,
    biterator,
    bytes_to_bits,
    hex_str_to_bits,
    int_to_bits,
    iter_bits,
    str_to_bits,
    translate_to_bits,
)
from biterator.bits import Bits
from biterator.const import ONES, ZEROS
from biterator.types import DirtyBits, ValidBit

__version__ = "0.1.0"

__all__ = [
    "Bits",
    "biterator",
    "ONES",
    "ZEROS",
    "bin_str_to_bits",
    "bytes_to_bits",
    "hex_str_to_bits",
    "int_to_bits",
    "iter_bits",
    "str_to_bits",
    "translate_to_bits",
    "DirtyBits",
    "ValidBit",
    "__version__",
]
