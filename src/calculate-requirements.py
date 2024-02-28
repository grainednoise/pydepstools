#!/usr/bin/env python3

import click
from packaging.version import parse as version_parse

import pydepstools.screenout
from pydepstools.screenout import log_info, log_debug
from pydepstools.pypiclient import Client
from pydepstools.pypidata import PypiData
from pydepstools.pythonversions import validate_python_version, PythonType, PythonOs


@click.command()
@click.option(
    "--target-os",
    "-o",
    type=click.Choice(
        ["linux_86_64", "linux_32_64", "windows_32", "windows_64", "mac"]
    ),
    default="linux_86_64",
    show_default=True,
    help="The OS these requirements are for",
)
@click.option(
    "--python-version",
    "-v",
    type=click.UNPROCESSED,
    callback=validate_python_version,
    default="3.8",
    show_default=True,
    help="The target Python version for the requirements",
)
@click.option(
    "--python-type",
    "-t",
    type=click.Choice(["cp", "pp"]),
    default="cp",
    show_default=True,
    help="The target Python type for the requirements",
)
@click.option(
    "--verbose",
    "-v",
    type=bool,
    default=False,
    show_default=True,
    is_flag=True,
    help="Use verbose logging",
)
@click.argument(
    "requirements", type=click.Path(exists=True, dir_okay=False, readable=True)
)
def process(target_os, python_version, python_type, requirements, verbose):
    pydepstools.screenout.VERBOSE = verbose

    log_info(f"Starting {python_version} {target_os}")
    client = Client()

    python_type = PythonType(python_type)
    target_os = PythonOs(target_os)

    for line in open(requirements):
        if line.startswith("#"):
            print(line.strip())
        else:
            package, version = line.strip().split("==")
            version = version_parse(version)
            log_info(f"{package} -> {version}")

            info = client.package_info(package)
            # info = client.package_info("odfpy")
            # pprint(info["releases"])
            # pprint(info.keys())
            # pprint(info["releases"].keys())
            # pprint(info["releases"])

            ppp = PypiData.from_data(info)

            compatible_version = None
            compatible_release = None
            for release_version, releases in ppp.releases.items():
                if release_version < version:
                    log_debug(f"Too old: {release_version}")
                    continue
                else:
                    log_debug(release_version)

                compatible = False
                for r in releases:
                    compatible = r.is_compatible(python_version, python_type, target_os)
                    log_debug(f"!!!!!!!!!!!!!!!! - {r} - {compatible}")
                    if compatible:
                        compatible_release = r
                        compatible_version = release_version
                        break

                if compatible:
                    log_info(f"COMPATIBLE {compatible_version}: {compatible_release}")
                    print(f"{package}=={compatible_version}  # Upgraded from {version}")
                    break
            else:
                log_info("INCOMPATIBLE")
                raise Exception(f"No compatible version for {package} > {version}")
            # print(ppp)

            # break


#

if __name__ == "__main__":
    process()
