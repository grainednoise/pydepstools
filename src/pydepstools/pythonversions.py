import re
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

import click
from packaging.version import Version, InvalidVersion

from pydepstools.screenout import log_debug

released_python_versions = frozenset(
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


def validate_python_version(ctx, param, value):
    if isinstance(value, Version):
        return value

    try:
        version = Version(value)

    except InvalidVersion as e:
        raise click.BadParameter(str(e))

    if version not in released_python_versions:
        raise click.BadParameter("Not a released Python version")

    return version


regex_op = re.compile(
    r"^(?P<operation>>=|!=|>|<=|<)(?P<version>\d\.\d+)(\.0|\.\*|\*)?$"
)

regex_op_subversion = re.compile(r"^(?P<operation>>=)(?P<version>\d\.\d+\.\d+)$")


def compatible_python_versions(
    requires: str, available_versions=released_python_versions
):
    remaining = released_python_versions

    for part in requires.split(","):
        part = part.strip()
        if part == "<4":
            pass  # Basically a NOOP

        elif mobj := regex_op.match(part):
            operation = mobj.group("operation")
            version = Version(mobj.group("version"))

            if operation == ">=":
                remaining = {v for v in remaining if v >= version}

            if operation == ">":
                remaining = {v for v in remaining if v > version}

            if operation == "<=":
                remaining = {v for v in remaining if v <= version}

            if operation == "<":
                remaining = {v for v in remaining if v < version}

            elif operation == "!=":
                remaining = {v for v in remaining if v != version}

        elif mobj := regex_op_subversion.match(part):
            operation = mobj.group("operation")
            version = Version(mobj.group("version"))
            version = Version(f"{version.major}.{version.minor + 1}")

            if operation == ">=":
                remaining = {v for v in remaining if v >= version}
        else:
            raise Exception(f"What? {part}")

    return frozenset(remaining)


class PackageType(Enum):
    SDIST = "sdist"
    BDIST_WHEEL = "bdist_wheel"
    BDIST_EGG = "bdist_egg"
    BDIST_WININST = "bdist_wininst"
    BDIST_MSI = "bdist_msi"


class PythonType(Enum):
    CPYTHON = "cp"
    PYPY = "pp"

    def is_compatible_abi_tag(self, abi_tag: str, python_version: Version) -> bool:
        if self == PythonType.CPYTHON:
            if abi_tag == "abi3":
                return True

            if abi_tag == f"cp{python_version.major}{python_version.minor}":
                return True

            return False

        raise Exception("Only cpython supported")



class PythonOs(Enum):
    LINUX_86_64 = "linux_86_64"
    LINUX_32_64 = "linux_32_64"
    MAC = "mac"
    WINDOWS_64 = "windows_64"
    WINDOWS_32 = "windows_32"

    def is_platform_tag_compatible(self, platform_tag: str):
        if self == PythonOs.LINUX_86_64:
            return platform_tag in {
                "manylinux1_x86_64",
                "manylinux2010_x86_64",
                # "musllinux_1_1_x86_64",
                "manylinux_2_17_x86_64",
                "manylinux2014_x86_64",
            }

        if self == PythonOs.LINUX_32_64:
            return platform_tag in {
                "manylinux1_i686",
                "manylinux2010_i686",
                # "musllinux_1_1_i686",
                "manylinux_2_5_i686",
                "manylinux_2_17_i686",
                "manylinux2014_i686",
            }

        if self == PythonOs.WINDOWS_64:
            return platform_tag in ("win_amd64",)

        if self == PythonOs.WINDOWS_32:
            return platform_tag in ("win32",)

        return False


python_tag_regex = re.compile(r"^(?P<type>cp|pp)(?P<major>[23])(?P<minor>\d+)$")


def split_tagged_python_version(tag: str) -> Tuple[PythonType, Version]:
    mobj = python_version_regex.match(tag)
    if mobj is None:
        raise ValueError(f"Unparsable tag: {tag}")

    return PythonType(mobj.group("type")), Version(
        f"{mobj.group('major')}.{mobj.group('minor')}"
    )


python_version_regex = re.compile(r"^(?P<type>\w\w)(?P<major>\d)(?P<minor>\d+)$")


class PythonVersionType(Enum):
    FULLY_SPECIFIED = "fully_specified"
    VERSION_SPECIFIED = "version_specified"
    ANY_2_OR_3 = "py2.py3"
    ANY_2 = "py2"
    ANY_3 = "py3"
    SOURCE = "source"


@dataclass(frozen=True)
class PythonVersion:
    version_type: PythonVersionType
    type: PythonType | None
    version: Version | None

    @staticmethod
    def from_str(data: str) -> "PythonVersion":
        if data == "source":
            return PythonVersion(PythonVersionType.SOURCE, None, None)

        if data == "py2":
            return PythonVersion(PythonVersionType.ANY_2, None, None)

        if (
            data == "py2.py3" or data == "any" or data == "sdk"
        ):  # Old azure stuff uses 'sdk'
            return PythonVersion(PythonVersionType.ANY_2_OR_3, None, None)

        if data == "py3":
            return PythonVersion(PythonVersionType.ANY_3, None, None)

        try:
            return PythonVersion(
                PythonVersionType.VERSION_SPECIFIED, None, Version(data)
            )

        except:
            pass

        mobj = python_version_regex.match(data)
        if mobj is None:
            raise ValueError(f"Unparseable python version: {data}")
        python_type = PythonType(mobj.group("type"))
        python_version = Version(f"{mobj.group('major')}.{mobj.group('minor')}")
        return PythonVersion(
            PythonVersionType.FULLY_SPECIFIED, python_type, python_version
        )

    def is_compatible(
        self, python_version: Version, python_type: PythonType = PythonType.CPYTHON
    ) -> bool:
        if self.version_type in (
            PythonVersionType.SOURCE,
            PythonVersionType.ANY_2_OR_3,
        ):
            return True

        elif self.version_type == PythonVersionType.ANY_2:
            return python_version.major == 2

        elif self.version_type == PythonVersionType.ANY_3:
            return python_version.major == 3

        elif self.version_type == PythonVersionType.VERSION_SPECIFIED:
            return python_version == self.version

        elif self.version_type == PythonVersionType.FULLY_SPECIFIED:
            return python_version == self.version and python_type == self.version_type

        raise Exception(f"unhandled PythonVersionType enum: {self.version_type}")
