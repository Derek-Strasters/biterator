"""Iterators that deal in bits."""
from typing import ByteString, Container, Iterable, Iterator

from biterator.const import ONES, PAD, ZEROS


def iter_bits(bits: Iterable) -> Iterator[bool]:
    # NOTE: Pycharm has a bug with doctests, so I have silenced them https://youtrack.jetbrains.com/issue/PY-45009
    # noinspection PyUnresolvedReferences
    """
    Attempt iterating over an Iterable of ValidBits {0, "0", 1, "1", True, False} yielding Boolean values.

    >>> "".join(str(int(elem)) for elem in iter_bits([1, 0, 1, 0]))
    '1010'

    :param bits: The Iterable over which to iterate.
    """
    for bit in bits:
        if bit in ONES:
            yield True
            continue
        if bit in ZEROS:
            yield False
            continue
        if str(bit) in ONES:
            yield True
            continue
        if str(bit) in ZEROS:
            yield False
            continue
        if int(bit) in ONES:
            yield True
            continue
        if int(bit) in ZEROS:
            yield False
            continue
        raise ValueError(f"non valid bit {repr(bit)} was found in {repr(bits)}")


def bytes_to_bits(byte_bits: ByteString) -> Iterator[bool]:
    # noinspection PyUnresolvedReferences
    """
    Iterate over bytes-like objects one bit at a time yielding Boolean values.

    >>> "".join(str(int(bit_)) for bit_ in bytes_to_bits(b'hi'))
    '0110100001101001'

    :param byte_bits:
    """
    for byte in byte_bits:
        yield from int_to_bits(byte, 8)


def int_to_bits(value: int, bit_length: int) -> Iterator[bool]:
    # noinspection PyUnresolvedReferences
    """
    Iterate the bits of an integer as Booleans given it's bit_length.

    >>> "".join(str(int(bit)) for bit in int_to_bits(15, 4))
    '1111'

    :param value: The integer to iterate.
    :param bit_length: Number of bits the integer is meant to have.
    """
    if bit_length <= 0:
        raise ValueError("bit_length must be greater than one")
    # If the value is greater than the bit length, ensure the first bit yielded is the leftmost bit.
    if value.bit_length() > bit_length:
        value >>= value.bit_length() - bit_length
    yield from (bool((1 << i) & value) for i in range(bit_length - 1, -1, -1))


def translate_to_bits(elements: Iterable, ones: Container = None, zeros: Container = None) -> Iterator[bool]:
    # noinspection PyUnresolvedReferences
    """
    Iterate over generic elements; matching symbols yield as True or False.

    If both zeros and ones are defined, elements not found in either will be excluded.
    If one or the other is set, elements will be checked against that container
    and matching elements will yield accordingly while all others will be yield the opposite.

    >>> "".join(str(int(sym)) for sym in translate_to_bits("ffffabababffff", ones={"a"}, zeros={"b"}))
    '101010'
    >>> "".join(str(int(sym)) for sym in translate_to_bits("ffffabababffff", ones={"f"}))
    '11110000001111'
    >>> "".join(str(int(sym)) for sym in translate_to_bits("ffffabababffff", zeros={"a"}))
    '11110101011111'

    :param elements: The elements to interpret.
    :param ones: If set, items in this collection that match an element yield a True bit.
    :param zeros: If set, items in this collection that match an element yield a False bit.
    """
    if ones is not None and zeros is not None:
        for bit in elements:
            if bit in ones:
                yield True
            elif bit in zeros:
                yield False
        return

    if ones is not None:
        yield from (bit in ones for bit in elements)
        return

    if zeros is not None:
        yield from (bit not in zeros for bit in elements)
        return

    raise ValueError("'ones' or 'zeros' or both must be defined")


def hex_str_to_bits(hex_str: str) -> Iterator[bool]:
    # noinspection PyUnresolvedReferences
    """
    Iterate the bits of hexadecimal bytes represented in a string.

    >>> "".join(str(int(bit)) for bit in hex_str_to_bits("0xFF"))
    '11111111'
    >>> "".join(str(int(bit)) for bit in hex_str_to_bits(" 0xFF 0xAAAA 0x0X00X0X0x00x0xF0xB "))
    '1111111110101010101010100000000011111011'

    :param hex_str: The string containing representations of hex.
    """

    def _nibble_check(nibble_bits: str) -> Iterator[bool]:
        """Check if a character is padding, then yield the bits its value."""
        try:
            if nibble_bits not in PAD:
                yield from int_to_bits(int(nibble_bits, 16), 4)
        except ValueError as ex:
            raise ValueError("non-hex value found in string with hex prefix") from ex

    # Removes unwanted characters without resorting to `str.replace()` which is O(n).
    old = ""
    for nibble in hex_str:
        new = nibble
        if old:
            # Removes all occurrences of 0x and 0X.
            if old == "0" and new in {"x", "X"}:
                # By making `old` falsy again, two characters are skipped (thus removing 0x or 0X).
                old = ""
                continue
            # Remove other whitespace characters.
            yield from _nibble_check(old)
        old = new
    # Check last character.
    yield from _nibble_check(old)


def bin_str_to_bits(bin_str: str) -> Iterator[bool]:
    # noinspection PyUnresolvedReferences
    """
    Iterate the bits in hexadecimal bytes represented in a string.

    >>> "".join(str(int(bin_bit)) for bin_bit in bin_str_to_bits("0b10101010"))
    '10101010'

    :param bin_str: The string containing representations of binary.
    """

    def _bit_check(check_bit: str) -> Iterator[bool]:
        """Check if a character is padding, then yield it's Boolean value."""
        if check_bit not in PAD:
            if check_bit == "1":
                yield True
            elif check_bit == "0":
                yield False
            else:
                raise ValueError(f"non valid binary {repr(check_bit)} was found in the string")

    old = ""
    for bit in bin_str:
        new = bit
        if old:
            if old == "0" and new in {"b", "B"}:
                old = ""
                continue
            yield from _bit_check(old)
        old = new
    yield from _bit_check(old)


def str_to_bits(bit_str: str) -> Iterator[bool]:
    # noinspection PyUnresolvedReferences
    """
    Iterate a string for bits; will return Booleans for hex or bin bit values.

    >>> "".join(str(int(bit)) for bit in str_to_bits('0b1111'))
    '1111'
    >>> "".join(str(int(bit)) for bit in str_to_bits('0xAA'))
    '10101010'

    :param bit_str: The string to to be interpreted.
    """
    if bit_str.startswith(("0x", "0X")):
        yield from hex_str_to_bits(bit_str)
        return

    yield from bin_str_to_bits(bit_str)
