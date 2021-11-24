# Biterator

__Biterator is a Python library for dealing with bits. One at a time. But in a nice way.__

The name biterator is a portmanteau of the words 'bit' and 'iterator' which hints at the utility of this package. Two of
the most useful tools herein are:

1. [`biterator.biterate(bit_values[, bit_length][, ones][, zeros])`](biterator/_biterators.py)
2. [`biterator.Bits([bit_values][, bit_length][, ones][, zeros])`](biterator/_bits.py)

The first tool `biterate()` being a function that will attempt by a variety of techniques to return the most logical
sequence of bits (as Booleans) for any given iterable object, and some objects that are not typically iterable, like
integers. It will parse strings for bit-like and byte like signatures and iterate over what it can detect.

The `Bits()` class expands upon this utility by efficiently storing bits as they are found. Further; `Bits()` supports
all bitwise operators, and manipulation tools for convenient handling.

## Installation

The biterator library is pip installable:

```shell
pip install biterator
```

## Usage

Some straightforward examples using the `biterate()` function:

```doctest
>>> import biterator

# Iterate a list of booleans.
>>> list(biterator.biterate([True, False, True, False]))
[True, False, True, False]

# Iterate a tuple of integer 0 and 1 literals.
>>> list(biterator.biterate(tuple([1, 0, 1, 0])))
[True, False, True, False]

# Iterate a list of string "0" and "1" literals.
>>> list(biterator.biterate(["1", "0", "1", "0"]))
[True, False, True, False]

```

More advanced examples:

```doctest
...

# Iterate a string containing a prefixed binary number.
>>> list(biterator.biterate("0b1010"))
[True, False, True, False]

# Iterate the bits of an integer, given it's total bit_length.
>>> list(biterator.biterate(bit_values=10, bit_length=6))
[False, False, True, False, True, False]

# Iterate the bits of a raw byte-string.
>>> list(biterator.biterate(b"U"))
[False, True, False, True, False, True, False, True]

# Iterate the bits of an integer represented as a prefixed hexadecimal string.
>>> list(biterator.biterate("0xAF"))
[True, False, True, False, True, True, True, True]

# Iterate a generator.
>>> list(biterator.biterate(i % 2 for i in range(4)))
[True, False, True, False, True]

```

The `Bits()` class expands upon the utility of `biterate()` by efficiently storing bits as they are iterated over.  
`Bits()` support all bitwise operators and handles concatenation gracefully.

```doctest
>>> from biterator import Bits

# Instantiate with all the types supported by biterate.
>>> bits = Bits('0101')
>>> list(bits)
[True, False, True, False]

# Supports concatenation with naked biterable types.
>>> "0xFF" + bits + "0000"
Bits("0b1111111101010000")

# Supports all bitwise operators, also works with naked biterable types.
>>> (Bits("1100") | Bits("0011")) & "1111"
Bits("0b1111")

# Supports slicing.
>>> Bits('10101010')[0:8:2]
Bits("0b1111")

```

`Bits()` supports a variety of ways to represent data.

```doctest
...

# Binary.
>>> Bits("0xDEADBEEF").bin()
'0b1101_1110 0b1010_1101 0b1011_1110 0b1110_1111'

# Hexadecimal.
>>> Bits("0b10111010110111000000110111100101").hex(compact=True)
'0xBADC0DE5'

# Raw bytes (instantiated from an integer with provided bit_length).
>>> bytes(Bits(5735816763073854918203775149089, 104))
b'Hello, World!'

# Decode bytes with your favorite encoder!
>>> Bits("0x4F682C206869204D61726B21F09F988A").decode("utf-8")
'Oh, hi Mark!😊'

```

Quickly implement complex bit operations!

```doctest
...

# Implement a symmetric XOR cypher with ease! https://en.wikipedia.org/wiki/XOR_cipher
>>> secret_code = Bits('0xBF658DC46D3068D57F9F61DBC676666A9A689E75DBD46F31')

# XOR each bit with a bit from the key (the key repeats over the message)
>>> def xor_cypher(msg: Bits, key: Bits):
...     return Bits(a ^ b for i in range(0, len(msg), len(key)) for a, b in zip(msg[i : i+len(key)], key))

>>> decrypted = xor_cypher(secret_code, Bits("0xF100FBA11"))
>>> bytes(decrypted)
b'Never gonna give you up!'

# Because it's symmetric, you change it back with the same key!
>>> secret_code == xor_cypher(decrypted, Bits("0xF100FBA11"))
True

```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate and follow all linting procedures prescribed by the project file.

## Development install

To set up the development environment, fork or clone the repo and from inside the project directory run the
following is a shell separate from pycharm (Windows machines will need to run a shell with admin privileges):

```shell
sudo ./init-development.sh
```

On Windows, PyCharm will need to be fully closed and restarted.

This will install pyenv, poetry, and activate the git-hooks for the pre-commit config.

[Poetry](https://python-poetry.org/docs/master/) is used to manage the virtual environment, to add packages use:
`poetry add <package_name>`. Please visit the poetry website for further information and instruction.

Git hooks will run linting, type checking, and doctests on commit, if any checks fail the commit will be rejected.

## TODO

__Milestones for Version 1.0.0 release:__

- [ ] Create UnitTest suite.
- [ ] Code coverage in git-hooks.
- [ ] Create a workflow that publishes on PR merge to master.
- [ ] Workflow to bump patch on each commit, bump minor on each merge to master (major bump is left as manual)
- [ ] Add agument parsing to init-development.sh to allow uninstalling.
- [ ] Git hook to assert pyproject.toml matches .python-version and that version is installed
- [ ] Git hook to update pyenv on all OS's
- [ ] Git hook to create requrirements.txt (investigate if there is actual need for this)
- [ ] Add more of the default pre-commit-hooks for line endings etc.
- [ ] Add install validation to init-development.sh script.
- [ ] In init-development.sh, validate that pyenv-win\bin and pyenv-win\shims has not already been added to path.

## License

[MIT License](https://choosealicense.com/licenses/mit/)

Copyright (c) 2021 Derek Strasters

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.