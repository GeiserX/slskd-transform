"""Backwards-compatibility shim. Use `slskd-transform rename` instead."""
import sys

from slskd_transform.cli import cli

if __name__ == '__main__':
    cli(["rename"])
