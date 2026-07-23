#!/usr/bin/env python3
"""Structural Earth Centre v0.5.0 structural innovation resolver.

Implements four bounded capabilities:
- Structural Centre Differential
- Centre Stability Envelope with genuine RESOLVED_REGION output
- Symmetry Certificate
- Centre Resolution Certificate

The module is dependency-light and uses exact rational coordinates for the
structural innovation layer. It does not claim that a finite sample envelope
represents uncertainty outside the explicitly declared perturbation family.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SYSTEM_VERSION = "0.5.0"
INNOVATION_PROFILE = "SEC-STRUCTURAL-CENTRE-INNOVATION-1-D01"
ENVELOPE_PROFILE = "SEC-CENTRE-STABILITY-ENVELOPE-1-D01"
DIFFERENTIAL_PROFILE = "SEC-STRUCTURAL-CENTRE-DIFFERENTIAL-1-D01"
SYMMETRY_PROFILE = "SEC-SYMMETRY-CERTIFICATE-1-D01"
CERTIFICATE_PROFILE = "SEC-CENTRE-RESOLUTION-CERTIFICATE-3-D01"
CLAIM_PROFILE = "SEC-CENTRE-CLAIM-IDENTITY-1-D01"

RESOLVED_STATES = {"RESOLVED_POINT", "RESOLVED_REGION", "MULTI_CENTRE"}
MAX_DIMENSION = 16
MAX_SAMPLES = 10000
MAX_DEPENDENCIES = 256


class SECInnovationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def structural_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def parse_fraction(value: Any) -> Fraction:
    if isinstance(value, bool):
        raise SECInnovationError("BOOLEAN_IS_NOT_RATIONAL")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        return Fraction(value)
    if isinstance(value, Mapping) and set(value).issuperset({"n", "d"}):
        denominator = int(value["d"])
        if denominator == 0:
            raise SECInnovationError("ZERO_DENOMINATOR")
        return Fraction(int(value["n"]), denominator)
    if isinstance(value, (list, tuple)) and len(value) == 2:
        denominator = int(value[1])
        if denominator == 0:
            raise SECInnovationError("ZERO_DENOMINATOR")
        return Fraction(int(value[0]), denominator)
    raise SECInnovationError("UNSUPPORTED_RATIONAL")


def canonical_rational(value: Any) -> Dict[str, str]:
    f = parse_fraction(value)
    return {"n": str(f.numerator), "d": str(f.denominator)}


def canonical_point(point: Sequence[Any]) -> List[Dict[str, str]]:
    if isinstance(point, (str, bytes)) or not isinstance(point, Sequence):
        raise SECInnovationError("POINT_NOT_SEQUENCE")
    if not point or len(point) > MAX_DIMENSION:
        raise SECInnovationError("POINT_DIMENSION_OUT_OF_RANGE")
    return [canonical_rational(value) for value in point]


def point_key(point: Sequence[Any]) -> Tuple[Tuple[int, int], ...]:
    return tuple((parse_fraction(v).numerator, parse_fraction(v).denominator) for v in point)


def canonical_dependencies(dependencies: Mapping[str, Any]) -> Dict[str, Any]:
    if len(dependencies) > MAX_DEPENDENCIES:
        raise SECInnovationError("DEPENDENCY_LIMIT_EXCEEDED")
    return json.loads(canonical_bytes(dict(dependencies)).decode("utf-8"))


def claim_identity_material(claim: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema": CLAIM_PROFILE,
        "system_version": SYSTEM_VERSION,
        "carrier_id": claim.get("carrier_id", "UNDECLARED"),
        "centre_profile_id": claim.get("centre_profile_id", "UNDECLARED"),
        "dependency_fingerprint_id": claim.get("dependency_fingerprint_id", "UNDECLARED"),
        "authority_scope": claim.get("authority_scope", "BOUNDED_CLAIM_ONLY"),
        "claim_kind": claim.get("claim_kind", "CENTRE_CLAIM"),
    }


def claim_id(claim: Mapping[str, Any]) -> str:
    return structural_hash(claim_identity_material(claim))


def _canonical_samples(samples: Sequence[Mapping[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    if len(samples) > MAX_SAMPLES:
        raise SECInnovationError("SAMPLE_LIMIT_EXCEEDED")
    normalized: List[Dict[str, Any]] = []
    dimensions: set[int] = set()
    for index, sample in enumerate(samples):
        if not isinstance(sample, Mapping) or "point" not in sample:
            raise SECInnovationError("MALFORMED_STABILITY_SAMPLE")
        point = canonical_point(sample["point"])
        dimensions.add(len(point))
        normalized.append({
            "sample_id": str(sample.get("sample_id", f"S{index+1:04d}")),
            "point": point,
        })
    normalized.sort(key=lambda item: (point_key(item["point"]), item["sample_id"]))
    dimension = next(iter(dimensions)) if len(dimensions) == 1 else -1
    return normalized, dimension


def resolve_stability_envelope(
    samples: Sequence[Mapping[str, Any]],
    *,
    perturbation_family: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    perturbation = deepcopy(dict(perturbation_family or {"family": "DECLARED_FINITE_FAMILY"}))
    perturbation_family_id = structural_hash({
        "schema": "SEC-PERTURBATION-FAMILY-1-D01",
        "system_version": SYSTEM_VERSION,
        "definition": perturbation,
    })

    try:
        normalized, dimension = _canonical_samples(samples)
    except SECInnovationError as exc:
        body = {
            "schema": ENVELOPE_PROFILE,
            "system_version": SYSTEM_VERSION,
            "resolution_state": "UNSUPPORTED",
            "reason": str(exc),
            "perturbation_family_id": perturbation_family_id,
        }
        return {**body, "stability_envelope_id": structural_hash(body)}

    if not normalized:
        body = {
            "schema": ENVELOPE_PROFILE,
            "system_version": SYSTEM_VERSION,
            "resolution_state": "INCOMPLETE",
            "reason": "NO_ADMITTED_PERTURBATION_RESULTS",
            "perturbation_family_id": perturbation_family_id,
            "sample_count": 0,
        }
        return {**body, "stability_envelope_id": structural_hash(body)}

    if dimension < 0:
        body = {
            "schema": ENVELOPE_PROFILE,
            "system_version": SYSTEM_VERSION,
            "resolution_state": "CONFLICT",
            "reason": "PERTURBATION_RESULT_DIMENSION_MISMATCH",
            "perturbation_family_id": perturbation_family_id,
            "sample_count": len(normalized),
        }
        return {**body, "stability_envelope_id": structural_hash(body)}

    unique_by_key: Dict[Tuple[Tuple[int, int], ...], List[Dict[str, str]]] = {}
    for sample in normalized:
        unique_by_key[point_key(sample["point"])] = sample["point"]
    unique_points = [unique_by_key[key] for key in sorted(unique_by_key)]

    if len(unique_points) == 1:
        result = {
            "schema": ENVELOPE_PROFILE,
            "system_version": SYSTEM_VERSION,
            "resolution_state": "RESOLVED_POINT",
            "centre_type": "POINT",
            "centre_value": unique_points[0],
            "perturbation_family_id": perturbation_family_id,
            "sample_count": len(normalized),
            "unique_point_count": 1,
            "witness": {
                "all_admitted_samples_coincide": True,
                "region_required": False,
            },
        }
        return {**result, "stability_envelope_id": structural_hash(result)}

    lower: List[Dict[str, str]] = []
    upper: List[Dict[str, str]] = []
    for axis in range(dimension):
        values = [parse_fraction(point[axis]) for point in unique_points]
        lower.append(canonical_rational(min(values)))
        upper.append(canonical_rational(max(values)))

    region = {
        "region_type": "AXIS_ALIGNED_EXACT_RATIONAL_ENVELOPE",
        "dimension": dimension,
        "lower_bound": lower,
        "upper_bound": upper,
    }
    result = {
        "schema": ENVELOPE_PROFILE,
        "system_version": SYSTEM_VERSION,
        "resolution_state": "RESOLVED_REGION",
        "centre_type": "REGION",
        "centre_region": region,
        "region_id": structural_hash(region),
        "perturbation_family_id": perturbation_family_id,
        "sample_count": len(normalized),
        "unique_point_count": len(unique_points),
        "witness": {
            "all_admitted_samples_inside": True,
            "minimal_axis_aligned_bounds_over_declared_samples": True,
            "inference_outside_declared_family": False,
        },
    }
    return {**result, "stability_envelope_id": structural_hash(result)}


def point_in_region(point: Sequence[Any], region: Mapping[str, Any]) -> bool:
    candidate = canonical_point(point)
    lower = region.get("lower_bound", [])
    upper = region.get("upper_bound", [])
    if len(candidate) != len(lower) or len(candidate) != len(upper):
        return False
    return all(
        parse_fraction(lo) <= parse_fraction(value) <= parse_fraction(hi)
        for value, lo, hi in zip(candidate, lower, upper)
    )


def build_symmetry_certificate(
    candidates: Sequence[Any],
    equivalence_class: Sequence[Any],
    symmetry_breaker: Any = None,
) -> Dict[str, Any]:
    canonical_candidates = sorted({str(value) for value in candidates})
    canonical_equivalence = sorted({str(value) for value in equivalence_class})
    breaker = None if symmetry_breaker is None else str(symmetry_breaker)

    if not canonical_equivalence:
        state = "INCOMPLETE"
        reason = "NO_DECLARED_EQUIVALENCE_CLASS"
    elif breaker is not None and breaker not in canonical_equivalence:
        state = "CONFLICT"
        reason = "SYMMETRY_BREAKER_OUTSIDE_EQUIVALENCE_CLASS"
    elif breaker is not None:
        state = "UNIQUE_CENTRE_ADMITTED"
        reason = "DECLARED_SYMMETRY_BREAKER_SELECTS_MEMBER"
    elif len(canonical_equivalence) > 1:
        state = "UNIQUE_CENTRE_REFUSED"
        reason = "NO_ADMITTED_SYMMETRY_BREAKER"
    else:
        state = "UNIQUE_CENTRE_ADMITTED"
        reason = "EQUIVALENCE_CLASS_HAS_SINGLE_MEMBER"

    body = {
        "schema": SYMMETRY_PROFILE,
        "system_version": SYSTEM_VERSION,
        "symmetry_state": state,
        "reason": reason,
        "candidates": canonical_candidates,
        "equivalence_class": canonical_equivalence,
        "symmetry_breaker": breaker,
    }
    return {**body, "symmetry_certificate_id": structural_hash(body)}


def _result_is_resolved(result: Mapping[str, Any]) -> bool:
    return result.get("resolution_state") in RESOLVED_STATES


def build_structural_differential(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> Dict[str, Any]:
    left_dependencies = canonical_dependencies(left.get("dependencies", {}))
    right_dependencies = canonical_dependencies(right.get("dependencies", {}))

    keys = sorted(set(left_dependencies) | set(right_dependencies))
    changed = [key for key in keys if left_dependencies.get(key) != right_dependencies.get(key)]
    if left.get("centre_profile_id") != right.get("centre_profile_id"):
        changed = ["centre_profile_id", *changed]

    left_result = deepcopy(dict(left.get("result", {})))
    right_result = deepcopy(dict(right.get("result", {})))
    left_result_id = structural_hash(left_result)
    right_result_id = structural_hash(right_result)
    result_equivalent = left_result == right_result

    left_claim = {
        "carrier_id": left.get("carrier_id", "UNDECLARED"),
        "centre_profile_id": left.get("centre_profile_id", "UNDECLARED"),
        "dependency_fingerprint_id": structural_hash(left_dependencies),
        "authority_scope": left.get("authority_scope", "BOUNDED_CLAIM_ONLY"),
    }
    right_claim = {
        "carrier_id": right.get("carrier_id", "UNDECLARED"),
        "centre_profile_id": right.get("centre_profile_id", "UNDECLARED"),
        "dependency_fingerprint_id": structural_hash(right_dependencies),
        "authority_scope": right.get("authority_scope", "BOUNDED_CLAIM_ONLY"),
    }

    if not _result_is_resolved(left_result) or not _result_is_resolved(right_result):
        state = "UNRESOLVED_COMPARISON"
    elif not changed and result_equivalent:
        state = "NO_STRUCTURAL_DIFFERENCE"
    elif changed and result_equivalent:
        state = "CLAIM_DISTINCT_RESULT_EQUIVALENT"
    elif len(changed) == 1:
        state = "SINGLE_DEPENDENCY_DIVERGENCE"
    else:
        state = "MULTI_DEPENDENCY_DIVERGENCE"

    body = {
        "schema": DIFFERENTIAL_PROFILE,
        "system_version": SYSTEM_VERSION,
        "differential_state": state,
        "left_claim_id": claim_id(left_claim),
        "right_claim_id": claim_id(right_claim),
        "left_result_id": left_result_id,
        "right_result_id": right_result_id,
        "result_equivalent": result_equivalent,
        "changed_dependencies": changed,
        "changed_dependency_count": len(changed),
        "interpretation": (
            "CONTROLLED_SINGLE_DECLARED_DIFFERENCE" if len(changed) == 1
            else "MULTIPLE_OR_NO_DECLARED_DIFFERENCES"
        ),
    }
    return {**body, "differential_id": structural_hash(body)}


def build_resolution_certificate(
    claim: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    resolution_witness: Optional[Mapping[str, Any]] = None,
    symmetry_certificate: Optional[Mapping[str, Any]] = None,
    stability_envelope: Optional[Mapping[str, Any]] = None,
    evidence_id: Optional[str] = None,
    declared_result_id: Optional[str] = None,
) -> Dict[str, Any]:
    claim_material = claim_identity_material(claim)
    result_copy = deepcopy(dict(result))
    result_material_hash = structural_hash(result_copy)
    result_id = str(declared_result_id) if declared_result_id is not None else result_material_hash

    witness = deepcopy(dict(resolution_witness or {}))
    witness.setdefault("state_is_explicit", "resolution_state" in result_copy)
    witness.setdefault("resolved_state", result_copy.get("resolution_state") in RESOLVED_STATES)

    body: Dict[str, Any] = {
        "schema": CERTIFICATE_PROFILE,
        "system_version": SYSTEM_VERSION,
        "claim_id": structural_hash(claim_material),
        "claim_material": claim_material,
        "result_id": result_id,
        "result_material_hash": result_material_hash,
        "result_id_source": "DECLARED_RESULT_ID" if declared_result_id is not None else "STRUCTURAL_MATERIAL_HASH",
        "resolution_state": result_copy.get("resolution_state", "UNDECLARED"),
        "resolution_witness": witness,
        "authority_scope": claim_material["authority_scope"],
    }
    if symmetry_certificate is not None:
        body["symmetry_certificate_id"] = symmetry_certificate.get("symmetry_certificate_id")
    if stability_envelope is not None:
        body["stability_envelope_id"] = stability_envelope.get("stability_envelope_id")
    if evidence_id is not None:
        body["evidence_id"] = evidence_id

    return {**body, "certificate_id": structural_hash(body)}


def evaluate_vector(vector: Mapping[str, Any]) -> Dict[str, Any]:
    operation = vector["operation"]
    payload = vector.get("input", {})
    if operation == "STABILITY_ENVELOPE":
        return resolve_stability_envelope(
            payload.get("samples", []),
            perturbation_family=payload.get("perturbation_family"),
        )
    if operation == "STRUCTURAL_DIFFERENTIAL":
        return build_structural_differential(payload["left"], payload["right"])
    if operation == "SYMMETRY_CERTIFICATE":
        return build_symmetry_certificate(
            payload.get("candidates", []),
            payload.get("equivalence_class", []),
            payload.get("symmetry_breaker"),
        )
    if operation == "RESOLUTION_CERTIFICATE":
        stability = payload.get("stability_envelope")
        symmetry = payload.get("symmetry_certificate")
        return build_resolution_certificate(
            payload["claim"],
            payload["result"],
            resolution_witness=payload.get("resolution_witness"),
            symmetry_certificate=symmetry,
            stability_envelope=stability,
            evidence_id=payload.get("evidence_id"),
            declared_result_id=payload.get("declared_result_id"),
        )
    raise SECInnovationError(f"UNKNOWN_OPERATION:{operation}")


def verify_self_hash(obj: Mapping[str, Any], field: str) -> bool:
    expected = obj.get(field)
    body = {k: v for k, v in obj.items() if k != field}
    return structural_hash(body) == expected


def audit_vector_corpus(corpus: Mapping[str, Any], *, verbose: bool = False) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: Any) -> None:
        checks.append({"check_id": check_id, "pass": bool(passed), "detail": detail})
        if verbose:
            print("PASS" if passed else "FAIL", check_id, detail)

    add("CORPUS_ID", verify_self_hash(corpus, "vector_corpus_id"), corpus.get("vector_corpus_id"))
    actual_set = "secinv_" + hashlib.sha256(canonical_bytes([v["vector_hash"] for v in corpus.get("vectors", [])])).hexdigest()
    add("VECTOR_SET_ID", actual_set == corpus.get("vector_set_id"), actual_set)
    add("INNOVATION_PROFILE", corpus.get("innovation_profile") == INNOVATION_PROFILE, corpus.get("innovation_profile"))

    vector_map: Dict[str, Mapping[str, Any]] = {}
    for vector in corpus.get("vectors", []):
        vector_map[vector["vector_id"]] = vector
        vector_hash_ok = verify_self_hash(vector, "vector_hash")
        actual = evaluate_vector(vector)
        passed = vector_hash_ok and actual == vector.get("expected")
        add(vector["vector_id"], passed, actual.get("resolution_state", actual.get("differential_state", actual.get("symmetry_state", "CERTIFICATE"))))

    # Permanent meta-properties over the frozen vectors.
    base = vector_map["SEC-INV-S003"]["input"]
    reversed_samples = list(reversed(base["samples"]))
    permuted = resolve_stability_envelope(reversed_samples, perturbation_family=base["perturbation_family"])
    add("ENVELOPE_PERMUTATION_INVARIANCE", permuted == vector_map["SEC-INV-S003"]["expected"], permuted.get("stability_envelope_id"))

    duplicate_samples = base["samples"] + [deepcopy(base["samples"][0])]
    duplicate = resolve_stability_envelope(duplicate_samples, perturbation_family=base["perturbation_family"])
    reference = vector_map["SEC-INV-S003"]["expected"]
    duplicate_ok = (
        duplicate.get("centre_region") == reference.get("centre_region")
        and duplicate.get("resolution_state") == "RESOLVED_REGION"
        and duplicate.get("unique_point_count") == reference.get("unique_point_count")
    )
    add("DUPLICATE_SAMPLE_REGION_INVARIANCE", duplicate_ok, duplicate.get("region_id"))

    differential_input = vector_map["SEC-INV-D003"]["input"]
    forward = build_structural_differential(differential_input["left"], differential_input["right"])
    reverse = build_structural_differential(differential_input["right"], differential_input["left"])
    add(
        "DIFFERENTIAL_CHANGED_SET_DIRECTION_INVARIANCE",
        forward["changed_dependencies"] == reverse["changed_dependencies"],
        forward["changed_dependencies"],
    )

    claim_a = {"carrier_id": "C", "centre_profile_id": "P", "dependency_fingerprint_id": "D1"}
    claim_b = {"carrier_id": "C", "centre_profile_id": "P", "dependency_fingerprint_id": "D2"}
    add("CLAIM_ID_DEPENDENCY_SENSITIVITY", claim_id(claim_a) != claim_id(claim_b), [claim_id(claim_a), claim_id(claim_b)])

    cert_vector = vector_map["SEC-INV-C002"]
    cert = evaluate_vector(cert_vector)
    tampered_result = deepcopy(cert_vector["input"]["result"])
    tampered_result["resolution_state"] = "RESOLVED_POINT"
    tampered = build_resolution_certificate(cert_vector["input"]["claim"], tampered_result)
    add("CERTIFICATE_TAMPER_SENSITIVITY", cert["certificate_id"] != tampered["certificate_id"], tampered["certificate_id"])

    region = vector_map["SEC-INV-S003"]["expected"]["centre_region"]
    membership_ok = point_in_region([1, 1], region) and not point_in_region([9, 9], region)
    add("REGION_MEMBERSHIP_BOUNDARY", membership_ok, region)

    passed = sum(1 for check in checks if check["pass"])
    total = len(checks)
    core = {
        "schema": "SEC-STRUCTURAL-CENTRE-INNOVATION-AUDIT-1-D01",
        "system_version": SYSTEM_VERSION,
        "status": "PASS" if passed == total else "FAIL",
        "passed": passed,
        "total": total,
        "vector_set_id": corpus.get("vector_set_id"),
        "vector_corpus_id": corpus.get("vector_corpus_id"),
        "checks": checks,
    }
    return {**core, "evidence_id": structural_hash(core)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vectors", type=Path, default=Path("profiles") / "SEC_Structural_Centre_Innovation_Vectors_v0_5_0.json")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    corpus = json.loads(args.vectors.read_text(encoding="utf-8"))
    result = audit_vector_corpus(corpus, verbose=args.verbose)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print("STRUCTURAL EARTH CENTRE STRUCTURAL INNOVATION RESOLVER v0.5.0")
        print("STATUS", result["status"])
        print("TOTAL", f"{result['passed']}/{result['total']}", result["status"])
        print("VECTOR SET", result["vector_set_id"])
        print("EVIDENCE ID", result["evidence_id"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
