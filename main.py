"""Backwards-compatibility shim. Use `slskd-transform search` instead."""
import sys

from slskd_transform.cli import cli

if __name__ == '__main__':
    cli(["search"])
