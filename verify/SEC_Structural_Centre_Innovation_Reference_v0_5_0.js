(function(global){
  "use strict";
  const SYSTEM_VERSION="0.5.0";
  const INNOVATION_PROFILE="SEC-STRUCTURAL-CENTRE-INNOVATION-1-D01";
  const ENVELOPE_PROFILE="SEC-CENTRE-STABILITY-ENVELOPE-1-D01";
  const DIFFERENTIAL_PROFILE="SEC-STRUCTURAL-CENTRE-DIFFERENTIAL-1-D01";
  const SYMMETRY_PROFILE="SEC-SYMMETRY-CERTIFICATE-1-D01";
  const CERTIFICATE_PROFILE="SEC-CENTRE-RESOLUTION-CERTIFICATE-3-D01";
  const CLAIM_PROFILE="SEC-CENTRE-CLAIM-IDENTITY-1-D01";
  const RESOLVED_STATES=new Set(["RESOLVED_POINT","RESOLVED_REGION","MULTI_CENTRE"]);

  function clone(x){return JSON.parse(JSON.stringify(x));}
  function canonicalStringify(value){
    if(value===null)return "null";
    if(typeof value==="string"||typeof value==="number"||typeof value==="boolean")return JSON.stringify(value);
    if(Array.isArray(value))return "["+value.map(canonicalStringify).join(",")+"]";
    if(typeof value==="object"){
      const keys=Object.keys(value).sort();
      return "{"+keys.map(k=>JSON.stringify(k)+":"+canonicalStringify(value[k])).join(",")+"}";
    }
    throw new TypeError("Unsupported canonical value type");
  }
  function utf8Bytes(text){
    if(typeof TextEncoder!=="undefined")return new TextEncoder().encode(text);
    return Uint8Array.from(Buffer.from(text,"utf8"));
  }
  function sha256Hex(text){
    const bytes=utf8Bytes(text);
    const K=new Uint32Array([
      0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
      0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
      0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
      0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
      0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
      0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
      0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
      0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    ]);
    const H=new Uint32Array([0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]);
    const bitLen=BigInt(bytes.length)*8n;
    const paddedLen=Math.ceil((bytes.length+9)/64)*64;
    const data=new Uint8Array(paddedLen); data.set(bytes); data[bytes.length]=0x80;
    for(let i=0;i<8;i++)data[paddedLen-1-i]=Number((bitLen>>BigInt(8*i))&0xffn);
    const W=new Uint32Array(64); const rotr=(x,n)=>(x>>>n)|(x<<(32-n));
    for(let offset=0;offset<data.length;offset+=64){
      for(let i=0;i<16;i++){const j=offset+i*4;W[i]=((data[j]<<24)|(data[j+1]<<16)|(data[j+2]<<8)|data[j+3])>>>0;}
      for(let i=16;i<64;i++){const x=W[i-15],y=W[i-2];const s0=(rotr(x,7)^rotr(x,18)^(x>>>3))>>>0;const s1=(rotr(y,17)^rotr(y,19)^(y>>>10))>>>0;W[i]=(W[i-16]+s0+W[i-7]+s1)>>>0;}
      let [a,b,c,d,e,f,g,h]=H;
      for(let i=0;i<64;i++){const S1=(rotr(e,6)^rotr(e,11)^rotr(e,25))>>>0;const ch=((e&f)^((~e)&g))>>>0;const t1=(h+S1+ch+K[i]+W[i])>>>0;const S0=(rotr(a,2)^rotr(a,13)^rotr(a,22))>>>0;const maj=((a&b)^(a&c)^(b&c))>>>0;const t2=(S0+maj)>>>0;h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;}
      H[0]=(H[0]+a)>>>0;H[1]=(H[1]+b)>>>0;H[2]=(H[2]+c)>>>0;H[3]=(H[3]+d)>>>0;H[4]=(H[4]+e)>>>0;H[5]=(H[5]+f)>>>0;H[6]=(H[6]+g)>>>0;H[7]=(H[7]+h)>>>0;
    }
    return Array.from(H).map(x=>x.toString(16).padStart(8,"0")).join("");
  }
  function structuralHash(value){return "sha256:"+sha256Hex(canonicalStringify(value));}

  function absBig(x){return x<0n?-x:x;}
  function gcd(a,b){a=absBig(a);b=absBig(b);while(b!==0n){const t=a%b;a=b;b=t;}return a;}
  function rat(value){
    let n,d;
    if(typeof value==="bigint"){n=value;d=1n;}
    else if(typeof value==="number"&&Number.isInteger(value)){n=BigInt(value);d=1n;}
    else if(typeof value==="string"){
      if(value.includes("/")){const parts=value.split("/");n=BigInt(parts[0]);d=BigInt(parts[1]);}
      else {n=BigInt(value);d=1n;}
    }
    else if(value&&typeof value==="object"&&!Array.isArray(value)&&("n" in value)&&("d" in value)){n=BigInt(value.n);d=BigInt(value.d);}
    else if(Array.isArray(value)&&value.length===2){n=BigInt(value[0]);d=BigInt(value[1]);}
    else throw new Error("UNSUPPORTED_RATIONAL");
    if(d===0n)throw new Error("ZERO_DENOMINATOR"); if(d<0n){n=-n;d=-d;} if(n===0n)return {n:0n,d:1n}; const g=gcd(n,d);return {n:n/g,d:d/g};
  }
  function ratJSON(v){const x=rat(v);return {n:x.n.toString(),d:x.d.toString()};}
  function cmpRat(a,b){const x=rat(a),y=rat(b);const z=x.n*y.d-y.n*x.d;return z<0n?-1:z>0n?1:0;}
  function canonicalPoint(p){if(!Array.isArray(p)||p.length<1||p.length>16)throw new Error("POINT_DIMENSION_OUT_OF_RANGE");return p.map(ratJSON);}
  function pointKey(p){return canonicalStringify(canonicalPoint(p));}
  function canonicalDependencies(d){const obj=clone(d||{});return JSON.parse(canonicalStringify(obj));}

  function claimIdentityMaterial(claim){return {schema:CLAIM_PROFILE,system_version:SYSTEM_VERSION,carrier_id:claim.carrier_id||"UNDECLARED",centre_profile_id:claim.centre_profile_id||"UNDECLARED",dependency_fingerprint_id:claim.dependency_fingerprint_id||"UNDECLARED",authority_scope:claim.authority_scope||"BOUNDED_CLAIM_ONLY",claim_kind:claim.claim_kind||"CENTRE_CLAIM"};}
  function claimId(claim){return structuralHash(claimIdentityMaterial(claim));}

  function resolveStabilityEnvelope(samples,perturbationFamily){
    const perturbation=clone(perturbationFamily||{family:"DECLARED_FINITE_FAMILY"});
    const perturbation_family_id=structuralHash({schema:"SEC-PERTURBATION-FAMILY-1-D01",system_version:SYSTEM_VERSION,definition:perturbation});
    let normalized=[]; let dims=new Set();
    try{
      if(!Array.isArray(samples)||samples.length>10000)throw new Error("SAMPLE_LIMIT_EXCEEDED");
      normalized=samples.map((s,i)=>{if(!s||typeof s!=="object"||!("point" in s))throw new Error("MALFORMED_STABILITY_SAMPLE");const point=canonicalPoint(s.point);dims.add(point.length);return {sample_id:String(s.sample_id||`S${String(i+1).padStart(4,"0")}`),point};});
      normalized.sort((a,b)=>pointKey(a.point).localeCompare(pointKey(b.point))||a.sample_id.localeCompare(b.sample_id));
    }catch(err){const body={schema:ENVELOPE_PROFILE,system_version:SYSTEM_VERSION,resolution_state:"UNSUPPORTED",reason:String(err.message||err),perturbation_family_id};return {...body,stability_envelope_id:structuralHash(body)};}
    if(normalized.length===0){const body={schema:ENVELOPE_PROFILE,system_version:SYSTEM_VERSION,resolution_state:"INCOMPLETE",reason:"NO_ADMITTED_PERTURBATION_RESULTS",perturbation_family_id,sample_count:0};return {...body,stability_envelope_id:structuralHash(body)};}
    if(dims.size!==1){const body={schema:ENVELOPE_PROFILE,system_version:SYSTEM_VERSION,resolution_state:"CONFLICT",reason:"PERTURBATION_RESULT_DIMENSION_MISMATCH",perturbation_family_id,sample_count:normalized.length};return {...body,stability_envelope_id:structuralHash(body)};}
    const byKey=new Map();for(const s of normalized)byKey.set(pointKey(s.point),s.point);const unique=Array.from(byKey.entries()).sort((a,b)=>a[0].localeCompare(b[0])).map(x=>x[1]);
    if(unique.length===1){const body={schema:ENVELOPE_PROFILE,system_version:SYSTEM_VERSION,resolution_state:"RESOLVED_POINT",centre_type:"POINT",centre_value:unique[0],perturbation_family_id,sample_count:normalized.length,unique_point_count:1,witness:{all_admitted_samples_coincide:true,region_required:false}};return {...body,stability_envelope_id:structuralHash(body)};}
    const dimension=unique[0].length,lower=[],upper=[];
    for(let axis=0;axis<dimension;axis++){let lo=unique[0][axis],hi=unique[0][axis];for(const p of unique){if(cmpRat(p[axis],lo)<0)lo=p[axis];if(cmpRat(p[axis],hi)>0)hi=p[axis];}lower.push(ratJSON(lo));upper.push(ratJSON(hi));}
    const region={region_type:"AXIS_ALIGNED_EXACT_RATIONAL_ENVELOPE",dimension,lower_bound:lower,upper_bound:upper};
    const body={schema:ENVELOPE_PROFILE,system_version:SYSTEM_VERSION,resolution_state:"RESOLVED_REGION",centre_type:"REGION",centre_region:region,region_id:structuralHash(region),perturbation_family_id,sample_count:normalized.length,unique_point_count:unique.length,witness:{all_admitted_samples_inside:true,minimal_axis_aligned_bounds_over_declared_samples:true,inference_outside_declared_family:false}};
    return {...body,stability_envelope_id:structuralHash(body)};
  }
  function pointInRegion(point,region){const p=canonicalPoint(point),lo=region.lower_bound||[],hi=region.upper_bound||[];if(p.length!==lo.length||p.length!==hi.length)return false;return p.every((v,i)=>cmpRat(v,lo[i])>=0&&cmpRat(v,hi[i])<=0);}

  function buildSymmetryCertificate(candidates,equivalenceClass,symmetryBreaker){
    const cc=Array.from(new Set((candidates||[]).map(String))).sort(),eq=Array.from(new Set((equivalenceClass||[]).map(String))).sort();const br=symmetryBreaker===undefined||symmetryBreaker===null?null:String(symmetryBreaker);let state,reason;
    if(eq.length===0){state="INCOMPLETE";reason="NO_DECLARED_EQUIVALENCE_CLASS";}else if(br!==null&&!eq.includes(br)){state="CONFLICT";reason="SYMMETRY_BREAKER_OUTSIDE_EQUIVALENCE_CLASS";}else if(br!==null){state="UNIQUE_CENTRE_ADMITTED";reason="DECLARED_SYMMETRY_BREAKER_SELECTS_MEMBER";}else if(eq.length>1){state="UNIQUE_CENTRE_REFUSED";reason="NO_ADMITTED_SYMMETRY_BREAKER";}else{state="UNIQUE_CENTRE_ADMITTED";reason="EQUIVALENCE_CLASS_HAS_SINGLE_MEMBER";}
    const body={schema:SYMMETRY_PROFILE,system_version:SYSTEM_VERSION,symmetry_state:state,reason,candidates:cc,equivalence_class:eq,symmetry_breaker:br};return {...body,symmetry_certificate_id:structuralHash(body)};
  }
  function isResolved(r){return RESOLVED_STATES.has(r&&r.resolution_state);}
  function buildStructuralDifferential(left,right){
    const ld=canonicalDependencies(left.dependencies||{}),rd=canonicalDependencies(right.dependencies||{});const keys=Array.from(new Set([...Object.keys(ld),...Object.keys(rd)])).sort();let changed=keys.filter(k=>canonicalStringify(ld[k])!==canonicalStringify(rd[k]));if(left.centre_profile_id!==right.centre_profile_id)changed=["centre_profile_id",...changed];
    const lr=clone(left.result||{}),rr=clone(right.result||{}),left_result_id=structuralHash(lr),right_result_id=structuralHash(rr),equiv=canonicalStringify(lr)===canonicalStringify(rr);
    const lc={carrier_id:left.carrier_id||"UNDECLARED",centre_profile_id:left.centre_profile_id||"UNDECLARED",dependency_fingerprint_id:structuralHash(ld),authority_scope:left.authority_scope||"BOUNDED_CLAIM_ONLY"};
    const rc={carrier_id:right.carrier_id||"UNDECLARED",centre_profile_id:right.centre_profile_id||"UNDECLARED",dependency_fingerprint_id:structuralHash(rd),authority_scope:right.authority_scope||"BOUNDED_CLAIM_ONLY"};
    let state;if(!isResolved(lr)||!isResolved(rr))state="UNRESOLVED_COMPARISON";else if(changed.length===0&&equiv)state="NO_STRUCTURAL_DIFFERENCE";else if(changed.length>0&&equiv)state="CLAIM_DISTINCT_RESULT_EQUIVALENT";else if(changed.length===1)state="SINGLE_DEPENDENCY_DIVERGENCE";else state="MULTI_DEPENDENCY_DIVERGENCE";
    const body={schema:DIFFERENTIAL_PROFILE,system_version:SYSTEM_VERSION,differential_state:state,left_claim_id:claimId(lc),right_claim_id:claimId(rc),left_result_id,right_result_id,result_equivalent:equiv,changed_dependencies:changed,changed_dependency_count:changed.length,interpretation:changed.length===1?"CONTROLLED_SINGLE_DECLARED_DIFFERENCE":"MULTIPLE_OR_NO_DECLARED_DIFFERENCES"};return {...body,differential_id:structuralHash(body)};
  }
  function buildResolutionCertificate(claim,result,options){options=options||{};const cm=claimIdentityMaterial(claim),r=clone(result),result_material_hash=structuralHash(r),hasDeclared=options.declared_result_id!==undefined&&options.declared_result_id!==null,result_id=hasDeclared?String(options.declared_result_id):result_material_hash,w=clone(options.resolution_witness||{});if(!("state_is_explicit" in w))w.state_is_explicit=("resolution_state" in r);if(!("resolved_state" in w))w.resolved_state=RESOLVED_STATES.has(r.resolution_state);const body={schema:CERTIFICATE_PROFILE,system_version:SYSTEM_VERSION,claim_id:structuralHash(cm),claim_material:cm,result_id,result_material_hash,result_id_source:hasDeclared?"DECLARED_RESULT_ID":"STRUCTURAL_MATERIAL_HASH",resolution_state:r.resolution_state||"UNDECLARED",resolution_witness:w,authority_scope:cm.authority_scope};if(options.symmetry_certificate)body.symmetry_certificate_id=options.symmetry_certificate.symmetry_certificate_id;if(options.stability_envelope)body.stability_envelope_id=options.stability_envelope.stability_envelope_id;if(options.evidence_id)body.evidence_id=options.evidence_id;return {...body,certificate_id:structuralHash(body)};}
  function evaluateVector(v){const p=v.input||{};switch(v.operation){case "STABILITY_ENVELOPE":return resolveStabilityEnvelope(p.samples||[],p.perturbation_family);case "STRUCTURAL_DIFFERENTIAL":return buildStructuralDifferential(p.left,p.right);case "SYMMETRY_CERTIFICATE":return buildSymmetryCertificate(p.candidates||[],p.equivalence_class||[],p.symmetry_breaker);case "RESOLUTION_CERTIFICATE":return buildResolutionCertificate(p.claim,p.result,{resolution_witness:p.resolution_witness,symmetry_certificate:p.symmetry_certificate,stability_envelope:p.stability_envelope,evidence_id:p.evidence_id,declared_result_id:p.declared_result_id});default:throw new Error("UNKNOWN_OPERATION:"+v.operation);}}

  const api={SYSTEM_VERSION,INNOVATION_PROFILE,canonicalStringify,structuralHash,resolveStabilityEnvelope,pointInRegion,buildSymmetryCertificate,buildStructuralDifferential,buildResolutionCertificate,evaluateVector,claimId};
  global.SEC_INNOVATION_CORE=api;
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof globalThis!=="undefined"?globalThis:this);
