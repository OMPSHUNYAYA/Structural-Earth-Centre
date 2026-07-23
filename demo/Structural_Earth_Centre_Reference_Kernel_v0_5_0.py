#!/usr/bin/env python3
"""Structural Earth Centre Reference Kernel v0.5.0.

Deterministic exact reference implementation for the bounded SEC v0.5.0
conformance profiles and frozen vector corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SYSTEM_VERSION = "0.5.0"
ARCHITECTURE_PROFILE = "SEC-ARCH-1-D01"
RULES_PROFILE = "SEC-RULES-1-D01"
CANONICALIZATION_PROFILE = "SEC-CANON-1-D01"
EXACT_ARITHMETIC_PROFILE = "SEC-EXACT-1-D01"
CERTIFICATE_PROFILE = "SEC-CERT-1-D01"
RESULT_PROFILE = "SEC-RESULT-1-D01"

SUPPORTED_CARRIER_TYPES = {
    "FINITE_WEIGHTED_POINT_SET",
    "FINITE_CANDIDATE_METRIC_SPACE",
    "DECLARED_SYMMETRY_CLASS",
}
SUPPORTED_METRICS = {
    "NOT_MATERIAL",
    "MANHATTAN_L1",
    "SQUARED_EUCLIDEAN_L2_SQUARED",
}
RESOLVED_STATES = {"RESOLVED_POINT", "MULTI_CENTRE"}

MAX_DIMENSION = 16
MAX_SUPPORT_POINTS = 10000
MAX_CANDIDATE_POINTS = 10000
MAX_INTEGER_DIGITS = 2048
MAX_DEPENDENCIES = 128


class SECError(Exception):
    pass


class InputLimitError(SECError):
    pass


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def structural_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _digit_count(text: str) -> int:
    text = text.lstrip("+-")
    return len(text)


def parse_fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        return Fraction(value)
    if isinstance(value, Mapping) and "n" in value and "d" in value:
        n_text = str(value["n"])
        d_text = str(value["d"])
        if _digit_count(n_text) > MAX_INTEGER_DIGITS or _digit_count(d_text) > MAX_INTEGER_DIGITS:
            raise InputLimitError("Rational integer digit limit exceeded")
        n = int(n_text)
        d = int(d_text)
        if d == 0:
            raise SECError("Rational denominator must not be zero")
        return Fraction(n, d)
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return Fraction(int(value[0]), int(value[1]))
    raise SECError(f"Unsupported rational representation: {value!r}")


def canonical_rational(value: Any) -> Dict[str, str]:
    f = parse_fraction(value)
    return {"n": str(f.numerator), "d": str(f.denominator)}


def canonical_point(point: Sequence[Any]) -> List[Dict[str, str]]:
    if not isinstance(point, Sequence) or isinstance(point, (str, bytes)):
        raise SECError("Point must be a coordinate sequence")
    if len(point) < 1 or len(point) > MAX_DIMENSION:
        raise InputLimitError("Point dimension outside supported limit")
    return [canonical_rational(value) for value in point]


def point_key(point: Sequence[Any]) -> Tuple[Tuple[int, int], ...]:
    return tuple(
        (parse_fraction(value).numerator, parse_fraction(value).denominator)
        for value in point
    )


def canonical_carrier(carrier: Mapping[str, Any]) -> Dict[str, Any]:
    carrier_type = carrier.get("carrier_type")

    if carrier_type == "FINITE_WEIGHTED_POINT_SET":
        raw_points = carrier.get("points", [])
        if len(raw_points) > MAX_SUPPORT_POINTS:
            raise InputLimitError("Support point limit exceeded")
        entries: List[Dict[str, Any]] = []
        for entry in raw_points:
            entries.append(
                {
                    "point": canonical_point(entry["point"]),
                    "weight": canonical_rational(entry["weight"]),
                }
            )
        entries.sort(
            key=lambda entry: (
                point_key(entry["point"]),
                int(entry["weight"]["n"]),
                int(entry["weight"]["d"]),
            )
        )
        return {"carrier_type": carrier_type, "points": entries}

    if carrier_type == "FINITE_CANDIDATE_METRIC_SPACE":
        raw_support = carrier.get("support", [])
        raw_candidates = carrier.get("candidates", [])
        if len(raw_support) > MAX_SUPPORT_POINTS:
            raise InputLimitError("Support point limit exceeded")
        if len(raw_candidates) > MAX_CANDIDATE_POINTS:
            raise InputLimitError("Candidate point limit exceeded")

        support = [canonical_point(point) for point in raw_support]
        candidates = [canonical_point(point) for point in raw_candidates]

        support_by_bytes = {_canonical_json_bytes(point): point for point in support}
        candidates_by_bytes = {_canonical_json_bytes(point): point for point in candidates}

        support = sorted(support_by_bytes.values(), key=point_key)
        candidates = sorted(candidates_by_bytes.values(), key=point_key)

        return {
            "carrier_type": carrier_type,
            "support": support,
            "candidates": candidates,
        }

    if carrier_type == "DECLARED_SYMMETRY_CLASS":
        candidates = sorted(set(carrier.get("candidates", [])))
        equivalence_class = sorted(set(carrier.get("equivalence_class", [])))
        result: Dict[str, Any] = {
            "carrier_type": carrier_type,
            "candidates": candidates,
            "equivalence_class": equivalence_class,
        }
        if "symmetry_breaker" in carrier:
            result["symmetry_breaker"] = carrier["symmetry_breaker"]
        return result

    return deepcopy(dict(carrier))


def dependency_fingerprint(
    carrier_id: str,
    profile: Mapping[str, Any],
    dependencies: Mapping[str, Any],
) -> Tuple[Dict[str, Any], str]:
    if len(dependencies) > MAX_DEPENDENCIES:
        raise InputLimitError("Dependency count limit exceeded")

    fingerprint: Dict[str, Any] = {
        "schema": "SEC-DEPENDENCY-1-D01",
        "carrier_id": carrier_id,
        "boundary_id": dependencies.get("boundary_id", "IMPLICIT_IN_CANONICAL_CARRIER"),
        "measure_id": dependencies.get("measure_id", profile.get("weight_policy", "NOT_MATERIAL")),
        "metric_id": dependencies.get("metric_id", profile.get("metric", "NOT_MATERIAL")),
        "objective_id": dependencies.get("objective_id", profile.get("objective", "NOT_MATERIAL")),
        "frame_id": dependencies.get("frame", "NOT_MATERIAL"),
        "epoch_id": dependencies.get("epoch", "NOT_MATERIAL"),
        "precision_policy_id": profile.get("precision_policy", "NOT_MATERIAL"),
        "symmetry_policy_id": profile.get("symmetry_policy", "NOT_MATERIAL"),
        "rules_profile": profile["rules_profile"],
    }

    if "equivalence_class" in dependencies:
        fingerprint["equivalence_class_id"] = structural_hash(
            {"equivalence_class": dependencies["equivalence_class"]}
        )
    if "symmetry_breaker" in dependencies:
        fingerprint["symmetry_breaker_id"] = structural_hash(
            {"symmetry_breaker": dependencies["symmetry_breaker"]}
        )
    if "evidence_class" in dependencies:
        fingerprint["evidence_class"] = dependencies["evidence_class"]
    if "conflict" in dependencies:
        fingerprint["declared_conflict"] = dependencies["conflict"]

    return fingerprint, structural_hash(fingerprint)


def result_object(
    state: str,
    centre_type: str = "NONE",
    *,
    centre_value: Any = None,
    centre_values: Any = None,
    field: Optional[Mapping[str, Any]] = None,
    claim_evaluation: Optional[str] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "resolution_state": state,
        "centre_type": centre_type,
    }
    if centre_value is not None:
        result["centre_value"] = centre_value
    if centre_values is not None:
        result["centre_values"] = centre_values
    if field is not None:
        field_copy = deepcopy(dict(field))
        result["field"] = field_copy
        result["field_id"] = structural_hash(field_copy)
    if claim_evaluation is not None:
        result["claim_evaluation"] = claim_evaluation
    return result


def _point_dimensions(points: Iterable[Sequence[Any]]) -> set[int]:
    return {len(point) for point in points}


def _missing_required_dependency(
    profile: Mapping[str, Any],
    dependencies: Mapping[str, Any],
    canonical: Mapping[str, Any],
) -> bool:
    for dependency in profile.get("required_dependencies", []):
        if dependency == "frame":
            if "frame" not in dependencies:
                return True
        elif dependency == "candidate_set":
            if "candidate_set" not in dependencies or not canonical.get("candidates", []):
                return True
        elif dependency == "metric":
            if "metric_id" not in dependencies:
                return True
        elif dependency == "equivalence_class":
            if "equivalence_class" not in dependencies or not canonical.get("equivalence_class", []):
                return True
        elif dependency == "symmetry_breaker":
            if "symmetry_breaker" not in dependencies or "symmetry_breaker" not in canonical:
                return True
        elif dependency == "evidence_class":
            if "evidence_class" not in dependencies:
                return True
        elif dependency not in dependencies:
            return True
    return False


def _has_conflict(
    profile: Mapping[str, Any],
    dependencies: Mapping[str, Any],
    canonical: Mapping[str, Any],
) -> bool:
    if "conflict" in dependencies:
        return True

    frame = dependencies.get("frame")
    if isinstance(frame, (list, tuple, set)) and len(frame) != 1:
        return True

    carrier_type = canonical.get("carrier_type")
    if carrier_type == "FINITE_WEIGHTED_POINT_SET":
        dimensions = _point_dimensions(entry["point"] for entry in canonical.get("points", []))
        if len(dimensions) > 1:
            return True
    elif carrier_type == "FINITE_CANDIDATE_METRIC_SPACE":
        dimensions = _point_dimensions(
            list(canonical.get("support", [])) + list(canonical.get("candidates", []))
        )
        if len(dimensions) > 1:
            return True

    return False


def _profile_supported(profile: Mapping[str, Any], canonical: Mapping[str, Any]) -> bool:
    carrier_type = canonical.get("carrier_type")
    if carrier_type not in SUPPORTED_CARRIER_TYPES:
        return False
    if carrier_type != profile.get("carrier_type"):
        return False
    if profile.get("metric", "NOT_MATERIAL") not in SUPPORTED_METRICS:
        return False
    return True


def _dependency_metric_supported(profile: Mapping[str, Any], dependencies: Mapping[str, Any]) -> bool:
    expected_metric = profile.get("metric", "NOT_MATERIAL")
    declared_metric = dependencies.get("metric_id")
    if declared_metric is None:
        return True
    if declared_metric not in SUPPORTED_METRICS:
        return False
    return declared_metric == expected_metric


def _weights_supported(canonical: Mapping[str, Any], profile: Mapping[str, Any]) -> bool:
    if canonical.get("carrier_type") != "FINITE_WEIGHTED_POINT_SET":
        return True
    if profile.get("weight_policy") != "EXPLICIT_POSITIVE_RATIONAL":
        return True
    for entry in canonical.get("points", []):
        if parse_fraction(entry["weight"]) <= 0:
            return False
    return True


def exact_weighted_centroid(canonical: Mapping[str, Any]) -> List[Dict[str, str]]:
    entries = canonical.get("points", [])
    if not entries:
        raise SECError("Weighted centroid requires at least one point")
    dimensions = len(entries[0]["point"])
    total_weight = sum((parse_fraction(entry["weight"]) for entry in entries), Fraction(0, 1))
    if total_weight <= 0:
        raise SECError("Total weight must be positive")

    centre: List[Dict[str, str]] = []
    for index in range(dimensions):
        weighted_sum = sum(
            (
                parse_fraction(entry["weight"]) * parse_fraction(entry["point"][index])
                for entry in entries
            ),
            Fraction(0, 1),
        )
        centre.append(canonical_rational(weighted_sum / total_weight))
    return centre


def exact_distance(point_a: Sequence[Any], point_b: Sequence[Any], metric: str) -> Fraction:
    a = [parse_fraction(value) for value in point_a]
    b = [parse_fraction(value) for value in point_b]
    if len(a) != len(b):
        raise SECError("Distance points have different dimensions")

    if metric == "MANHATTAN_L1":
        return sum((abs(x - y) for x, y in zip(a, b)), Fraction(0, 1))
    if metric == "SQUARED_EUCLIDEAN_L2_SQUARED":
        return sum(((x - y) ** 2 for x, y in zip(a, b)), Fraction(0, 1))
    raise SECError(f"Unsupported exact metric: {metric}")


def exact_medoid(
    canonical: Mapping[str, Any],
    metric: str,
) -> Tuple[List[List[Dict[str, str]]], Dict[str, Any]]:
    support = canonical.get("support", [])
    candidates = canonical.get("candidates", [])
    if not support or not candidates:
        raise SECError("Finite medoid requires support and candidates")

    costs: List[Tuple[List[Dict[str, str]], Fraction]] = []
    for candidate in candidates:
        cost = sum(
            (exact_distance(candidate, point, metric) for point in support),
            Fraction(0, 1),
        )
        costs.append((candidate, cost))

    minimum = min(cost for _, cost in costs)
    minimizers = [deepcopy(candidate) for candidate, cost in costs if cost == minimum]
    minimizers.sort(key=point_key)

    field = {
        "entries": [
            {
                "candidate": deepcopy(candidate),
                "cost": canonical_rational(cost),
                "pressure": canonical_rational(cost - minimum),
            }
            for candidate, cost in sorted(costs, key=lambda item: point_key(item[0]))
        ],
        "K_min": canonical_rational(minimum),
    }
    return minimizers, field


def _claim_evaluation(claim: Optional[Mapping[str, Any]], result: Mapping[str, Any]) -> Optional[str]:
    if claim is None:
        return None

    state = result["resolution_state"]
    if state not in RESOLVED_STATES:
        return "CLAIM_UNRESOLVED"

    if claim.get("candidate_type") != "POINT":
        return "CLAIM_UNSUPPORTED"

    candidate = canonical_point(claim.get("candidate_value", []))
    if state == "RESOLVED_POINT":
        return "CLAIM_CONFIRMED" if candidate == result.get("centre_value") else "CLAIM_NOT_CENTRE"
    if state == "MULTI_CENTRE":
        return "CLAIM_MEMBER" if candidate in result.get("centre_values", []) else "CLAIM_NOT_CENTRE"
    return "CLAIM_UNSUPPORTED"


def resolve(
    carrier: Mapping[str, Any],
    profile: Mapping[str, Any],
    dependencies: Mapping[str, Any],
    claim: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    canonical = canonical_carrier(carrier)

    if _missing_required_dependency(profile, dependencies, canonical):
        base = result_object("INCOMPLETE")
    elif _has_conflict(profile, dependencies, canonical):
        base = result_object("CONFLICT")
    elif not _profile_supported(profile, canonical):
        base = result_object("UNSUPPORTED")
    elif not _dependency_metric_supported(profile, dependencies):
        base = result_object("UNSUPPORTED")
    elif not _weights_supported(canonical, profile):
        base = result_object("UNSUPPORTED")
    elif "EVIDENCE_CLASS_BELOW_VERIFIABLE" in profile.get("abstention_rules", []) and dependencies.get("evidence_class") != "VERIFIABLE":
        base = result_object("ABSTAIN")
    else:
        objective = profile.get("objective")
        if objective == "EXACT_WEIGHTED_CENTROID":
            try:
                centre = exact_weighted_centroid(canonical)
            except SECError:
                base = result_object("UNSUPPORTED")
            else:
                base = result_object("RESOLVED_POINT", "POINT", centre_value=centre)

        elif objective == "FINITE_EXACT_MEDOID":
            metric = profile.get("metric")
            try:
                minimizers, field = exact_medoid(canonical, metric)
            except SECError:
                base = result_object("INCOMPLETE")
            else:
                if len(minimizers) == 1:
                    base = result_object(
                        "RESOLVED_POINT",
                        "POINT",
                        centre_value=minimizers[0],
                        field=field,
                    )
                else:
                    base = result_object(
                        "MULTI_CENTRE",
                        "POINT_SET",
                        centre_values=minimizers,
                        field=field,
                    )

        elif objective == "DECLARED_SYMMETRY_UNIQUENESS":
            equivalence_class = list(canonical.get("equivalence_class", []))
            breaker = canonical.get("symmetry_breaker")
            if breaker is not None:
                if breaker not in equivalence_class:
                    base = result_object("CONFLICT")
                else:
                    base = result_object("RESOLVED_POINT", "POINT", centre_value=breaker)
            elif len(equivalence_class) > 1:
                base = result_object(
                    "AMBIGUOUS",
                    "EQUIVALENCE_CLASS",
                    centre_values=equivalence_class,
                )
            elif len(equivalence_class) == 1:
                base = result_object("RESOLVED_POINT", "POINT", centre_value=equivalence_class[0])
            else:
                base = result_object("INCOMPLETE")
        else:
            base = result_object("UNSUPPORTED")

    claim_state = _claim_evaluation(claim, base)
    if claim_state is not None:
        base = deepcopy(base)
        base["claim_evaluation"] = claim_state
    return base


def certificate_input(
    profile_id: str,
    profile_hash: str,
    carrier_id: str,
    dependency_fingerprint_id: str,
    result: Mapping[str, Any],
) -> Dict[str, Any]:
    result_id = structural_hash(result)
    return {
        "certificate_schema": CERTIFICATE_PROFILE,
        "system_version": SYSTEM_VERSION,
        "architecture_profile": ARCHITECTURE_PROFILE,
        "rules_profile": RULES_PROFILE,
        "canonicalization_profile": CANONICALIZATION_PROFILE,
        "exact_arithmetic_profile": EXACT_ARITHMETIC_PROFILE,
        "carrier_id": carrier_id,
        "centre_profile": profile_id,
        "centre_profile_hash": profile_hash,
        "dependency_fingerprint_id": dependency_fingerprint_id,
        "result_id": result_id,
        "canonical_result": deepcopy(dict(result)),
    }


def reconstruct_vector(
    vector: Mapping[str, Any],
    profiles: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    profile_id = vector["centre_profile"]
    profile = profiles[profile_id]
    carrier = vector["input"]["carrier"]
    dependencies = vector["input"].get("dependencies", {})
    claim = vector.get("claim")

    canonical = canonical_carrier(carrier)
    carrier_id = structural_hash(canonical)
    fingerprint, fingerprint_id = dependency_fingerprint(carrier_id, profile, dependencies)
    result = resolve(carrier, profile, dependencies, claim)
    result_id = structural_hash(result)
    cert_input = certificate_input(
        profile_id,
        vector["centre_profile_hash"],
        carrier_id,
        fingerprint_id,
        result,
    )
    certificate_id = structural_hash(cert_input)

    return {
        "canonical_carrier": canonical,
        "carrier_id": carrier_id,
        "dependency_fingerprint": fingerprint,
        "dependency_fingerprint_id": fingerprint_id,
        "result": result,
        "result_id": result_id,
        "certificate_input": cert_input,
        "certificate_id": certificate_id,
    }


def compare_regular_vector(vector: Mapping[str, Any], actual: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    canonical_expectations = vector["canonical_expectations"]
    expected = vector["expected"]

    checks = [
        ("CANONICAL_CARRIER_MISMATCH", actual["canonical_carrier"], canonical_expectations["canonical_carrier"]),
        ("CARRIER_ID_MISMATCH", actual["carrier_id"], canonical_expectations["carrier_id"]),
        ("DEPENDENCY_FINGERPRINT_MISMATCH", actual["dependency_fingerprint"], canonical_expectations["dependency_fingerprint"]),
        ("DEPENDENCY_ID_MISMATCH", actual["dependency_fingerprint_id"], canonical_expectations["dependency_fingerprint_id"]),
    ]
    for label, observed, wanted in checks:
        if observed != wanted:
            errors.append(label)

    expected_result = {
        key: value
        for key, value in expected.items()
        if key not in {"result_id", "certificate_id"}
    }
    if actual["result"] != expected_result:
        errors.append("RESULT_STRUCTURE_MISMATCH")
    if actual["result_id"] != expected["result_id"]:
        errors.append("RESULT_ID_MISMATCH")
    if actual["certificate_id"] != expected["certificate_id"]:
        errors.append("CERTIFICATE_ID_MISMATCH")
    return errors


def first_tamper_mismatch(
    vector: Mapping[str, Any],
    actual: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> str:
    mutation_class = vector["verification_expectation"]["mutation_class"]

    if mutation_class == "result":
        recomputed_reference_result = {
            key: value
            for key, value in reference["expected"].items()
            if key not in {"result_id", "certificate_id"}
        }
        claimed_result = {
            key: value
            for key, value in vector["expected"].items()
            if key not in {"result_id", "certificate_id"}
        }
        if claimed_result != recomputed_reference_result:
            return "RESULT_ID_MISMATCH"

    if actual["carrier_id"] != reference["canonical_expectations"]["carrier_id"]:
        return "CARRIER_ID_MISMATCH"
    if vector["centre_profile_hash"] != reference["centre_profile_hash"]:
        return "PROFILE_ID_MISMATCH"
    if actual["dependency_fingerprint_id"] != reference["canonical_expectations"]["dependency_fingerprint_id"]:
        return "DEPENDENCY_ID_MISMATCH"

    if mutation_class == "certificate":
        if vector["expected"]["certificate_id"] != reference["expected"]["certificate_id"]:
            return "CERTIFICATE_ID_MISMATCH"

    if actual["result_id"] != reference["expected"]["result_id"]:
        return "RESULT_ID_MISMATCH"
    if actual["certificate_id"] != reference["expected"]["certificate_id"]:
        return "CERTIFICATE_ID_MISMATCH"
    return "NO_MISMATCH"


@dataclass
class CorpusPackage:
    corpus: Dict[str, Any]
    profile_registry: Dict[str, Any]
    manifest: Optional[Dict[str, Any]]


def _load_json_from_zip(zf: zipfile.ZipFile, suffix: str) -> Dict[str, Any]:
    matches = [name for name in zf.namelist() if name.endswith(suffix)]
    if len(matches) != 1:
        raise SECError(f"Expected one {suffix} in package, found {len(matches)}")
    return json.loads(zf.read(matches[0]).decode("utf-8"))


def load_package(path: Path) -> CorpusPackage:
    if path.is_dir():
        corpus_path = path / "SEC_Conformance_Corpus_v0_5_0.json"
        registry_path = path / "SEC_Profile_Registry_v0_5_0.json"
        manifest_path = path / "SEC_Vector_Manifest_v0_5_0.json"
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
        return CorpusPackage(corpus, registry, manifest)

    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as zf:
            corpus = _load_json_from_zip(zf, "SEC_Conformance_Corpus_v0_5_0.json")
            registry = _load_json_from_zip(zf, "SEC_Profile_Registry_v0_5_0.json")
            try:
                manifest = _load_json_from_zip(zf, "SEC_Vector_Manifest_v0_5_0.json")
            except SECError:
                manifest = None
        return CorpusPackage(corpus, registry, manifest)

    if path.name.endswith("SEC_Conformance_Corpus_v0_5_0.json"):
        corpus = json.loads(path.read_text(encoding="utf-8"))
        registry_path = path.with_name("SEC_Profile_Registry_v0_5_0.json")
        manifest_path = path.with_name("SEC_Vector_Manifest_v0_5_0.json")
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
        return CorpusPackage(corpus, registry, manifest)

    raise SECError("Corpus path must be the SEC package ZIP, corpus directory, or corpus JSON file")


def validate_package_identity(package: CorpusPackage) -> List[str]:
    errors: List[str] = []
    registry = deepcopy(package.profile_registry)
    claimed_registry_id = registry.pop("profile_registry_id", None)
    observed_registry_id = structural_hash(registry)
    if claimed_registry_id != observed_registry_id:
        errors.append("PROFILE_REGISTRY_ID_MISMATCH")

    corpus = deepcopy(package.corpus)
    claimed_corpus_id = corpus.pop("corpus_id", None)
    observed_corpus_id = structural_hash(corpus)
    if claimed_corpus_id != observed_corpus_id:
        errors.append("CORPUS_ID_MISMATCH")

    vector_payload = [
        {"vector_id": vector["vector_id"], "vector_hash": vector["vector_hash"]}
        for vector in package.corpus.get("vectors", [])
    ]
    observed_vector_set_id = "secv_" + hashlib.sha256(_canonical_json_bytes(vector_payload)).hexdigest()
    if package.corpus.get("vector_set_id") != observed_vector_set_id:
        errors.append("VECTOR_SET_ID_MISMATCH")

    if package.manifest is not None:
        manifest = deepcopy(package.manifest)
        claimed_manifest_id = manifest.pop("manifest_id", None)
        observed_manifest_id = structural_hash(manifest)
        if claimed_manifest_id != observed_manifest_id:
            errors.append("MANIFEST_ID_MISMATCH")
        if package.manifest.get("corpus_id") != package.corpus.get("corpus_id"):
            errors.append("MANIFEST_CORPUS_LINK_MISMATCH")
        if package.manifest.get("vector_set_id") != package.corpus.get("vector_set_id"):
            errors.append("MANIFEST_VECTOR_SET_LINK_MISMATCH")

    return errors


def audit_package(package: CorpusPackage, *, verbose: bool = False) -> Dict[str, Any]:
    package_errors = validate_package_identity(package)
    profile_map = {
        profile["profile_id"]: profile
        for profile in package.profile_registry.get("profiles", [])
    }
    vector_map = {
        vector["vector_id"]: vector
        for vector in package.corpus.get("vectors", [])
    }

    group_totals: Dict[str, int] = {}
    group_passed: Dict[str, int] = {}
    failures: List[Dict[str, Any]] = []

    for vector in package.corpus.get("vectors", []):
        category = vector["category"]
        group_totals[category] = group_totals.get(category, 0) + 1
        vector_errors: List[str] = []

        try:
            actual = reconstruct_vector(vector, profile_map)
            if "verification_expectation" in vector:
                reference_id = vector["verification_expectation"]["reference_vector"]
                reference = vector_map[reference_id]
                observed_mismatch = first_tamper_mismatch(vector, actual, reference)
                expected_mismatch = vector["verification_expectation"]["expected_first_mismatch"]
                if observed_mismatch != expected_mismatch:
                    vector_errors.append(
                        f"TAMPER_MISMATCH_EXPECTED_{expected_mismatch}_OBSERVED_{observed_mismatch}"
                    )
            else:
                vector_errors.extend(compare_regular_vector(vector, actual))
        except Exception as exc:  # deterministic audit reporting boundary
            vector_errors.append(f"EXCEPTION:{type(exc).__name__}:{exc}")

        if vector_errors:
            failures.append({"vector_id": vector["vector_id"], "errors": vector_errors})
            if verbose:
                print(f"FAIL {vector['vector_id']}: {', '.join(vector_errors)}")
        else:
            group_passed[category] = group_passed.get(category, 0) + 1
            if verbose:
                print(f"PASS {vector['vector_id']}")

    total = sum(group_totals.values())
    passed = total - len(failures)
    status = "PASS" if not package_errors and not failures else "FAIL"

    return {
        "schema": "SEC-AUDIT-RESULT-1-D01",
        "system_version": SYSTEM_VERSION,
        "status": status,
        "passed": passed,
        "total": total,
        "package_errors": package_errors,
        "groups": {
            group: {"passed": group_passed.get(group, 0), "total": group_totals[group]}
            for group in sorted(group_totals)
        },
        "failures": failures,
        "vector_set_id": package.corpus.get("vector_set_id"),
        "corpus_id": package.corpus.get("corpus_id"),
        "profile_registry_id": package.corpus.get("profile_registry_id"),
    }


def _find_default_corpus(script_path: Path) -> Optional[Path]:
    candidates = [
        script_path.with_name("Structural_Earth_Centre_Conformance_Corpus_v0_5_0.zip"),
        script_path.with_name("SEC_Conformance_Corpus_v0_5_0"),
        script_path.with_name("SEC_Conformance_Corpus_v0_5_0.json"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def print_audit(result: Mapping[str, Any]) -> None:
    print("STRUCTURAL EARTH CENTRE REFERENCE KERNEL v0.5.0")
    print(f"STATUS {result['status']}")
    for group, counts in result["groups"].items():
        print(f"{group} {counts['passed']}/{counts['total']} {'PASS' if counts['passed'] == counts['total'] else 'FAIL'}")
    print(f"TOTAL {result['passed']}/{result['total']} {'PASS' if result['passed'] == result['total'] else 'FAIL'}")
    if result["package_errors"]:
        print("PACKAGE ERRORS")
        for error in result["package_errors"]:
            print(f"- {error}")
    if result["failures"]:
        print("VECTOR FAILURES")
        for failure in result["failures"]:
            print(f"- {failure['vector_id']}: {', '.join(failure['errors'])}")
    print(f"VECTOR SET {result['vector_set_id']}")
    print(f"CORPUS {result['corpus_id']}")
    print(f"PROFILE REGISTRY {result['profile_registry_id']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deterministic exact reference kernel for Structural Earth Centre v0.5.0"
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        help="Path to the SEC conformance package ZIP, corpus directory, or corpus JSON",
    )
    parser.add_argument("--audit", action="store_true", help="Run the frozen corpus audit")
    parser.add_argument("--vector", help="Reconstruct one vector by vector ID")
    parser.add_argument("--list", action="store_true", help="List vector IDs")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--verbose", action="store_true", help="Print every audit vector result")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    corpus_path = args.corpus or _find_default_corpus(Path(__file__).resolve())
    if corpus_path is None:
        parser.error("No corpus supplied and no default SEC conformance package found beside the script")

    try:
        package = load_package(corpus_path)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    profile_map = {
        profile["profile_id"]: profile
        for profile in package.profile_registry.get("profiles", [])
    }

    if args.list:
        for vector in package.corpus.get("vectors", []):
            print(f"{vector['vector_id']}\t{vector['category']}\t{vector['title']}")
        return 0

    if args.vector:
        vector = next(
            (item for item in package.corpus.get("vectors", []) if item["vector_id"] == args.vector),
            None,
        )
        if vector is None:
            print(f"ERROR: Unknown vector ID {args.vector}", file=sys.stderr)
            return 2
        actual = reconstruct_vector(vector, profile_map)
        payload = {
            "vector_id": vector["vector_id"],
            "centre_profile": vector["centre_profile"],
            "reconstruction": actual,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(f"VECTOR {vector['vector_id']}")
            print(f"STATE {actual['result']['resolution_state']}")
            print(f"RESULT ID {actual['result_id']}")
            print(f"CERTIFICATE ID {actual['certificate_id']}")
        return 0

    if args.audit or not (args.vector or args.list):
        result = audit_package(package, verbose=args.verbose)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print_audit(result)
        return 0 if result["status"] == "PASS" else 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
