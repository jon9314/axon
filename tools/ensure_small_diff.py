import subprocess
import sys


def run(cmd: list[str], allow_failure: bool = False) -> list[str] | None:
    """Run a command and return its output lines.

    Args:
        cmd: Command to run as list of strings
        allow_failure: If True, return None on failure instead of exiting

    Returns:
        List of output lines, or None if command failed and allow_failure=True
    """
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        if allow_failure:
            return None
        print(f"Failed to run {' '.join(cmd)}", file=sys.stderr)
        sys.exit(1)
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    # Get current branch name
    current_branch_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    current_branch = (
        current_branch_result.stdout.strip() if current_branch_result.returncode == 0 else ""
    )

    # Determine comparison base
    # If we're on main/master, compare to previous commit; otherwise compare to main
    if current_branch in ("main", "master"):
        # On main branch in CI, we just pushed changes, so compare to previous commit
        base_ref = "HEAD~1"
    else:
        base_ref = "main"

    # Try to get base files - may fail in shallow clones (CI)
    base_files_result = run(["git", "diff", "--name-only", f"{base_ref}...HEAD"], allow_failure=True)
    if base_files_result is None:
        print(
            f"⚠️  Skipping diff check: cannot access {base_ref} (shallow clone or missing history)",
            file=sys.stderr,
        )
        return 0

    base_files = set(base_files_result)
    modified_result = run(["git", "ls-files", "-m"], allow_failure=False)
    modified = set(modified_result or [])
    extra = [f for f in modified if f not in base_files]
    if len(extra) > 100:
        print(f"❌ tooling modified {len(extra)} unrelated files")
        for f in extra[:10]:
            print(f"  {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
