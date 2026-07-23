#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


SYSTEM_VERSION = "0.5.0"
PROFILE_ID = "SEC-REAL-LAND-AREA-VECTOR-CENTRE-1-D02"
PROFILE_DIFFERENTIAL_ENTRY_POINT = "verify/SEC_Real_Land_Profile_Differential_v0_5_0.py"
DEFAULT_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/refs/heads/master/geojson/ne_110m_land.geojson"
DEFAULT_IDENTITY_DECIMAL_PLACES = 9


class InputAdmissionError(ValueError):
    def __init__(self, reason_code: str, detail: str = "") -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.detail = detail


class UnsupportedInputError(ValueError):
    def __init__(self, reason_code: str, detail: str = "") -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.detail = detail


class ProfileValidationError(ValueError):
    def __init__(self, reason_code: str, detail: str = "") -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.detail = detail


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def structural_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def vec_add(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vec_sub(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vec_scale(a: Sequence[float], s: float) -> Tuple[float, float, float]:
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Sequence[float], b: Sequence[float]) -> Tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a: Sequence[float]) -> float:
    return math.sqrt(dot(a, a))


def normalize(a: Sequence[float]) -> Tuple[float, float, float]:
    n = norm(a)
    if n == 0.0:
        raise ValueError("ZERO_VECTOR")
    return (a[0] / n, a[1] / n, a[2] / n)


def lonlat_to_unit(lon_deg: float, lat_deg: float) -> Tuple[float, float, float]:
    lon = math.radians(lon_deg)
    lat = math.radians(lat_deg)
    c = math.cos(lat)
    return (c * math.cos(lon), c * math.sin(lon), math.sin(lat))


def unit_to_lonlat(v: Sequence[float]) -> Tuple[float, float]:
    u = normalize(v)
    lon = math.degrees(math.atan2(u[1], u[0]))
    lat = math.degrees(math.asin(max(-1.0, min(1.0, u[2]))))
    if lon <= -180.0:
        lon = 180.0
    return lon, lat


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_position(position: Any, path: str) -> None:
    if not isinstance(position, (list, tuple)) or len(position) < 2:
        raise InputAdmissionError("MALFORMED_POSITION", path)

    lon = position[0]
    lat = position[1]
    if not is_number(lon) or not is_number(lat):
        raise InputAdmissionError("NON_NUMERIC_COORDINATE", path)

    lon_f = float(lon)
    lat_f = float(lat)
    if not math.isfinite(lon_f) or not math.isfinite(lat_f):
        raise InputAdmissionError("NON_FINITE_COORDINATE", path)
    if lon_f < -180.0 or lon_f > 180.0:
        raise InputAdmissionError("LONGITUDE_OUT_OF_RANGE", path)
    if lat_f < -90.0 or lat_f > 90.0:
        raise InputAdmissionError("LATITUDE_OUT_OF_RANGE", path)


def positions_equal(a: Sequence[Any], b: Sequence[Any]) -> bool:
    return len(a) >= 2 and len(b) >= 2 and a[0] == b[0] and a[1] == b[1]


def validate_ring(ring: Any, path: str) -> None:
    if not isinstance(ring, list) or len(ring) < 4:
        raise InputAdmissionError("RING_TOO_SHORT", path)
    for index, position in enumerate(ring):
        validate_position(position, f"{path}[{index}]")
    if not positions_equal(ring[0], ring[-1]):
        raise InputAdmissionError("RING_NOT_CLOSED", path)


def validate_polygon(polygon: Any, path: str) -> None:
    if not isinstance(polygon, list) or not polygon:
        raise InputAdmissionError("POLYGON_HAS_NO_RINGS", path)
    for ring_index, ring in enumerate(polygon):
        validate_ring(ring, f"{path}[{ring_index}]")


def validate_geometry(geometry: Mapping[str, Any], path: str) -> None:
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if kind == "Polygon":
        validate_polygon(coordinates, path + ".coordinates")
        return

    if kind == "MultiPolygon":
        if not isinstance(coordinates, list) or not coordinates:
            raise InputAdmissionError("MULTIPOLYGON_HAS_NO_POLYGONS", path + ".coordinates")
        for polygon_index, polygon in enumerate(coordinates):
            validate_polygon(polygon, f"{path}.coordinates[{polygon_index}]")
        return

    raise UnsupportedInputError("UNSUPPORTED_GEOMETRY_TYPE", str(kind))


