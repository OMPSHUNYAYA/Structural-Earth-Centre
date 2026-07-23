# Structural Earth Centre Verification Guide

## Dependency-Governed Centre Resolution and Structural Portability

**Release:** `v0.5.0`  
**Core Conformance:** `38/38 PASS`  
**Earth Profile Validation:** `20/20 PASS`  
**Structural Innovation:** `24/24 PASS`  
**Advanced Structural Layer:** `30/30 PASS`  
**Integrated Centre Laboratory:** `132/132 PASS`  
**Structural Portability:** `40/40 PASS`  
**Portability Parity:** `27/27 PASS`

---

## 1. Verification Boundaries

SEC separates the following verification boundaries:

`exact core conformance`

`Python/browser core parity`

`bounded Earth profile validation`

`real-land computation and reproducibility`

`structural innovation qualification`

`same-dataset controlled differential`

`advanced centre claim-relation, spectrum, frontier, and exact graph-centre qualification`

`integrated centre browser qualification`

`cross-domain structural portability qualification`

`Python/JavaScript structural portability parity`

A PASS in one layer should not be interpreted as a broader claim from another layer.

The `132/132` integrated centre laboratory and `40/40` portability laboratory are deliberately separate. The portability proof is not added to the integrated centre count.

---

## 2. Requirements

Core Python verification:

- Python 3.10 or newer.

Cross-implementation parity:

- Python 3.10 or newer;
- Node.js 18 or newer.

Browser verification:

- current desktop browser;
- JavaScript enabled.

The verification scripts require no third-party Python package.

`SHA256SUMS.txt` covers every file under `corpus/`, `data/`, `demo/`, `evidence/`, `profiles/`, and `verify/`. Documentation and root-level repository files are outside this technical byte-freeze boundary.

SEC structural identities are canonical identities computed over declared normalized content. The SHA-256 values in `SHA256SUMS.txt` are digests of raw file bytes. A canonical structural identity is therefore not expected to equal the file digest of the artifact that contains or reports it.

---

## 3. Exact Core

Run:

```text
python demo/Structural_Earth_Centre_Reference_Kernel_v0_5_0.py --corpus corpus --audit
```

Expected:

`38/38 PASS`

Frozen identities:

`VECTOR SET secv_9c24f0f89d5b5caf744f0ebb5b4ca2435e55b15dd744bd147ad24d843503ad5d`

`CORPUS sha256:fbdad21cf55b17a02e5130c8a214d5859ff6a51a04be330e0448d80396ef7bd6`

`PROFILE REGISTRY sha256:9ce322a33d2b918088952f1f32293eae08acaff86dcc9cbf113dae5978f80f2e`

---

## 4. Core Python/Browser Parity

Run:

```text
python verify/SEC_Cross_Implementation_Parity_Auditor_v0_5_0.py --root . --verbose
```

Expected:

`38/38 PASS`

Parity evidence:

`sha256:a08c55f02a5648c2f928ea58f6154e99ca81c2dc585e138fb4253d1caeae8ccd`

---

## 5. Earth Profile Validation

Run:

```text
python verify/SEC_Earth_Profile_Validator_v0_5_0.py --profiles profiles --verbose
```

Expected:

`20/20 PASS`

The 20 checks cover 14 bounded Earth vectors together with registry, linkage, identity, and comparison checks.

Current identities:

`SOURCE REGISTRY sha256:6538112c642f1b3cc4ddeba4fbdcbb1f8c55e39e680202b64ffdb0348eb08238`

`CARRIER REGISTRY sha256:f4f5ce4e13f98445df5e9f6bfbb642ead472c5e714b3fee713017ef9abee0216`

`PROFILE REGISTRY sha256:252d5945bad22ac90aaee972a8e33cdf094dc81d8762de92e6730bb624962a26`

`VECTOR SET secearthv_761a8c1ff99a85c7e268a17d3bfe1f52f0689d89769469fcd3c752b6635f3ed6`

