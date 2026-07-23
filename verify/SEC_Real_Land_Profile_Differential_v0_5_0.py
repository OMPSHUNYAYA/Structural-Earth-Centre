#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

SYSTEM_VERSION="0.5.0"
FAMILY_PROFILE="SEC-REAL-LAND-VECTOR-CENTRE-FAMILY-1-D01"
FROZEN_DATASET_SHA256="sha256:9e0729ee253ca7d7a5c4ae9395fb1902264c5377c52e224d13dd85010e2835d9"


def load_module(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(f"Cannot load {path}")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def canonical_bytes(value:Any)->bytes:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")


def structural_hash(value:Any)->str:
    return "sha256:"+hashlib.sha256(canonical_bytes(value)).hexdigest()


def read_profile(path:Path)->Dict[str,Any]:
    profile=json.loads(path.read_text(encoding="utf-8"))
    expected=profile["profile_hash"]
    actual=structural_hash({k:v for k,v in profile.items() if k!="profile_hash"})
    if expected!=actual: raise ValueError(f"PROFILE_HASH_MISMATCH:{path.name}")
    if profile.get("system_version")!=SYSTEM_VERSION: raise ValueError(f"PROFILE_VERSION_MISMATCH:{path.name}")
    return profile


def vec_add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def vec_scale(a,s): return (a[0]*s,a[1]*s,a[2]*s)
def dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a): return math.sqrt(dot(a,a))
def normalize(a):
    n=norm(a)
    if n<=1e-18: raise ValueError("ZERO_VECTOR")
    return (a[0]/n,a[1]/n,a[2]/n)

def lonlat_to_unit(lon_deg:float,lat_deg:float):
    lon=math.radians(lon_deg); lat=math.radians(lat_deg); c=math.cos(lat)
    return (c*math.cos(lon),c*math.sin(lon),math.sin(lat))

def unit_to_lonlat(v):
    u=normalize(v); lon=math.degrees(math.atan2(u[1],u[0])); lat=math.degrees(math.asin(max(-1.0,min(1.0,u[2]))))
    if lon<=-180.0: lon=180.0
    return lon,lat


def boundary_ring_measure(points)->Tuple[float,Tuple[float,float,float],int]:
    units=[lonlat_to_unit(float(p[0]),float(p[1])) for p in points]
    total=0.0; moment=(0.0,0.0,0.0)
    for a,b in zip(units[:-1],units[1:]):
        c=cross(a,b); c_norm=norm(c); d=max(-1.0,min(1.0,dot(a,b)))
        theta=math.atan2(c_norm,d)
        if theta<=1e-18: continue
        midpoint_raw=vec_add(a,b)
        if norm(midpoint_raw)<=1e-15:
            raise ValueError("ANTIPODAL_BOUNDARY_EDGE_UNSUPPORTED")
        midpoint=normalize(midpoint_raw)
        moment=vec_add(moment,vec_scale(midpoint,theta)); total+=theta
    return total,moment,len(units)-1


