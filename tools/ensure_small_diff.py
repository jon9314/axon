import subprocess
import sys


def run(cmd: list[str]) -> list[str]:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
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

    base_files = set(run(["git", "diff", "--name-only", f"{base_ref}...HEAD"]))
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