def validate_feature_collection(data: Any) -> None:
    if not isinstance(data, Mapping):
        raise InputAdmissionError("ROOT_IS_NOT_OBJECT", "root")
    if data.get("type") != "FeatureCollection":
        raise UnsupportedInputError("EXPECTED_FEATURE_COLLECTION", str(data.get("type")))

    features = data.get("features")
    if not isinstance(features, list):
        raise InputAdmissionError("FEATURES_IS_NOT_ARRAY", "features")

    for feature_index, feature in enumerate(features):
        if not isinstance(feature, Mapping):
            raise InputAdmissionError("FEATURE_IS_NOT_OBJECT", f"features[{feature_index}]")
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        if not isinstance(geometry, Mapping):
            raise InputAdmissionError("GEOMETRY_IS_NOT_OBJECT", f"features[{feature_index}].geometry")
        validate_geometry(geometry, f"features[{feature_index}].geometry")


def close_ring(points: Sequence[Sequence[float]]) -> List[Sequence[float]]:
    if len(points) < 4:
        raise ValueError("RING_TOO_SHORT")
    return list(points)


def signed_triangle_area(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> float:
    det = dot(a, cross(b, c))
    den = 1.0 + dot(a, b) + dot(b, c) + dot(c, a)
    return 2.0 * math.atan2(det, den)


def ring_area_and_moment(points: Sequence[Sequence[float]]) -> Tuple[float, Tuple[float, float, float], int]:
    ring = close_ring(points)
    units = [lonlat_to_unit(float(p[0]), float(p[1])) for p in ring]
    unique_units = units[:-1]
    if len(unique_units) < 3:
        raise ValueError("RING_TOO_SHORT")

    area_signed = 0.0
    anchor = unique_units[0]
    for i in range(1, len(unique_units) - 1):
        area_signed += signed_triangle_area(anchor, unique_units[i], unique_units[i + 1])

    moment = (0.0, 0.0, 0.0)
    for i in range(len(units) - 1):
        a = units[i]
        b = units[i + 1]
        c = cross(a, b)
        c_norm = norm(c)
        if c_norm <= 1e-18:
            continue
        theta = math.atan2(c_norm, max(-1.0, min(1.0, dot(a, b))))
        edge = vec_scale(c, 0.5 * theta / c_norm)
        moment = vec_add(moment, edge)

    mean = (0.0, 0.0, 0.0)
    for u in unique_units:
        mean = vec_add(mean, u)

    if norm(mean) > 1e-15 and dot(moment, mean) < 0.0:
        moment = vec_scale(moment, -1.0)

    return abs(area_signed), moment, len(unique_units)


def polygon_area_and_moment(rings: Sequence[Sequence[Sequence[float]]]) -> Tuple[float, Tuple[float, float, float], int, int]:
    if not rings:
        raise ValueError("POLYGON_HAS_NO_RINGS")

    outer_area, outer_moment, outer_vertices = ring_area_and_moment(rings[0])
    total_area = outer_area
    total_moment = outer_moment
    vertex_count = outer_vertices
    ring_count = 1

    for hole in rings[1:]:
        hole_area, hole_moment, hole_vertices = ring_area_and_moment(hole)
        total_area -= hole_area
        total_moment = vec_sub(total_moment, hole_moment)
        vertex_count += hole_vertices
        ring_count += 1

    return total_area, total_moment, ring_count, vertex_count


def iter_polygons(geometry: Mapping[str, Any]) -> Iterable[Sequence[Sequence[Sequence[float]]]]:
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if kind == "Polygon":
        yield coordinates
        return

    if kind == "MultiPolygon":
        for polygon in coordinates:
            yield polygon
        return

    raise UnsupportedInputError("UNSUPPORTED_GEOMETRY_TYPE", str(kind))


def result_material(
    profile_hash: str,
    dataset_sha256: str,
    structural_result: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "schema": "SEC-REAL-LAND-CENTRE-RESULT-MATERIAL-1-D02",
        "system_version": SYSTEM_VERSION,
        "profile_id": PROFILE_ID,
        "algorithm_profile_hash": profile_hash,
        "dataset_sha256": dataset_sha256,
        "structural_result": dict(structural_result),
    }


def evidence_material(
    result_id: str,
    profile_hash: str,
    dataset_sha256: str,
    dataset_byte_length: int,
    feature_count: int,
    polygon_count: int,
    ring_count: int,
    vertex_count: int,
    source_locator: str,
    acquisition_mode: str,
    identity_quantization_decimal_places: int,
) -> Dict[str, Any]:
    return {
        "schema": "SEC-REAL-LAND-CENTRE-EVIDENCE-1-D02",
        "system_version": SYSTEM_VERSION,
        "result_id": result_id,
        "dataset_sha256": dataset_sha256,
        "dataset_byte_length": dataset_byte_length,
        "feature_count": feature_count,
        "polygon_count": polygon_count,
        "ring_count": ring_count,
        "vertex_count": vertex_count,
        "source_locator": source_locator,
        "acquisition_mode": acquisition_mode,
        "algorithm_profile_hash": profile_hash,
        "identity_quantization_decimal_places": identity_quantization_decimal_places,
    }


def refusal_material(
    input_sha256: str,
    input_byte_length: int,
    source_locator: str,
    acquisition_mode: str,
    reason_code: str,
    detail: str,
) -> Dict[str, Any]:
    material = {
        "schema": "SEC-REAL-LAND-INPUT-REFUSAL-1-D01",
        "system_version": SYSTEM_VERSION,
        "resolution_state": "INPUT_REJECTED",
        "reason_code": reason_code,
        "input_sha256": input_sha256,
        "input_byte_length": input_byte_length,
        "source_locator": source_locator,
        "acquisition_mode": acquisition_mode,
    }
    if detail:
        material["detail"] = detail
    return material


def make_input_refusal(
    input_sha256: str,
    input_byte_length: int,
    source_locator: str,
    acquisition_mode: str,
    reason_code: str,
    detail: str = "",
) -> Dict[str, Any]:
    material = refusal_material(
        input_sha256,
        input_byte_length,
        source_locator,
        acquisition_mode,
        reason_code,
        detail,
    )
    return {**material, "refusal_id": structural_hash(material)}


def finalize_result(
    structural_result: Mapping[str, Any],
    profile_hash: str,
    dataset_sha256: str,
    dataset_byte_length: int,
    feature_count: int,
    polygon_count: int,
    ring_count: int,
    vertex_count: int,
    source_locator: str,
    acquisition_mode: str,
    identity_quantization_decimal_places: int,
) -> Dict[str, Any]:
    result_id = structural_hash(result_material(profile_hash, dataset_sha256, structural_result))
    evidence = evidence_material(
        result_id=result_id,
        profile_hash=profile_hash,
        dataset_sha256=dataset_sha256,
        dataset_byte_length=dataset_byte_length,
        feature_count=feature_count,
        polygon_count=polygon_count,
        ring_count=ring_count,
        vertex_count=vertex_count,
        source_locator=source_locator,
        acquisition_mode=acquisition_mode,
        identity_quantization_decimal_places=identity_quantization_decimal_places,
    )
    evidence_id = structural_hash(evidence)
    return {
        **dict(structural_result),
        "result_id": result_id,
        "evidence": evidence,
        "evidence_id": evidence_id,
    }


def resolve_geojson(
    data: Mapping[str, Any],
    dataset_sha256: str,
    dataset_byte_length: int,
    source_locator: str,
    acquisition_mode: str,
    profile_hash: str,
    identity_quantization_decimal_places: int = DEFAULT_IDENTITY_DECIMAL_PLACES,
) -> Dict[str, Any]:
    try:
        validate_feature_collection(data)
    except InputAdmissionError as exc:
        return make_input_refusal(
            dataset_sha256,
            dataset_byte_length,
            source_locator,
            acquisition_mode,
            exc.reason_code,
            exc.detail,
        )
    except UnsupportedInputError as exc:
        structural_result = {
            "resolution_state": "UNSUPPORTED",
            "reason": exc.reason_code,
        }
        if exc.detail:
            structural_result["detail"] = exc.detail
        return finalize_result(
            structural_result,
            profile_hash,
            dataset_sha256,
            dataset_byte_length,
            0,
            0,
            0,
            0,
            source_locator,
            acquisition_mode,
            identity_quantization_decimal_places,
        )

    total_area = 0.0
    total_moment = (0.0, 0.0, 0.0)
    feature_count = 0
    polygon_count = 0
    ring_count = 0
    vertex_count = 0

    for feature in data.get("features", []):
        geometry = feature.get("geometry")
        if geometry is None:
            continue
        feature_count += 1
        for polygon in iter_polygons(geometry):
            area, moment, rings, vertices = polygon_area_and_moment(polygon)
            total_area += area
            total_moment = vec_add(total_moment, moment)
            polygon_count += 1
            ring_count += rings
            vertex_count += vertices

    moment_norm = norm(total_moment)

    if feature_count == 0 or polygon_count == 0:
        structural_result = {
            "resolution_state": "INCOMPLETE",
            "reason": "NO_SUPPORTED_POLYGON_GEOMETRY",
        }
        return finalize_result(
            structural_result,
            profile_hash,
            dataset_sha256,
            dataset_byte_length,
            feature_count,
            polygon_count,
            ring_count,
            vertex_count,
            source_locator,
            acquisition_mode,
            identity_quantization_decimal_places,
        )

    if total_area <= 0.0:
        structural_result = {
            "resolution_state": "CONFLICT",
            "reason": "NON_POSITIVE_NET_SPHERICAL_AREA",
        }
        return finalize_result(
            structural_result,
            profile_hash,
            dataset_sha256,
            dataset_byte_length,
            feature_count,
            polygon_count,
            ring_count,
            vertex_count,
            source_locator,
            acquisition_mode,
            identity_quantization_decimal_places,
        )

    if moment_norm <= 1e-15:
        structural_result = {
            "resolution_state": "AMBIGUOUS",
            "reason": "AREA_VECTOR_MOMENT_CANCELS_TO_ZERO",
            "identity_quantization_decimal_places": identity_quantization_decimal_places,
            "spherical_area_steradians": round(total_area, identity_quantization_decimal_places),
            "surface_fraction": round(total_area / (4.0 * math.pi), identity_quantization_decimal_places),
        }
        return finalize_result(
            structural_result,
            profile_hash,
            dataset_sha256,
            dataset_byte_length,
            feature_count,
            polygon_count,
            ring_count,
            vertex_count,
            source_locator,
            acquisition_mode,
            identity_quantization_decimal_places,
        )

    unit = normalize(total_moment)
    lon, lat = unit_to_lonlat(unit)

    structural_result = {
        "resolution_state": "RESOLVED_POINT",
        "centre_type": "SPHERICAL_SURFACE_AREA_VECTOR_CENTRE_DIRECTION",
        "identity_quantization_decimal_places": identity_quantization_decimal_places,
        "latitude_deg": round(lat, identity_quantization_decimal_places),
        "longitude_deg": round(lon, identity_quantization_decimal_places),
        "unit_vector_xyz": [
            round(unit[0], identity_quantization_decimal_places),
            round(unit[1], identity_quantization_decimal_places),
            round(unit[2], identity_quantization_decimal_places),
        ],
        "spherical_area_steradians": round(total_area, identity_quantization_decimal_places),
        "surface_fraction": round(total_area / (4.0 * math.pi), identity_quantization_decimal_places),
    }
    return finalize_result(
        structural_result,
        profile_hash,
        dataset_sha256,
        dataset_byte_length,
        feature_count,
        polygon_count,
        ring_count,
        vertex_count,
        source_locator,
        acquisition_mode,
        identity_quantization_decimal_places,
    )


def reject_json_constant(value: str) -> Any:
    raise ValueError("NON_STANDARD_JSON_CONSTANT:" + value)


def resolve_bytes(
    raw: bytes,
    source_locator: str,
    acquisition_mode: str,
    profile: Mapping[str, Any],
) -> Dict[str, Any]:
    dataset_sha256 = "sha256:" + hashlib.sha256(raw).hexdigest()
    byte_length = len(raw)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return make_input_refusal(
            dataset_sha256,
            byte_length,
            source_locator,
            acquisition_mode,
            "INVALID_UTF8",
            f"byte_offset={exc.start}",
        )

    try:
        data = json.loads(text, parse_constant=reject_json_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        return make_input_refusal(
            dataset_sha256,
            byte_length,
            source_locator,
            acquisition_mode,
            "INVALID_JSON",
            type(exc).__name__,
        )

    quantization = int(
        profile.get("numerical_contract", {}).get(
            "identity_quantization_decimal_places",
            DEFAULT_IDENTITY_DECIMAL_PLACES,
        )
    )
    return resolve_geojson(
        data=data,
        dataset_sha256=dataset_sha256,
        dataset_byte_length=byte_length,
        source_locator=source_locator,
        acquisition_mode=acquisition_mode,
        profile_hash=profile["profile_hash"],
        identity_quantization_decimal_places=quantization,
    )


def validate_profile(profile: Mapping[str, Any]) -> None:
    body = {k: v for k, v in profile.items() if k != "profile_hash"}
    actual = structural_hash(body)
    if actual != profile.get("profile_hash"):
        raise ProfileValidationError("PROFILE_HASH_MISMATCH")

    declared_profile_id = profile.get("profile_id")
    if declared_profile_id != PROFILE_ID:
        raise ProfileValidationError(
            "PROFILE_ID_MISMATCH",
            f"supplied_profile={declared_profile_id}; supported_profile={PROFILE_ID}",
        )

    declared_version = profile.get("system_version")
    if declared_version != SYSTEM_VERSION:
        raise ProfileValidationError(
            "PROFILE_VERSION_MISMATCH",
            f"supplied_version={declared_version}; supported_version={SYSTEM_VERSION}",
        )

    quantization = profile.get("numerical_contract", {}).get(
        "identity_quantization_decimal_places"
    )
    if quantization != DEFAULT_IDENTITY_DECIMAL_PLACES:
        raise ProfileValidationError(
            "IDENTITY_QUANTIZATION_POLICY_MISMATCH",
            (
                f"supplied_quantization={quantization}; "
                f"required_quantization={DEFAULT_IDENTITY_DECIMAL_PLACES}"
            ),
        )


def read_profile(path: Path) -> Dict[str, Any]:
    profile = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_json_constant)
    validate_profile(profile)
    return profile


def profile_refusal_payload(error: ProfileValidationError, profile_path: Path) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "schema": "SEC-REAL-LAND-PROFILE-REFUSAL-1-D01",
        "system_version": SYSTEM_VERSION,
        "status": "PROFILE_REJECTED",
        "reason_code": error.reason_code,
        "profile_path": str(profile_path).replace("\\", "/"),
    }
    if error.detail:
        payload["detail"] = error.detail
    if error.reason_code == "PROFILE_ID_MISMATCH":
        payload["supported_profile_id"] = PROFILE_ID
        payload["comparison_entry_point"] = PROFILE_DIFFERENTIAL_ENTRY_POINT
    return payload


