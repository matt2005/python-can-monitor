#!/usr/bin/env python3
"""
Entry point for running canmonitor as a module.

This allows the package to be executed with:
    python -m canmonitor
"""

from .canmonitor import run

if __name__ == "__main__":
    run()
