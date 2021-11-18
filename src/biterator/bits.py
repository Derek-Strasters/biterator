"""Bits Utility."""
import math
from abc import abstractmethod
from collections.abc import MutableSequence
from copy import deepcopy
from typing import (
    Any,
    ByteString,
    Container,
    Iterable,
    Iterator,
    SupportsInt,
    Tuple,
    Union,
    overload,
)

from biterator.biterators import (
    bytes_to_bits,
    int_to_bits,
    iter_bits,
    str_to_bits,
    translate_to_bits,
)
from biterator.const import ONES, ZEROS
from biterator.exceptions import SubscriptError
from biterator.types import DirtyBits, ValidBit


class Bits(MutableSequence[bool]):
    """
    Stores bits in a list-like object, supports all bit-wise operators.

    Bits can be instantiated with:
        * A string of binary e.g. "1010" or "0b1100_0010".
        * A prefixed string of hexadecimals e.g. "0x1f 0xb2" or "0xbadc0de".
        * A bytes-like object.
        * An integer-like object with a specified bit_length.
        * An Iterable containing any of: True, False, 0, 1, "0", "1".
        * An Iterable of arbitrary objects specifed by 'ones' and 'zero' collections as arguments.
    The add (+) operator functions as concatination only, and supports all of
    the above schemes.  Addition may be done by first casting to int.
    Binary and hexadecimal representations may be accessed with the 'bin' and
    'hex' properties and the 'decode' method may be used to read the bits as
    bytes using a specified codec.

    >>> bits = Bits(); bits.extend('1010'); bits.bin()  # Concatenate regular strings of binary.
    '0b1010'
    >>> bits.extend(dict(value=15, bit_length=4)); bits.bin()  # Concatenate bits from an integer.
    '0b1010_1111'
    >>> bits.extend(b"A"); bits.bin(compact=True)  # Concatenate bytes-like objects.
    '0b1010111101000001'
    >>> Bits("0xFF") + "0b1001_1001" # Concatenation directly with (+) operator.
    Bits("0b1111111110011001")
    >>> Bits("1111 0011 0000 1010")[:8] # Instantiate with binary; slicing is supported.
    Bits("0b11110011")
    >>> Bits("0xAAAA")[0:8:2] # Instantiate with hex; advanced slicing
    Bits("0b1111")
    >>> Bits("1111") << 4 # Bitshift operators supported
    Bits("0b11110000")
    >>> Bits(15, bit_length=4) # Add bits from integers
    Bits("0b1111")

    All bitwise operators are supported.
    'NOR' mask example, left and right 'NOR' with eachother when the mask is active:
    >>> mask_ = Bits('00001111')
    >>> left_ = Bits('01010101')
    >>> right = Bits('00110011')
    >>> ((mask_ ^ left_) & (mask_ | left_) & ~(mask_ & right)).bin()
    '0b0101_1000'

    """

    # Pylint literally crashes on this line for some reason.
    __slots__ = ["__bytes", "__last_byte", "__len_last_byte", "__len"]  # pylint: disable=all (literally will crash)

    __bytes: bytearray
    __len: int
    # Contains the trailing (incomplete) byte; has less than the 8 bits of an actual byte.
    __last_byte: int
    __len_last_byte: int

    def __init__(
        self,
        bit_values: Union[Iterable, int] = None,
        bit_length: int = None,
        ones: Container = None,
        zeros: Container = None,
    ):
        """
        Create a new Bits object from an Iterable of bit like object.

        Create from a string of binary e.g.: "1010", "0b1001", or "0b1001_1101"
        Create from a string of hex values: "0xFA 0xDE", "0XFFAA", "0Xab"
        Create from bytes-like objects.
        Create from Iterable of arbitrary objects by specifying containers
        of objects for 'ones' and 'zeros'.

        >>> Bits("10011001")
        Bits("0b10011001")
        >>> Bits("ffffabababffff", ones={"a"}, zeros={"b"})
        Bits("0b101010")
        >>> Bits("0xFF")
        Bits("0b11111111")
        >>> Bits("MPMPEEMP", ones="M", zeros="EP")
        Bits("0b10100010")
        >>> Bits() + b"Hi"
        Bits("0b0100100001101001")
        >>> def double_gen(size: int):
        ...     if size:
        ...         yield size % 4 < 2
        ...         yield from double_gen(size - 1)
        >>> Bits(double_gen(16)) # Supports generators
        Bits("0b1001100110011001")

        :param bit_values: Values to initialize a Bits object with.
        :param bit_length: Bit length if an integer is given for bit_values.
        :param ones: If set, symbols in this collection will represent True bits.
        :param zeros: If set, symbols in this collection will represent False bits.
        """
        self.__bytes = bytearray()
        self.__len_last_byte = 0
        self.__last_byte = 0
        self.__len = 0

        if bit_values is None and any(arg is not None for arg in (bit_length, ones, zeros)):
            raise ValueError("unexpected argument, 'bit_values' must be set or none must be set")

        elif bit_values is not None:
            if isinstance(bit_values, int):
                if isinstance(bit_length, int):
                    self.extend(self._clean_bits(dict(value=bit_values, bit_length=bit_length), ones, zeros))
                    return
                raise TypeError("argument 'bit_length' must be set if 'bit_values' is an integer")
            else:
                self.extend(self._clean_bits(bit_values, ones, zeros))
                return

    @classmethod
    def _clean_bits(
        cls,
        dirty_bits: DirtyBits,
        ones: Container = None,
        zeros: Container = None,
    ) -> Iterator[bool]:
        """
        Attempt, by a variety of means, to iterate over `dirty_bits`; yields Booleans.

        `dirty_bits` can be a dictionary of the form {"value": 15, "bit_length": 4}
        to iterate over the bits of an integer.

        :param dirty_bits: The bits containing object.
        :param ones: If set, symbols in this collection will represent True bits.
        :param zeros: If set, symbols in this collection will represent False bits.
        """
        # Iterate from another Bits object.
        if isinstance(dirty_bits, cls):
            yield from dirty_bits
            return

        # Translate elements of any kind in to bits.
        if ones is not None or zeros is not None:
            yield from translate_to_bits(dirty_bits, ones, zeros)
            return

        # Iterate the bits of an integer.
        if isinstance(dirty_bits, dict):
            if "value" in dirty_bits and "bit_length" in dirty_bits:
                yield from int_to_bits(**dirty_bits)
                return
            raise ValueError(f"unsupported dict format {repr(dirty_bits)}")

        # Iterate the bits of a Hexadecimal or Binary expressed as a string.
        if isinstance(dirty_bits, str):
            yield from str_to_bits(dirty_bits)
            return

        # Iterate bytes-like objects.
        if isinstance(dirty_bits, ByteString):
            yield from bytes_to_bits(dirty_bits)
            return

        # Attempt to iterate from any Iterable.
        if isinstance(dirty_bits, Iterable):
            yield from iter_bits(dirty_bits)
            return

        raise TypeError(f"unsupported type {repr(dirty_bits)}")

    def copy(self) -> "Bits":
        """
        Return a deep copy of the Bits object.

        >>> bits_1 = Bits('1111')
        >>> bits_2 = bits_1.copy()
        >>> bits_2 += '1111'
        >>> bits_2.bin(True, prefix="")
        '11111111'
        >>> bits_1.bin(True, prefix="")
        '1111'
        """
        return deepcopy(self)

    def __repr__(self) -> str:
        """
        Represent the Bits object.

        Equivalent to code which would create an identical object
        but only up to a size of 64 bytes; after which it is abbreviated.

        >>> Bits([1, 0]*32)
        Bits("0b1010101010101010101010101010101010101010101010101010101010101010")
        >>> Bits('0xCAB00D1E'*6)
        Bits(4969887947907717934627081996608040267272832614365316255006, 192)
        >>> Bits('0xBA5EBA11'*10)
        Bits("0xba5eba11ba5eba11ba5eba11ba5eba11ba5eba11ba5eba11ba5eba11ba5eba11ba5eba11ba5eba11")
        >>> Bits('0x0DDBA11'*20)
        Bits("0x0D 0xDB 0xA1 ... 0xDD 0xBA 0x11")
        >>> Bits('0x0DDBA11'*20) + '1001'
        Bits("0x0D 0xDB 0xA1 ... 0xBA 0x11 0x90")
        """
        if len(self) <= 64:
            return f'Bits("{format(int(self), f"#0{self.__len + 2}b")}")'

        largest_possible_decimal = int(math.log(1 << self.__len, 10))
        if largest_possible_decimal <= 64:
            return f'Bits({format(int(self), f"0{largest_possible_decimal}d")}, {self.__len})'

        if len(self) // 8 <= 64:
            return f'Bits("{format(int(self), f"#0{len(self) // 8 + 2}x")}")'
        if self.__len_last_byte > 0:
            return f'Bits("{self[:24].hex()} ... {self[-(self.__len_last_byte + 16):].hex()}")'
        return f'Bits("{self[:24].hex()} ... {self[-24:].hex()}")'

    def iter_bytes(self) -> Iterator[int]:
        # noinspection PyUnresolvedReferences
        """
        Generate bytes from the bits.

        Yield an integer representation of each byte, uless `as_bytes` is set,
        in which case return single `bytes` objects.
        An incomplete byte will be written from the left, for example:

        >>> for byte in Bits('10101010 1111').iter_bytes(): print(bin(byte))
        0b10101010
        0b11110000

        :return: The Iterator.
        """
        yield from self.__bytes
        if self.__len_last_byte:
            yield self.__last_byte << 8 - self.__len_last_byte

    def __bytes__(self) -> bytes:
        r"""
        Return bytes object; an incomplete byte is written from the left.

        For example:
        >>> bytes(Bits('1111'))
        b'\xf0'
        """
        return bytes(self.iter_bytes())

    def decode(self, *args, **kwargs) -> str:
        """
        Decode the bytes using the codec registered for encoding.

        Wraps the `bytes.decode()` method.

        >>> Bits('01101000 01101001 00100000 01101101 01100001 01110010 01101011').decode('utf-8')
        'hi mark'

        :param args:
        :param kwargs:
        :return:
        """
        return bytes(self).decode(*args, **kwargs)

    def __bool__(self):
        """Return true if not empty."""
        return len(self.__bytes) > 0 or bool(self.__last_byte)

    def _byte_bit_indices(self, index: int) -> Tuple[int, int, int]:
        """
        Calculate byte index, bit index (on the byte), and apply clipping to the original index.

        :param index: The index to calculate.
        :return: The tuple with computed index values.
        """
        if index >= len(self) or index < -len(self):
            raise IndexError

        # Modulo corrects negative indices
        if index < 0:
            index %= len(self)

        # The first is the index of the byte that the index is within.
        # The second is the index of the bit within the byte (counting from the left).
        return index // 8, index % 8, index

    @classmethod
    def _clean_bit(cls, value: ValidBit) -> bool:
        """
        Ensure bit is a ValidBit, cast to bool.

        >>> Bits._clean_bit('1')
        True
        >>> Bits._clean_bit(0)
        False
        >>> Bits._clean_bit('a')
        Traceback (most recent call last):
        TypeError: could not determine single bit value for 'a'

        :param value: The value to check.
        :return: The bool representation.
        """
        if value in ONES:
            return True
        if value in ZEROS:
            return False

        raise TypeError(f"could not determine single bit value for {repr(value)}")

    def insert(self, index: int, value: ValidBit) -> None:
        """
        Insert a bit at given index.

        >>> bits = Bits('001'); bits.insert(0, True); bits.bin()
        '0b1001'
        >>> for _ in range(4): bits.insert(len(bits), False)
        >>> bits.bin()
        '0b1001_0000'
        >>> bits.insert(5, "1"); bits.bin()
        '0b1001_0100 0b0'
        >>> bits.insert(-2, 1); bits.bin()
        '0b1001_0101 0b00'
        >>> bits = Bits('11110000 11110000 11110000 '); bits.insert(5, "1"); bits.bin(prefix="", group=False)
        '11110100 01111000 01111000 0'

        :param index: The index at whitch to insert the bit.
        :param value: The bit to be inserted.
        """
        if not isinstance(value, bool):
            value = self._clean_bit(value)

        # If the index is above the length, set it to the length.
        # If the index is below the negative length, set it to the negative length.
        # Then if the new index is negative, take the modulo to get the correct positive index.
        if len(self) == 0:
            index = 0
        else:
            if index >= 0:
                index = min(len(self), index)
            else:
                index = max(-len(self), index) % len(self)
        byte_index, bit_index = index // 8, index % 8

        # If appending to the end.
        if index == len(self):
            self.__last_byte = (self.__last_byte << 1) | value
            self._increment_last_byte()

        # If inserting within the last (incomplete) byte.
        elif byte_index == len(self.__bytes):
            self.__last_byte = self._insert_bit_in_byte(self.__last_byte, self.__len_last_byte, bit_index, value)
            self._increment_last_byte()

        # If inserting anywhere else.
        else:
            # Insert the bit then remove the rightmost bit to carry over into the next byte to the right.
            new_byte = self._insert_bit_in_byte(self.__bytes[byte_index], 8, bit_index, value)
            carry = new_byte & 1
            new_byte >>= 1
            # Append the byte with the carry over bit removed.
            self.__bytes[byte_index] = new_byte
            # Repeat for the remaining whole bytes to the right of the index.
            for i in range(byte_index + 1, len(self.__bytes)):
                new_byte = (carry << 8) | self.__bytes[i]
                carry = new_byte & 1
                new_byte >>= 1
                self.__bytes[i] = new_byte
            # Append the last carry bit to the last (incomplete) byte, and increment it's length.
            self.__last_byte = (carry << self.__len_last_byte) | self.__last_byte
            self._increment_last_byte()

    def append(self, value: ValidBit) -> None:
        """Override of the mixin to add data validation."""
        super().append(self._clean_bit(value) if not isinstance(value, bool) else value)

    def extend(self, values: DirtyBits) -> None:
        """Override of the mixin to add data validation."""
        # Prevent race conditions
        for v in self.copy() if values is self else self._clean_bits(values):
            self.append(v)

    @staticmethod
    def _insert_bit_in_byte(byte: int, length: int, index: int, value: bool) -> int:
        """
        Insert a bit in a byte, indexed from the left.

        >>> bin(Bits._insert_bit_in_byte(0b1010010, 7, 4, True))
        '0b10101010'

        :param byte: Byte in which to insert the bit.
        :param length: Length of the Byte.
        :param index: Index at which to insert the bit.
        :param value: Value to be inserted.
        :return: Byte with new bit inserted.
        """
        right_index = length - index
        left_bits = byte >> right_index
        right_bits = byte & ((1 << right_index) - 1)
        return (((left_bits << 1) | value) << right_index) | right_bits

    def _increment_last_byte(self) -> None:
        """
        Call when a bit has been added anywhere in the last (incomplete) byte.

        >>> bits = Bits(0b111_1111, 7); bits.last_byte_length
        7
        >>> bits.append(False); bits.last_byte_length
        0
        >>> len(bits)
        8

        """
        self.__len_last_byte += 1
        self.__len += 1
        if self.__len_last_byte == 8:
            self.__bytes.append(self.__last_byte)
            self.__last_byte = 0
            self.__len_last_byte = 0

    @overload
    @abstractmethod
    def __getitem__(self, i: int) -> bool:
        """Retrieve a bit."""
        ...

    @overload
    @abstractmethod
    def __getitem__(self, s: slice) -> "Bits":
        """Retrieve a slice of bits."""
        ...

    def __getitem__(self, index):
        """
        Retrieve a bit or a slice of bits.

        >>> Bits('0001 0000')[3]
        True
        >>> Bits('0001 0000')[-5]
        True
        >>> Bits('0001 1000')[3:5]
        Bits("0b11")
        >>> Bits("00001111 00110011 01010101")[:-16]
        Bits("0b00001111")
        >>> Bits("00001111 00110011 01010101")[-8:]
        Bits("0b01010101")
        >>> Bits('01001001')["s"]
        Traceback (most recent call last):
        ...
        biterator.exceptions.SubscriptError: unsupported subscript, 'Bits' does not support 'str' subscripts

        :param index: The index or slice to retrieve.
        :return: The new Bits object or a bit value.
        """
        if isinstance(index, int):
            byte_index, bit_index, index = self._byte_bit_indices(index)

            # If the index is in the last (incomplete) byte.
            if byte_index == len(self.__bytes):
                return self._get_bit_from_byte(self.__last_byte, self.__len_last_byte, bit_index)

            # If the index is anywhere else.
            return self._get_bit_from_byte(self.__bytes[byte_index], 8, bit_index)

        if isinstance(index, slice):
            start, stop, step = index.indices(len(self))

            # For the case where the slice starts from a whole byte.
            if step == 1 and start % 8 == 0:
                last_byte_index, last_bit_index = stop // 8, stop % 8
                start_byte_index = start // 8
                new = type(self)(self.__bytes[start_byte_index:last_byte_index])
                # Append any remaining bits.
                if last_bit_index:
                    for i in range(stop - last_bit_index, stop):
                        # Recurse into the branch for integers
                        new.append(self[i])
                return new

            # For all other cases (not particularly efficient).
            new = type(self)()
            for i in range(start, stop, step):
                # Recurse into the branch for integers
                new.append(self[i])
            return new

        raise SubscriptError(self, index)

    @staticmethod
    def _get_bit_from_byte(byte: int, length: int, index: int) -> bool:
        """
        Return the bit value at the given index, indexed from the left.

        >>> Bits._get_bit_from_byte(0b00000100, 8, 5)
        True

        :param byte: Byte from which to get a bit.
        :param index: Index of bit to retrieve.
        :param length: Length of byte.
        :return: The value of the bit.
        """
        right_index = length - index - 1
        return bool((1 << right_index) & byte)

    @overload
    @abstractmethod
    def __setitem__(self, i: int, o: ValidBit) -> None:
        """Set a bit."""
        ...

    @overload
    @abstractmethod
    def __setitem__(self, s: slice, o: DirtyBits) -> None:
        """Set a slice of bits."""
        ...

    def __setitem__(self, index, other):
        """
        Set a bit or slice of bits.

        >>> bits = Bits('1111 1111 1111'); bits[4:8] = '0000'; bits.bin()
        '0b1111_0000 0b1111'
        >>> bits[4:8] = 15; bits.bin()
        '0b1111_1111 0b1111'
        >>> bits[-4:] = '0000'; bits.bin()
        '0b1111_1111 0b0000'
        >>> bits[0] = False; bits.bin()
        '0b0111_1111 0b0000'

        :param index: The index or slice to modify.
        :param other: The bit or bits to replace the old bit or bits.
        """
        if isinstance(index, int):
            other = self._clean_bit(other)
            byte_index, bit_index, index = self._byte_bit_indices(index)

            # If the index is in the last (incomplete) byte.
            if byte_index == len(self.__bytes):
                self.__last_byte = self._set_bit_in_byte(self.__last_byte, self.__len_last_byte, bit_index, other)

            # If the index is anywhere else.
            else:
                self.__bytes[byte_index] = self._set_bit_in_byte(self.__bytes[byte_index], 8, bit_index, other)

        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self))

            # Cast other to a Bits object
            if isinstance(other, int):
                other_bit = iter(type(self)(other, stop - start))
            else:
                other_bit = iter(type(self)(other))

            try:
                for i in range(start, stop, step):
                    # Recurse into the branch for integers
                    self[i] = next(other_bit)
            except StopIteration:
                pass

        else:
            raise SubscriptError(self, index)

    @classmethod
    def _set_bit_in_byte(cls, byte: int, length: int, index: int, value: bool) -> int:
        """
        Modify a bit in a byte, indexed from the left.

        >>> Bits._set_bit_in_byte(0b11011111, 8, 2, True)
        255

        :param byte: Byte in which to modify a bit.
        :param length: Length of the byte.
        :param index: Index of the bit to modify.
        :param value: Value to modify the bit to.
        :return: The Byte with bit modified.
        """
        right_index = length - index - 1
        # If the bit is the same, do nothing.
        if bool((1 << right_index) & byte) == value:
            return byte
        # The bit is different, flip it.
        return (1 << right_index) ^ byte

    @overload
    @abstractmethod
    def __delitem__(self, i: int) -> None:
        """Remove a single bit."""
        ...

    @overload
    @abstractmethod
    def __delitem__(self, i: slice) -> None:
        """Remove a slice."""
        ...

    def __delitem__(self, index):
        """
        Remove a bit or a slice.

        >>> bits = Bits("1000 0000 0000 0100 0001"); del bits[13]; bits.bin()
        '0b1000_0000 0b0000_0000 0b001'
        >>> bits = Bits("1010 1010 1010 1010 0000"); del bits[1::2]; bits.bin()
        '0b1111_1111 0b00'
        >>> del bits[8:10]; bits.bin()
        '0b1111_1111'
        >>> del bits[-4:]; bits.bin()
        '0b1111'

        :param index: Index or slice to delete.
        """
        if isinstance(index, int):
            byte_index, bit_index, index = self._byte_bit_indices(index)

            # If the bit deleted in in the last (incomplete) byte.
            if byte_index == len(self.__bytes):
                self.__last_byte = self._del_bit_from_byte(self.__last_byte, self.__len_last_byte, bit_index)
                self._decrement_last_byte()

            # All other cases.
            else:
                # Remove the bit from the target byte, then append the first bit from the next byte.
                # Cascade similarly through the list of bytes.
                new_byte = self._del_bit_from_byte(self.__bytes[byte_index], 8, bit_index)
                for i in range(byte_index + 1, len(self.__bytes)):
                    first_bit = bool(self.__bytes[i] & 0b1000_0000)
                    self.__bytes[i - 1] = (new_byte << 1) | first_bit
                    new_byte = self.__bytes[i] & 0b0111_1111

                # If the last (incomplete) byte is not empty, append the first bit from it.
                if self.__len_last_byte:
                    first_bit = bool(self.__last_byte & (1 << self.__len_last_byte - 1))
                    self.__bytes[-1] = (new_byte << 1) | first_bit
                    # Truncate the first bit of the last (incomplete) byte.
                    self.__last_byte &= (1 << self.__len_last_byte - 1) - 1

                # If the last (incomplete) byte is empty, remove the last full byte.
                else:
                    self.__bytes.pop()
                    # The former last full byte becomes the last (incomplete) byte with it's first bit removed.
                    self.__last_byte = new_byte

                # Decrement the length and last (incomplete) byte length in both cases.
                self._decrement_last_byte()

        elif isinstance(index, slice):
            start, stop, step = index.indices(len(self))

            # NOTE: ***VERY inefficient*** Consider refactor.
            # NOTE: Good opportunity to use interval library to remove all deleted bits and concat what remains.
            # Always proceeds in reverse order to not mess up the indexing.
            removal_indices = sorted(list(range(start, stop, step)), reverse=True)
            for i in removal_indices:
                del self[i]

        else:
            raise SubscriptError(self, index)

    @staticmethod
    def _del_bit_from_byte(byte: int, length: int, index: int) -> int:
        """
        Remove a bit from a byte, indexed from the left.

        >>> Bits._del_bit_from_byte(0b00010000, 8, 3)
        0

        :param byte: Byte from which to remove a bit.
        :param length: Length of the byte.
        :param index: Index of the bit to remove.
        :return: The Byte with bit removed.
        """
        right_index = length - index
        left_bits = (byte >> right_index) << right_index - 1
        right_bits = byte & ((1 << right_index - 1) - 1)
        return left_bits | right_bits

    def _decrement_last_byte(self) -> None:
        """
        Call when a bit has been removed anywhere in the last (incomplete) byte.

        >>> bits = Bits(0b010001000, 9); bits.last_byte_length
        1
        >>> del bits[0]; bits.last_byte_length
        0
        """
        self.__len_last_byte -= 1
        self.__len -= 1
        if self.__len_last_byte < 0:
            self.__len_last_byte = 7

    def __invert__(self) -> "Bits":
        """
        Return a Bits object with each bit inverted.

        >>> (~Bits('01001110')).bin()
        '0b1011_0001'

        :return: The Bits object with inverted bits.
        """
        return type(self)(not bit for bit in self)

    def __int__(self) -> int:
        """
        Represent the sequence of bits as an int.

        >>> int(Bits("0xff"))
        255
        >>> int(Bits("0xfff"))
        4095
        >>> int(Bits("0xffff"))
        65535

        :return: The integer representation.
        """
        return (int.from_bytes(self.__bytes, "big") << self.__len_last_byte) | self.__last_byte

    def __len__(self) -> int:
        """Total number of bits."""
        return self.__len

    def __lt__(self, other: SupportsInt) -> bool:
        """Int value of bits is less than the int value of other."""
        if isinstance(other, SupportsInt):
            return int(self) < int(other)
        return NotImplemented

    def __le__(self, other: SupportsInt) -> bool:
        """Int value of bits is less than or equal to the int value of other."""
        if isinstance(other, SupportsInt):
            return int(self) <= int(other)
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        """Int value of bits is equal to the int value of other."""
        if isinstance(other, SupportsInt):
            return int(self) == int(other)
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        """Int value of bits is not equal to the int value of other."""
        if isinstance(other, SupportsInt):
            return int(self) != int(other)
        return NotImplemented

    def __gt__(self, other: SupportsInt) -> bool:
        """Int value of bits is greater than the int value of other."""
        if isinstance(other, SupportsInt):
            return int(self) > int(other)
        return NotImplemented

    def __ge__(self, other: SupportsInt) -> bool:
        """Int value of bits is greater than or equal to the int value of other."""
        if isinstance(other, SupportsInt):
            return int(self) >= int(other)
        return NotImplemented

    # Concatenate

    def __add__(self, other: DirtyBits) -> "Bits":
        """
        Concatenate bits; NOT addition.

        >>> (Bits("0110") + Bits("1001")).bin()
        '0b0110_1001'
        >>> (Bits("0110") + "1001").bin()
        '0b0110_1001'
        >>> (Bits("0110") + dict(value=15, bit_length=4)).bin()  # Concat an integer
        '0b0110_1111'
        >>> bits = Bits('10'*10); bits += bits; bits.bin(True, "")
        '1010101010101010101010101010101010101010'

        :param other: Other object to be concatenated.
        :return: New Bits object that is a concatenation of the inputs.
        """
        if isinstance(other, (Iterable, dict)):
            new = self.copy()
            new.extend(other)
            return new
        return NotImplemented

    def __radd__(self, other: DirtyBits) -> "Bits":
        """
        Right concatenation.

        >>> "1001" + Bits("0110")
        Bits("0b10010110")
        """
        if isinstance(other, (Iterable, dict)):
            new = type(self)()
            new.extend(other)
            new.extend(self)
            return new
        return NotImplemented

    def __iadd__(self, other: DirtyBits) -> "Bits":
        """
        Extend in-place.

        >>> bits = Bits("1111"); bits += "0000"; bits.bin()
        '0b1111_0000'
        >>> bits += dict(value=255, bit_length=8); bits.bin()
        '0b1111_0000 0b1111_1111'

        :param other: Bits to extend.
        :return: The Bits object that was modified in place.
        """
        if isinstance(other, (Iterable, dict)):
            self.extend(other)
            return self
        return NotImplemented

    # Left Bitshift

    def __lshift__(self, index: int) -> "Bits":
        """
        Left shift the bits.

        >>> (Bits("1111") << 4).bin()
        '0b1111_0000'

        :param index: Number of places to shift
        :return: Shifted Bits object
        """
        if isinstance(index, SupportsInt):
            new = self.copy()
            new.extend(type(self)(0, int(index)))
            return new
        return NotImplemented

    def __ilshift__(self, index: int) -> "Bits":
        """
        Left bitshift in-place.

        >>> bits = Bits("1111"); bits <<= 4; bits.bin()
        '0b1111_0000'

        :param index: Number of places to shift.
        :return: The Bits object that was modified in place.
        """
        if isinstance(index, SupportsInt):
            self.extend({"value": 0, "bit_length": int(index)})
            return self
        return NotImplemented

    # Right Bitshift

    def __rshift__(self, index: int) -> "Bits":
        """
        Right shift the bits.

        >>> (Bits("11110000") >> 4).bin()
        '0b1111'

        :param index: Number of places to shift
        :return: Shifted Bits object
        """
        if isinstance(index, SupportsInt):
            return type(self)(self[: -int(index)])
        return NotImplemented

    def __irshift__(self, index: int) -> "Bits":
        """
        Right bitshift in-place.

        >>> bits = Bits("1111 1111"); bits >>= 4; bits.bin()
        '0b1111'

        :param index: Number of places to shift.
        :return: The Bits object that was modified in place.
        """
        if index:
            del self[-index:]
        return self

    # AND

    def __and__(self, other: DirtyBits) -> "Bits":
        """
        Bitwise and operation.

        >>> (Bits('01111000') & Bits('00011110')).bin()
        '0b0001_1000'
        >>> (Bits('0111') & Bits('00011110')).bin()
        '0b0001'
        >>> (Bits("1110") & "0b0111").bin()
        '0b0110'
        >>> Bits("1110") & dict(value=7, bit_length=4)
        Bits("0b0110")

        :param other: Other Bits to 'and' with
        :return: Combined Bits objects
        """
        if isinstance(other, (Iterable, dict)):
            return type(self)(a & b for a, b in zip(self, self._clean_bits(other)))
        return NotImplemented

    __rand__ = __and__

    def __iand__(self, other: DirtyBits) -> "Bits":
        """
        Bitwise 'and' with other bits; in-place.

        >>> bits_ = Bits("1110"); bits_ &= "0111"; bits_.bin()
        '0b0110'

        :param other: The Iterable bits to 'and' with.
        :return: The Bits object that was modified in place.
        """
        if isinstance(other, (Iterable, dict)):
            len_other = 1
            for index, bits in enumerate(zip(self, self._clean_bits(other))):
                self[index] = bits[0] & bits[1]
                len_other += 1
            if len(self) > len_other:
                del self[-len_other:]
            return self
        return NotImplemented

    # XOR

    def __xor__(self, other: DirtyBits) -> "Bits":
        """
        Bitwise xor operation.

        >>> (Bits('01111000') ^ Bits('00011110')).bin()
        '0b0110_0110'
        >>> (Bits('01111000') ^ '0b00011110').bin()
        '0b0110_0110'
        >>> (Bits("1110") ^ "0111").bin()
        '0b1001'

        :param other: Other Bits to 'xor' with
        :return: Combined Bits objects
        """
        if isinstance(other, (Iterable, dict)):
            return type(self)(a ^ b for a, b in zip(self, self._clean_bits(other)))
        return NotImplemented

    __rxor__ = __xor__

    def __ixor__(self, other: DirtyBits) -> "Bits":
        """
        Bitwise 'xor' with other bits; in-place.

        >>> bits_ = Bits("0110"); bits_ ^= "0101"; bits_.bin()
        '0b0011'

        :param other: The Iterable bits to 'xor' with.
        :return: The Bits object that was modified in place.
        """
        len_other = 1
        for index, bits in enumerate(zip(self, self._clean_bits(other))):
            self[index] = bits[0] ^ bits[1]
            len_other += 1
        if len(self) > len_other:
            del self[-len_other:]
        return self

    # OR

    def __or__(self, other: DirtyBits) -> "Bits":
        """
        Bitwise or operation.

        >>> (Bits('01111000') | Bits('00011110')).bin()
        '0b0111_1110'
        >>> (Bits("1100") | "0011").bin()
        '0b1111'

        :param other: Other Bits to 'or' with
        :return: Combined Bits objects
        """
        return type(self)(a | b for a, b in zip(self, self._clean_bits(other)))

    __ror__ = __or__

    def __ior__(self, other: DirtyBits) -> "Bits":
        """
        Bitwise 'or' with other bits; in-place.

        >>> bits_ = Bits("1100"); bits_ |= "0011"; bits_.bin()
        '0b1111'

        :param other: The Iterable bits to 'or' with.
        :return: The Bits object that was modified in place.
        """
        len_other = 1
        for index, bits in enumerate(zip(self, self._clean_bits(other))):
            self[index] = bits[0] | bits[1]
            len_other += 1
        if len(self) > len_other:
            del self[-len_other:]
        return self

    @property
    def last_byte_length(self):
        """
        If the totall number of bits is not divisible by 8, get the remainder.

        This property gives the length of the last incomplete byte in the object.

        >>> bits = Bits("10011001 1010"); bits[-bits.last_byte_length:].bin(True, prefix="")
        '1010'

        :return: Number of bits in the last incomplete byte.
        """
        return self.__len_last_byte

    def hex(self, compact: bool = False, prefix: str = "0x", sep: str = " ", fmt: str = None) -> str:
        r"""
        Return a string with hexadecimal representation of each byte.

        NOTE: The prefix argument can be set to the empty string and then
        enabled in the formatting argument if that is preferred.

        >>> Bits("0b1111").hex()
        '0xF0'
        >>> Bits("0b00_1111").hex() # Interpreted as 0011_1100
        '0x3C'
        >>> Bits("0b1111_1111 0b1111").hex()
        '0xFF 0xF0'
        >>> Bits("0b1111_1111 0b1111_1111").hex(compact=True, prefix=r"\x")
        '\\xFFFF'
        >>> Bits("0b1011_0001 0b1010_1101 0b1110_0101").hex(prefix="", compact=True)
        'B1ADE5'
        >>> Bits("0b1111_1111 0b1111_1111").hex(compact=True, prefix='', fmt="4X")
        '  FF  FF'

        :param compact: No separators and only prefixed at the beggining.
        :param prefix: Prefix for each byte, default: '0x'.
        :param sep: Separator between bytes, default ' '.
        :param fmt: Formatting for each byte.
        :return: The string representation of the bytes as hexadecimal.
        """
        if compact:
            ret_str = prefix + "".join(format(byte, fmt or "02X") for byte in self.iter_bytes())
        else:
            ret_str = sep.join(prefix + format(byte, fmt or "02X") for byte in self.iter_bytes())

        return ret_str

    def bin(self, compact: bool = False, prefix: str = "0b", sep: str = " ", group: bool = True) -> str:
        """
        Return a string with the binary representations of each byte.

        NOTE: The prefix argument can be set to the empty string and then
        enabled in the formatting argument if that is preferred.

        >>> Bits(255, 8).bin()
        '0b1111_1111'
        >>> Bits(4095, 12).bin(prefix="")
        '1111_1111 1111'
        >>> Bits(65535, 16).bin(group=False)
        '0b11111111 0b11111111'
        >>> Bits("1111 11").bin()
        '0b11_1111'
        >>> Bits(43690, 16).bin(compact=True, prefix="")
        '1010101010101010'

        :param compact: No separators or grouping, only prefixed at the beggining.
        :param prefix: Prefix on each byte, default '0b'.
        :param sep: Spacer between bytes, default: ' '.
        :param group: Digit grouping symbol, may be '_' or None default: '_'.
        :return: The string of the bits in binary representation.
        """
        if compact:
            ret_str = "".join(format(byte, "08b") for byte in self.__bytes)
            if self.__len_last_byte:
                ret_str += format(self.__last_byte, f"0{self.__len_last_byte}b")
            ret_str = prefix + ret_str
        else:
            ret_str = sep.join(prefix + format(byte, "09_b" if group else "08b") for byte in self.__bytes)
            if self.__len_last_byte:
                ret_str += sep if ret_str else ""
                if group:
                    has_group = 1 if self.__len_last_byte > 4 else 0
                    last_byte_fmt = f"0{self.__len_last_byte + has_group}_b"
                else:
                    last_byte_fmt = f"0{self.__len_last_byte}b"
                ret_str += prefix + format(self.__last_byte, last_byte_fmt)
        return ret_str
