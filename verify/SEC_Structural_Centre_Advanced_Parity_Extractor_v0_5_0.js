#!/usr/bin/env node
"use strict";
const fs=require("fs"),path=require("path");
let root=".";const args=process.argv.slice(2);for(let i=0;i<args.length;i++)if(args[i]==="--root"&&i+1<args.length)root=args[++i];
const core=require(path.resolve(root,"verify","SEC_Structural_Centre_Advanced_Reference_v0_5_0.js"));
const corpus=JSON.parse(fs.readFileSync(path.resolve(root,"profiles","SEC_Structural_Centre_Advanced_Vectors_v0_5_0.json"),"utf8"));
const outputs={};for(const v of corpus.vectors)outputs[v.vector_id]=core.evaluateVector(v);
process.stdout.write(JSON.stringify({schema:"SEC-STRUCTURAL-CENTRE-ADVANCED-JS-EXTRACTION-1-D01",system_version:core.SYSTEM_VERSION,advanced_profile:core.ADVANCED_PROFILE,vector_set_id:corpus.vector_set_id,vector_corpus_id:corpus.vector_corpus_id,vector_count:corpus.vector_count,outputs}));
