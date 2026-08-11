"""Optional local Hermes MCP smoke test.

This script never installs Hermes and never reads or prints secrets. Configure
the server in ~/.hermes/config.yaml first, then run this script.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="multicloud_semantic")
    args = parser.parse_args()
    executable = shutil.which("hermes")
    if executable is None:
        print("Hermes executable not available; smoke test not run.", file=sys.stderr)
        return 2
    completed = subprocess.run(
        [executable, "mcp", "test", args.server],
        check=False,
        capture_output=True,
        text=True,
    )
    sys.stdout.write(completed.stdout)
    if completed.returncode:
        sys.stderr.write(completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
