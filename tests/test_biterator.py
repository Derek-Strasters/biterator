"""Tests for the biterator package."""

from biterator import __version__


def test_version():
    """Testing module and biterator module are on the same version"""
    assert __version__ == "0.1.0"