`VECTOR CORPUS sha256:fd9eb495e90004607ef052f970412d261a6f91287d651e2f44d986dadb9358bd`

---

## 6. Real-Land Resolver

Run:

```text
python verify/SEC_Real_Land_Centre_Resolver_v0_5_0.py --self-test
```

Expected:

`26/26 PASS`

Stored self-test evidence:

`evidence/SEC_Real_Land_Centre_Resolver_Self_Test_v0_5_0.json`

The standalone real-land resolver accepts the declared area-vector profile. Supplying the boundary-vector profile is rejected with `PROFILE_ID_MISMATCH` and identifies the bounded comparison entry point:

`verify/SEC_Real_Land_Profile_Differential_v0_5_0.py`

Current area profile hash:

`sha256:264e68d25e9c8edbfcd2af00f2d99dc81a92d057f47347f02e073a9290e94361`

Recompute the frozen area-vector result:

```text
python verify/SEC_Real_Land_Centre_Resolver_v0_5_0.py --geojson data/ne_110m_land.geojson
```

Expected structural result:

`RESOLVED_POINT`

`LATITUDE_DEG 44.847286603`

`LONGITUDE_DEG 28.41498761`

`DATASET sha256:9e0729ee253ca7d7a5c4ae9395fb1902264c5377c52e224d13dd85010e2835d9`

`RESULT ID sha256:ece1e949b32b52102a60e296fc6fa170528d569cec65c0af08ce44dde0aa42aa`

---

## 7. Real-Data Reproducibility

Self-test:

```text
python verify/SEC_Real_Land_Reproducibility_Verifier_v0_5_0.py --self-test
```

Expected:

`9/9 PASS`

Verify stored evidence:

```text
python verify/SEC_Real_Land_Reproducibility_Verifier_v0_5_0.py --fetch-evidence evidence/SEC_Real_Land_Centre_Natural_Earth_110m_Fetch_v0_5_0.json --offline-evidence evidence/SEC_Real_Land_Centre_Natural_Earth_110m_Offline_v0_5_0.json
```

Expected:

`9/9 PASS`

Expected common result identity:

`sha256:ece1e949b32b52102a60e296fc6fa170528d569cec65c0af08ce44dde0aa42aa`

Expected reproducibility evidence identity:

`sha256:866879f8eb735348bf93e822eb525e7d46b7765e500f1ce27c67b774bc63670e`

---

## 8. Structural Innovation Layer

Run:

```text
python verify/SEC_Structural_Centre_Resolver_v0_5_0.py --audit --verbose
```

Expected:

`24/24 PASS`

Innovation vector set:

`secinv_7718daa3768043daf43790ca5c4e0f83f01f207d444b8418e6067700d8af1973`

Innovation vector corpus:

`sha256:7d32586925603334c9c8366aca2cd7ae69d7543e41b28ee40239e4e2d4597f49`

Innovation audit evidence:

`sha256:6821172bdea22cf559730eb534ad81a570d19b5fb4b1ed0ada18df7e6589ccb9`

Parity:

```text
python verify/SEC_Structural_Centre_Innovation_Parity_Auditor_v0_5_0.py --root . --verbose
```

Expected:

`18/18 PASS`

Parity evidence:

`sha256:31961a9e9e52f2e54c9739bae04823395ce909c2b3a063f01af178d8d0991451`

---

## 9. Same-Dataset Profile Differential

Run:

```text
python verify/SEC_Real_Land_Profile_Differential_v0_5_0.py --root . --verbose
```

Expected:

`13/13 PASS`

Expected bounded comparison:

`AREA 44.847286603 28.41498761`

`BOUNDARY 71.590921549 66.736078802`

`ANGULAR SEPARATION DEG 32.350594616`

`DIFFERENTIAL SINGLE_DEPENDENCY_DIVERGENCE ['measure']`

Evidence identity:

