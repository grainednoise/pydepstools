import re
from dataclasses import dataclass
from typing import Dict, List

from packaging.version import parse, Version

from pydepstools.pythonversions import PackageType, PythonVersion, compatible_python_versions

python_classifier_regex = re.compile(
    r"^Programming Language :: Python :: (?P<version>\d\.\d+)$"
)


class Classifiers:
    python_versions: frozenset[Version]

    @staticmethod
    def from_classifier_list(data: List[str]) -> "Classifiers":
        versions = []
        for classifier in data:
            if mobj := python_classifier_regex.match(classifier):
                versions.append(parse(mobj.group("version")))

        return Classifiers(frozenset(versions))

    def __init__(self, python_versions: frozenset[Version]):
        self.python_versions = python_versions

    def __str__(self):
        return f"Classifiers(python_versions={self.python_versions})"


@dataclass(frozen=True)
class Release:
    filename: str
    packagetype: PackageType
    python_versions: PythonVersion
    requires_python: frozenset[Version] | None
    yanked: bool

    @staticmethod
    def from_release_data(data: dict) -> "Release":
        filename = data["filename"]
        packagetype = PackageType(data["packagetype"])
        python_version = PythonVersion.from_str(data["python_version"])
        requires_python = data["requires_python"]
        if requires_python is not None:
            requires_python = compatible_python_versions(requires_python)

        yanked = data["yanked"]

        return Release(filename, packagetype, python_version, requires_python, yanked)


class PypiInfo:
    classifiers: Classifiers

    @staticmethod
    def from_info(data: dict) -> "PypiInfo":
        classifiers = Classifiers.from_classifier_list(data["classifiers"])

        return PypiInfo(classifiers)

    def __init__(self, classifiers: Classifiers):
        self.classifiers = classifiers

    def __str__(self):
        return f"PypiInfo(classifiers={self.classifiers})"


pytz_atrocities_regex = re.compile(r"^20[01]\d[a-z]$")


class PypiData:
    info: PypiInfo
    releases: Dict[Version, List[Release]]

    @staticmethod
    def from_data(data: dict) -> "PypiData":
        info = PypiInfo.from_info(data["info"])

        releases = {}
        release_data = data["releases"]
        for v, r in release_data.items():
            if v == "2.0.0-final" or pytz_atrocities_regex.match(v):
                continue

            releases[parse(v)] = [Release.from_release_data(rr) for rr in r]

        return PypiData(info, releases)

    def __init__(self, info: PypiInfo, releases: Dict[Version, List[Release]]):
        self.info = info
        self.releases = releases

    def __str__(self):
        return f"PypiData(\ninfo={self.info}\nreleases={list(self.releases.keys())})"
