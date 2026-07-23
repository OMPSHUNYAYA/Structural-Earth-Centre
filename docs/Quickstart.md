# ⭐ Structural Earth Centre — Quickstart

## Dependency-Governed Resolution of Centre Claims and Structural Portability

**Release:** `v0.5.0`  
**Core:** `38/38 PASS`  
**Earth Profiles:** `20/20 PASS`  
**Structural Innovation:** `24/24 PASS`  
**Advanced Structural Layer:** `30/30 PASS`  
**Integrated Centre Laboratory:** `132/132 PASS`  
**Structural Portability:** `40/40 PASS`  
**Portability Parity:** `27/27 PASS`

---

# 60-Second Start

## Centre stack

Open:

`demo/Structural_Earth_Centre_Laboratory_v0_5_0.html`

Run in the browser console:

```javascript
await SEC_LAB_AUDIT.runAll({verbose:true})
```

Expected:

```text
CORE                 38/38 PASS
EARTH                20/20 PASS
REAL LAND             7/7 PASS
INNOVATION            24/24 PASS
PROFILE DIFFERENTIAL 13/13 PASS
ADVANCED              30/30 PASS
TOTAL                132/132 PASS
```

## Structural portability proof

Open:

`demo/Structural_Earth_Centre_Portability_Laboratory_v0_5_0.html`

Run:

```javascript
await SEC_PORTABILITY_AUDIT.runAll({verbose:true})
```

Expected:

`40/40 PASS`

The portability laboratory is a separate verification boundary from the `132/132` integrated centre laboratory.

---

# What v0.5.0 Demonstrates

SEC v0.5.0 retains the complete centre-resolution stack and adds a bounded cross-domain portability proof.

The shared generic primitive set is:

`CLAIM_RELATION`

`RESULT_SPECTRUM`

`RESOLUTION_FRONTIER`

`RESOLUTION_CERTIFICATE`

The same generic primitives are exercised through:

`generic structural kernel + exact centre adapter`

and:

`generic structural kernel + synthetic admissibility adapter`

The adapters own domain-specific rules. The generic kernel owns the shared structural semantics.

The portability proof also verifies:

- matched relation semantics across both domains;
- matched spectrum semantics across both domains;
- matched frontier semantics across both domains;
- shared certificate binding;
- generic-kernel/domain-adapter separation;
- certificate tamper sensitivity;
- Python/JavaScript parity;
- a bounded portability certificate.

The centre stack continues to demonstrate:

- exact bounded centre resolution;
- explicit non-result and refusal states;
- same-dataset profile divergence;
- Structural Centre Differential;
- Centre Stability Envelope and genuine `RESOLVED_REGION`;
- Symmetry Certificates;
- Centre Resolution Certificates;
- Structural Claim Relation;
- Centre Spectrum without blind averaging;
- Resolution Frontier over declared repair options;
- exact finite graph-centre resolution.

The central separations are:

`coordinate != carrier != centre profile != centre claim != result identity != evidence identity`

`claim relation != result relation`

`generic structural semantics != domain adapter semantics`

---

# Minimum Requirements

Browser:

- current desktop browser;
- JavaScript enabled.

Python verification:

- Python 3.10 or newer;
- no third-party Python package required.

Parity verification:

- Node.js 18 or newer.

Ordinary verification against the included files does not require network access.

---

# Repository Layout

