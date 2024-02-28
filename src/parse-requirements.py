#!/usr/bin/env python3

import click
from packaging.version import parse as version_parse

from pydepstools import screenout
from pydepstools.pypiclient import Client
from pydepstools.pypidata import PypiData


@click.command()
@click.argument(
    "requirements", type=click.Path(exists=True, dir_okay=False, readable=True)
)
def process(requirements):
    print("Starting")
    client = Client()
    screenout.VERBOSE = True

    for line in open(requirements):
        if not line.startswith("#"):
            package, version = line.strip().split("==")
            version = version_parse(version)
            print(f"{package} -> {version}")

            info = client.package_info(package)
            # pprint(info["releases"])
            # pprint(info.keys())
            # pprint(info["releases"].keys())
            # pprint(info["releases"])

            ppp = PypiData.from_data(info)
            for k, v in ppp.releases.items():
                print(k)
                for r in v:
                    print(f" - {r}")
            # print(ppp)

            # break


if __name__ == "__main__":
    process()
