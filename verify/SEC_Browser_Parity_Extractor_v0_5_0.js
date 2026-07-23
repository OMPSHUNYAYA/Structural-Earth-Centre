#!/usr/bin/env node
"use strict";

const fs = require("fs");
const vm = require("vm");

function usage() {
  console.error("Usage: node SEC_Browser_Parity_Extractor_v0_5_0.js <browser-html>");
  process.exit(2);
}

if (process.argv.length !== 3) usage();

const htmlPath = process.argv[2];
const html = fs.readFileSync(htmlPath, "utf8");
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map(m => m[1]);

if (!scripts.length) {
  throw new Error("No executable script block found in browser reference.");
}

const source = scripts[scripts.length - 1];

const context = {
  console: {
    log: () => {},
    error: (...args) => console.error(...args),
    warn: (...args) => console.error(...args)
  },
  TextEncoder,
  TextDecoder,
  Uint8Array,
  Uint32Array,
  BigInt,
  Map,
  Set,
  Array,
  Object,
  JSON,
  Math,
  Number,
  String,
  Boolean,
  Error,
  TypeError,
  RegExp,
  Date,
  Promise
};
context.globalThis = context;

vm.createContext(context);
vm.runInContext(source, context, {
  filename: htmlPath,
  timeout: 30000
});

if (!context.SEC_CORE || !context.SEC_AUDIT) {
  throw new Error("Browser reference did not expose SEC_CORE and SEC_AUDIT.");
}

const corpus = vm.runInContext("SEC_FROZEN_CORPUS", context);
const registry = vm.runInContext("SEC_FROZEN_PROFILE_REGISTRY", context);

if (!corpus || !Array.isArray(corpus.vectors)) {
  throw new Error("Frozen browser corpus is unavailable.");
}

const records = corpus.vectors.map(vector => {
  const actual = context.SEC_CORE.resolveVector(vector.vector_id);
  return {
    vector_id: vector.vector_id,
    category: vector.category,
    resolution_state: actual.result.resolution_state,
    centre_type: actual.result.centre_type,
    result: actual.result,
    canonical_carrier: actual.canonical_carrier,
    carrier_id: actual.carrier_id,
    dependency_fingerprint: actual.dependency_fingerprint,
    dependency_fingerprint_id: actual.dependency_fingerprint_id,
    result_id: actual.result_id,
    certificate_id: actual.certificate_id,
    profile_hash: actual.profile_hash
  };
});

const registryCheck = context.SEC_AUDIT.verifyRegistry();
const corpusCheck = context.SEC_AUDIT.verifyFrozenCorpusIdentity();

const output = {
  schema: "SEC-BROWSER-PARITY-EXPORT-1-D01",
  system_version: "0.5.0",
  vector_count: records.length,
  vector_set_id: corpus.vector_set_id,
  corpus_id: corpus.corpus_id,
  profile_registry_id: registry.profile_registry_id,
  registry_identity_pass: registryCheck.pass === true,
  corpus_identity_pass: corpusCheck.pass === true,
  records
};

process.stdout.write(JSON.stringify(output));
