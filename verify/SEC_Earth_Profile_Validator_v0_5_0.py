#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def structural_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_self_hash(obj: Mapping[str, Any], field: str) -> bool:
    expected = obj[field]
    body = {k: v for k, v in obj.items() if k != field}
    return structural_hash(body) == expected


def has_conflict(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 1


def resolve_vector(vector: Mapping[str, Any], profile: Mapping[str, Any]) -> Dict[str, Any]:
    claim_scope = vector["claim_scope"]
    dependencies = vector["dependencies"]

    if claim_scope not in profile["admitted_claim_scopes"]:
        return {"resolution_state": "UNSUPPORTED"}

    for rule in profile["conflict_rules"]:
        if rule == "SINGLE_FRAME_REQUIRED" and has_conflict(dependencies.get("frame")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_FRAME_REALIZATION_REQUIRED" and has_conflict(dependencies.get("frame_realization")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_EPOCH_REQUIRED" and has_conflict(dependencies.get("epoch")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_MASS_SCOPE_REQUIRED" and has_conflict(dependencies.get("mass_scope")):
            return {"resolution_state": "CONFLICT"}
        if rule == "AT_MOST_ONE_SYMMETRY_BREAKER" and has_conflict(dependencies.get("symmetry_breaker")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_LAND_MASK_REQUIRED" and has_conflict(dependencies.get("land_mask_id")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_COASTLINE_POLICY_REQUIRED" and has_conflict(dependencies.get("coastline_policy")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_POPULATION_DATASET_REQUIRED" and has_conflict(dependencies.get("population_dataset_id")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_ALLOCATION_RULE_REQUIRED" and has_conflict(dependencies.get("allocation_rule")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_METRIC_REQUIRED" and has_conflict(dependencies.get("metric")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_GRAVITY_MODEL_REQUIRED" and has_conflict(dependencies.get("gravity_model_id")):
            return {"resolution_state": "CONFLICT"}
        if rule == "SINGLE_OBJECTIVE_REQUIRED" and has_conflict(dependencies.get("objective")):
            return {"resolution_state": "CONFLICT"}

    missing = [key for key in profile["required_dependencies"] if key not in dependencies]
    if missing:
        return {"resolution_state": "INCOMPLETE", "missing_dependencies": missing}

    mode = profile["resolution_mode"]

    if mode in {"DECLARED_GEOMETRIC_ORIGIN", "DECLARED_REFERENCE_ORIGIN"}:
        return {"resolution_state": "RESOLVED_POINT", "centre_value": profile["declared_result"]}

    if mode == "SYMMETRY_UNIQUENESS":
        breaker = dependencies.get("symmetry_breaker")
        if not breaker:
            return {"resolution_state": "AMBIGUOUS"}
        return {
            "resolution_state": "RESOLVED_POINT",
            "centre_value": {"kind": "DECLARED_SURFACE_POINT", "id": breaker},
        }

    if mode in {"EXTERNAL_EVIDENCE_REQUIRED", "EXTERNAL_DATASET_REQUIRED", "EXTERNAL_FIELD_OBJECTIVE_REQUIRED"}:
        return {"resolution_state": "UNSUPPORTED", "reason": "EXTERNAL_RESOLUTION_NOT_IMPLEMENTED_IN_THIS_LAYER"}

    return {"resolution_state": "UNSUPPORTED", "reason": "UNKNOWN_RESOLUTION_MODE"}


def compare_result(actual: Mapping[str, Any], expected: Mapping[str, Any]) -> bool:
    for key, value in expected.items():
        if actual.get(key) != value:
            return False
    return True


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", type=Path, default=Path("profiles"))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    root = args.profiles
    source_registry = load_json(root / "SEC_Earth_Source_Registry_v0_5_0.json")
    carrier_registry = load_json(root / "SEC_Earth_Carrier_Registry_v0_5_0.json")
    profile_registry = load_json(root / "SEC_Earth_Centre_Profile_Registry_v0_5_0.json")
    vector_corpus = load_json(root / "SEC_Earth_Bounded_Claim_Vectors_v0_5_0.json")

    checks = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"check_id": check_id, "pass": passed, "detail": detail})
        if args.verbose:
            print(("PASS" if passed else "FAIL"), check_id, detail)

    add("SOURCE_REGISTRY_ID", verify_self_hash(source_registry, "source_registry_id"), source_registry["source_registry_id"])

    carrier_self_ok = verify_self_hash(carrier_registry, "carrier_registry_id")
    carrier_items_ok = all(
        structural_hash({k: v for k, v in carrier.items() if k != "carrier_id"}) == carrier["carrier_id"]
        for carrier in carrier_registry["carriers"]
    )
    add("CARRIER_REGISTRY_ID", carrier_self_ok and carrier_items_ok, carrier_registry["carrier_registry_id"])

    profile_self_ok = verify_self_hash(profile_registry, "profile_registry_id")
    profile_items_ok = all(
        structural_hash({k: v for k, v in profile.items() if k != "profile_hash"}) == profile["profile_hash"]
        for profile in profile_registry["profiles"]
    )
    add("PROFILE_REGISTRY_ID", profile_self_ok and profile_items_ok, profile_registry["profile_registry_id"])

    vector_self_ok = verify_self_hash(vector_corpus, "vector_corpus_id")
    vector_items_ok = all(
        structural_hash({k: v for k, v in vector.items() if k != "vector_hash"}) == vector["vector_hash"]
        for vector in vector_corpus["vectors"]
    )
    vector_set_actual = "secearthv_" + hashlib.sha256(
        canonical_bytes([vector["vector_hash"] for vector in vector_corpus["vectors"]])
    ).hexdigest()
    add(
        "VECTOR_CORPUS_ID",
        vector_self_ok and vector_items_ok and vector_set_actual == vector_corpus["vector_set_id"],
        vector_corpus["vector_corpus_id"],
    )

    source_ids = {source["source_id"] for source in source_registry["sources"]}
    carrier_keys = {carrier["carrier_key"] for carrier in carrier_registry["carriers"]}
    profile_map = {profile["profile_id"]: profile for profile in profile_registry["profiles"]}

    source_links_ok = all(
        set(carrier["source_ids"]).issubset(source_ids)
        for carrier in carrier_registry["carriers"]
    )
    profile_links_ok = all(
        profile["carrier_key"] in carrier_keys
        for profile in profile_registry["profiles"]
    )
    add("REFERENCE_LINKS", source_links_ok and profile_links_ok, "source and carrier references")

    resolved = {}
    for vector in vector_corpus["vectors"]:
        profile = profile_map[vector["profile_id"]]
        actual = resolve_vector(vector, profile)
        passed = compare_result(actual, vector["expected"])
        resolved[vector["vector_id"]] = actual
        add(vector["vector_id"], passed, actual["resolution_state"])

    comparisons_ok = True
    for comparison in vector_corpus["comparisons"]:
        left_vector = next(v for v in vector_corpus["vectors"] if v["vector_id"] == comparison["left_vector_id"])
        right_vector = next(v for v in vector_corpus["vectors"] if v["vector_id"] == comparison["right_vector_id"])
        left_profile = profile_map[left_vector["profile_id"]]
        right_profile = profile_map[right_vector["profile_id"]]
        left_result = resolved[left_vector["vector_id"]]
        right_result = resolved[right_vector["vector_id"]]
        passed = (
            left_result.get("centre_value") == right_result.get("centre_value")
            and left_profile["profile_id"] != right_profile["profile_id"]
            and left_profile["carrier_key"] != right_profile["carrier_key"]
        )
        comparisons_ok = comparisons_ok and passed
        add(comparison["comparison_id"], passed, comparison["expected_relation"])

    passed_count = sum(1 for check in checks if check["pass"])
    total_count = len(checks)
    status = "PASS" if passed_count == total_count else "FAIL"

    evidence_core = {
        "schema": "SEC-EARTH-PROFILE-VALIDATION-EVIDENCE-1-D01",
        "system_version": "0.5.0",
        "status": status,
        "passed": passed_count,
        "total": total_count,
        "source_registry_id": source_registry["source_registry_id"],
        "carrier_registry_id": carrier_registry["carrier_registry_id"],
        "profile_registry_id": profile_registry["profile_registry_id"],
        "vector_set_id": vector_corpus["vector_set_id"],
        "vector_corpus_id": vector_corpus["vector_corpus_id"],
        "checks": checks,
    }
    evidence = {**evidence_core, "evidence_id": structural_hash(evidence_core)}

    print("STRUCTURAL EARTH CENTRE BOUNDED EARTH PROFILE VALIDATOR v0.5.0")
    print("STATUS", status)
    print("TOTAL", f"{passed_count}/{total_count}", "PASS" if status == "PASS" else "CHECK")
    print("VECTOR SET", vector_corpus["vector_set_id"])
    print("PROFILE REGISTRY", profile_registry["profile_registry_id"])
    print("CARRIER REGISTRY", carrier_registry["carrier_registry_id"])
    print("EVIDENCE ID", evidence["evidence_id"])

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
