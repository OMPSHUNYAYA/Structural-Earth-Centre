#!/usr/bin/env node
"use strict";
const fs=require("fs");
const path=require("path");

function main(){
  const args=process.argv.slice(2);
  let root=".";
  for(let i=0;i<args.length;i++) if(args[i]==="--root"&&i+1<args.length) root=args[++i];
  const core=require(path.resolve(root,"verify","SEC_Structural_Centre_Innovation_Reference_v0_5_0.js"));
  const corpus=JSON.parse(fs.readFileSync(path.resolve(root,"profiles","SEC_Structural_Centre_Innovation_Vectors_v0_5_0.json"),"utf8"));
  const outputs={};
  for(const vector of corpus.vectors) outputs[vector.vector_id]=core.evaluateVector(vector);
  const payload={
    schema:"SEC-STRUCTURAL-CENTRE-INNOVATION-JS-EXTRACTION-1-D01",
    system_version:core.SYSTEM_VERSION,
    innovation_profile:core.INNOVATION_PROFILE,
    vector_set_id:corpus.vector_set_id,
    vector_corpus_id:corpus.vector_corpus_id,
    vector_count:corpus.vector_count,
    outputs
  };
  process.stdout.write(JSON.stringify(payload));
}
main();
