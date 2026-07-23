#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

SYSTEM_VERSION = "0.5.0"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def structural_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load module.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    node = shutil.which("node")
    if not node:
        print("STATUS UNSUPPORTED")
        print("REASON NODE_NOT_AVAILABLE")
        return 2

    corpus = json.loads((root / "profiles" / "SEC_Structural_Portability_Vectors_v0_5_0.json").read_text(encoding="utf-8"))
    py = load_module("sec_portability_py", root / "verify" / "SEC_Structural_Portability_Kernel_v0_5_0.py")
    python_outputs = {vector["vector_id"]: py.evaluate_vector(vector) for vector in corpus["vectors"]}

    completed = subprocess.run(
        [
            node,
            str(root / "verify" / "SEC_Structural_Portability_Parity_Extractor_v0_5_0.js"),
            "--root",
            str(root),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    javascript = json.loads(completed.stdout)

    checks = []

    def add(check_id: str, passed: bool, detail: Any) -> None:
        checks.append({"check_id": check_id, "pass": bool(passed), "detail": detail})
        if args.verbose:
            print("PASS" if passed else "FAIL", check_id, detail)

    add("SYSTEM_VERSION", javascript.get("system_version") == SYSTEM_VERSION, javascript.get("system_version"))
    add("VECTOR_SET_ID", javascript.get("vector_set_id") == corpus.get("vector_set_id"), javascript.get("vector_set_id"))
    add("VECTOR_CORPUS_ID", javascript.get("vector_corpus_id") == corpus.get("vector_corpus_id"), javascript.get("vector_corpus_id"))

    for vector in corpus["vectors"]:
        vector_id = vector["vector_id"]
        add(vector_id, python_outputs[vector_id] == javascript.get("outputs", {}).get(vector_id), vector_id)

    passed = sum(1 for check in checks if check["pass"])
    total = len(checks)
    core = {
        "schema": "SEC-STRUCTURAL-PORTABILITY-PARITY-EVIDENCE-1-D01",
        "system_version": SYSTEM_VERSION,
        "status": "PASS" if passed == total else "FAIL",
        "passed": passed,
        "total": total,
        "vector_set_id": corpus["vector_set_id"],
        "vector_corpus_id": corpus["vector_corpus_id"],
        "checks": checks,
    }
    evidence = {**core, "evidence_id": structural_hash(core)}

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    print("STRUCTURAL EARTH CENTRE STRUCTURAL PORTABILITY PARITY AUDITOR v0.5.0")
    print("STATUS", evidence["status"])
    print("TOTAL", f"{passed}/{total}", evidence["status"])
    print("EVIDENCE ID", evidence["evidence_id"])
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
