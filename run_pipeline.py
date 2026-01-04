import os
import subprocess
import sys
from typing import List, Tuple


def _parse_args(argv: List[str]) -> Tuple[bool, List[str]]:
    """
    Returns (cleanup_enabled, forwarded_args_for_main).
    """
    cleanup_enabled = True
    forwarded: List[str] = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--no-cleanup":
            cleanup_enabled = False
            i += 1
            continue
        forwarded.append(arg)
        i += 1

    return cleanup_enabled, forwarded


def run() -> None:
    project_root = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(project_root, "main.py")
    cleanup_py = os.path.join(project_root, "cleanup.py")

    print("Starting automated crypto video pipeline...")

    if not os.path.exists(main_py):
        print(f"Error: main.py not found at {main_py}")
        sys.exit(1)

    cleanup_enabled, forwarded_args = _parse_args(sys.argv[1:])

    # Provide cwd-independent defaults for scheduled runs.
    if "--token-file" not in forwarded_args:
        forwarded_args += ["--token-file", os.path.join(project_root, "token.json")]
    if "--client-secrets" not in forwarded_args:
        forwarded_args += ["--client-secrets", os.path.join(project_root, "client_secrets.json")]

    cmd = [sys.executable, main_py, "--fetch", "--upload", "--privacy", "public"] + forwarded_args
    print(f"Running command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=False, cwd=project_root)
        exit_code = result.returncode
        if exit_code == 0:
            print("Pipeline completed successfully.")
        else:
            print(f"Pipeline failed with exit code {exit_code}")
    except KeyboardInterrupt:
        print("\nPipeline cancelled by user.")
        exit_code = 1
    finally:
        if cleanup_enabled:
            if os.path.exists(cleanup_py):
                cleanup_cmd = [sys.executable, cleanup_py, "--all"]
                print(f"Running cleanup: {' '.join(cleanup_cmd)}")
                cleanup_result = subprocess.run(cleanup_cmd, check=False, cwd=project_root)
                if cleanup_result.returncode != 0:
                    print(f"Cleanup failed with exit code {cleanup_result.returncode}")
            else:
                print(f"Cleanup skipped (cleanup.py not found at {cleanup_py})")

    sys.exit(exit_code)


if __name__ == "__main__":
    run()

