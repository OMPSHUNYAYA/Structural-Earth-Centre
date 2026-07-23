# Structural Earth Centre — FAQ

## Release v0.5.0

### 1. What problem does SEC address?

SEC addresses a structural problem: a centre claim can be underdetermined even when a coordinate-producing algorithm is available.

The system asks:

`what declared structure makes this particular centre claim admissible?`

It separates the carrier, boundary, measure, metric, objective, frame, epoch, rules, and evidence rather than silently inheriting defaults.

### 2. Does SEC claim that centre definitions depend on those choices for the first time?

No.

Dependency-sensitive centre definitions and explicit reference structures are established ideas in mature mathematical and scientific practice. SEC's contribution is an executable claim-resolution architecture that combines explicit dependencies, bounded non-result states, structural differentials, stability envelopes, claim relations, resolution frontiers, certificates, and reproducible identities.

### 3. Is SEC a replacement for professional geodesy or other domain-specific centre methods?

No.

The Earth-centre question is a demonstration domain. SEC does not claim to replace mature domain-specific methods, reference systems, or measurement practice.

### 4. What is new in v0.5.0?

v0.5.0 adds a bounded Structural Portability Proof built around four shared generic primitives:

- `CLAIM_RELATION`;
- `RESULT_SPECTRUM`;
- `RESOLUTION_FRONTIER`;
- `RESOLUTION_CERTIFICATE`.

The same generic primitives are exercised through two distinct bounded domain adapters:

- an exact one-dimensional centre adapter;
- a synthetic admissibility adapter with `execution_authority = NONE`.

The portability audit tests matched structural semantics across the two domains, Python/JavaScript parity, generic-kernel/domain-adapter separation, certificate tamper sensitivity, and reconstruction of a portability certificate.

The earlier Structural Centre Differential, Centre Stability Envelope, Symmetry Certificate, Centre Resolution Certificate, Structural Claim Relation, Centre Spectrum, Resolution Frontier, same-dataset differential, and exact graph-centre demonstration remain part of the retained SEC architecture.

### 5. What is the generic structural kernel?

It is a bounded domain-neutral layer that operates on generic claim, result, dependency, repair, and certificate structures.

Its profile is:

`SEC-GENERIC-STRUCTURAL-KERNEL-1-D01`

The generic kernel does not contain centre mathematics or synthetic admissibility rules. Domain-specific resolution remains inside declared adapters.

### 6. What does the portability proof demonstrate?

Within the frozen two-domain corpus, the same generic structural primitives preserve matched relation, spectrum, frontier, and certificate semantics when the subject matter changes.

The claim is bounded:

`same generic structural primitives + different declared domain adapters -> matched generic structural semantics over the frozen portability corpus`

It is not a claim of universal portability across every possible domain.

### 7. Why use a synthetic admissibility domain?

It provides a non-centre subject matter without adding another external dataset or introducing uncontrolled operational authority.

The adapter resolves bounded synthetic outcomes from declared `eligibility_class` and `evidence_status` dependencies. Its results explicitly carry:

`execution_authority = NONE`

### 8. Does the generic kernel decide domain-specific subject matter?

No.

The separation contract states:

`generic structural semantics != domain adapter semantics`

The adapters resolve subject matter. The generic kernel compares claims, preserves result families, computes bounded repair frontiers, and binds resolution certificates.

### 9. What is a Structural Centre Differential?

It compares two declared claim structures and their results.

A controlled single dependency change can produce:

`SINGLE_DEPENDENCY_DIVERGENCE`

Multiple declared changes remain explicit as:

`MULTI_DEPENDENCY_DIVERGENCE`

The differential does not silently claim causal proof when several dependencies change.

### 10. What does CLAIM_DISTINCT_RESULT_EQUIVALENT mean?

Two structurally different claims can happen to produce the same result.

`same coordinate != same claim identity`

SEC preserves that distinction.

### 11. What is a Centre Stability Envelope?

It resolves an explicitly declared finite family of admissible centre results.

If every admitted result is identical, the envelope returns `RESOLVED_POINT`.

If multiple exact rational results are admitted, the current profile returns the smallest exact axis-aligned rational envelope containing those declared samples and reports `RESOLVED_REGION`.

### 12. Does RESOLVED_REGION describe all possible uncertainty between or beyond the samples?

No.

The current envelope is bounded to the explicitly declared finite perturbation family.

`finite declared family -> bounded sample envelope`

It makes no inference outside that family.

### 13. Is RESOLVED_REGION genuinely implemented?

Yes.

The structural innovation resolver, independent JavaScript reference, dedicated browser laboratory, frozen innovation vectors, and integrated laboratory implement and verify the state.

The frozen 38-vector exact core remains a separate profile family and does not need to emit every state supported elsewhere in SEC.

### 14. What is a Symmetry Certificate?

It records why uniqueness is admitted or refused.

`equivalent candidates + no admitted symmetry breaker -> UNIQUE_CENTRE_REFUSED`

The certificate is a witness about the declared symmetry structure. It does not prove a broader physical symmetry that was never supplied to the system.

### 15. What is a Centre Resolution Certificate?

It binds a claim to its bounded resolution structure.

The certificate can carry:

- claim identity;
- declared result identity;
- result material hash;
- result identity source;
- resolution state;
- resolution witness;
- symmetry certificate identity;
- stability envelope identity;
- evidence identity.

A certificate does not create authority beyond the claim scope recorded inside it.

### 16. Why are result_id and result_material_hash both present?

