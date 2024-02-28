import re
from dataclasses import dataclass
from typing import Dict, List

from packaging.version import parse, Version
from wheel_filename import parse_wheel_filename

from pydepstools.pythonversions import (
    PackageType,
    PythonVersion,
    compatible_python_versions,
    PythonType,
    PythonOs, split_tagged_python_version,
)
from pydepstools.screenout import log_debug

python_classifier_regex = re.compile(
    r"^Programming Language :: Python :: (?P<version>\d\.\d+)$"
)


@dataclass(frozen=True)
class Classifiers:
    python_versions: frozenset[Version]

    @staticmethod
    def from_classifier_list(data: List[str]) -> "Classifiers":
        versions = []
        for classifier in data:
            if mobj := python_classifier_regex.match(classifier):
                versions.append(parse(mobj.group("version")))

        return Classifiers(frozenset(versions))


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

    def is_compatible(
        self,
        python_version,
        python_type: PythonType.CPYTHON,
        target_os: PythonOs = PythonOs.LINUX_86_64,
    ) -> bool:
        if self.yanked:
            log_debug("yanked")
            return False

        if self.packagetype != PackageType.BDIST_WHEEL:
            log_debug("Not a wheel")
            return False

        if self.requires_python is None:
            if not self.python_versions.is_compatible(python_version):
                log_debug(f"python_versions problem: {self.python_versions}")
                return False
        else:
            if python_version not in self.requires_python:
                log_debug(f"unsupported requires: {self.requires_python}")
                return False

        log_debug(f"Need to check {self.filename}")
        parsed = parse_wheel_filename(self.filename)
        log_debug(f"Parsed {parsed._asdict()}")

        assert len(parsed.abi_tags) < 2, f"ABI {parsed.abi_tags}"
        if "none" not in parsed.abi_tags:
            if not any(
                map(
                    lambda abi_tag: python_type.is_compatible_abi_tag(abi_tag, python_version),
                    parsed.abi_tags),
            ):
                log_debug(f"Bad ABI tags: {parsed.abi_tags}")
                return False

        # if "abi3" in parsed.abi_tags:
            if not any(
                map(
                    lambda tag: target_os.is_platform_tag_compatible(tag),
                    parsed.platform_tags,
                )
            ):
                log_debug(f"Bad platform: {parsed.platform_tags}")
                return False

            log_debug("abi3 check ok")

            # Relaxed version check, as the build may be for a previous version
            for pt in parsed.python_tags:
                tp, vr = split_tagged_python_version(pt)
                if tp == python_type and vr <= python_version:
                    break

            else:
                log_debug(f"Incompatible type ({python_type}) or version (>= {python_version})")
                return False

            return True

        else:
            if "any" not in parsed.platform_tags:
                log_debug(f"Bad platform2: {parsed.platform_tags}")
                return False

            # TODO check parsed.python_tags?

            if not self.python_versions.is_compatible(python_version):
                log_debug(f"incompatible python_versions problem: {self.python_versions}")
                return False

            return True

        # log_debug(f"Need to check {self.filename}")
        # parsed = parse_wheel_filename(self.filename)
        # log_debug(f"Parsed {parsed._asdict()}")
        log_debug("fall")
        return False


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


@dataclass(frozen=True)
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

        releases = {rel: releases[rel] for rel in sorted(releases.keys())}

        return PypiData(info, releases)