`sha256:e6150e95d3e60ee24510ba0921172ec789008c52472007a3e4c394f2b900a71e`

---

## 10. Advanced Centre Structural Layer

This layer qualifies:

- Structural Claim Relation;
- Centre Spectrum;
- Resolution Frontier;
- exact finite graph-centre resolution.

Run:

```text
python verify/SEC_Structural_Centre_Advanced_Resolver_v0_5_0.py --audit --verbose
```

Expected:

`30/30 PASS`

Advanced vector set:

`secadv_eb83c11f6082d243cb2dfdd1745c980167d41d4f4418a329741dab4b7300b067`

Advanced vector corpus:

`sha256:34ae50e716024ddec125b35ed38afd7fa3b06dbb151ce1348ba75ac2ea0ae62b`

Advanced audit evidence:

`sha256:4731690078d89a503ad2cebad654d0541ea4968c3092c96a3bc914ecd6e01443`

Run advanced Python/JavaScript parity:

```text
python verify/SEC_Structural_Centre_Advanced_Parity_Auditor_v0_5_0.py --root . --verbose
```

Expected:

`22/22 PASS`

Advanced parity evidence:

`sha256:43c77dcea8e10a48c54a033829217eb85c63af03ed7fd6808d3f805938d348b1`

---

## 11. Structural Portability Proof

The v0.5.0 portability layer uses one shared generic structural kernel and two bounded domain adapters.

Shared primitives:

`CLAIM_RELATION`

`RESULT_SPECTRUM`

`RESOLUTION_FRONTIER`

`RESOLUTION_CERTIFICATE`

Adapters:

`SEC-PORTABILITY-ADAPTER-CENTRE-1-D01`

`SEC-PORTABILITY-ADAPTER-ADMISSIBILITY-1-D01`

Run the Python portability audit:

```text
python verify/SEC_Structural_Portability_Kernel_v0_5_0.py --profiles profiles --audit --verbose
```

Expected:

`40/40 PASS`

Run Python/JavaScript portability parity:

```text
python verify/SEC_Structural_Portability_Parity_Auditor_v0_5_0.py --root . --verbose
```

Expected:

`27/27 PASS`

Frozen identities:

`GENERIC KERNEL PROFILE sha256:60b473acd3458abe23d0a095e1b3a1d81ce4e61cd517c9b7d244e5c5efa508a9`

`CENTRE ADAPTER PROFILE sha256:268d710e4b320e6eee9a674282a1f499832ac27e0d2135948a7dc28b89b49ef2`

`ADMISSIBILITY ADAPTER PROFILE sha256:f706969920fe3a01ffc79188dfba4c3fb897c22e94c02b81805083a31ee516f1`

`PORTABILITY PROFILE sha256:30aaec976f2b38bfe0b1d8e6f201ed941b0432af515b477293d926d60f9ed51f`

`VECTOR SET secport_a392c25a59ae68f6505b183e26f96af64f842e30745df9e7ae9f68d895f99cd4`

`VECTOR CORPUS sha256:720b5c795efef23489ed800fd0b7bb3d1ec2b2e6e20fe0ec9c0f2aeca54c5ae7`

`PORTABILITY CERTIFICATE sha256:660af7631ca9e7cc630ec3695c0cb78ead5fa43f62e09be6e4555361b3a8eb21`

`AUDIT EVIDENCE sha256:41933da5589cb12615d2a8d470f725918d70c7fad3da033c6d663fc2344ec4d1`

`PARITY EVIDENCE sha256:7b99708a80daf405825f5ca4aed764e0803a9eb38ed369a092c93e5f947e358f`

The synthetic admissibility adapter carries `execution_authority = NONE`.

---

## 12. Browser Laboratories

### Integrated centre laboratory

Open:

`demo/Structural_Earth_Centre_Laboratory_v0_5_0.html`

Run:

```javascript
await SEC_LAB_AUDIT.runAll({verbose:true})
```

Expected:

