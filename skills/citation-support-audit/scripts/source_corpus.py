"""Thin entry point for the vendored source-checker runtime."""

import sys

sys.dont_write_bytecode = True

from source_checker.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