def compute_boundary_result(data:Mapping[str,Any],raw:bytes,profile:Mapping[str,Any],area_module,source_locator:str)->Dict[str,Any]:
    dataset_sha256="sha256:"+hashlib.sha256(raw).hexdigest(); byte_length=len(raw)
    try:
        area_module.validate_feature_collection(data)
    except area_module.InputAdmissionError as exc:
        return area_module.make_input_refusal(dataset_sha256,byte_length,source_locator,"LOCAL_FILE",exc.reason_code,exc.detail)
    except area_module.UnsupportedInputError as exc:
        return {"resolution_state":"UNSUPPORTED","reason":exc.reason_code,"detail":exc.detail}

    total_length=0.0; total_moment=(0.0,0.0,0.0); features=polygons=rings=vertices=0
    try:
        for feature in data.get("features",[]):
            geometry=feature.get("geometry")
            if geometry is None: continue
            features+=1
            for polygon in area_module.iter_polygons(geometry):
                polygons+=1
                for ring in polygon:
                    length,moment,vertex_count=boundary_ring_measure(ring)
                    total_length+=length; total_moment=vec_add(total_moment,moment); rings+=1; vertices+=vertex_count
    except ValueError as exc:
        structural_result={"resolution_state":"UNSUPPORTED","reason":str(exc)}
        return finalize_boundary(structural_result,profile,dataset_sha256,byte_length,features,polygons,rings,vertices,source_locator)

    if features==0 or polygons==0:
        return finalize_boundary({"resolution_state":"INCOMPLETE","reason":"NO_SUPPORTED_POLYGON_GEOMETRY"},profile,dataset_sha256,byte_length,features,polygons,rings,vertices,source_locator)
    if total_length<=0.0:
        return finalize_boundary({"resolution_state":"INCOMPLETE","reason":"NO_POSITIVE_BOUNDARY_LENGTH"},profile,dataset_sha256,byte_length,features,polygons,rings,vertices,source_locator)
    if norm(total_moment)<=1e-15:
        return finalize_boundary({"resolution_state":"AMBIGUOUS","reason":"BOUNDARY_VECTOR_MOMENT_CANCELS_TO_ZERO"},profile,dataset_sha256,byte_length,features,polygons,rings,vertices,source_locator)

    q=int(profile["numerical_contract"]["identity_quantization_decimal_places"])
    unit=normalize(total_moment); lon,lat=unit_to_lonlat(unit)
    structural_result={
        "resolution_state":"RESOLVED_POINT",
        "centre_type":"SPHERICAL_BOUNDARY_LENGTH_VECTOR_CENTRE_DIRECTION",
        "identity_quantization_decimal_places":q,
        "latitude_deg":round(lat,q),
        "longitude_deg":round(lon,q),
        "unit_vector_xyz":[round(x,q) for x in unit],
        "boundary_length_radians":round(total_length,q),
    }
    return finalize_boundary(structural_result,profile,dataset_sha256,byte_length,features,polygons,rings,vertices,source_locator)


def finalize_boundary(structural_result,profile,dataset_sha256,byte_length,features,polygons,rings,vertices,source_locator):
    result_material={
        "schema":"SEC-REAL-LAND-CENTRE-RESULT-MATERIAL-1-D03",
        "system_version":SYSTEM_VERSION,
        "profile_id":profile["profile_id"],
        "algorithm_profile_hash":profile["profile_hash"],
        "dataset_sha256":dataset_sha256,
        "structural_result":dict(structural_result),
    }
    result_id=structural_hash(result_material)
    evidence={
        "schema":"SEC-REAL-LAND-CENTRE-EVIDENCE-1-D03",
        "system_version":SYSTEM_VERSION,
        "result_id":result_id,
        "dataset_sha256":dataset_sha256,
        "dataset_byte_length":byte_length,
        "feature_count":features,
        "polygon_count":polygons,
        "ring_count":rings,
        "vertex_count":vertices,
        "source_locator":source_locator,
        "acquisition_mode":"LOCAL_FILE",
        "algorithm_profile_hash":profile["profile_hash"],
        "identity_quantization_decimal_places":profile["numerical_contract"]["identity_quantization_decimal_places"],
    }
    return {**dict(structural_result),"result_id":result_id,"evidence":evidence,"evidence_id":structural_hash(evidence)}


def structural_part(result:Mapping[str,Any])->Dict[str,Any]:
    return {k:v for k,v in result.items() if k not in {"result_id","evidence","evidence_id"}}


def angular_separation_deg(a:Mapping[str,Any],b:Mapping[str,Any])->float:
    ua=a["unit_vector_xyz"]; ub=b["unit_vector_xyz"]
    d=max(-1.0,min(1.0,sum(float(x)*float(y) for x,y in zip(ua,ub))))
    return math.degrees(math.acos(d))


