import re
from dataclasses import dataclass
from enum import StrEnum, auto

from packaging.version import Version

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

regex_op = re.compile(r"^(?P<operation>>=|!=|>|<=|<)(?P<version>\d\.\d+)(\.0|\.\*|\*)?$")

regex_op_subversion = re.compile(r"^(?P<operation>>=)(?P<version>\d\.\d+\.\d+)$")


def compatible_python_versions(
        requires: str, available_versions=released_python_versions
):
    remaining = released_python_versions

    for part in requires.split(","):
        part = part.strip()
        if part == "<4":
            pass    # Basically a NOOP

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


class PackageType(StrEnum):
    SDIST = auto()
    BDIST_WHEEL = auto()
    BDIST_EGG = auto()
    BDIST_WININST = auto()
    BDIST_MSI = auto()


class PythonType(StrEnum):
    CPYTHON = "cp"
    PYPY = "pp"


python_version_regex = re.compile(r"^(?P<type>\w\w)(?P<major>\d)(?P<minor>\d+)$")


class PythonVersionType(StrEnum):
    FULLY_SPECIFIED = auto()
    VERSION_SPECIFIED = auto()
    ANY_2_OR_3 = auto()
    ANY_2 = auto()
    ANY_3 = auto()
    SOURCE = auto()


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

        if data == "py2.py3" or data == "any" or data == "sdk":  # Old azure stuff uses 'sdk'
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
            raise ValueError(f"Unparsable python version: {data}")
        python_type = PythonType(mobj.group("type"))
        python_version = Version(f"{mobj.group('major')}.{mobj.group('minor')}")
        return PythonVersion(
            PythonVersionType.FULLY_SPECIFIED, python_type, python_version
        )
