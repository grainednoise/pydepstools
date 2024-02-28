import re

import pytest
from packaging.version import Version, InvalidVersion

from pydepstools.pythonversions import compatible_python_versions


def test_compatible_versions1():
    compat = compatible_python_versions(">=3.6")
    assert compat == frozenset(
        [
            Version("3.6"),
            Version("3.7"),
            Version("3.8"),
            Version("3.9"),
            Version("3.10"),
            Version("3.11"),
            Version("3.12"),
        ]
    )


def test_compatible_versions2():
    compat = compatible_python_versions(
        ">=3.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.9.*"
    )
    assert compat == frozenset(
        [
            Version("3.7"),
            Version("3.8"),
            Version("3.10"),
            Version("3.11"),
            Version("3.12"),
        ]
    )


def test_compatible_versions3():
    compat = compatible_python_versions(">3.5.0")
    assert compat == frozenset(
        [
            Version("3.6"),
            Version("3.7"),
            Version("3.8"),
            Version("3.9"),
            Version("3.10"),
            Version("3.11"),
            Version("3.12"),
        ]
    )


def test_compatible_versions4():
    compat = compatible_python_versions("!=3.9*")

    assert compat == frozenset(
        [
            Version("2.7"),
            Version("3.6"),
            Version("3.7"),
            Version("3.8"),
            Version("3.10"),
            Version("3.11"),
            Version("3.12"),
        ]
    )


def test_compatible_versions5():
    compat = compatible_python_versions("<4")

    assert compat == frozenset(
        [
            Version("2.7"),
            Version("3.6"),
            Version("3.7"),
            Version("3.8"),
            Version("3.9"),
            Version("3.10"),
            Version("3.11"),
            Version("3.12"),
        ]
    )


def test_extend_version1():
    with pytest.raises(InvalidVersion):
        Version("2.0.0-final")


def test_tag():
    assert P
