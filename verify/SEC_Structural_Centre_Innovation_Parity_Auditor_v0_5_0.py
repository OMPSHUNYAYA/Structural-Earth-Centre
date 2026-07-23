#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

SYSTEM_VERSION="0.5.0"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def structural_hash(value: Any) -> str:
    import hashlib
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_python_core(root: Path):
    path=root/"verify"/"SEC_Structural_Centre_Resolver_v0_5_0.py"
    spec=importlib.util.spec_from_file_location("sec_innovation_python",path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load Python innovation resolver")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: Optional[Sequence[str]]=None)->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--out",type=Path)
    parser.add_argument("--verbose",action="store_true")
    args=parser.parse_args(argv)
    root=args.root.resolve()
    node=shutil.which("node")
    if not node:
        print("STATUS UNSUPPORTED")
        print("REASON NODE_NOT_AVAILABLE")
        return 2

    corpus=json.loads((root/"profiles"/"SEC_Structural_Centre_Innovation_Vectors_v0_5_0.json").read_text(encoding="utf-8"))
    pycore=load_python_core(root)
    py_outputs={v["vector_id"]:pycore.evaluate_vector(v) for v in corpus["vectors"]}
    proc=subprocess.run([
        node,str(root/"verify"/"SEC_Structural_Centre_Innovation_Parity_Extractor_v0_5_0.js"),"--root",str(root)
    ],check=True,capture_output=True,text=True)
    js=json.loads(proc.stdout)

    checks=[]
    def add(cid:str,passed:bool,detail:Any):
        checks.append({"check_id":cid,"pass":bool(passed),"detail":detail})
        if args.verbose: print("PASS" if passed else "FAIL",cid,detail)

    add("SYSTEM_VERSION",js.get("system_version")==SYSTEM_VERSION,js.get("system_version"))
    add("VECTOR_SET_ID",js.get("vector_set_id")==corpus.get("vector_set_id"),js.get("vector_set_id"))
    add("VECTOR_CORPUS_ID",js.get("vector_corpus_id")==corpus.get("vector_corpus_id"),js.get("vector_corpus_id"))
    for vector in corpus["vectors"]:
        vid=vector["vector_id"]
        add(vid,py_outputs[vid]==js["outputs"].get(vid),vid)

    passed=sum(1 for c in checks if c["pass"])
    total=len(checks)
    core={
        "schema":"SEC-STRUCTURAL-CENTRE-INNOVATION-PARITY-EVIDENCE-1-D01",
        "system_version":SYSTEM_VERSION,
        "status":"PASS" if passed==total else "FAIL",
        "passed":passed,
        "total":total,
        "vector_set_id":corpus["vector_set_id"],
        "vector_corpus_id":corpus["vector_corpus_id"],
        "checks":checks,
    }
    evidence={**core,"evidence_id":structural_hash(core)}
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(evidence,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("STRUCTURAL EARTH CENTRE INNOVATION PARITY AUDITOR v0.5.0")
    print("STATUS",evidence["status"])
    print("TOTAL",f"{passed}/{total}",evidence["status"])
    print("EVIDENCE ID",evidence["evidence_id"])
    return 0 if evidence["status"]=="PASS" else 1

if __name__=="__main__":
    raise SystemExit(main())
