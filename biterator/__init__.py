"""
Bit manipulation tools.

The primary tools available are the `biterator()` function:
 * Attempt to parse any iterable for bit-like values.
And the `Bits()` class:
 * Holds bit values which can be iterated over and supports all bitwise operators.
"""
from biterator._biterators import (
    bin_str_to_bits,
    biterate,
    bytes_to_bits,
    hex_str_to_bits,
    int_to_bits,
    iter_bits,
    str_to_bits,
    translate_to_bits,
)
from biterator._bits import Bits

__all__ = [
    "Bits",
    "biterate",
    "bin_str_to_bits",
    "bytes_to_bits",
    "hex_str_to_bits",
    "int_to_bits",
    "iter_bits",
    "str_to_bits",
    "translate_to_bits",
]