A result can already have a domain-specific identity derived under its own profile.

The certificate therefore preserves a supplied `result_id` while separately hashing the exact result material it was given.

`declared result identity != certificate view of result material`

Both remain explicit.

### 17. Why can the same exact dataset produce two different centre coordinates?

Because the declared measure can change what is being aggregated.

The demonstration keeps the exact dataset bytes and comparison family fixed while changing:

`SPHERICAL_SURFACE_AREA`

to:

`SPHERICAL_BOUNDARY_ARC_LENGTH`

The resulting coordinates differ, and the Structural Centre Differential identifies `measure` as the single declared changed dependency.

### 18. What are the two same-dataset results?

Area-vector centre:

`44.847286603, 28.41498761`

Boundary-vector centre:

`71.590921549, 66.736078802`

Angular separation:

`32.350594616 degrees`

### 19. Does this mean one result is more correct?

No.

They answer different declared centre questions. A centre claim must be evaluated relative to its profile and authority boundary.

### 20. What happens to malformed JSON or impossible geographic coordinates?

The real-land boundary applies input admission before centre resolution.

Malformed input and geographically inadmissible coordinates return `INPUT_REJECTED` with deterministic refusal material rather than being silently coerced into an ordinary centre result.

### 21. Why is the real-land identity quantized to 9 decimal places?

The real-land path uses floating-point transcendental operations. Identity-bearing structural fields are quantized before hashing so that meaningless low-order platform arithmetic differences do not become accidental identity authority.

The exact core and exact portability centre adapter use rational arithmetic and do not share this numerical path.

### 22. Does SEC claim raw floating-point intermediates are identical across all platforms?

No.

The identity contract applies to the declared quantized structural result, not to every raw intermediate value produced by a platform mathematics library.

### 23. What does 20/20 Earth Profile Validation mean if there are 14 Earth vectors?

It means 20 validation checks covering 14 bounded Earth vectors plus registry, linkage, identity, and comparison checks.

### 24. Why are there several audit counts?

Each audit has a separate boundary.

`38/38` — exact core conformance.

`20/20` — bounded Earth profile validation.

`7/7` — browser real-land evidence consistency.

`24/24` — structural innovation audit.

`13/13` — same-dataset profile differential.

`30/30` — advanced structural audit.

`132/132` — integrated centre laboratory combining the core, Earth, real-land, structural innovation, same-dataset differential, and advanced structural layers.

`40/40` — structural portability audit over the generic kernel and two bounded adapters.

`27/27` — Python/JavaScript structural portability parity.

The `132/132` integrated centre laboratory and `40/40` portability laboratory are separate verification boundaries.

### 25. What do the parity audits verify?

The parity audits compare independently implemented Python and JavaScript paths over frozen bounded corpora.

Current results include:

- core parity: `38/38 PASS`;
- structural innovation parity: `18/18 PASS`;
- advanced structural parity: `22/22 PASS`;
- structural portability parity: `27/27 PASS`.

Parity verifies agreement within the declared frozen boundary. It does not by itself establish universal correctness.

### 26. Is the evidence byte-reproducible?

The deterministic evidence objects used by the current verification paths omit timestamps. Regeneration from the same bounded inputs, profiles, and rules is therefore designed to reproduce the same canonical evidence identity.

### 27. Does ordinary verification require network access?

No.

The browser laboratories are self-contained, and the included Python verification paths use local files. The real-land resolver retains an optional reacquisition path, but ordinary repository verification does not require it.

### 28. Is any additional external dataset required for v0.5.0 portability?

No.

The same-dataset differential continues to use the included frozen land dataset. The new structural portability proof uses exact synthetic centre and admissibility cases, so it introduces no additional external dataset dependency.

### 29. What is the Structural Claim Relation?

It classifies how two declared claim structures relate independently of whether their computed results happen to be equal.

Current bounded relations include:

`CLAIM_EQUIVALENT`

`LEFT_REFINES_RIGHT`

`RIGHT_REFINES_LEFT`

`COMPATIBLE_OVERLAP`

`DECLARATION_CONFLICT`

`DISJOINT_DECLARATIONS`

### 30. What is the Centre Spectrum?

The Centre Spectrum preserves a family of centre claims without silently averaging structurally distinct results. It records claim identities, result identities, result-equivalence classes, and pairwise claim relations.

### 31. What is the Resolution Frontier?

It computes minimal repair sets only from explicitly declared repair options and a bounded admissibility contract.

It does not invent missing evidence or claim that the smallest structural repair is the best real-world decision.

### 32. Why retain the exact graph-centre demonstration if v0.5.0 has a broader portability proof?

They demonstrate different boundaries.

The graph example shows that centre resolution can operate over a non-geographical carrier while remaining a centre problem.

The v0.5.0 portability proof goes further by exercising the same generic structural primitives across a centre domain and a non-centre synthetic admissibility domain.

### 33. What is the strongest current SEC portability claim?

The strongest bounded claim is:

`the same declared generic claim-relation, result-spectrum, resolution-frontier, and certificate semantics reproduce across two bounded domain adapters under the frozen portability corpus`

The evidence includes `40/40 PASS` structural portability qualification and `27/27 PASS` Python/JavaScript parity.

### 34. What is not claimed?

SEC does not claim universal centre authority, comprehensive uncertainty quantification, replacement of mature scientific reference systems, automatic causal proof from arbitrary differentials, universal portability across all domains, production authority for the synthetic admissibility adapter, or third-party verification.
