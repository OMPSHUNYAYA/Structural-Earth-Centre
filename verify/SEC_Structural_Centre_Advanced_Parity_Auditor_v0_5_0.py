#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
from typing import Any,Optional,Sequence
SYSTEM_VERSION="0.5.0"
def cb(v:Any)->bytes:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
def sh(v:Any)->str:return "sha256:"+hashlib.sha256(cb(v)).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def main(argv:Optional[Sequence[str]]=None)->int:
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path("."));p.add_argument("--out",type=Path);p.add_argument("--verbose",action="store_true");a=p.parse_args(argv);root=a.root.resolve();node=shutil.which("node")
 if not node: print("STATUS UNSUPPORTED\nREASON NODE_NOT_AVAILABLE");return 2
 corpus=json.loads((root/"profiles/SEC_Structural_Centre_Advanced_Vectors_v0_5_0.json").read_text());py=load("sec_adv_py",root/"verify/SEC_Structural_Centre_Advanced_Resolver_v0_5_0.py");pyout={v["vector_id"]:py.evaluate_vector(v) for v in corpus["vectors"]}
 proc=subprocess.run([node,str(root/"verify/SEC_Structural_Centre_Advanced_Parity_Extractor_v0_5_0.js"),"--root",str(root)],check=True,capture_output=True,text=True);js=json.loads(proc.stdout)
 checks=[]
 def add(cid,ok,detail):checks.append({"check_id":cid,"pass":bool(ok),"detail":detail});a.verbose and print("PASS" if ok else "FAIL",cid,detail)
 add("SYSTEM_VERSION",js.get("system_version")==SYSTEM_VERSION,js.get("system_version"));add("VECTOR_SET_ID",js.get("vector_set_id")==corpus.get("vector_set_id"),js.get("vector_set_id"));add("VECTOR_CORPUS_ID",js.get("vector_corpus_id")==corpus.get("vector_corpus_id"),js.get("vector_corpus_id"))
 for v in corpus["vectors"]:vid=v["vector_id"];add(vid,pyout[vid]==js["outputs"].get(vid),vid)
 passed=sum(c["pass"] for c in checks);total=len(checks);core={"schema":"SEC-STRUCTURAL-CENTRE-ADVANCED-PARITY-EVIDENCE-1-D01","system_version":SYSTEM_VERSION,"status":"PASS" if passed==total else "FAIL","passed":passed,"total":total,"vector_set_id":corpus["vector_set_id"],"vector_corpus_id":corpus["vector_corpus_id"],"checks":checks};ev={**core,"evidence_id":sh(core)}
 if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(ev,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
 print("STRUCTURAL EARTH CENTRE ADVANCED PARITY AUDITOR v0.5.0");print("STATUS",ev["status"]);print("TOTAL",f"{passed}/{total}",ev["status"]);print("EVIDENCE ID",ev["evidence_id"]);return 0 if ev["status"]=="PASS" else 1
if __name__=="__main__":raise SystemExit(main())
