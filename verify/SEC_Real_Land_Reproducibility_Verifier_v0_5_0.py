#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence


SYSTEM_VERSION = "0.5.0"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def structural_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def result_material(record: Mapping[str, Any]) -> Dict[str, Any]:
    structural_result = {
        key: value
        for key, value in record.items()
        if key not in {"result_id", "evidence", "evidence_id"}
    }
    evidence = record["evidence"]
    return {
        "schema": "SEC-REAL-LAND-CENTRE-RESULT-MATERIAL-1-D02",
        "system_version": SYSTEM_VERSION,
        "profile_id": "SEC-REAL-LAND-AREA-VECTOR-CENTRE-1-D02",
        "algorithm_profile_hash": evidence["algorithm_profile_hash"],
        "dataset_sha256": evidence["dataset_sha256"],
        "structural_result": structural_result,
    }


def verify_record(record: Mapping[str, Any]) -> Dict[str, bool]:
    evidence = record.get("evidence", {})
    result_id_valid = structural_hash(result_material(record)) == record.get("result_id")
    evidence_id_valid = structural_hash(evidence) == record.get("evidence_id")
    evidence_result_link = evidence.get("result_id") == record.get("result_id")
    return {
        "result_id_valid": result_id_valid,
        "evidence_id_valid": evidence_id_valid,
        "evidence_result_link": evidence_result_link,
    }


def compare(fetch_record: Mapping[str, Any], offline_record: Mapping[str, Any]) -> Dict[str, Any]:
    fetch_checks = verify_record(fetch_record)
    offline_checks = verify_record(offline_record)

    result_fields = [
        "resolution_state",
        "centre_type",
        "identity_quantization_decimal_places",
        "latitude_deg",
        "longitude_deg",
        "unit_vector_xyz",
        "spherical_area_steradians",
        "surface_fraction",
    ]

    checks = [
        {
            "check_id": "FETCH_RESULT_ID_VALID",
            "pass": fetch_checks["result_id_valid"],
        },
        {
            "check_id": "FETCH_EVIDENCE_ID_VALID",
            "pass": fetch_checks["evidence_id_valid"] and fetch_checks["evidence_result_link"],
        },
        {
            "check_id": "OFFLINE_RESULT_ID_VALID",
            "pass": offline_checks["result_id_valid"],
        },
        {
            "check_id": "OFFLINE_EVIDENCE_ID_VALID",
            "pass": offline_checks["evidence_id_valid"] and offline_checks["evidence_result_link"],
        },
        {
            "check_id": "DATASET_IDENTITY_MATCH",
            "pass": fetch_record["evidence"]["dataset_sha256"] == offline_record["evidence"]["dataset_sha256"],
        },
        {
            "check_id": "PROFILE_IDENTITY_MATCH",
            "pass": fetch_record["evidence"]["algorithm_profile_hash"] == offline_record["evidence"]["algorithm_profile_hash"],
        },
        {
            "check_id": "STRUCTURAL_RESULT_MATCH",
            "pass": all(fetch_record.get(field) == offline_record.get(field) for field in result_fields),
        },
        {
            "check_id": "RESULT_ID_MATCH",
            "pass": fetch_record.get("result_id") == offline_record.get("result_id"),
        },
        {
            "check_id": "PROVENANCE_IS_SEPARATE_FROM_RESULT_ID",
            "pass": (
                fetch_record["evidence"].get("source_locator") != offline_record["evidence"].get("source_locator")
                and fetch_record.get("result_id") == offline_record.get("result_id")
            ),
        },
    ]

    passed = sum(1 for check in checks if check["pass"])
    total = len(checks)
    core = {
        "schema": "SEC-REAL-LAND-REPRODUCIBILITY-EVIDENCE-1-D02",
        "system_version": SYSTEM_VERSION,
        "status": "PASS" if passed == total else "FAIL",
        "passed": passed,
        "total": total,
        "dataset_sha256": fetch_record["evidence"]["dataset_sha256"],
        "result_id": fetch_record.get("result_id") if fetch_record.get("result_id") == offline_record.get("result_id") else None,
        "fetch_evidence_id": fetch_record.get("evidence_id"),
        "offline_evidence_id": offline_record.get("evidence_id"),
        "checks": checks,
    }
    return {**core, "reproducibility_evidence_id": structural_hash(core)}


