#!/usr/bin/env python3
"""Structural Earth Centre v0.5.0 repository verification runner.

Runs the bounded command-line verification stack from one entry point and
checks the declared frozen technical surface for transient Python bytecode.
When manifest checking is enabled, SHA256SUMS.txt must exactly cover every
file under corpus/, data/, demo/, evidence/, profiles/, and verify/.

The runner uses only the Python standard library and does not modify repository
artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

VERSION = "0.5.0"
MANIFEST_NAME = "SHA256SUMS.txt"
FREEZE_DIRS = ("corpus", "data", "demo", "evidence", "profiles", "verify")
FORBIDDEN_DIR_NAMES = {"__pycache__"}
FORBIDDEN_FILE_SUFFIXES = {".pyc", ".pyo"}
MANIFEST_RE = re.compile(r"^([0-9a-fA-F]{64})  (.+)$")


@dataclass(frozen=True)
class Stage:
    name: str
    args: tuple[str, ...]
    expected: str
    supports_verbose: bool = False


STAGES: tuple[Stage, ...] = (
    Stage(
        "CORE",
        (
            "demo/Structural_Earth_Centre_Reference_Kernel_v0_5_0.py",
            "--corpus",
            "corpus",
            "--audit",
        ),
        "TOTAL 38/38 PASS",
        True,
    ),
    Stage(
        "CORE PARITY",
        (
            "verify/SEC_Cross_Implementation_Parity_Auditor_v0_5_0.py",
            "--root",
            ".",
        ),
        "TOTAL 38/38 PASS",
        True,
    ),
    Stage(
        "EARTH PROFILES",
        (
            "verify/SEC_Earth_Profile_Validator_v0_5_0.py",
            "--profiles",
            "profiles",
        ),
        "TOTAL 20/20 PASS",
        True,
    ),
    Stage(
        "REAL-LAND SELF-TEST",
        (
            "verify/SEC_Real_Land_Centre_Resolver_v0_5_0.py",
            "--self-test",
        ),
        "TOTAL 26/26 PASS",
    ),
    Stage(
        "REPRODUCIBILITY SELF-TEST",
        (
            "verify/SEC_Real_Land_Reproducibility_Verifier_v0_5_0.py",
            "--self-test",
        ),
        "TOTAL 9/9 PASS",
    ),
    Stage(
        "STORED REPRODUCIBILITY",
        (
            "verify/SEC_Real_Land_Reproducibility_Verifier_v0_5_0.py",
            "--fetch-evidence",
            "evidence/SEC_Real_Land_Centre_Natural_Earth_110m_Fetch_v0_5_0.json",
            "--offline-evidence",
            "evidence/SEC_Real_Land_Centre_Natural_Earth_110m_Offline_v0_5_0.json",
        ),
        "TOTAL 9/9 PASS",
    ),
    Stage(
        "STRUCTURAL INNOVATION",
        (
            "verify/SEC_Structural_Centre_Resolver_v0_5_0.py",
            "--audit",
        ),
        "TOTAL 24/24 PASS",
        True,
    ),
    Stage(
        "INNOVATION PARITY",
        (
            "verify/SEC_Structural_Centre_Innovation_Parity_Auditor_v0_5_0.py",
            "--root",
            ".",
        ),
        "TOTAL 18/18 PASS",
        True,
    ),
    Stage(
        "SAME-DATASET DIFFERENTIAL",
        (
            "verify/SEC_Real_Land_Profile_Differential_v0_5_0.py",
            "--root",
            ".",
        ),
        "TOTAL 13/13 PASS",
        True,
    ),
    Stage(
        "ADVANCED STRUCTURAL",
        (
            "verify/SEC_Structural_Centre_Advanced_Resolver_v0_5_0.py",
            "--audit",
        ),
        "TOTAL 30/30 PASS",
        True,
    ),
    Stage(
        "ADVANCED STRUCTURAL PARITY",
        (
            "verify/SEC_Structural_Centre_Advanced_Parity_Auditor_v0_5_0.py",
            "--root",
            ".",
        ),
        "TOTAL 22/22 PASS",
        True,
    ),
    Stage(
        "STRUCTURAL PORTABILITY",
        (
            "verify/SEC_Structural_Portability_Kernel_v0_5_0.py",
            "--profiles",
            "profiles",
            "--audit",
        ),
        "TOTAL 40/40 PASS",
        True,
    ),
    Stage(
        "PORTABILITY PARITY",
        (
            "verify/SEC_Structural_Portability_Parity_Auditor_v0_5_0.py",
            "--root",
            ".",
        ),
        "TOTAL 27/27 PASS",
        True,
    ),
)


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def frozen_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for directory_name in FREEZE_DIRS:
        directory = root / directory_name
        if not directory.is_dir():
            raise FileNotFoundError(f"MISSING_FREEZE_DIRECTORY: {directory_name}")
        result.extend(path for path in directory.rglob("*") if path.is_file())
    return sorted(result, key=lambda path: relative_posix(path, root))


def find_forbidden_artifacts(root: Path) -> list[str]:
    hits: list[str] = []
    for directory_name in FREEZE_DIRS:
        directory = root / directory_name
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_dir() and path.name in FORBIDDEN_DIR_NAMES:
                hits.append(relative_posix(path, root) + "/")
            elif path.is_file() and path.suffix.lower() in FORBIDDEN_FILE_SUFFIXES:
                hits.append(relative_posix(path, root))
    return sorted(set(hits))


def parse_manifest(manifest_path: Path) -> dict[str, str]:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"MISSING_MANIFEST: {manifest_path.name}")

    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        manifest_path.read_text(encoding="ascii").splitlines(), start=1
    ):
        if not raw_line.strip():
            continue
        match = MANIFEST_RE.fullmatch(raw_line)
        if not match:
            raise ValueError(f"MALFORMED_MANIFEST_LINE: {line_number}")

        digest = match.group(1).lower()
        relative_path = match.group(2)
        candidate = Path(relative_path)

        if "\\" in relative_path or candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"UNSAFE_MANIFEST_PATH: {relative_path}")
        if relative_path in entries:
            raise ValueError(f"DUPLICATE_MANIFEST_ENTRY: {relative_path}")

        entries[relative_path] = digest

    if not entries:
        raise ValueError("EMPTY_MANIFEST")
    return entries


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_manifest(root: Path, verbose: bool) -> tuple[bool, str]:
    manifest_path = root / MANIFEST_NAME
    try:
        entries = parse_manifest(manifest_path)
        actual_paths = {relative_posix(path, root) for path in frozen_files(root)}
    except (FileNotFoundError, ValueError) as exc:
        return False, str(exc)

    manifest_paths = set(entries)
    missing_from_manifest = sorted(actual_paths - manifest_paths)
    missing_from_disk = sorted(manifest_paths - actual_paths)

    if missing_from_manifest or missing_from_disk:
        if verbose:
            for path in missing_from_manifest:
                print(f"  MISSING_FROM_MANIFEST {path}")
            for path in missing_from_disk:
                print(f"  MANIFEST_ENTRY_MISSING_FROM_DISK {path}")
        details = (
            f"manifest={len(manifest_paths)} disk={len(actual_paths)} "
            f"missing_from_manifest={len(missing_from_manifest)} "
            f"missing_from_disk={len(missing_from_disk)}"
        )
        return False, details

    mismatches: list[str] = []
    for relative_path in sorted(entries):
        actual_digest = sha256_file(root / Path(relative_path))
        if actual_digest != entries[relative_path]:
            mismatches.append(relative_path)
            if verbose:
                print(f"  HASH_MISMATCH {relative_path}")

    if mismatches:
        return False, f"{len(mismatches)} hash mismatch(es)"
    return True, f"{len(entries)}/{len(entries)} PASS"


def stage_entrypoints(root: Path) -> list[str]:
    missing: list[str] = []
    for stage in STAGES:
        script_path = root / stage.args[0]
        if not script_path.is_file():
            missing.append(stage.args[0])
    return sorted(set(missing))


def build_stage_command(stage: Stage, verbose: bool) -> list[str]:
    command = [sys.executable, "-B", *stage.args]
    if verbose and stage.supports_verbose:
        command.append("--verbose")
    return command


def run_stage(root: Path, stage: Stage, verbose: bool) -> tuple[bool, str, str]:
    command = build_stage_command(stage, verbose)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    completed = subprocess.run(
        command,
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    combined = (completed.stdout or "") + (completed.stderr or "")
    passed = completed.returncode == 0 and stage.expected in combined

    if completed.returncode != 0:
        reason = f"exit={completed.returncode}"
    elif stage.expected not in combined:
        reason = f"missing expected marker: {stage.expected}"
    else:
        reason = stage.expected
    return passed, reason, combined.rstrip()


def print_child_output(output: str) -> None:
    if not output:
        return
    for line in output.splitlines():
        print(f"    {line}")


def run_self_test(root: Path, verbose: bool) -> int:
    print(f"STRUCTURAL EARTH CENTRE VERIFICATION RUNNER v{VERSION}")
    print("MODE SELF-TEST")

    checks: list[tuple[str, bool, str]] = []

    python_ok = sys.version_info >= (3, 10)
    checks.append(("PYTHON_VERSION", python_ok, sys.version.split()[0]))

    missing_dirs = [name for name in FREEZE_DIRS if not (root / name).is_dir()]
    checks.append(
        (
            "FREEZE_DIRECTORIES",
            not missing_dirs,
            "OK" if not missing_dirs else ", ".join(missing_dirs),
        )
    )

    missing_entrypoints = stage_entrypoints(root)
    checks.append(
        (
            "VERIFICATION_ENTRYPOINTS",
            not missing_entrypoints,
            "OK" if not missing_entrypoints else ", ".join(missing_entrypoints),
        )
    )

    node = shutil.which("node")
    checks.append(("NODE_AVAILABLE", node is not None, node or "NOT FOUND"))

    forbidden = find_forbidden_artifacts(root)
    checks.append(
        (
            "FREEZE_HYGIENE",
            not forbidden,
            "OK" if not forbidden else f"{len(forbidden)} forbidden artifact(s)",
        )
    )

    try:
        manifest_entries = parse_manifest(root / MANIFEST_NAME)
        manifest_ok = True
        manifest_detail = f"{len(manifest_entries)} syntactically valid entries"
    except (FileNotFoundError, ValueError) as exc:
        manifest_ok = False
        manifest_detail = str(exc)
    checks.append(("MANIFEST_SYNTAX", manifest_ok, manifest_detail))

    passed = 0
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"{status} {name} - {detail}")
        if ok:
            passed += 1
        elif verbose and name == "FREEZE_HYGIENE":
            for path in forbidden:
                print(f"  FORBIDDEN {path}")

    print(f"TOTAL {passed}/{len(checks)} {'PASS' if passed == len(checks) else 'FAIL'}")
    print(f"FINAL STATUS {'PASS' if passed == len(checks) else 'FAIL'}")
    return 0 if passed == len(checks) else 1


def run_full(root: Path, skip_manifest: bool, verbose: bool) -> int:
    print(f"STRUCTURAL EARTH CENTRE VERIFICATION RUNNER v{VERSION}")
    print(f"ROOT {root}")
    print(f"PYTHON {sys.version.split()[0]}")
    print(f"NODE {shutil.which('node') or 'NOT FOUND'}")

    if sys.version_info < (3, 10):
        print("FAIL PYTHON_VERSION - Python 3.10 or newer is required")
        print("FINAL STATUS FAIL")
        return 1

    missing_entrypoints = stage_entrypoints(root)
    if missing_entrypoints:
        for path in missing_entrypoints:
            print(f"FAIL MISSING_VERIFICATION_ENTRYPOINT {path}")
        print("FINAL STATUS FAIL")
        return 1

    if shutil.which("node") is None:
        print("FAIL NODE_AVAILABLE - Node.js is required for parity verification")
        print("FINAL STATUS FAIL")
        return 1

    forbidden_before = find_forbidden_artifacts(root)
    if forbidden_before:
        print(f"FAIL FREEZE_HYGIENE - {len(forbidden_before)} forbidden artifact(s)")
        for path in forbidden_before:
            print(f"  FORBIDDEN {path}")
        print("FINAL STATUS FAIL")
        return 1
    print("PASS FREEZE_HYGIENE")

    if skip_manifest:
        print("SKIP SHA256_MANIFEST - disabled by command-line option")
    else:
        manifest_ok, manifest_detail = verify_manifest(root, verbose)
        print(f"{'PASS' if manifest_ok else 'FAIL'} SHA256_MANIFEST - {manifest_detail}")
        if not manifest_ok:
            print("FINAL STATUS FAIL")
            return 1

    passed_stages = 0
    for index, stage in enumerate(STAGES, start=1):
        passed, reason, output = run_stage(root, stage, verbose)
        print(f"{'PASS' if passed else 'FAIL'} [{index:02d}/{len(STAGES):02d}] {stage.name} - {reason}")
        if verbose or not passed:
            print_child_output(output)
        if not passed:
            print(f"TOTAL STAGES {passed_stages}/{len(STAGES)} PASS")
            print("FINAL STATUS FAIL")
            return 1
        passed_stages += 1

    forbidden_after = find_forbidden_artifacts(root)
    if forbidden_after:
        print(f"FAIL POST_RUN_HYGIENE - {len(forbidden_after)} forbidden artifact(s)")
        for path in forbidden_after:
            print(f"  FORBIDDEN {path}")
        print(f"TOTAL STAGES {passed_stages}/{len(STAGES)} PASS")
        print("FINAL STATUS FAIL")
        return 1
    print("PASS POST_RUN_HYGIENE")

    print(f"TOTAL STAGES {passed_stages}/{len(STAGES)} PASS")
    print("FINAL STATUS PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Structural Earth Centre v0.5.0 command-line verification stack "
            "and enforce the declared frozen technical surface."
        )
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Validate runner prerequisites and configuration without running the full stack.",
    )
    parser.add_argument(
        "--skip-manifest",
        action="store_true",
        help=(
            "Skip SHA256SUMS.txt completeness and digest verification for runs that "
            "intentionally do not enforce the repository manifest."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show child verifier output and detailed manifest diagnostics.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repository_root()
    if args.self_test:
        return run_self_test(root, args.verbose)
    return run_full(root, args.skip_manifest, args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