```text
Structural-Earth-Centre/
├── LICENSE
├── README.md
├── SHA256SUMS.txt
├── corpus/
│   ├── SEC_Conformance_Corpus_Identity_v0_5_0.txt
│   ├── SEC_Conformance_Corpus_v0_5_0.json
│   ├── SEC_Profile_Registry_v0_5_0.json
│   └── SEC_Vector_Manifest_v0_5_0.json
├── data/
│   └── ne_110m_land.geojson
├── demo/
│   ├── Structural_Earth_Centre_Advanced_Laboratory_v0_5_0.html
│   ├── Structural_Earth_Centre_Browser_Reference_v0_5_0.html
│   ├── Structural_Earth_Centre_Innovation_Laboratory_v0_5_0.html
│   ├── Structural_Earth_Centre_Laboratory_v0_5_0.html
│   ├── Structural_Earth_Centre_Portability_Laboratory_v0_5_0.html
│   └── Structural_Earth_Centre_Reference_Kernel_v0_5_0.py
├── docs/
│   ├── FAQ.md
│   ├── Quickstart.md
│   ├── SEC_Bounded_Earth_Carrier_and_Centre_Profile_Specification_v0_5_0.txt
│   ├── SEC_Claim_Relation_Spectrum_Frontier_and_Portability_v0_5_0.txt
│   ├── SEC_Cross_Implementation_Parity_Verification_v0_5_0.txt
│   ├── SEC_Real_Land_Centre_Computation_v0_5_0.txt
│   ├── SEC_Structural_Centre_Differential_Stability_and_Certification_v0_5_0.txt
│   ├── SEC_Structural_Portability_Proof_v0_5_0.txt
│   ├── Structural-Earth-Centre-Architecture-Diagram.png
│   ├── Structural_Earth_Centre_Concept_and_Architecture_v0_5_0.txt
│   ├── Structural_Earth_Centre_Core_Mathematical_and_Resolution_Specification_v0_5_0.txt
│   └── VERIFY.md
├── evidence/
│   ├── SEC_Cross_Implementation_Parity_Evidence_v0_5_0.json
│   ├── SEC_Cross_Implementation_Parity_Summary_v0_5_0.txt
│   ├── SEC_Earth_Profile_Validation_Evidence_v0_5_0.json
│   ├── SEC_Real_Land_Centre_Natural_Earth_110m_Fetch_v0_5_0.json
│   ├── SEC_Real_Land_Centre_Natural_Earth_110m_Offline_v0_5_0.json
│   ├── SEC_Real_Land_Centre_Resolver_Self_Test_v0_5_0.json
│   ├── SEC_Real_Land_Reproducibility_Evidence_v0_5_0.json
│   ├── SEC_Real_Land_Reproducibility_Verifier_Self_Test_v0_5_0.json
│   ├── SEC_Real_Land_Same_Dataset_Differential_Evidence_v0_5_0.json
│   ├── SEC_Structural_Centre_Advanced_Audit_v0_5_0.json
│   ├── SEC_Structural_Centre_Advanced_Parity_Evidence_v0_5_0.json
│   ├── SEC_Structural_Centre_Innovation_Audit_v0_5_0.json
│   ├── SEC_Structural_Centre_Innovation_Parity_Evidence_v0_5_0.json
│   ├── SEC_Structural_Portability_Audit_v0_5_0.json
│   └── SEC_Structural_Portability_Parity_Evidence_v0_5_0.json
├── profiles/
│   ├── SEC_Earth_Bounded_Claim_Vectors_v0_5_0.json
│   ├── SEC_Earth_Carrier_Registry_v0_5_0.json
│   ├── SEC_Earth_Centre_Profile_Registry_v0_5_0.json
│   ├── SEC_Earth_Source_Registry_v0_5_0.json
│   ├── SEC_Generic_Structural_Kernel_Profile_v0_5_0.json
│   ├── SEC_Portability_Admissibility_Adapter_Profile_v0_5_0.json
│   ├── SEC_Portability_Centre_Adapter_Profile_v0_5_0.json
│   ├── SEC_Real_Land_Area_Vector_Centre_Profile_v0_5_0.json
│   ├── SEC_Real_Land_Boundary_Vector_Centre_Profile_v0_5_0.json
│   ├── SEC_Structural_Centre_Advanced_Profile_v0_5_0.json
│   ├── SEC_Structural_Centre_Advanced_Vectors_v0_5_0.json
│   ├── SEC_Structural_Centre_Innovation_Profile_v0_5_0.json
│   ├── SEC_Structural_Centre_Innovation_Vectors_v0_5_0.json
│   ├── SEC_Structural_Portability_Profile_v0_5_0.json
│   └── SEC_Structural_Portability_Vectors_v0_5_0.json
└── verify/
    ├── SEC_Browser_Parity_Extractor_v0_5_0.js
    ├── SEC_Cross_Implementation_Parity_Auditor_v0_5_0.py
    ├── SEC_Earth_Profile_Validator_v0_5_0.py
    ├── SEC_Real_Land_Centre_Resolver_v0_5_0.py
    ├── SEC_Real_Land_Profile_Differential_v0_5_0.py
    ├── SEC_Real_Land_Reproducibility_Verifier_v0_5_0.py
    ├── SEC_Structural_Centre_Advanced_Parity_Auditor_v0_5_0.py
    ├── SEC_Structural_Centre_Advanced_Parity_Extractor_v0_5_0.js
    ├── SEC_Structural_Centre_Advanced_Reference_v0_5_0.js
    ├── SEC_Structural_Centre_Advanced_Resolver_v0_5_0.py
    ├── SEC_Structural_Centre_Innovation_Parity_Auditor_v0_5_0.py
    ├── SEC_Structural_Centre_Innovation_Parity_Extractor_v0_5_0.js
    ├── SEC_Structural_Centre_Innovation_Reference_v0_5_0.js
    ├── SEC_Structural_Centre_Resolver_v0_5_0.py
    ├── SEC_Structural_Portability_Kernel_v0_5_0.py
    ├── SEC_Structural_Portability_Parity_Auditor_v0_5_0.py
    ├── SEC_Structural_Portability_Parity_Extractor_v0_5_0.js
    ├── SEC_Structural_Portability_Reference_v0_5_0.js
    └── SEC_Verification_Runner_v0_5_0.py
```

