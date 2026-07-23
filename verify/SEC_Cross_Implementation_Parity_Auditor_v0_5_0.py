#!/usr/bin/env python3
"""Structural Earth Centre Cross-Implementation Parity Auditor v0.5.0."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence


SYSTEM_VERSION = "0.5.0"
PARITY_PROFILE = "SEC-PARITY-1-D01"
EVIDENCE_PROFILE = "SEC-PARITY-EVIDENCE-1-D01"

PARITY_FIELDS = (
    "resolution_state",
    "centre_type",
    "result",
    "canonical_carrier",
    "carrier_id",
    "dependency_fingerprint",
    "dependency_fingerprint_id",
    "result_id",
    "certificate_id",
    "profile_hash",
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def structural_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_kernel(path: Path):
    spec = importlib.util.spec_from_file_location("sec_reference_kernel", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load Python reference kernel.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def resolve_paths(root: Path) -> Dict[str, Path]:
    paths = {
        "kernel": root / "demo" / "Structural_Earth_Centre_Reference_Kernel_v0_5_0.py",
        "browser": root / "demo" / "Structural_Earth_Centre_Browser_Reference_v0_5_0.html",
        "corpus": root / "corpus" / "SEC_Conformance_Corpus_v0_5_0.json",
        "registry": root / "corpus" / "SEC_Profile_Registry_v0_5_0.json",
        "manifest": root / "corpus" / "SEC_Vector_Manifest_v0_5_0.json",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required file(s): " + "; ".join(missing))
    return paths


def python_export(kernel: Any, corpus: Mapping[str, Any], registry: Mapping[str, Any]) -> Dict[str, Any]:
    profiles = {
        profile["profile_id"]: {
            key: value
            for key, value in profile.items()
            if key != "profile_hash"
        }
        for profile in registry["profiles"]
    }
    profile_hashes = {
        profile["profile_id"]: profile["profile_hash"]
        for profile in registry["profiles"]
    }

    records = []
    for vector in corpus["vectors"]:
        actual = kernel.reconstruct_vector(vector, profiles)
        records.append(
            {
                "vector_id": vector["vector_id"],
                "category": vector["category"],
                "resolution_state": actual["result"]["resolution_state"],
                "centre_type": actual["result"]["centre_type"],
                "result": actual["result"],
                "canonical_carrier": actual["canonical_carrier"],
                "carrier_id": actual["carrier_id"],
                "dependency_fingerprint": actual["dependency_fingerprint"],
                "dependency_fingerprint_id": actual["dependency_fingerprint_id"],
                "result_id": actual["result_id"],
                "certificate_id": actual["certificate_id"],
                "profile_hash": profile_hashes[vector["centre_profile"]],
            }
        )

    return {
        "schema": "SEC-PYTHON-PARITY-EXPORT-1-D01",
        "system_version": SYSTEM_VERSION,
        "vector_count": len(records),
        "vector_set_id": corpus["vector_set_id"],
        "corpus_id": corpus["corpus_id"],
        "profile_registry_id": registry["profile_registry_id"],
        "records": records,
    }


def browser_export(extractor: Path, browser: Path) -> Dict[str, Any]:
    completed = subprocess.run(
        ["node", str(extractor), str(browser)],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError("Browser parity extraction failed.\n" + completed.stderr.strip())
    return json.loads(completed.stdout)


def compare_exports(
    python_data: Mapping[str, Any],
    browser_data: Mapping[str, Any],
) -> Dict[str, Any]:
    python_by_id = {record["vector_id"]: record for record in python_data["records"]}
    browser_by_id = {record["vector_id"]: record for record in browser_data["records"]}

    all_ids = sorted(set(python_by_id) | set(browser_by_id))
    records = []
    group_counts: Dict[str, Dict[str, int]] = {}

    for vector_id in all_ids:
        py = python_by_id.get(vector_id)
        br = browser_by_id.get(vector_id)
        category = (py or br or {}).get("category", "UNKNOWN")
        mismatches = []

        if py is None:
            mismatches.append("PYTHON_VECTOR_MISSING")
        elif br is None:
            mismatches.append("BROWSER_VECTOR_MISSING")
        else:
            for field in PARITY_FIELDS:
                if py.get(field) != br.get(field):
                    mismatches.append(field.upper() + "_MISMATCH")

        passed = not mismatches
        records.append(
            {
                "vector_id": vector_id,
                "category": category,
                "pass": passed,
                "mismatches": mismatches,
                "python_result_id": py.get("result_id") if py else None,
                "browser_result_id": br.get("result_id") if br else None,
                "python_certificate_id": py.get("certificate_id") if py else None,
                "browser_certificate_id": br.get("certificate_id") if br else None,
            }
        )

        group = group_counts.setdefault(category, {"pass": 0, "total": 0})
        group["total"] += 1
        if passed:
            group["pass"] += 1

    return {
        "records": records,
        "group_counts": dict(sorted(group_counts.items())),
        "passed": sum(1 for record in records if record["pass"]),
        "total": len(records),
    }


def build_evidence(
    paths: Mapping[str, Path],
    corpus: Mapping[str, Any],
    registry: Mapping[str, Any],
    manifest: Mapping[str, Any],
    python_data: Mapping[str, Any],
    browser_data: Mapping[str, Any],
    comparison: Mapping[str, Any],
) -> Dict[str, Any]:
    identity_match = (
        python_data["vector_set_id"] == browser_data["vector_set_id"] == corpus["vector_set_id"]
        and python_data["corpus_id"] == browser_data["corpus_id"] == corpus["corpus_id"]
        and python_data["profile_registry_id"]
        == browser_data["profile_registry_id"]
        == registry["profile_registry_id"]
    )

    browser_identity_pass = (
        browser_data.get("registry_identity_pass") is True
        and browser_data.get("corpus_identity_pass") is True
    )

    status = (
        "PASS"
        if comparison["passed"] == comparison["total"]
        and comparison["total"] == corpus["vector_count"]
        and identity_match
        and browser_identity_pass
        else "FAIL"
    )

    evidence_core = {
        "schema": "SEC-CROSS-IMPLEMENTATION-PARITY-EVIDENCE-1-D01",
        "system_version": SYSTEM_VERSION,
        "parity_profile": PARITY_PROFILE,
        "evidence_profile": EVIDENCE_PROFILE,
        "status": status,
        "frozen_identities": {
            "vector_set_id": corpus["vector_set_id"],
            "corpus_id": corpus["corpus_id"],
            "profile_registry_id": registry["profile_registry_id"],
            "manifest_id": manifest["manifest_id"],
        },
        "implementation_hashes": {
            "python_reference_kernel_sha256": file_sha256(paths["kernel"]),
            "browser_reference_sha256": file_sha256(paths["browser"]),
            "corpus_json_sha256": file_sha256(paths["corpus"]),
            "profile_registry_json_sha256": file_sha256(paths["registry"]),
            "vector_manifest_json_sha256": file_sha256(paths["manifest"]),
        },
        "identity_checks": {
            "cross_export_identity_match": identity_match,
            "browser_registry_identity_pass": browser_data.get("registry_identity_pass") is True,
            "browser_corpus_identity_pass": browser_data.get("corpus_identity_pass") is True,
        },
        "parity_fields": list(PARITY_FIELDS),
        "group_counts": comparison["group_counts"],
        "passed": comparison["passed"],
        "total": comparison["total"],
        "records": comparison["records"],
    }

    return {**evidence_core, "evidence_id": structural_hash(evidence_core)}


def print_summary(evidence: Mapping[str, Any]) -> None:
    print("STRUCTURAL EARTH CENTRE CROSS-IMPLEMENTATION PARITY v0.5.0")
    print("STATUS", evidence["status"])
    for category, counts in evidence["group_counts"].items():
        print(f"{category} {counts['pass']}/{counts['total']} PASS")
    print(f"TOTAL {evidence['passed']}/{evidence['total']} PASS")
    print("VECTOR SET", evidence["frozen_identities"]["vector_set_id"])
    print("CORPUS", evidence["frozen_identities"]["corpus_id"])
    print("PROFILE REGISTRY", evidence["frozen_identities"]["profile_registry_id"])
    print("EVIDENCE ID", evidence["evidence_id"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare Structural Earth Centre Python and browser reference implementations across the frozen corpus."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing demo/ and corpus/.",
    )
    parser.add_argument(
        "--extractor",
        type=Path,
        default=None,
        help="Path to SEC_Browser_Parity_Extractor_v0_5_0.js.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional JSON evidence output path.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print one parity line per vector.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    paths = resolve_paths(root)

    extractor = (
        args.extractor.resolve()
        if args.extractor is not None
        else Path(__file__).with_name("SEC_Browser_Parity_Extractor_v0_5_0.js")
    )
    if not extractor.is_file():
        raise FileNotFoundError(str(extractor))

    corpus = load_json(paths["corpus"])
    registry = load_json(paths["registry"])
    manifest = load_json(paths["manifest"])

    kernel = load_kernel(paths["kernel"])
    python_data = python_export(kernel, corpus, registry)
    browser_data = browser_export(extractor, paths["browser"])
    comparison = compare_exports(python_data, browser_data)
    evidence = build_evidence(
        paths,
        corpus,
        registry,
        manifest,
        python_data,
        browser_data,
        comparison,
    )

    if args.verbose:
        for record in evidence["records"]:
            if record["pass"]:
                print("PASS", record["vector_id"])
            else:
                print("FAIL", record["vector_id"], ",".join(record["mismatches"]))

    print_summary(evidence)

    if args.out is not None:
        output = args.out.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
