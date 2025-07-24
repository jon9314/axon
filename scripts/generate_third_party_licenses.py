#!/usr/bin/env python
"""Generate THIRD_PARTY_LICENSES.md using pip-licenses."""

import pathlib
import subprocess
import sys

OUTPUT_FILE = pathlib.Path(__file__).resolve().parent.parent / "THIRD_PARTY_LICENSES.md"


def main() -> None:
    cmd = [sys.executable, "-m", "piplicenses", "--format=plain"]
    with OUTPUT_FILE.open("w") as f:
        subprocess.run(cmd, check=True, stdout=f)
    print(f"Wrote licenses to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