def main(argv:Optional[Sequence[str]]=None)->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--out",type=Path)
    parser.add_argument("--verbose",action="store_true")
    args=parser.parse_args(argv); root=args.root.resolve()
    area_module=load_module("sec_area",root/"verify"/"SEC_Real_Land_Centre_Resolver_v0_5_0.py")
    innovation=load_module("sec_innovation",root/"verify"/"SEC_Structural_Centre_Resolver_v0_5_0.py")
    area_profile=read_profile(root/"profiles"/"SEC_Real_Land_Area_Vector_Centre_Profile_v0_5_0.json")
    boundary_profile=read_profile(root/"profiles"/"SEC_Real_Land_Boundary_Vector_Centre_Profile_v0_5_0.json")
    data_path=root/"data"/"ne_110m_land.geojson"; raw=data_path.read_bytes(); data=json.loads(raw.decode("utf-8"))
    dataset_sha256="sha256:"+hashlib.sha256(raw).hexdigest()
    area_result=area_module.resolve_bytes(raw,"data/ne_110m_land.geojson","LOCAL_FILE",area_profile)
    boundary_result=compute_boundary_result(data,raw,boundary_profile,area_module,"data/ne_110m_land.geojson")

    left={"carrier_id":dataset_sha256,"centre_profile_id":FAMILY_PROFILE,"dependencies":{"measure":"SPHERICAL_SURFACE_AREA","objective_family":"NORMALIZED_VECTOR_MOMENT_DIRECTION","surface_model":"UNIT_SPHERE"},"authority_scope":"EXACT_DATASET_BOUNDED_CLAIM","result":structural_part(area_result)}
    right={"carrier_id":dataset_sha256,"centre_profile_id":FAMILY_PROFILE,"dependencies":{"measure":"SPHERICAL_BOUNDARY_ARC_LENGTH","objective_family":"NORMALIZED_VECTOR_MOMENT_DIRECTION","surface_model":"UNIT_SPHERE"},"authority_scope":"EXACT_DATASET_BOUNDED_CLAIM","result":structural_part(boundary_result)}
    differential=innovation.build_structural_differential(left,right)

    area_claim={"carrier_id":dataset_sha256,"centre_profile_id":area_profile["profile_id"],"dependency_fingerprint_id":structural_hash(left["dependencies"]),"authority_scope":"EXACT_DATASET_BOUNDED_CLAIM"}
    boundary_claim={"carrier_id":dataset_sha256,"centre_profile_id":boundary_profile["profile_id"],"dependency_fingerprint_id":structural_hash(right["dependencies"]),"authority_scope":"EXACT_DATASET_BOUNDED_CLAIM"}
    area_certificate=innovation.build_resolution_certificate(
        area_claim,
        structural_part(area_result),
        resolution_witness={"dataset_identity_checked":True,"profile_hash_checked":True},
        evidence_id=area_result.get("evidence_id"),
        declared_result_id=area_result.get("result_id"),
    )
    boundary_certificate=innovation.build_resolution_certificate(
        boundary_claim,
        structural_part(boundary_result),
        resolution_witness={"dataset_identity_checked":True,"profile_hash_checked":True},
        evidence_id=boundary_result.get("evidence_id"),
        declared_result_id=boundary_result.get("result_id"),
    )

    checks=[]
    def add(cid,passed,detail):
        checks.append({"check_id":cid,"pass":bool(passed),"detail":detail})
        if args.verbose: print("PASS" if passed else "FAIL",cid,detail)
    add("FROZEN_DATASET_IDENTITY",dataset_sha256==FROZEN_DATASET_SHA256,dataset_sha256)
    add("AREA_PROFILE_HASH_VALID",read_profile(root/"profiles"/"SEC_Real_Land_Area_Vector_Centre_Profile_v0_5_0.json")["profile_hash"]==area_profile["profile_hash"],area_profile["profile_hash"])
    add("BOUNDARY_PROFILE_HASH_VALID",read_profile(root/"profiles"/"SEC_Real_Land_Boundary_Vector_Centre_Profile_v0_5_0.json")["profile_hash"]==boundary_profile["profile_hash"],boundary_profile["profile_hash"])
    add("AREA_RESULT_RESOLVED",area_result.get("resolution_state")=="RESOLVED_POINT",area_result.get("resolution_state"))
    add("BOUNDARY_RESULT_RESOLVED",boundary_result.get("resolution_state")=="RESOLVED_POINT",boundary_result.get("resolution_state"))
    add("SAME_EXACT_DATASET",area_result.get("evidence",{}).get("dataset_sha256")==boundary_result.get("evidence",{}).get("dataset_sha256")==dataset_sha256,dataset_sha256)
    add("DISTINCT_PROFILE_IDENTITIES",area_profile["profile_hash"]!=boundary_profile["profile_hash"],[area_profile["profile_hash"],boundary_profile["profile_hash"]])
    add("DISTINCT_RESULT_IDENTITIES",area_result.get("result_id")!=boundary_result.get("result_id"),[area_result.get("result_id"),boundary_result.get("result_id")])
    add("COORDINATES_DIVERGE",(area_result.get("latitude_deg"),area_result.get("longitude_deg"))!=(boundary_result.get("latitude_deg"),boundary_result.get("longitude_deg")),[area_result.get("latitude_deg"),area_result.get("longitude_deg"),boundary_result.get("latitude_deg"),boundary_result.get("longitude_deg")])
    add("SINGLE_DEPENDENCY_DIFFERENTIAL",differential.get("differential_state")=="SINGLE_DEPENDENCY_DIVERGENCE",differential.get("differential_state"))
    add("MEASURE_IS_DECLARED_DIFFERENCE",differential.get("changed_dependencies")==["measure"],differential.get("changed_dependencies"))
    add("AREA_CERTIFICATE_BINDS_RESULT_AND_EVIDENCE",area_certificate.get("result_id")==area_result.get("result_id") and area_certificate.get("evidence_id")==area_result.get("evidence_id"),area_certificate.get("certificate_id"))
    add("BOUNDARY_CERTIFICATE_BINDS_RESULT_AND_EVIDENCE",boundary_certificate.get("result_id")==boundary_result.get("result_id") and boundary_certificate.get("evidence_id")==boundary_result.get("evidence_id"),boundary_certificate.get("certificate_id"))

    passed=sum(1 for c in checks if c["pass"]); total=len(checks)
    core={
        "schema":"SEC-REAL-LAND-SAME-DATASET-DIFFERENTIAL-EVIDENCE-1-D01",
        "system_version":SYSTEM_VERSION,
        "status":"PASS" if passed==total else "FAIL",
        "passed":passed,"total":total,
        "dataset_sha256":dataset_sha256,
        "area_profile_id":area_profile["profile_id"],"area_profile_hash":area_profile["profile_hash"],"area_result":area_result,
        "boundary_profile_id":boundary_profile["profile_id"],"boundary_profile_hash":boundary_profile["profile_hash"],"boundary_result":boundary_result,
        "angular_separation_deg":round(angular_separation_deg(area_result,boundary_result),9),
        "structural_differential":differential,
        "area_resolution_certificate":area_certificate,
        "boundary_resolution_certificate":boundary_certificate,
        "checks":checks,
    }
    evidence={**core,"evidence_id":structural_hash(core)}
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(evidence,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STRUCTURAL EARTH CENTRE SAME-DATASET PROFILE DIFFERENTIAL v0.5.0")
    print("STATUS",evidence["status"])
    print("TOTAL",f"{passed}/{total}",evidence["status"])
    print("AREA",area_result.get("latitude_deg"),area_result.get("longitude_deg"))
    print("BOUNDARY",boundary_result.get("latitude_deg"),boundary_result.get("longitude_deg"))
    print("ANGULAR SEPARATION DEG",evidence["angular_separation_deg"])
    print("DIFFERENTIAL",differential.get("differential_state"),differential.get("changed_dependencies"))
    print("EVIDENCE ID",evidence["evidence_id"])
    return 0 if evidence["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
