#!/usr/bin/env python3
"""Structural Earth Centre v0.5.0 structural portability kernel.

This module implements domain-neutral structural primitives and two bounded
adapters used by the portability proof:
- an exact one-dimensional centre adapter;
- a synthetic admissibility adapter.

The generic relation, spectrum, frontier, and certificate functions are shared
unchanged by both adapters. Domain adapters provide only domain-specific
resolution semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

SYSTEM_VERSION = "0.5.0"
PORTABILITY_PROFILE = "SEC-STRUCTURAL-PORTABILITY-PROOF-1-D01"
GENERIC_KERNEL_PROFILE = "SEC-GENERIC-STRUCTURAL-KERNEL-1-D01"
CENTRE_ADAPTER_PROFILE = "SEC-PORTABILITY-ADAPTER-CENTRE-1-D01"
ADMISSIBILITY_ADAPTER_PROFILE = "SEC-PORTABILITY-ADAPTER-ADMISSIBILITY-1-D01"

CLAIM_RELATION_SCHEMA = "SEC-GENERIC-CLAIM-RELATION-1-D01"
RESULT_SPECTRUM_SCHEMA = "SEC-GENERIC-RESULT-SPECTRUM-1-D01"
RESOLUTION_FRONTIER_SCHEMA = "SEC-GENERIC-RESOLUTION-FRONTIER-1-D01"
RESOLUTION_CERTIFICATE_SCHEMA = "SEC-GENERIC-RESOLUTION-CERTIFICATE-1-D01"
PORTABILITY_CERTIFICATE_SCHEMA = "SEC-STRUCTURAL-PORTABILITY-CERTIFICATE-1-D01"

RESOLVED_STATE = "RESOLVED"
MAX_CLAIMS = 256
MAX_REPAIR_OPTIONS = 16
MAX_DEPENDENCIES = 256
MAX_CENTRE_POINTS = 10000


class PortabilityError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def structural_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def canonical_map(value: Mapping[str, Any]) -> Dict[str, Any]:
    return json.loads(canonical_bytes(dict(value)).decode("utf-8"))


def verify_self_hash(obj: Mapping[str, Any], field: str) -> bool:
    expected = obj.get(field)
    body = {k: v for k, v in obj.items() if k != field}
    return expected == structural_hash(body)


def _is_conflict(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 1


def _resolved(result: Mapping[str, Any]) -> bool:
    return result.get("resolution_state") == RESOLVED_STATE


def generic_claim_material(claim: Mapping[str, Any]) -> Dict[str, Any]:
    dependencies = canonical_map(claim.get("dependencies", {}))
    if len(dependencies) > MAX_DEPENDENCIES:
        raise PortabilityError("DEPENDENCY_LIMIT_EXCEEDED")
    return {
        "schema": "SEC-GENERIC-CLAIM-MATERIAL-1-D01",
        "system_version": SYSTEM_VERSION,
        "domain_id": claim.get("domain_id", "UNDECLARED"),
        "scope_id": claim.get("scope_id", "UNDECLARED"),
        "profile_id": claim.get("profile_id", "UNDECLARED"),
        "dependencies": dependencies,
    }


def generic_claim_id(claim: Mapping[str, Any]) -> str:
    return structural_hash(generic_claim_material(claim))


def generic_result_id(result: Mapping[str, Any]) -> str:
    return structural_hash(canonical_map(result))


def _result_relation(left: Mapping[str, Any], right: Mapping[str, Any]) -> str:
    if not _resolved(left) or not _resolved(right):
        return "UNRESOLVED_RESULT_RELATION"
    return "RESULT_EQUIVALENT" if canonical_map(left) == canonical_map(right) else "RESULT_DIVERGENT"


def build_claim_relation(left: Mapping[str, Any], right: Mapping[str, Any]) -> Dict[str, Any]:
    left_material = generic_claim_material(left)
    right_material = generic_claim_material(right)
    ld = left_material["dependencies"]
    rd = right_material["dependencies"]

    shared = sorted(set(ld) & set(rd))
    conflicts = [key for key in shared if ld[key] != rd[key]]
    left_only = sorted(set(ld) - set(rd))
    right_only = sorted(set(rd) - set(ld))

    same_domain = left_material["domain_id"] == right_material["domain_id"]
    same_scope = (
        same_domain
        and left_material["scope_id"] == right_material["scope_id"]
        and left_material["profile_id"] == right_material["profile_id"]
    )

    if not same_domain:
        relation = "DISJOINT_DOMAINS"
    elif conflicts:
        relation = "DECLARATION_CONFLICT"
    elif same_scope and not left_only and not right_only:
        relation = "CLAIM_EQUIVALENT"
    elif same_scope and left_only and not right_only:
        relation = "LEFT_REFINES_RIGHT"
    elif same_scope and right_only and not left_only:
        relation = "RIGHT_REFINES_LEFT"
    elif shared:
        relation = "COMPATIBLE_OVERLAP"
    else:
        relation = "DISJOINT_DECLARATIONS"

    left_result = canonical_map(left.get("result", {}))
    right_result = canonical_map(right.get("result", {}))
    body = {
        "schema": CLAIM_RELATION_SCHEMA,
        "system_version": SYSTEM_VERSION,
        "claim_relation": relation,
        "result_relation": _result_relation(left_result, right_result),
        "shared_dependencies": shared,
        "conflicting_dependencies": conflicts,
        "left_only_dependencies": left_only,
        "right_only_dependencies": right_only,
        "left_claim_id": structural_hash(left_material),
        "right_claim_id": structural_hash(right_material),
    }
    return {**body, "claim_relation_id": structural_hash(body)}


def build_result_spectrum(claims: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    if len(claims) > MAX_CLAIMS:
        body = {
            "schema": RESULT_SPECTRUM_SCHEMA,
            "system_version": SYSTEM_VERSION,
            "spectrum_state": "UNSUPPORTED",
            "reason": "CLAIM_LIMIT_EXCEEDED",
        }
        return {**body, "spectrum_id": structural_hash(body)}

    members: List[Dict[str, Any]] = []
    for index, claim in enumerate(claims):
        material = generic_claim_material(claim)
        result = canonical_map(claim.get("result", {}))
        members.append({
            "member_id": str(claim.get("member_id", f"M{index + 1:04d}")),
            "claim_id": structural_hash(material),
            "result_id": structural_hash(result),
            "resolution_state": result.get("resolution_state", "UNDECLARED"),
            "claim_material": material,
            "result": result,
        })
    members.sort(key=lambda item: (item["claim_id"], item["result_id"], item["member_id"]))

    if not members:
        state = "INCOMPLETE"
    else:
        resolved = [member for member in members if member["resolution_state"] == RESOLVED_STATE]
        if not resolved:
            state = "UNRESOLVED_FAMILY"
        elif len(resolved) != len(members):
            state = "MIXED_RESOLUTION_FAMILY"
        else:
            claim_count = len({member["claim_id"] for member in members})
            result_count = len({member["result_id"] for member in members})
            if claim_count == 1 and result_count == 1:
                state = "SINGLE_CLAIM_FAMILY"
            elif result_count == 1:
                state = "RESULT_CONVERGENT_CLAIM_DIVERSE"
            else:
                state = "RESULT_DIVERGENT_FAMILY"

    body = {
        "schema": RESULT_SPECTRUM_SCHEMA,
        "system_version": SYSTEM_VERSION,
        "spectrum_state": state,
        "member_count": len(members),
        "resolved_member_count": sum(member["resolution_state"] == RESOLVED_STATE for member in members),
        "distinct_claim_count": len({member["claim_id"] for member in members}),
        "distinct_result_count": len({member["result_id"] for member in members}),
        "aggregation_policy": "NO_BLIND_AGGREGATION_OF_STRUCTURALLY_DISTINCT_RESULTS",
        "members": members,
    }
    return {**body, "spectrum_id": structural_hash(body)}


def _apply_operations(current: Mapping[str, Any], operations: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    result = canonical_map(current)
    for operation in operations:
        op = operation.get("op")
        key = str(operation.get("key", ""))
        if not key:
            raise PortabilityError("REPAIR_KEY_REQUIRED")
        if op == "SET":
            result[key] = deepcopy(operation.get("value"))
        elif op == "REMOVE":
            result.pop(key, None)
        else:
            raise PortabilityError("UNSUPPORTED_REPAIR_OPERATION")
    return canonical_map(result)


def build_resolution_frontier(
    current_dependencies: Mapping[str, Any],
    *,
    repair_options: Sequence[Mapping[str, Any]],
    resolver: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    domain_id: str,
    adapter_profile_id: str,
) -> Dict[str, Any]:
    if len(repair_options) > MAX_REPAIR_OPTIONS:
        body = {
            "schema": RESOLUTION_FRONTIER_SCHEMA,
            "system_version": SYSTEM_VERSION,
            "frontier_state": "UNSUPPORTED",
            "reason": "REPAIR_OPTION_LIMIT_EXCEEDED",
            "domain_id": domain_id,
            "adapter_profile_id": adapter_profile_id,
        }
        return {**body, "resolution_frontier_id": structural_hash(body)}

    current = canonical_map(current_dependencies)
    current_result = canonical_map(resolver(current))
    if _resolved(current_result):
        body = {
            "schema": RESOLUTION_FRONTIER_SCHEMA,
            "system_version": SYSTEM_VERSION,
            "frontier_state": "ALREADY_ADMISSIBLE",
            "domain_id": domain_id,
            "adapter_profile_id": adapter_profile_id,
            "current_dependencies": current,
            "current_result": current_result,
            "minimal_repair_size": 0,
            "minimal_repair_sets": [],
            "repair_policy": "DECLARED_OPTIONS_ONLY",
        }
        return {**body, "resolution_frontier_id": structural_hash(body)}

    options = [canonical_map(option) for option in repair_options]
    options.sort(key=lambda item: canonical_bytes(item))
    minimal_sets: List[Dict[str, Any]] = []
    minimal_size: Optional[int] = None

    for size in range(1, len(options) + 1):
        for combo in itertools.combinations(options, size):
            try:
                repaired = _apply_operations(current, combo)
                result = canonical_map(resolver(repaired))
            except PortabilityError:
                continue
            if _resolved(result):
                minimal_sets.append({
                    "operations": list(combo),
                    "resulting_dependencies": repaired,
                    "result": result,
                })
        if minimal_sets:
            minimal_size = size
            break

    if not minimal_sets:
        state = "NO_ADMISSIBLE_FRONTIER"
    elif len(minimal_sets) == 1:
        state = "UNIQUE_MINIMAL_FRONTIER"
    else:
        state = "MULTIPLE_MINIMAL_FRONTIERS"

    minimal_sets.sort(key=lambda item: canonical_bytes(item))
    body = {
        "schema": RESOLUTION_FRONTIER_SCHEMA,
        "system_version": SYSTEM_VERSION,
        "frontier_state": state,
        "domain_id": domain_id,
        "adapter_profile_id": adapter_profile_id,
        "current_dependencies": current,
        "current_result": current_result,
        "minimal_repair_size": minimal_size,
        "minimal_repair_sets": minimal_sets,
        "declared_repair_option_count": len(options),
        "repair_policy": "DECLARED_OPTIONS_ONLY",
        "invents_missing_evidence": False,
    }
    return {**body, "resolution_frontier_id": structural_hash(body)}


def build_resolution_certificate(
    claim: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    adapter_profile_id: str,
    evidence_id: Optional[str] = None,
) -> Dict[str, Any]:
    claim_material = generic_claim_material(claim)
    result_material = canonical_map(result)
    body = {
        "schema": RESOLUTION_CERTIFICATE_SCHEMA,
        "system_version": SYSTEM_VERSION,
        "generic_kernel_profile": GENERIC_KERNEL_PROFILE,
        "adapter_profile_id": adapter_profile_id,
        "claim_id": structural_hash(claim_material),
        "result_id": structural_hash(result_material),
        "claim_material": claim_material,
        "result_material": result_material,
        "evidence_id": evidence_id or "NO_EXTERNAL_EVIDENCE_DECLARED",
    }
    return {**body, "certificate_id": structural_hash(body)}


def _canonical_fraction(value: Any) -> Fraction:
    if isinstance(value, bool):
        raise PortabilityError("BOOLEAN_IS_NOT_RATIONAL")
    if isinstance(value, int):
        return Fraction(value, 1)
    if isinstance(value, str):
        return Fraction(value)
    if isinstance(value, Mapping) and set(value).issuperset({"n", "d"}):
        denominator = int(value["d"])
        if denominator == 0:
            raise PortabilityError("ZERO_DENOMINATOR")
        return Fraction(int(value["n"]), denominator)
    raise PortabilityError("UNSUPPORTED_RATIONAL")


def _fraction_json(value: Fraction) -> Dict[str, str]:
    return {"n": str(value.numerator), "d": str(value.denominator)}


def resolve_centre_adapter(
    subject: Mapping[str, Any],
    dependencies: Mapping[str, Any],
    *,
    profile_id: str = "CENTRE_EXACT_MEAN_1D",
) -> Dict[str, Any]:
    deps = canonical_map(dependencies)
    required = ["frame", "measure"]
    conflicts = [key for key in required if _is_conflict(deps.get(key))]
    if conflicts:
        return {"resolution_state": "CONFLICT", "conflicting_dependencies": conflicts}
    missing = [key for key in required if key not in deps]
    if missing:
        return {"resolution_state": "INCOMPLETE", "missing_dependencies": missing}
    if profile_id != "CENTRE_EXACT_MEAN_1D":
        return {"resolution_state": "UNSUPPORTED", "reason": "UNSUPPORTED_CENTRE_PROFILE"}
    if deps.get("measure") not in {"UNIFORM_POINT_MASS", "DECLARED_EQUAL_WEIGHTS"}:
        return {"resolution_state": "UNSUPPORTED", "reason": "UNSUPPORTED_CENTRE_MEASURE"}

    points = subject.get("points", [])
    if not isinstance(points, list) or not points or len(points) > MAX_CENTRE_POINTS:
        return {"resolution_state": "INCOMPLETE", "reason": "NO_ADMITTED_POINTS"}
    values = [_canonical_fraction(value) for value in points]
    centre = sum(values, Fraction(0, 1)) / len(values)
    return {
        "resolution_state": RESOLVED_STATE,
        "outcome": "CENTRE_POINT",
        "value": [_fraction_json(centre)],
    }


def resolve_admissibility_adapter(
    subject: Mapping[str, Any],
    dependencies: Mapping[str, Any],
    *,
    profile_id: str = "ADMISSIBILITY_STANDARD",
) -> Dict[str, Any]:
    deps = canonical_map(dependencies)
    required = ["eligibility_class", "evidence_status"]
    conflicts = [key for key in required if _is_conflict(deps.get(key))]
    if conflicts:
        return {"resolution_state": "CONFLICT", "conflicting_dependencies": conflicts}
    missing = [key for key in required if key not in deps]
    if missing:
        return {"resolution_state": "INCOMPLETE", "missing_dependencies": missing}
    if profile_id != "ADMISSIBILITY_STANDARD":
        return {"resolution_state": "UNSUPPORTED", "reason": "UNSUPPORTED_ADMISSIBILITY_PROFILE"}

    evidence_status = deps.get("evidence_status")
    eligibility_class = deps.get("eligibility_class")
    if evidence_status not in {"VERIFIED", "ATTESTED"}:
        return {"resolution_state": "ABSTAIN", "reason": "EVIDENCE_STATUS_NOT_ADMITTED"}
    if eligibility_class == "STANDARD":
        outcome = "ADMITTED"
    elif eligibility_class == "BLOCKED":
        outcome = "REFUSED"
    else:
        return {"resolution_state": "UNSUPPORTED", "reason": "UNSUPPORTED_ELIGIBILITY_CLASS"}
    return {
        "resolution_state": RESOLVED_STATE,
        "outcome": outcome,
        "decision_scope": "BOUNDED_SYNTHETIC_ADMISSIBILITY",
        "execution_authority": "NONE",
    }


def resolve_adapter(domain_id: str, subject: Mapping[str, Any], dependencies: Mapping[str, Any], profile_id: str) -> Dict[str, Any]:
    if domain_id == "CENTRE":
        return resolve_centre_adapter(subject, dependencies, profile_id=profile_id)
    if domain_id == "ADMISSIBILITY":
        return resolve_admissibility_adapter(subject, dependencies, profile_id=profile_id)
    return {"resolution_state": "UNSUPPORTED", "reason": "UNKNOWN_DOMAIN_ADAPTER"}


def _adapter_profile_id(domain_id: str) -> str:
    if domain_id == "CENTRE":
        return CENTRE_ADAPTER_PROFILE
    if domain_id == "ADMISSIBILITY":
        return ADMISSIBILITY_ADAPTER_PROFILE
    raise PortabilityError("UNKNOWN_DOMAIN_ADAPTER")


def evaluate_vector(vector: Mapping[str, Any]) -> Dict[str, Any]:
    operation = vector.get("operation")
    data = vector.get("input", {})

    if operation == "CLAIM_RELATION":
        return build_claim_relation(data["left"], data["right"])
    if operation == "RESULT_SPECTRUM":
        return build_result_spectrum(data["claims"])
    if operation == "RESOLUTION_FRONTIER":
        domain_id = data["domain_id"]
        subject = data["subject"]
        profile_id = data["profile_id"]
        resolver = lambda deps: resolve_adapter(domain_id, subject, deps, profile_id)
        return build_resolution_frontier(
            data["current_dependencies"],
            repair_options=data["repair_options"],
            resolver=resolver,
            domain_id=domain_id,
            adapter_profile_id=_adapter_profile_id(domain_id),
        )
    if operation == "RESOLUTION_CERTIFICATE":
        domain_id = data["domain_id"]
        return build_resolution_certificate(
            data["claim"],
            data["result"],
            adapter_profile_id=_adapter_profile_id(domain_id),
            evidence_id=data.get("evidence_id"),
        )
    if operation == "DOMAIN_RESOLVE":
        return resolve_adapter(data["domain_id"], data["subject"], data["dependencies"], data["profile_id"])
    raise PortabilityError("UNKNOWN_PORTABILITY_OPERATION")


def build_portability_certificate(
    corpus: Mapping[str, Any],
    portability_profile: Mapping[str, Any],
    generic_profile: Mapping[str, Any],
    centre_adapter_profile: Mapping[str, Any],
    admissibility_adapter_profile: Mapping[str, Any],
) -> Dict[str, Any]:
    body = {
        "schema": PORTABILITY_CERTIFICATE_SCHEMA,
        "system_version": SYSTEM_VERSION,
        "portability_profile_id": PORTABILITY_PROFILE,
        "portability_profile_hash": portability_profile["profile_hash"],
        "generic_kernel_profile_id": GENERIC_KERNEL_PROFILE,
        "generic_kernel_profile_hash": generic_profile["profile_hash"],
        "adapter_profiles": [
            {
                "domain_id": "ADMISSIBILITY",
                "adapter_profile_id": ADMISSIBILITY_ADAPTER_PROFILE,
                "adapter_profile_hash": admissibility_adapter_profile["profile_hash"],
            },
            {
                "domain_id": "CENTRE",
                "adapter_profile_id": CENTRE_ADAPTER_PROFILE,
                "adapter_profile_hash": centre_adapter_profile["profile_hash"],
            },
        ],
        "vector_set_id": corpus["vector_set_id"],
        "vector_corpus_id": corpus["vector_corpus_id"],
        "proof_scope": "SHARED_GENERIC_PRIMITIVES_ACROSS_TWO_BOUNDED_DOMAIN_ADAPTERS",
    }
    return {**body, "portability_certificate_id": structural_hash(body)}


def audit_vector_corpus(
    corpus: Mapping[str, Any],
    *,
    portability_profile: Mapping[str, Any],
    generic_profile: Mapping[str, Any],
    centre_adapter_profile: Mapping[str, Any],
    admissibility_adapter_profile: Mapping[str, Any],
    verbose: bool = False,
) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: Any) -> None:
        checks.append({"check_id": check_id, "pass": bool(passed), "detail": detail})
        if verbose:
            print("PASS" if passed else "FAIL", check_id, detail)

    profiles = [
        portability_profile,
        generic_profile,
        centre_adapter_profile,
        admissibility_adapter_profile,
    ]
    add(
        "PROFILE_IDENTITIES",
        all(verify_self_hash(profile, "profile_hash") for profile in profiles),
        [profile["profile_hash"] for profile in profiles],
    )
    add("CORPUS_ID", verify_self_hash(corpus, "vector_corpus_id"), corpus.get("vector_corpus_id"))
    actual_set = "secport_" + hashlib.sha256(canonical_bytes([v["vector_hash"] for v in corpus.get("vectors", [])])).hexdigest()
    add("VECTOR_SET_ID", actual_set == corpus.get("vector_set_id"), actual_set)

    vector_map: Dict[str, Mapping[str, Any]] = {}
    for vector in corpus.get("vectors", []):
        vector_map[vector["vector_id"]] = vector
        actual = evaluate_vector(vector)
        passed = verify_self_hash(vector, "vector_hash") and actual == vector.get("expected")
        detail = actual.get(
            "claim_relation",
            actual.get(
                "spectrum_state",
                actual.get(
                    "frontier_state",
                    actual.get("resolution_state", "CERTIFICATE"),
                ),
            ),
        )
        add(vector["vector_id"], passed, detail)

    relation_pairs = [
        ("SEC-PORT-RC001", "SEC-PORT-RA001"),
        ("SEC-PORT-RC002", "SEC-PORT-RA002"),
        ("SEC-PORT-RC003", "SEC-PORT-RA003"),
        ("SEC-PORT-RC004", "SEC-PORT-RA004"),
    ]
    for index, (left_id, right_id) in enumerate(relation_pairs, start=1):
        left = evaluate_vector(vector_map[left_id])
        right = evaluate_vector(vector_map[right_id])
        add(
            f"RELATION_SEMANTICS_DOMAIN_INVARIANT_{index}",
            left["claim_relation"] == right["claim_relation"],
            [left["claim_relation"], right["claim_relation"]],
        )

    spectrum_pairs = [
        ("SEC-PORT-SC001", "SEC-PORT-SA001"),
        ("SEC-PORT-SC002", "SEC-PORT-SA002"),
        ("SEC-PORT-SC003", "SEC-PORT-SA003"),
    ]
    for index, (left_id, right_id) in enumerate(spectrum_pairs, start=1):
        left = evaluate_vector(vector_map[left_id])
        right = evaluate_vector(vector_map[right_id])
        add(
            f"SPECTRUM_SEMANTICS_DOMAIN_INVARIANT_{index}",
            left["spectrum_state"] == right["spectrum_state"],
            [left["spectrum_state"], right["spectrum_state"]],
        )

    frontier_pairs = [
        ("SEC-PORT-FC001", "SEC-PORT-FA001"),
        ("SEC-PORT-FC002", "SEC-PORT-FA002"),
        ("SEC-PORT-FC003", "SEC-PORT-FA003"),
    ]
    for index, (left_id, right_id) in enumerate(frontier_pairs, start=1):
        left = evaluate_vector(vector_map[left_id])
        right = evaluate_vector(vector_map[right_id])
        add(
            f"FRONTIER_SEMANTICS_DOMAIN_INVARIANT_{index}",
            left["frontier_state"] == right["frontier_state"]
            and left["minimal_repair_size"] == right["minimal_repair_size"],
            [
                left["frontier_state"],
                right["frontier_state"],
                left["minimal_repair_size"],
                right["minimal_repair_size"],
            ],
        )

    certificate_vector = vector_map["SEC-PORT-CA001"]
    certificate = evaluate_vector(certificate_vector)
    tampered_input = deepcopy(certificate_vector["input"])
    tampered_input["result"]["outcome"] = "REFUSED"
    tampered = evaluate_vector({**certificate_vector, "input": tampered_input})
    add(
        "CERTIFICATE_TAMPER_SENSITIVITY",
        certificate["certificate_id"] != tampered["certificate_id"],
        tampered["certificate_id"],
    )

    generic_ops = set(generic_profile.get("generic_operations", []))
    adapter_ops = set(centre_adapter_profile.get("domain_operations", [])) | set(admissibility_adapter_profile.get("domain_operations", []))
    add(
        "GENERIC_KERNEL_ADAPTER_SEPARATION",
        generic_ops == {"CLAIM_RELATION", "RESULT_SPECTRUM", "RESOLUTION_FRONTIER", "RESOLUTION_CERTIFICATE"}
        and "DOMAIN_RESOLVE" in adapter_ops
        and not (generic_ops & {"CENTRE_EXACT_MEAN", "SYNTHETIC_ADMISSIBILITY"}),
        sorted(generic_ops),
    )

    portability_certificate = build_portability_certificate(
        corpus,
        portability_profile,
        generic_profile,
        centre_adapter_profile,
        admissibility_adapter_profile,
    )
    certificate_body = {k: v for k, v in portability_certificate.items() if k != "portability_certificate_id"}
    add(
        "PORTABILITY_CERTIFICATE_RECONSTRUCTS",
        structural_hash(certificate_body) == portability_certificate["portability_certificate_id"],
        portability_certificate["portability_certificate_id"],
    )

    passed = sum(1 for check in checks if check["pass"])
    total = len(checks)
    core = {
        "schema": "SEC-STRUCTURAL-PORTABILITY-AUDIT-1-D01",
        "system_version": SYSTEM_VERSION,
        "status": "PASS" if passed == total else "FAIL",
        "passed": passed,
        "total": total,
        "portability_profile_id": PORTABILITY_PROFILE,
        "generic_kernel_profile_id": GENERIC_KERNEL_PROFILE,
        "vector_set_id": corpus.get("vector_set_id"),
        "vector_corpus_id": corpus.get("vector_corpus_id"),
        "portability_certificate": portability_certificate,
        "checks": checks,
    }
    return {**core, "evidence_id": structural_hash(core)}


def load_profiles(profile_dir: Path) -> Dict[str, Dict[str, Any]]:
    names = {
        "portability": "SEC_Structural_Portability_Profile_v0_5_0.json",
        "generic": "SEC_Generic_Structural_Kernel_Profile_v0_5_0.json",
        "centre": "SEC_Portability_Centre_Adapter_Profile_v0_5_0.json",
        "admissibility": "SEC_Portability_Admissibility_Adapter_Profile_v0_5_0.json",
    }
    return {
        key: json.loads((profile_dir / filename).read_text(encoding="utf-8"))
        for key, filename in names.items()
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vectors",
        type=Path,
        default=Path("profiles") / "SEC_Structural_Portability_Vectors_v0_5_0.json",
    )
    parser.add_argument("--profiles", type=Path, default=Path("profiles"))
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    corpus = json.loads(args.vectors.read_text(encoding="utf-8"))
    profiles = load_profiles(args.profiles)
    result = audit_vector_corpus(
        corpus,
        portability_profile=profiles["portability"],
        generic_profile=profiles["generic"],
        centre_adapter_profile=profiles["centre"],
        admissibility_adapter_profile=profiles["admissibility"],
        verbose=args.verbose,
    )

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print("STRUCTURAL EARTH CENTRE STRUCTURAL PORTABILITY KERNEL v0.5.0")
        print("STATUS", result["status"])
        print("TOTAL", f"{result['passed']}/{result['total']}", result["status"])
        print("VECTOR SET", result["vector_set_id"])
        print("CORPUS", result["vector_corpus_id"])
        print("PORTABILITY CERTIFICATE", result["portability_certificate"]["portability_certificate_id"])
        print("EVIDENCE ID", result["evidence_id"])

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