`132/132 PASS`

### Structural portability laboratory

Open:

`demo/Structural_Earth_Centre_Portability_Laboratory_v0_5_0.html`

Run:

```javascript
await SEC_PORTABILITY_AUDIT.runAll({verbose:true})
```

Expected:

`40/40 PASS`

### Core browser reference

Open:

`demo/Structural_Earth_Centre_Browser_Reference_v0_5_0.html`

Run:

```javascript
await SEC_AUDIT.runAll({verbose:true})
```

Expected:

`38/38 PASS`

### Structural innovation laboratory

Open:

`demo/Structural_Earth_Centre_Innovation_Laboratory_v0_5_0.html`

Run:

```javascript
await SEC_INNOVATION_AUDIT.runAll({verbose:true})
```

Expected:

`24/24 PASS`

### Advanced structural laboratory

Open:

`demo/Structural_Earth_Centre_Advanced_Laboratory_v0_5_0.html`

Run:

```javascript
await SEC_ADVANCED_AUDIT.runAll({verbose:true})
```

Expected:

`30/30 PASS`

A local `file:` origin warning may be displayed by the browser. The self-contained audit paths do not depend on network fetch or a browser cryptography service, so the warning is informational rather than a failed qualification result.

---

## 13. Recommended Complete Verification Sequence

Validate the verification runner configuration:

```text
python -B verify/SEC_Verification_Runner_v0_5_0.py --self-test
```

Expected:

`6/6 PASS`

Run the complete command-line verification stack:

```text
python -B verify/SEC_Verification_Runner_v0_5_0.py
```

Expected:

```text
TOTAL STAGES 13/13 PASS
FINAL STATUS PASS
```

The runner checks freeze hygiene before and after execution, verifies `SHA256SUMS.txt` completeness and file digests across the declared frozen technical surface, and runs all 13 command-line verification stages.

The same verification boundaries can also be executed individually:

```text
python demo/Structural_Earth_Centre_Reference_Kernel_v0_5_0.py --corpus corpus --audit
python verify/SEC_Cross_Implementation_Parity_Auditor_v0_5_0.py --root . --verbose
python verify/SEC_Earth_Profile_Validator_v0_5_0.py --profiles profiles --verbose
python verify/SEC_Real_Land_Centre_Resolver_v0_5_0.py --self-test
python verify/SEC_Real_Land_Reproducibility_Verifier_v0_5_0.py --self-test
python verify/SEC_Real_Land_Reproducibility_Verifier_v0_5_0.py --fetch-evidence evidence/SEC_Real_Land_Centre_Natural_Earth_110m_Fetch_v0_5_0.json --offline-evidence evidence/SEC_Real_Land_Centre_Natural_Earth_110m_Offline_v0_5_0.json
python verify/SEC_Structural_Centre_Resolver_v0_5_0.py --audit --verbose
python verify/SEC_Structural_Centre_Innovation_Parity_Auditor_v0_5_0.py --root . --verbose
python verify/SEC_Real_Land_Profile_Differential_v0_5_0.py --root . --verbose
python verify/SEC_Structural_Centre_Advanced_Resolver_v0_5_0.py --audit --verbose
python verify/SEC_Structural_Centre_Advanced_Parity_Auditor_v0_5_0.py --root . --verbose
python verify/SEC_Structural_Portability_Kernel_v0_5_0.py --profiles profiles --audit --verbose
python verify/SEC_Structural_Portability_Parity_Auditor_v0_5_0.py --root . --verbose
```

Then run the integrated centre browser audit and the structural portability browser audit.

---

## 14. Verification Principle

SEC separates:

`claim structure`

from:

`mathematical result`

from:

`result identity`

from:

`evidence provenance`

and separately preserves:

`claim relation != result relation`

For v0.5.0 portability it also enforces:

`generic structural semantics != domain adapter semantics`

The current portability claim remains bounded to the two declared adapters and frozen portability corpus.