`SHA256SUMS.txt` is kept at the repository root and covers every file under `corpus/`, `data/`, `demo/`, `evidence/`, `profiles/`, and `verify/`.

Documentation and root-level repository files are outside this technical byte-freeze boundary.

SEC structural identities are canonical identities computed over declared normalized content. `SHA256SUMS.txt` records SHA-256 digests of raw file bytes. These identity forms serve different purposes and are not expected to be equal.

# Complete Command-Line Verification

From the repository root, the primary command-line verification entry point is:

```text
python -B verify/SEC_Verification_Runner_v0_5_0.py
```

Expected ending:

```text
TOTAL STAGES 13/13 PASS
FINAL STATUS PASS
```

Runner configuration can be checked without executing the complete stack:

```text
python -B verify/SEC_Verification_Runner_v0_5_0.py --self-test
```

Expected:

`6/6 PASS`

For individual verification boundaries:

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

Expected headline results:

```text
CORE                             38/38 PASS
CORE PARITY                      38/38 PASS
EARTH                            20/20 PASS
REAL-LAND SELF-TEST              26/26 PASS
REPRODUCIBILITY SELF-TEST         9/9 PASS
STORED REPRODUCIBILITY            9/9 PASS
STRUCTURAL INNOVATION            24/24 PASS
INNOVATION PARITY                18/18 PASS
SAME-DATASET DIFFERENTIAL        13/13 PASS
ADVANCED STRUCTURAL              30/30 PASS
ADVANCED STRUCTURAL PARITY       22/22 PASS
STRUCTURAL PORTABILITY           40/40 PASS
PORTABILITY PARITY               27/27 PASS
```

On systems where Python 3 is exposed as `python3`, substitute `python3`.

---

# Primary Entry Points

The real-land resolver self-test evidence is stored at:

`evidence/SEC_Real_Land_Centre_Resolver_Self_Test_v0_5_0.json`

`README.md`

`demo/Structural_Earth_Centre_Laboratory_v0_5_0.html`

`demo/Structural_Earth_Centre_Portability_Laboratory_v0_5_0.html`

`demo/Structural_Earth_Centre_Advanced_Laboratory_v0_5_0.html`

`demo/Structural_Earth_Centre_Reference_Kernel_v0_5_0.py`

`verify/SEC_Verification_Runner_v0_5_0.py`

`docs/VERIFY.md`

`docs/SEC_Structural_Portability_Proof_v0_5_0.txt`

---

# Portability Files

Profiles:

- `profiles/SEC_Generic_Structural_Kernel_Profile_v0_5_0.json`
- `profiles/SEC_Portability_Centre_Adapter_Profile_v0_5_0.json`
- `profiles/SEC_Portability_Admissibility_Adapter_Profile_v0_5_0.json`
- `profiles/SEC_Structural_Portability_Profile_v0_5_0.json`
- `profiles/SEC_Structural_Portability_Vectors_v0_5_0.json`

Executable references and auditors:

- `verify/SEC_Structural_Portability_Kernel_v0_5_0.py`
- `verify/SEC_Structural_Portability_Reference_v0_5_0.js`
- `verify/SEC_Structural_Portability_Parity_Extractor_v0_5_0.js`
- `verify/SEC_Structural_Portability_Parity_Auditor_v0_5_0.py`

Evidence:

- `evidence/SEC_Structural_Portability_Audit_v0_5_0.json`
- `evidence/SEC_Structural_Portability_Parity_Evidence_v0_5_0.json`

Browser laboratory:

- `demo/Structural_Earth_Centre_Portability_Laboratory_v0_5_0.html`

---

# Portability Frozen Identities

Generic kernel profile:

`sha256:60b473acd3458abe23d0a095e1b3a1d81ce4e61cd517c9b7d244e5c5efa508a9`

Centre adapter profile:

`sha256:268d710e4b320e6eee9a674282a1f499832ac27e0d2135948a7dc28b89b49ef2`

Admissibility adapter profile:

`sha256:f706969920fe3a01ffc79188dfba4c3fb897c22e94c02b81805083a31ee516f1`

Portability profile:

`sha256:30aaec976f2b38bfe0b1d8e6f201ed941b0432af515b477293d926d60f9ed51f`

Vector set:

`secport_a392c25a59ae68f6505b183e26f96af64f842e30745df9e7ae9f68d895f99cd4`

Vector corpus:

`sha256:720b5c795efef23489ed800fd0b7bb3d1ec2b2e6e20fe0ec9c0f2aeca54c5ae7`

Portability certificate:

`sha256:660af7631ca9e7cc630ec3695c0cb78ead5fa43f62e09be6e4555361b3a8eb21`
