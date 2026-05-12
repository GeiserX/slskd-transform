"""Backwards-compatibility shim. Use `slskd-transform rename` instead."""
from slskd_transform.cli import cli

if __name__ == '__main__':
    cli(["rename"])