def fetch(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "Structural-Earth-Centre/0.5.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = response.read()
    destination.write_bytes(payload)


def resolve_file(
    path: Path,
    source_locator: str,
    acquisition_mode: str,
    profile: Mapping[str, Any],
) -> Dict[str, Any]:
    return resolve_bytes(path.read_bytes(), source_locator, acquisition_mode, profile)


def fixture_feature_collection(polygons: Sequence[Any]) -> Dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {}, "geometry": geometry}
            for geometry in polygons
        ],
    }


def run_self_test(profile: Mapping[str, Any]) -> Dict[str, Any]:
    profile_hash = profile["profile_hash"]
    quantization = profile["numerical_contract"]["identity_quantization_decimal_places"]
    checks = []

    def add(name: str, passed: bool, detail: Any) -> None:
        checks.append({"check_id": name, "pass": bool(passed), "detail": detail})

    def resolve_fixture(data: Mapping[str, Any], dataset_hash: str, locator: str, mode: str) -> Dict[str, Any]:
        return resolve_geojson(data, dataset_hash, 100, locator, mode, profile_hash, quantization)

    north_square = fixture_feature_collection([
        {
            "type": "Polygon",
            "coordinates": [[[-10, 60], [10, 60], [10, 80], [-10, 80], [-10, 60]]],
        }
    ])
    a = resolve_fixture(north_square, "sha256:test-a", "SELF_TEST_A", "SELF_TEST")
    add("NORTH_POLYGON_RESOLVES", a["resolution_state"] == "RESOLVED_POINT" and a["latitude_deg"] > 60, a["resolution_state"])

    reversed_square = fixture_feature_collection([
        {
            "type": "Polygon",
            "coordinates": [[[-10, 60], [-10, 80], [10, 80], [10, 60], [-10, 60]]],
        }
    ])
    b = resolve_fixture(reversed_square, "sha256:test-b", "SELF_TEST_B", "SELF_TEST")
    add(
        "RING_REVERSAL_INVARIANCE",
        a["latitude_deg"] == b["latitude_deg"] and a["longitude_deg"] == b["longitude_deg"],
        [a["latitude_deg"], a["longitude_deg"]],
    )

    dateline = fixture_feature_collection([
        {
            "type": "Polygon",
            "coordinates": [[[170, 10], [-170, 10], [-170, 30], [170, 30], [170, 10]]],
        }
    ])
    c = resolve_fixture(dateline, "sha256:test-c", "SELF_TEST_C", "SELF_TEST")
    add("DATELINE_POLYGON_RESOLVES", c["resolution_state"] == "RESOLVED_POINT" and abs(abs(c["longitude_deg"]) - 180) < 1e-6, c["resolution_state"])

    with_hole = fixture_feature_collection([
        {
            "type": "Polygon",
            "coordinates": [
                [[-20, 20], [20, 20], [20, 60], [-20, 60], [-20, 20]],
                [[-5, 35], [5, 35], [5, 45], [-5, 45], [-5, 35]],
            ],
        }
    ])
    d = resolve_fixture(with_hole, "sha256:test-d", "SELF_TEST_D", "SELF_TEST")
    add("HOLE_SUBTRACTION_RESOLVES", d["resolution_state"] == "RESOLVED_POINT" and d["surface_fraction"] > 0, d["resolution_state"])

    polygon = {
        "type": "Polygon",
        "coordinates": [[[-10, 40], [0, 50], [10, 40], [0, 30], [-10, 40]]],
    }
    multipolygon = {
        "type": "MultiPolygon",
        "coordinates": [
            [[[-10, 40], [0, 50], [10, 40], [0, 30], [-10, 40]]]
        ],
    }
    e1 = resolve_fixture(fixture_feature_collection([polygon]), "sha256:test-e", "SELF_TEST_E1", "SELF_TEST")
    e2 = resolve_fixture(fixture_feature_collection([multipolygon]), "sha256:test-e", "SELF_TEST_E2", "SELF_TEST")
    add(
        "POLYGON_MULTIPOLYGON_EQUIVALENCE",
        e1["latitude_deg"] == e2["latitude_deg"] and e1["longitude_deg"] == e2["longitude_deg"],
        e1["result_id"] == e2["result_id"],
    )

    f = resolve_fixture(fixture_feature_collection([polygon, polygon]), "sha256:test-f", "SELF_TEST_F", "SELF_TEST")
    add(
        "DUPLICATE_AREA_DIRECTION_STABLE",
        f["latitude_deg"] == e1["latitude_deg"] and f["longitude_deg"] == e1["longitude_deg"],
        f["resolution_state"],
    )

    empty = {"type": "FeatureCollection", "features": []}
    g = resolve_fixture(empty, "sha256:test-g", "SELF_TEST_G", "SELF_TEST")
    add("EMPTY_INPUT_INCOMPLETE", g["resolution_state"] == "INCOMPLETE", g["resolution_state"])

    unsupported = resolve_fixture(
        fixture_feature_collection([{"type": "LineString", "coordinates": [[0, 0], [1, 1]]}]),
        "sha256:test-h",
        "SELF_TEST_H",
        "SELF_TEST",
    )
    add("UNSUPPORTED_GEOMETRY_REFUSED", unsupported["resolution_state"] == "UNSUPPORTED", unsupported["resolution_state"])

    north_a = fixture_feature_collection([
        {"type": "Polygon", "coordinates": [[[-20, 50], [0, 70], [20, 50], [0, 40], [-20, 50]]]}
    ])
    north_b = fixture_feature_collection([
        {"type": "Polygon", "coordinates": [[[20, 50], [0, 40], [-20, 50], [0, 70], [20, 50]]]}
    ])
    h1 = resolve_fixture(north_a, "sha256:test-i", "SELF_TEST_I1", "SELF_TEST")
    h2 = resolve_fixture(north_b, "sha256:test-i", "SELF_TEST_I2", "SELF_TEST")
    add(
        "CYCLIC_RING_START_INVARIANCE",
        h1["latitude_deg"] == h2["latitude_deg"] and h1["longitude_deg"] == h2["longitude_deg"],
        h1["result_id"] == h2["result_id"],
    )

    source_binding_a = resolve_fixture(north_square, "sha256:data-a", "SOURCE_A", "FETCH_URL")
    source_binding_b = resolve_fixture(north_square, "sha256:data-b", "SOURCE_A", "FETCH_URL")
    add(
        "DATASET_IDENTITY_BINDS_RESULT",
        source_binding_a["result_id"] != source_binding_b["result_id"],
        [source_binding_a["result_id"], source_binding_b["result_id"]],
    )

    locator_a = resolve_fixture(north_square, "sha256:same-data", "https://example.test/data.geojson", "FETCH_URL")
    locator_b = resolve_fixture(north_square, "sha256:same-data", "data/local.geojson", "LOCAL_FILE")
    add(
        "SOURCE_LOCATOR_RESULT_ID_INVARIANCE",
        locator_a["result_id"] == locator_b["result_id"],
        [locator_a["result_id"], locator_b["result_id"]],
    )
    add(
        "SOURCE_LOCATOR_EVIDENCE_ID_DIVERGENCE",
        locator_a["evidence_id"] != locator_b["evidence_id"],
        [locator_a["evidence_id"], locator_b["evidence_id"]],
    )

    def invalid_position_fixture(position: Any) -> Dict[str, Any]:
        return fixture_feature_collection([
            {
                "type": "Polygon",
                "coordinates": [[[0, 0], [10, 0], position, [0, 10], [0, 0]]],
            }
        ])

    invalid_cases = [
        ("LATITUDE_ABOVE_RANGE_REJECTED", [5, 91], "LATITUDE_OUT_OF_RANGE"),
        ("LATITUDE_BELOW_RANGE_REJECTED", [5, -91], "LATITUDE_OUT_OF_RANGE"),
        ("LONGITUDE_ABOVE_RANGE_REJECTED", [181, 5], "LONGITUDE_OUT_OF_RANGE"),
        ("LONGITUDE_BELOW_RANGE_REJECTED", [-181, 5], "LONGITUDE_OUT_OF_RANGE"),
        ("BOOLEAN_COORDINATE_REJECTED", [True, 5], "NON_NUMERIC_COORDINATE"),
        ("NON_FINITE_COORDINATE_REJECTED", [5, float("nan")], "NON_FINITE_COORDINATE"),
    ]
    invalid_results = []
    for check_id, position, reason in invalid_cases:
        result = resolve_fixture(invalid_position_fixture(position), "sha256:invalid", check_id, "SELF_TEST")
        invalid_results.append(result)
        add(check_id, result.get("resolution_state") == "INPUT_REJECTED" and result.get("reason_code") == reason, result.get("reason_code"))

    malformed_position = resolve_fixture(
        invalid_position_fixture([5]),
        "sha256:malformed-position",
        "SELF_TEST_MALFORMED_POSITION",
        "SELF_TEST",
    )
    invalid_results.append(malformed_position)
    add(
        "MALFORMED_POSITION_REJECTED",
        malformed_position.get("resolution_state") == "INPUT_REJECTED"
        and malformed_position.get("reason_code") == "MALFORMED_POSITION",
        malformed_position.get("reason_code"),
    )

    short_ring = fixture_feature_collection([
        {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [0, 0]]],
        }
    ])
    short_ring_result = resolve_fixture(
        short_ring,
        "sha256:short-ring",
        "SELF_TEST_SHORT_RING",
        "SELF_TEST",
    )
    invalid_results.append(short_ring_result)
    add(
        "RING_TOO_SHORT_REJECTED",
        short_ring_result.get("resolution_state") == "INPUT_REJECTED"
        and short_ring_result.get("reason_code") == "RING_TOO_SHORT",
        short_ring_result.get("reason_code"),
    )

    open_ring = fixture_feature_collection([
        {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10]]],
        }
    ])
    open_ring_result = resolve_fixture(
        open_ring,
        "sha256:open-ring",
        "SELF_TEST_OPEN_RING",
        "SELF_TEST",
    )
    invalid_results.append(open_ring_result)
    add(
        "RING_NOT_CLOSED_REJECTED",
        open_ring_result.get("resolution_state") == "INPUT_REJECTED"
        and open_ring_result.get("reason_code") == "RING_NOT_CLOSED",
        open_ring_result.get("reason_code"),
    )

    malformed_json = resolve_bytes(b'{"type":"FeatureCollection","features":[', "SELF_TEST_JSON", "SELF_TEST", profile)
    add(
        "MALFORMED_JSON_REJECTED",
        malformed_json.get("resolution_state") == "INPUT_REJECTED" and malformed_json.get("reason_code") == "INVALID_JSON",
        malformed_json.get("reason_code"),
    )

    invalid_utf8 = resolve_bytes(b"\xff\xfe\xfd", "SELF_TEST_UTF8", "SELF_TEST", profile)
    add(
        "INVALID_UTF8_REJECTED",
        invalid_utf8.get("resolution_state") == "INPUT_REJECTED" and invalid_utf8.get("reason_code") == "INVALID_UTF8",
        invalid_utf8.get("reason_code"),
    )

    add(
        "INPUT_REFUSAL_HAS_NO_RESULT_ID",
        all("result_id" not in item and "refusal_id" in item for item in invalid_results + [malformed_json, invalid_utf8]),
        "refusal identity is separate from result identity",
    )

    add(
        "IDENTITY_QUANTIZATION_DECLARED",
        a.get("identity_quantization_decimal_places") == DEFAULT_IDENTITY_DECIMAL_PLACES
        and a.get("evidence", {}).get("identity_quantization_decimal_places") == DEFAULT_IDENTITY_DECIMAL_PLACES,
        DEFAULT_IDENTITY_DECIMAL_PLACES,
    )

    mismatched_profile = dict(profile)
    mismatched_profile["profile_id"] = "SEC-REAL-LAND-BOUNDARY-VECTOR-CENTRE-1-D01"
    mismatched_profile_body = {
        k: v for k, v in mismatched_profile.items() if k != "profile_hash"
    }
    mismatched_profile["profile_hash"] = structural_hash(mismatched_profile_body)
    try:
        validate_profile(mismatched_profile)
        mismatch_regression_passed = False
        mismatch_regression_detail = "NO_REFUSAL"
    except ProfileValidationError as exc:
        refusal = profile_refusal_payload(exc, Path("profiles/test-boundary-profile.json"))
        mismatch_regression_passed = (
            exc.reason_code == "PROFILE_ID_MISMATCH"
            and refusal.get("status") == "PROFILE_REJECTED"
            and refusal.get("supported_profile_id") == PROFILE_ID
            and refusal.get("comparison_entry_point") == PROFILE_DIFFERENTIAL_ENTRY_POINT
        )
        mismatch_regression_detail = exc.reason_code

    add(
        "PROFILE_ID_MISMATCH_HAS_BOUNDED_GUIDANCE",
        mismatch_regression_passed,
        mismatch_regression_detail,
    )

    passed = sum(1 for check in checks if check["pass"])
    total = len(checks)
    core = {
        "schema": "SEC-REAL-LAND-CENTRE-SELF-TEST-1-D05",
        "system_version": SYSTEM_VERSION,
        "status": "PASS" if passed == total else "FAIL",
        "passed": passed,
        "total": total,
        "profile_id": PROFILE_ID,
        "profile_hash": profile_hash,
        "checks": checks,
    }
    return {**core, "evidence_id": structural_hash(core)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        type=Path,
        default=Path("profiles") / "SEC_Real_Land_Area_Vector_Centre_Profile_v0_5_0.json",
    )
    parser.add_argument("--geojson", type=Path)
    parser.add_argument("--fetch-natural-earth", action="store_true")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--data-out", type=Path, default=Path("data") / "ne_110m_land.geojson")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profile = read_profile(args.profile)
    except ProfileValidationError as exc:
        refusal = profile_refusal_payload(exc, args.profile)
        if args.json:
            print(json.dumps(refusal, ensure_ascii=False, sort_keys=True))
        else:
            print("STRUCTURAL EARTH CENTRE REAL LAND RESOLVER v0.5.0")
            print("STATUS", refusal["status"])
            print("REASON", refusal["reason_code"])
            if refusal.get("detail"):
                print("DETAIL", refusal["detail"])
            if refusal.get("supported_profile_id"):
                print("SUPPORTED PROFILE", refusal["supported_profile_id"])
            if refusal.get("comparison_entry_point"):
                print("COMPARISON ENTRY POINT", refusal["comparison_entry_point"])
        return 2

    if args.self_test:
        result = run_self_test(profile)
    elif args.fetch_natural_earth:
        fetch(args.url, args.data_out)
        result = resolve_file(args.data_out, args.url, "FETCH_URL", profile)
    elif args.geojson is not None:
        result = resolve_file(args.geojson, str(args.geojson).replace("\\", "/"), "LOCAL_FILE", profile)
    else:
        raise SystemExit("Use --self-test, --fetch-natural-earth, or --geojson PATH.")

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif args.self_test:
        print("STRUCTURAL EARTH CENTRE REAL LAND RESOLVER v0.5.0")
        print("SELF TEST", result["status"])
        print("TOTAL", f"{result['passed']}/{result['total']}", result["status"])
        print("PROFILE", result["profile_hash"])
        print("EVIDENCE ID", result["evidence_id"])
    elif result.get("resolution_state") == "INPUT_REJECTED":
        print("STRUCTURAL EARTH CENTRE REAL LAND RESOLVER v0.5.0")
        print("STATUS INPUT_REJECTED")
        print("REASON", result["reason_code"])
        print("INPUT", result["input_sha256"])
        print("REFUSAL ID", result["refusal_id"])
    else:
        print("STRUCTURAL EARTH CENTRE REAL LAND RESOLVER v0.5.0")
        print("STATUS", result["resolution_state"])
        if result["resolution_state"] == "RESOLVED_POINT":
            print("LATITUDE_DEG", result["latitude_deg"])
            print("LONGITUDE_DEG", result["longitude_deg"])
            print("SURFACE_FRACTION", result["surface_fraction"])
            print("IDENTITY_QUANTIZATION_DECIMAL_PLACES", result["identity_quantization_decimal_places"])
        print("DATASET", result["evidence"]["dataset_sha256"])
        print("RESULT ID", result["result_id"])
        print("EVIDENCE ID", result["evidence_id"])

    if args.self_test:
        return 0 if result["status"] == "PASS" else 1
    if result.get("resolution_state") == "INPUT_REJECTED":
        return 2
    return 0 if result["resolution_state"] in {"RESOLVED_POINT", "AMBIGUOUS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