def synthetic_record(locator: str, mode: str) -> Dict[str, Any]:
    structural_result = {
        "resolution_state": "RESOLVED_POINT",
        "centre_type": "SPHERICAL_SURFACE_AREA_VECTOR_CENTRE_DIRECTION",
        "identity_quantization_decimal_places": 9,
        "latitude_deg": 10.0,
        "longitude_deg": 20.0,
        "unit_vector_xyz": [0.925416578, 0.336824089, 0.173648178],
        "spherical_area_steradians": 1.0,
        "surface_fraction": 0.079577472,
    }
    material = {
        "schema": "SEC-REAL-LAND-CENTRE-RESULT-MATERIAL-1-D02",
        "system_version": SYSTEM_VERSION,
        "profile_id": "SEC-REAL-LAND-AREA-VECTOR-CENTRE-1-D02",
        "algorithm_profile_hash": "sha256:synthetic-profile",
        "dataset_sha256": "sha256:synthetic-data",
        "structural_result": structural_result,
    }
    result_id = structural_hash(material)
    evidence = {
        "schema": "SEC-REAL-LAND-CENTRE-EVIDENCE-1-D02",
        "system_version": SYSTEM_VERSION,
        "result_id": result_id,
        "dataset_sha256": "sha256:synthetic-data",
        "dataset_byte_length": 100,
        "feature_count": 1,
        "polygon_count": 1,
        "ring_count": 1,
        "vertex_count": 4,
        "source_locator": locator,
        "acquisition_mode": mode,
        "algorithm_profile_hash": "sha256:synthetic-profile",
        "identity_quantization_decimal_places": 9,
    }
    return {
        **structural_result,
        "result_id": result_id,
        "evidence": evidence,
        "evidence_id": structural_hash(evidence),
    }


def run_self_test() -> Dict[str, Any]:
    a = synthetic_record("https://example.test/data.geojson", "FETCH_URL")
    b = synthetic_record("data\\data.geojson", "LOCAL_FILE")
    result = compare(a, b)
    core = {
        "schema": "SEC-REAL-LAND-REPRODUCIBILITY-SELF-TEST-1-D02",
        "system_version": SYSTEM_VERSION,
        "status": result["status"],
        "passed": result["passed"],
        "total": result["total"],
        "checks": result["checks"],
    }
    return {**core, "evidence_id": structural_hash(core)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch-evidence", type=Path)
    parser.add_argument("--offline-evidence", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        result = run_self_test()
        print("STRUCTURAL EARTH CENTRE REAL LAND REPRODUCIBILITY VERIFIER v0.5.0")
        print("SELF TEST", result["status"])
        print("TOTAL", f"{result['passed']}/{result['total']}", result["status"])
        print("EVIDENCE ID", result["evidence_id"])
        return 0 if result["status"] == "PASS" else 1

    if args.fetch_evidence is None or args.offline_evidence is None:
        raise SystemExit("Provide --fetch-evidence and --offline-evidence, or use --self-test.")

    result = compare(load_json(args.fetch_evidence), load_json(args.offline_evidence))

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    for check in result["checks"]:
        print("PASS" if check["pass"] else "FAIL", check["check_id"])
    print("STRUCTURAL EARTH CENTRE REAL LAND REPRODUCIBILITY VERIFIER v0.5.0")
    print("STATUS", result["status"])
    print("TOTAL", f"{result['passed']}/{result['total']}", result["status"])
    print("DATASET", result["dataset_sha256"])
    print("RESULT ID", result["result_id"])
    print("REPRODUCIBILITY EVIDENCE ID", result["reproducibility_evidence_id"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
