#!/usr/bin/env node
"use strict";
const fs=require("fs");
const path=require("path");

function parseArgs(argv){
  let root=".";
  for(let i=0;i<argv.length;i++){
    if(argv[i]==="--root"&&i+1<argv.length){root=argv[++i];}
  }
  return {root:path.resolve(root)};
}
const args=parseArgs(process.argv.slice(2));
const core=require(path.join(args.root,"verify","SEC_Structural_Portability_Reference_v0_5_0.js"));
const corpus=JSON.parse(fs.readFileSync(path.join(args.root,"profiles","SEC_Structural_Portability_Vectors_v0_5_0.json"),"utf8"));
const outputs={};
for(const vector of corpus.vectors)outputs[vector.vector_id]=core.evaluateVector(vector);
process.stdout.write(JSON.stringify({
  schema:"SEC-STRUCTURAL-PORTABILITY-JS-PARITY-EXPORT-1-D01",
  system_version:core.SYSTEM_VERSION,
  vector_set_id:corpus.vector_set_id,
  vector_corpus_id:corpus.vector_corpus_id,
  outputs
}));
