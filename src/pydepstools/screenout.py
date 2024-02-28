from typing import Any

import click

VERBOSE = False


def log_info(msg: Any, nl: bool = True):
    click.secho(msg, nl=nl, err=True, bold=True, fg="white")


def log_debug(msg: Any, nl: bool = True):
    if VERBOSE:
        click.secho(msg, nl=nl, err=True, dim=True, fg="white")
