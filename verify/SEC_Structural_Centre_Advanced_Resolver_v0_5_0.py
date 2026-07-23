#!/usr/bin/env python3
"""Structural Earth Centre v0.5.0 advanced structural centre resolver.

Implements four bounded capabilities:
- Structural Claim Relation
- Centre Spectrum
- Resolution Frontier
- Exact finite Graph Centre portability demonstration

The module does not infer causality, average structurally distinct centres, or
claim coverage outside declared repair options and finite carriers.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import deque
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

SYSTEM_VERSION = "0.5.0"
ADVANCED_PROFILE = "SEC-STRUCTURAL-CENTRE-ADVANCED-1-D01"
RELATION_PROFILE = "SEC-STRUCTURAL-CLAIM-RELATION-1-D01"
SPECTRUM_PROFILE = "SEC-CENTRE-SPECTRUM-1-D01"
FRONTIER_PROFILE = "SEC-RESOLUTION-FRONTIER-1-D01"
GRAPH_PROFILE = "SEC-EXACT-GRAPH-CENTRE-1-D01"
RESOLVED_STATES = {"RESOLVED_POINT", "RESOLVED_REGION", "MULTI_CENTRE"}
MAX_CLAIMS = 256
MAX_REPAIR_OPTIONS = 16
MAX_GRAPH_NODES = 256
MAX_GRAPH_EDGES = 4096


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def structural_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def canonical_map(value: Mapping[str, Any]) -> Dict[str, Any]:
    return json.loads(canonical_bytes(dict(value)).decode("utf-8"))


def _result_relation(left: Mapping[str, Any], right: Mapping[str, Any]) -> str:
    ls = left.get("resolution_state")
    rs = right.get("resolution_state")
    if ls not in RESOLVED_STATES or rs not in RESOLVED_STATES:
        return "UNRESOLVED_RESULT_RELATION"
    return "RESULT_EQUIVALENT" if canonical_map(left) == canonical_map(right) else "RESULT_DIVERGENT"


def build_claim_relation(left: Mapping[str, Any], right: Mapping[str, Any]) -> Dict[str, Any]:
    ld = canonical_map(left.get("dependencies", {}))
    rd = canonical_map(right.get("dependencies", {}))
    shared = sorted(set(ld) & set(rd))
    conflicts = [k for k in shared if ld[k] != rd[k]]
    lonly = sorted(set(ld) - set(rd))
    ronly = sorted(set(rd) - set(ld))

    same_scope = (
        left.get("carrier_id", "UNDECLARED") == right.get("carrier_id", "UNDECLARED")
        and left.get("centre_profile_id", "UNDECLARED") == right.get("centre_profile_id", "UNDECLARED")
    )

    if conflicts:
        relation = "DECLARATION_CONFLICT"
    elif same_scope and not lonly and not ronly:
        relation = "CLAIM_EQUIVALENT"
    elif same_scope and lonly and not ronly:
        relation = "LEFT_REFINES_RIGHT"
    elif same_scope and ronly and not lonly:
        relation = "RIGHT_REFINES_LEFT"
    elif shared:
        relation = "COMPATIBLE_OVERLAP"
    else:
        relation = "DISJOINT_DECLARATIONS"

    left_result = canonical_map(left.get("result", {}))
    right_result = canonical_map(right.get("result", {}))
    body = {
        "schema": RELATION_PROFILE,
        "system_version": SYSTEM_VERSION,
        "claim_relation": relation,
        "result_relation": _result_relation(left_result, right_result),
        "shared_dependencies": shared,
        "conflicting_dependencies": conflicts,
        "left_only_dependencies": lonly,
        "right_only_dependencies": ronly,
        "left_claim_material_id": structural_hash({
            "carrier_id": left.get("carrier_id", "UNDECLARED"),
            "centre_profile_id": left.get("centre_profile_id", "UNDECLARED"),
            "dependencies": ld,
        }),
        "right_claim_material_id": structural_hash({
            "carrier_id": right.get("carrier_id", "UNDECLARED"),
            "centre_profile_id": right.get("centre_profile_id", "UNDECLARED"),
            "dependencies": rd,
        }),
    }
    return {**body, "claim_relation_id": structural_hash(body)}


def build_centre_spectrum(claims: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    if len(claims) > MAX_CLAIMS:
        body = {"schema": SPECTRUM_PROFILE, "system_version": SYSTEM_VERSION, "spectrum_state": "UNSUPPORTED", "reason": "CLAIM_LIMIT_EXCEEDED"}
        return {**body, "spectrum_id": structural_hash(body)}
    normalized = []
    for i, item in enumerate(claims):
        deps = canonical_map(item.get("dependencies", {}))
        result = canonical_map(item.get("result", {}))
        claim_material = {
            "carrier_id": item.get("carrier_id", "UNDECLARED"),
            "centre_profile_id": item.get("centre_profile_id", "UNDECLARED"),
            "dependencies": deps,
        }
        normalized.append({
            "member_id": str(item.get("member_id", f"M{i+1:04d}")),
            "claim_id": structural_hash(claim_material),
            "result_id": structural_hash(result),
            "resolution_state": result.get("resolution_state", "UNDECLARED"),
            "claim_material": claim_material,
            "result": result,
        })
    normalized.sort(key=lambda x: (x["claim_id"], x["result_id"], x["member_id"]))
    if not normalized:
        state = "INCOMPLETE"
    else:
        resolved = [m for m in normalized if m["resolution_state"] in RESOLVED_STATES]
        if not resolved:
            state = "UNRESOLVED_FAMILY"
        elif len(resolved) != len(normalized):
            state = "MIXED_RESOLUTION_FAMILY"
        else:
            claim_count = len({m["claim_id"] for m in normalized})
            result_count = len({m["result_id"] for m in normalized})
            if claim_count == 1 and result_count == 1:
                state = "SINGLE_CLAIM_FAMILY"
            elif result_count == 1:
                state = "RESULT_CONVERGENT_CLAIM_DIVERSE"
            else:
                state = "RESULT_DIVERGENT_FAMILY"

    result_classes: Dict[str, List[str]] = {}
    for m in normalized:
        result_classes.setdefault(m["result_id"], []).append(m["claim_id"])
    classes = [
        {"result_id": rid, "claim_ids": sorted(set(cids)), "member_count": sum(1 for m in normalized if m["result_id"] == rid)}
        for rid, cids in sorted(result_classes.items())
    ]
    relations = []
    for a, b in itertools.combinations(normalized, 2):
        rel = build_claim_relation(
            {**a["claim_material"], "result": a["result"]},
            {**b["claim_material"], "result": b["result"]},
        )
        relations.append({
            "left_claim_id": a["claim_id"],
            "right_claim_id": b["claim_id"],
            "claim_relation": rel["claim_relation"],
            "result_relation": rel["result_relation"],
            "claim_relation_id": rel["claim_relation_id"],
        })
    body = {
        "schema": SPECTRUM_PROFILE,
        "system_version": SYSTEM_VERSION,
        "spectrum_state": state,
        "member_count": len(normalized),
        "resolved_member_count": sum(1 for m in normalized if m["resolution_state"] in RESOLVED_STATES),
        "distinct_claim_count": len({m["claim_id"] for m in normalized}),
        "distinct_result_count": len({m["result_id"] for m in normalized}),
        "members": [{k: m[k] for k in ("member_id", "claim_id", "result_id", "resolution_state")} for m in normalized],
        "result_equivalence_classes": classes,
        "pairwise_relations": relations,
        "aggregation_policy": "NO_BLIND_AVERAGING_OF_STRUCTURALLY_DISTINCT_RESULTS",
    }
    return {**body, "spectrum_id": structural_hash(body)}


def _admissibility(deps: Mapping[str, Any], required: Sequence[str], single_value_keys: Sequence[str]) -> Tuple[bool, List[str], List[str]]:
    missing = sorted(k for k in required if k not in deps)
    conflicts = sorted(k for k in single_value_keys if isinstance(deps.get(k), list) and len(deps.get(k)) > 1)
    return (not missing and not conflicts), missing, conflicts


def _apply_repairs(current: Mapping[str, Any], operations: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    out = deepcopy(dict(current))
    for op in operations:
        kind = op.get("op")
        key = str(op.get("key"))
        if kind == "SET":
            out[key] = deepcopy(op.get("value"))
        elif kind == "REMOVE":
            out.pop(key, None)
        else:
            raise ValueError("UNSUPPORTED_REPAIR_OPERATION")
    return canonical_map(out)


def build_resolution_frontier(
    current_dependencies: Mapping[str, Any],
    *,
    required_dependencies: Sequence[str],
    single_value_keys: Sequence[str] = (),
    repair_options: Sequence[Mapping[str, Any]] = (),
) -> Dict[str, Any]:
    current = canonical_map(current_dependencies)
    required = sorted(set(map(str, required_dependencies)))
    single = sorted(set(map(str, single_value_keys)))
    options = [canonical_map(o) for o in repair_options]
    options.sort(key=canonical_bytes)
    if len(options) > MAX_REPAIR_OPTIONS:
        body = {"schema": FRONTIER_PROFILE, "system_version": SYSTEM_VERSION, "frontier_state": "UNSUPPORTED", "reason": "REPAIR_OPTION_LIMIT_EXCEEDED"}
        return {**body, "resolution_frontier_id": structural_hash(body)}
    admitted, missing, conflicts = _admissibility(current, required, single)
    if admitted:
        body = {
            "schema": FRONTIER_PROFILE,
            "system_version": SYSTEM_VERSION,
            "frontier_state": "ALREADY_ADMISSIBLE",
            "current_dependencies": current,
            "missing_dependencies": [],
            "conflicting_dependencies": [],
            "minimal_repair_size": 0,
            "minimal_repair_sets": [],
        }
        return {**body, "resolution_frontier_id": structural_hash(body)}

    solutions = []
    for size in range(1, len(options) + 1):
        for combo in itertools.combinations(options, size):
            try:
                candidate = _apply_repairs(current, combo)
            except ValueError:
                continue
            ok, _, _ = _admissibility(candidate, required, single)
            if ok:
                solutions.append({"operations": list(combo), "resulting_dependencies": candidate})
        if solutions:
            break
    unique = {canonical_bytes(s): s for s in solutions}
    solutions = [unique[k] for k in sorted(unique)]
    if not solutions:
        state = "NO_ADMISSIBLE_FRONTIER"
        min_size = None
    elif len(solutions) == 1:
        state = "UNIQUE_MINIMAL_FRONTIER"
        min_size = len(solutions[0]["operations"])
    else:
        state = "MULTIPLE_MINIMAL_FRONTIERS"
        min_size = len(solutions[0]["operations"])
    body = {
        "schema": FRONTIER_PROFILE,
        "system_version": SYSTEM_VERSION,
        "frontier_state": state,
        "current_dependencies": current,
        "missing_dependencies": missing,
        "conflicting_dependencies": conflicts,
        "minimal_repair_size": min_size,
        "minimal_repair_sets": solutions,
        "repair_scope": "DECLARED_OPTIONS_ONLY",
    }
    return {**body, "resolution_frontier_id": structural_hash(body)}


def resolve_graph_centre(graph: Mapping[str, Any]) -> Dict[str, Any]:
    nodes = sorted(set(map(str, graph.get("nodes", []))))
    edges_raw = graph.get("edges", [])
    objective = graph.get("objective", "MINIMAX_SHORTEST_PATH")
    if not nodes:
        body = {"schema": GRAPH_PROFILE, "system_version": SYSTEM_VERSION, "resolution_state": "INCOMPLETE", "reason": "NO_GRAPH_NODES"}
        return {**body, "graph_result_id": structural_hash(body)}
    if len(nodes) > MAX_GRAPH_NODES or len(edges_raw) > MAX_GRAPH_EDGES:
        body = {"schema": GRAPH_PROFILE, "system_version": SYSTEM_VERSION, "resolution_state": "UNSUPPORTED", "reason": "GRAPH_LIMIT_EXCEEDED"}
        return {**body, "graph_result_id": structural_hash(body)}
    if objective != "MINIMAX_SHORTEST_PATH":
        body = {"schema": GRAPH_PROFILE, "system_version": SYSTEM_VERSION, "resolution_state": "UNSUPPORTED", "reason": "UNSUPPORTED_GRAPH_OBJECTIVE"}
        return {**body, "graph_result_id": structural_hash(body)}
    node_set = set(nodes)
    edges = set()
    for edge in edges_raw:
        if not isinstance(edge, Sequence) or isinstance(edge, (str, bytes)) or len(edge) != 2:
            body = {"schema": GRAPH_PROFILE, "system_version": SYSTEM_VERSION, "resolution_state": "UNSUPPORTED", "reason": "MALFORMED_GRAPH_EDGE"}
            return {**body, "graph_result_id": structural_hash(body)}
        a, b = map(str, edge)
        if a not in node_set or b not in node_set or a == b:
            body = {"schema": GRAPH_PROFILE, "system_version": SYSTEM_VERSION, "resolution_state": "CONFLICT", "reason": "INVALID_GRAPH_EDGE"}
            return {**body, "graph_result_id": structural_hash(body)}
        edges.add(tuple(sorted((a, b))))
    adjacency = {n: set() for n in nodes}
    for a, b in edges:
        adjacency[a].add(b); adjacency[b].add(a)

    def distances(start: str) -> Dict[str, int]:
        d = {start: 0}; q = deque([start])
        while q:
            u = q.popleft()
            for v in sorted(adjacency[u]):
                if v not in d:
                    d[v] = d[u] + 1; q.append(v)
        return d

    all_dist = {n: distances(n) for n in nodes}
    if any(len(d) != len(nodes) for d in all_dist.values()):
        body = {"schema": GRAPH_PROFILE, "system_version": SYSTEM_VERSION, "resolution_state": "CONFLICT", "reason": "DISCONNECTED_GRAPH"}
        return {**body, "graph_result_id": structural_hash(body)}
    candidates = sorted(set(map(str, graph.get("candidates", nodes))))
    if not candidates or not set(candidates).issubset(node_set):
        body = {"schema": GRAPH_PROFILE, "system_version": SYSTEM_VERSION, "resolution_state": "CONFLICT", "reason": "INVALID_CANDIDATE_SET"}
        return {**body, "graph_result_id": structural_hash(body)}
    eccentricities = {n: max(all_dist[n].values()) for n in candidates}
    best = min(eccentricities.values())
    centres = sorted(n for n, e in eccentricities.items() if e == best)
    body = {
        "schema": GRAPH_PROFILE,
        "system_version": SYSTEM_VERSION,
        "resolution_state": "RESOLVED_POINT" if len(centres) == 1 else "MULTI_CENTRE",
        "centre_type": "GRAPH_NODE" if len(centres) == 1 else "GRAPH_NODE_SET",
        "centre_value": centres[0] if len(centres) == 1 else centres,
        "objective": objective,
        "radius": best,
        "eccentricities": [{"node": n, "eccentricity": eccentricities[n]} for n in sorted(eccentricities)],
        "graph_id": structural_hash({"nodes": nodes, "edges": [list(e) for e in sorted(edges)]}),
    }
    return {**body, "graph_result_id": structural_hash(body)}


def evaluate_vector(vector: Mapping[str, Any]) -> Dict[str, Any]:
    op = vector["operation"]; p = vector.get("input", {})
    if op == "CLAIM_RELATION": return build_claim_relation(p["left"], p["right"])
    if op == "CENTRE_SPECTRUM": return build_centre_spectrum(p.get("claims", []))
    if op == "RESOLUTION_FRONTIER": return build_resolution_frontier(p.get("current_dependencies", {}), required_dependencies=p.get("required_dependencies", []), single_value_keys=p.get("single_value_keys", []), repair_options=p.get("repair_options", []))
    if op == "GRAPH_CENTRE": return resolve_graph_centre(p)
    raise ValueError("UNKNOWN_OPERATION")


def verify_self_hash(obj: Mapping[str, Any], field: str) -> bool:
    return structural_hash({k: v for k, v in obj.items() if k != field}) == obj.get(field)


def audit_vector_corpus(corpus: Mapping[str, Any], *, verbose: bool = False) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    def add(cid: str, passed: bool, detail: Any) -> None:
        checks.append({"check_id": cid, "pass": bool(passed), "detail": detail})
        if verbose: print("PASS" if passed else "FAIL", cid, detail)
    add("CORPUS_ID", verify_self_hash(corpus, "vector_corpus_id"), corpus.get("vector_corpus_id"))
    actual_set = "secadv_" + hashlib.sha256(canonical_bytes([v["vector_hash"] for v in corpus.get("vectors", [])])).hexdigest()
    add("VECTOR_SET_ID", actual_set == corpus.get("vector_set_id"), actual_set)
    add("ADVANCED_PROFILE", corpus.get("advanced_profile") == ADVANCED_PROFILE, corpus.get("advanced_profile"))
    vm = {}
    for v in corpus.get("vectors", []):
        vm[v["vector_id"]] = v
        actual = evaluate_vector(v)
        passed = verify_self_hash(v, "vector_hash") and actual == v.get("expected")
        detail = actual.get("claim_relation", actual.get("spectrum_state", actual.get("frontier_state", actual.get("resolution_state"))))
        add(v["vector_id"], passed, detail)

    # Meta-properties.
    rel = vm["SEC-ADV-R005"]["input"]
    fwd = build_claim_relation(rel["left"], rel["right"]); rev = build_claim_relation(rel["right"], rel["left"])
    add("RELATION_CONFLICT_DIRECTION_INVARIANCE", fwd["claim_relation"] == rev["claim_relation"] == "DECLARATION_CONFLICT", fwd["claim_relation"])

    sp = vm["SEC-ADV-SP003"]["input"]["claims"]
    a = build_centre_spectrum(sp); b = build_centre_spectrum(list(reversed(sp)))
    add("SPECTRUM_PERMUTATION_INVARIANCE", a == b, a.get("spectrum_id"))
    add("SPECTRUM_NO_BLIND_AVERAGING", "centre_value" not in a and a.get("aggregation_policy") == "NO_BLIND_AVERAGING_OF_STRUCTURALLY_DISTINCT_RESULTS", a.get("aggregation_policy"))

    fr = vm["SEC-ADV-F003"]["input"]
    a = build_resolution_frontier(fr["current_dependencies"], required_dependencies=fr["required_dependencies"], single_value_keys=fr["single_value_keys"], repair_options=fr["repair_options"])
    b = build_resolution_frontier(fr["current_dependencies"], required_dependencies=fr["required_dependencies"], single_value_keys=fr["single_value_keys"], repair_options=list(reversed(fr["repair_options"])))
    add("FRONTIER_OPTION_PERMUTATION_INVARIANCE", a == b, a.get("resolution_frontier_id"))
    add("FRONTIER_MINIMALITY", a.get("minimal_repair_size") == 1 and all(len(x["operations"]) == 1 for x in a.get("minimal_repair_sets", [])), a.get("minimal_repair_size"))

    graph = vm["SEC-ADV-G002"]["input"]
    ga = resolve_graph_centre(graph)
    gb = resolve_graph_centre({**graph, "nodes": list(reversed(graph["nodes"])), "edges": list(reversed([list(reversed(e)) for e in graph["edges"]]))})
    add("GRAPH_PERMUTATION_INVARIANCE", ga == gb, ga.get("graph_result_id"))
    add("GRAPH_MULTI_CENTRE_PRESERVED", ga.get("resolution_state") == "MULTI_CENTRE" and ga.get("centre_value") == ["B", "C"], ga.get("centre_value"))

    r6 = evaluate_vector(vm["SEC-ADV-R006"])
    add("CLAIM_RESULT_SEPARATION", r6.get("claim_relation") != "CLAIM_EQUIVALENT" and r6.get("result_relation") == "RESULT_EQUIVALENT", [r6.get("claim_relation"), r6.get("result_relation")])

    passed = sum(1 for c in checks if c["pass"]); total = len(checks)
    core = {"schema": "SEC-STRUCTURAL-CENTRE-ADVANCED-AUDIT-1-D01", "system_version": SYSTEM_VERSION, "status": "PASS" if passed == total else "FAIL", "passed": passed, "total": total, "vector_set_id": corpus.get("vector_set_id"), "vector_corpus_id": corpus.get("vector_corpus_id"), "checks": checks}
    return {**core, "evidence_id": structural_hash(core)}


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(); p.add_argument("--vectors", type=Path, default=Path("profiles") / "SEC_Structural_Centre_Advanced_Vectors_v0_5_0.json"); p.add_argument("--audit", action="store_true"); p.add_argument("--out", type=Path); p.add_argument("--json", action="store_true"); p.add_argument("--verbose", action="store_true"); a = p.parse_args(argv)
    corpus = json.loads(a.vectors.read_text(encoding="utf-8")); result = audit_vector_corpus(corpus, verbose=a.verbose)
    if a.out: a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if a.json: print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print("STRUCTURAL EARTH CENTRE ADVANCED STRUCTURAL RESOLVER v0.5.0"); print("STATUS", result["status"]); print("TOTAL", f"{result['passed']}/{result['total']}", result["status"]); print("VECTOR SET", result["vector_set_id"]); print("EVIDENCE ID", result["evidence_id"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
