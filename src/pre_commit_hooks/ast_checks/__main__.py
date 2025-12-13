"""Entry point for running ast_checks as a module.

Usage: python -m pre_commit_hooks.ast_checks
"""

import sys

from . import main

if __name__ == "__main__":
    sys.exit(main())
