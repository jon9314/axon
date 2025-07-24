import subprocess
import sys


def run(cmd: list[str]) -> list[str]:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"Failed to run {' '.join(cmd)}", file=sys.stderr)
        sys.exit(1)
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    base_files = set(run(["git", "diff", "--name-only", "main...HEAD"]))
    modified = set(run(["git", "ls-files", "-m"]))
    extra = [f for f in modified if f not in base_files]
    if len(extra) > 100:
        print(f"\u274c tooling modified {len(extra)} unrelated files")
        for f in extra[:10]:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
