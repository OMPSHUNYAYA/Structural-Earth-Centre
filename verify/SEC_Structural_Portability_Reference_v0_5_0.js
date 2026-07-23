(function(global){
  "use strict";

  const SYSTEM_VERSION="0.5.0";
  const PORTABILITY_PROFILE="SEC-STRUCTURAL-PORTABILITY-PROOF-1-D01";
  const GENERIC_KERNEL_PROFILE="SEC-GENERIC-STRUCTURAL-KERNEL-1-D01";
  const CENTRE_ADAPTER_PROFILE="SEC-PORTABILITY-ADAPTER-CENTRE-1-D01";
  const ADMISSIBILITY_ADAPTER_PROFILE="SEC-PORTABILITY-ADAPTER-ADMISSIBILITY-1-D01";
  const CLAIM_RELATION_SCHEMA="SEC-GENERIC-CLAIM-RELATION-1-D01";
  const RESULT_SPECTRUM_SCHEMA="SEC-GENERIC-RESULT-SPECTRUM-1-D01";
  const RESOLUTION_FRONTIER_SCHEMA="SEC-GENERIC-RESOLUTION-FRONTIER-1-D01";
  const RESOLUTION_CERTIFICATE_SCHEMA="SEC-GENERIC-RESOLUTION-CERTIFICATE-1-D01";
  const PORTABILITY_CERTIFICATE_SCHEMA="SEC-STRUCTURAL-PORTABILITY-CERTIFICATE-1-D01";
  const RESOLVED_STATE="RESOLVED";

  function clone(value){return JSON.parse(JSON.stringify(value));}
  function canonicalStringify(value){
    if(value===null)return "null";
    if(typeof value==="string"||typeof value==="number"||typeof value==="boolean")return JSON.stringify(value);
    if(Array.isArray(value))return "["+value.map(canonicalStringify).join(",")+"]";
    if(typeof value==="object"){
      const keys=Object.keys(value).sort();
      return "{"+keys.map(key=>JSON.stringify(key)+":"+canonicalStringify(value[key])).join(",")+"}";
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
    const data=new Uint8Array(paddedLen);data.set(bytes);data[bytes.length]=0x80;
    for(let i=0;i<8;i++)data[paddedLen-1-i]=Number((bitLen>>BigInt(8*i))&0xffn);
    const W=new Uint32Array(64);const rotr=(x,n)=>(x>>>n)|(x<<(32-n));
    for(let offset=0;offset<data.length;offset+=64){
      for(let i=0;i<16;i++){const j=offset+i*4;W[i]=((data[j]<<24)|(data[j+1]<<16)|(data[j+2]<<8)|data[j+3])>>>0;}
      for(let i=16;i<64;i++){const x=W[i-15],y=W[i-2];const s0=(rotr(x,7)^rotr(x,18)^(x>>>3))>>>0;const s1=(rotr(y,17)^rotr(y,19)^(y>>>10))>>>0;W[i]=(W[i-16]+s0+W[i-7]+s1)>>>0;}
      let [a,b,c,d,e,f,g,h]=H;
      for(let i=0;i<64;i++){
        const S1=(rotr(e,6)^rotr(e,11)^rotr(e,25))>>>0;const ch=((e&f)^((~e)&g))>>>0;
        const t1=(h+S1+ch+K[i]+W[i])>>>0;const S0=(rotr(a,2)^rotr(a,13)^rotr(a,22))>>>0;
        const maj=((a&b)^(a&c)^(b&c))>>>0;const t2=(S0+maj)>>>0;
        h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
      }
      H[0]=(H[0]+a)>>>0;H[1]=(H[1]+b)>>>0;H[2]=(H[2]+c)>>>0;H[3]=(H[3]+d)>>>0;
      H[4]=(H[4]+e)>>>0;H[5]=(H[5]+f)>>>0;H[6]=(H[6]+g)>>>0;H[7]=(H[7]+h)>>>0;
    }
    return Array.from(H).map(value=>value.toString(16).padStart(8,"0")).join("");
  }
  function structuralHash(value){return "sha256:"+sha256Hex(canonicalStringify(value));}
  function cmap(value){return JSON.parse(canonicalStringify(value||{}));}
  function compareCanonical(a,b){const x=canonicalStringify(a),y=canonicalStringify(b);return x<y?-1:x>y?1:0;}
  function omit(obj,key){const out=clone(obj);delete out[key];return out;}
  function verifySelfHash(obj,field){return obj[field]===structuralHash(omit(obj,field));}
  function isConflict(value){return Array.isArray(value)&&value.length>1;}
  function resolved(result){return result&&result.resolution_state===RESOLVED_STATE;}

  function genericClaimMaterial(claim){
    const dependencies=cmap(claim.dependencies||{});
    if(Object.keys(dependencies).length>256)throw new Error("DEPENDENCY_LIMIT_EXCEEDED");
    return {schema:"SEC-GENERIC-CLAIM-MATERIAL-1-D01",system_version:SYSTEM_VERSION,domain_id:claim.domain_id||"UNDECLARED",scope_id:claim.scope_id||"UNDECLARED",profile_id:claim.profile_id||"UNDECLARED",dependencies};
  }
  function genericClaimId(claim){return structuralHash(genericClaimMaterial(claim));}
  function genericResultId(result){return structuralHash(cmap(result));}
  function resultRelation(left,right){if(!resolved(left)||!resolved(right))return "UNRESOLVED_RESULT_RELATION";return canonicalStringify(cmap(left))===canonicalStringify(cmap(right))?"RESULT_EQUIVALENT":"RESULT_DIVERGENT";}

  function buildClaimRelation(left,right){
    const lm=genericClaimMaterial(left),rm=genericClaimMaterial(right),ld=lm.dependencies,rd=rm.dependencies;
    const lk=Object.keys(ld),rk=Object.keys(rd),shared=lk.filter(key=>rk.includes(key)).sort();
    const conflicts=shared.filter(key=>canonicalStringify(ld[key])!==canonicalStringify(rd[key]));
    const left_only=lk.filter(key=>!rk.includes(key)).sort(),right_only=rk.filter(key=>!lk.includes(key)).sort();
    const sameDomain=lm.domain_id===rm.domain_id;
    const sameScope=sameDomain&&lm.scope_id===rm.scope_id&&lm.profile_id===rm.profile_id;
    let relation;
    if(!sameDomain)relation="DISJOINT_DOMAINS";
    else if(conflicts.length)relation="DECLARATION_CONFLICT";
    else if(sameScope&&!left_only.length&&!right_only.length)relation="CLAIM_EQUIVALENT";
    else if(sameScope&&left_only.length&&!right_only.length)relation="LEFT_REFINES_RIGHT";
    else if(sameScope&&right_only.length&&!left_only.length)relation="RIGHT_REFINES_LEFT";
    else if(shared.length)relation="COMPATIBLE_OVERLAP";
    else relation="DISJOINT_DECLARATIONS";
    const body={schema:CLAIM_RELATION_SCHEMA,system_version:SYSTEM_VERSION,claim_relation:relation,result_relation:resultRelation(cmap(left.result||{}),cmap(right.result||{})),shared_dependencies:shared,conflicting_dependencies:conflicts,left_only_dependencies:left_only,right_only_dependencies:right_only,left_claim_id:structuralHash(lm),right_claim_id:structuralHash(rm)};
    return {...body,claim_relation_id:structuralHash(body)};
  }

  function buildResultSpectrum(claims){
    if((claims||[]).length>256){const body={schema:RESULT_SPECTRUM_SCHEMA,system_version:SYSTEM_VERSION,spectrum_state:"UNSUPPORTED",reason:"CLAIM_LIMIT_EXCEEDED"};return {...body,spectrum_id:structuralHash(body)};}
    const members=(claims||[]).map((claim,index)=>{
      const material=genericClaimMaterial(claim),result=cmap(claim.result||{});
      return {member_id:String(claim.member_id||`M${String(index+1).padStart(4,"0")}`),claim_id:structuralHash(material),result_id:structuralHash(result),resolution_state:result.resolution_state||"UNDECLARED",claim_material:material,result};
    }).sort((a,b)=>a.claim_id<b.claim_id?-1:a.claim_id>b.claim_id?1:a.result_id<b.result_id?-1:a.result_id>b.result_id?1:a.member_id<b.member_id?-1:a.member_id>b.member_id?1:0);
    let state;
    if(!members.length)state="INCOMPLETE";
    else{
      const resolvedMembers=members.filter(member=>member.resolution_state===RESOLVED_STATE);
      if(!resolvedMembers.length)state="UNRESOLVED_FAMILY";
      else if(resolvedMembers.length!==members.length)state="MIXED_RESOLUTION_FAMILY";
      else{
        const claimCount=new Set(members.map(member=>member.claim_id)).size,resultCount=new Set(members.map(member=>member.result_id)).size;
        if(claimCount===1&&resultCount===1)state="SINGLE_CLAIM_FAMILY";
        else if(resultCount===1)state="RESULT_CONVERGENT_CLAIM_DIVERSE";
        else state="RESULT_DIVERGENT_FAMILY";
      }
    }
    const body={schema:RESULT_SPECTRUM_SCHEMA,system_version:SYSTEM_VERSION,spectrum_state:state,member_count:members.length,resolved_member_count:members.filter(member=>member.resolution_state===RESOLVED_STATE).length,distinct_claim_count:new Set(members.map(member=>member.claim_id)).size,distinct_result_count:new Set(members.map(member=>member.result_id)).size,aggregation_policy:"NO_BLIND_AGGREGATION_OF_STRUCTURALLY_DISTINCT_RESULTS",members};
    return {...body,spectrum_id:structuralHash(body)};
  }

  function applyOperations(current,operations){
    const result=cmap(current);
    for(const operation of operations){
      const op=operation.op,key=String(operation.key||"");
      if(!key)throw new Error("REPAIR_KEY_REQUIRED");
      if(op==="SET")result[key]=clone(operation.value);
      else if(op==="REMOVE")delete result[key];
      else throw new Error("UNSUPPORTED_REPAIR_OPERATION");
    }
    return cmap(result);
  }
  function combinations(items,size){
    const out=[];
    function walk(start,chosen){if(chosen.length===size){out.push(chosen.slice());return;}for(let i=start;i<items.length;i++){chosen.push(items[i]);walk(i+1,chosen);chosen.pop();}}
    walk(0,[]);return out;
  }

  function buildResolutionFrontier(currentDependencies,{repairOptions,resolver,domainId,adapterProfileId}){
    if((repairOptions||[]).length>16){const body={schema:RESOLUTION_FRONTIER_SCHEMA,system_version:SYSTEM_VERSION,frontier_state:"UNSUPPORTED",reason:"REPAIR_OPTION_LIMIT_EXCEEDED",domain_id:domainId,adapter_profile_id:adapterProfileId};return {...body,resolution_frontier_id:structuralHash(body)};}
    const current=cmap(currentDependencies),currentResult=cmap(resolver(current));
    if(resolved(currentResult)){
      const body={schema:RESOLUTION_FRONTIER_SCHEMA,system_version:SYSTEM_VERSION,frontier_state:"ALREADY_ADMISSIBLE",domain_id:domainId,adapter_profile_id:adapterProfileId,current_dependencies:current,current_result:currentResult,minimal_repair_size:0,minimal_repair_sets:[],repair_policy:"DECLARED_OPTIONS_ONLY"};
      return {...body,resolution_frontier_id:structuralHash(body)};
    }
    const options=(repairOptions||[]).map(cmap).sort(compareCanonical);
    let minimalSets=[],minimalSize=null;
    for(let size=1;size<=options.length;size++){
      for(const combo of combinations(options,size)){
        let repaired,result;
        try{repaired=applyOperations(current,combo);result=cmap(resolver(repaired));}catch(_err){continue;}
        if(resolved(result))minimalSets.push({operations:combo,resulting_dependencies:repaired,result});
      }
      if(minimalSets.length){minimalSize=size;break;}
    }
    let state;if(!minimalSets.length)state="NO_ADMISSIBLE_FRONTIER";else if(minimalSets.length===1)state="UNIQUE_MINIMAL_FRONTIER";else state="MULTIPLE_MINIMAL_FRONTIERS";
    minimalSets.sort(compareCanonical);
    const body={schema:RESOLUTION_FRONTIER_SCHEMA,system_version:SYSTEM_VERSION,frontier_state:state,domain_id:domainId,adapter_profile_id:adapterProfileId,current_dependencies:current,current_result:currentResult,minimal_repair_size:minimalSize,minimal_repair_sets:minimalSets,declared_repair_option_count:options.length,repair_policy:"DECLARED_OPTIONS_ONLY",invents_missing_evidence:false};
    return {...body,resolution_frontier_id:structuralHash(body)};
  }

  function buildResolutionCertificate(claim,result,{adapterProfileId,evidenceId}){
    const claimMaterial=genericClaimMaterial(claim),resultMaterial=cmap(result);
    const body={schema:RESOLUTION_CERTIFICATE_SCHEMA,system_version:SYSTEM_VERSION,generic_kernel_profile:GENERIC_KERNEL_PROFILE,adapter_profile_id:adapterProfileId,claim_id:structuralHash(claimMaterial),result_id:structuralHash(resultMaterial),claim_material:claimMaterial,result_material:resultMaterial,evidence_id:evidenceId||"NO_EXTERNAL_EVIDENCE_DECLARED"};
    return {...body,certificate_id:structuralHash(body)};
  }

  function absBig(value){return value<0n?-value:value;}
  function gcd(a,b){a=absBig(a);b=absBig(b);while(b!==0n){const t=a%b;a=b;b=t;}return a;}
  function rat(value){
    let n,d;
    if(typeof value==="bigint"){n=value;d=1n;}
    else if(typeof value==="number"&&Number.isInteger(value)){n=BigInt(value);d=1n;}
    else if(typeof value==="string"){
      if(value.includes("/")){const parts=value.split("/");n=BigInt(parts[0]);d=BigInt(parts[1]);}
      else{n=BigInt(value);d=1n;}
    }else if(value&&typeof value==="object"&&!Array.isArray(value)&&("n" in value)&&("d" in value)){n=BigInt(value.n);d=BigInt(value.d);}
    else throw new Error("UNSUPPORTED_RATIONAL");
    if(d===0n)throw new Error("ZERO_DENOMINATOR");if(d<0n){n=-n;d=-d;}if(n===0n)return {n:0n,d:1n};const g=gcd(n,d);return {n:n/g,d:d/g};
  }
  function addRat(a,b){const x=rat(a),y=rat(b);return rat({n:(x.n*y.d+y.n*x.d).toString(),d:(x.d*y.d).toString()});}
  function divRat(a,n){const x=rat(a);return rat({n:x.n.toString(),d:(x.d*BigInt(n)).toString()});}
  function ratJSON(value){const x=rat(value);return {n:x.n.toString(),d:x.d.toString()};}

  function resolveCentreAdapter(subject,dependencies,profileId="CENTRE_EXACT_MEAN_1D"){
    const deps=cmap(dependencies),required=["frame","measure"],conflicts=required.filter(key=>isConflict(deps[key]));
    if(conflicts.length)return {resolution_state:"CONFLICT",conflicting_dependencies:conflicts};
    const missing=required.filter(key=>!(key in deps));if(missing.length)return {resolution_state:"INCOMPLETE",missing_dependencies:missing};
    if(profileId!=="CENTRE_EXACT_MEAN_1D")return {resolution_state:"UNSUPPORTED",reason:"UNSUPPORTED_CENTRE_PROFILE"};
    if(!new Set(["UNIFORM_POINT_MASS","DECLARED_EQUAL_WEIGHTS"]).has(deps.measure))return {resolution_state:"UNSUPPORTED",reason:"UNSUPPORTED_CENTRE_MEASURE"};
    const points=subject.points||[];if(!Array.isArray(points)||!points.length||points.length>10000)return {resolution_state:"INCOMPLETE",reason:"NO_ADMITTED_POINTS"};
    let sum=rat(0);for(const point of points)sum=addRat(sum,rat(point));const centre=divRat(sum,points.length);
    return {resolution_state:RESOLVED_STATE,outcome:"CENTRE_POINT",value:[ratJSON(centre)]};
  }

  function resolveAdmissibilityAdapter(subject,dependencies,profileId="ADMISSIBILITY_STANDARD"){
    const deps=cmap(dependencies),required=["eligibility_class","evidence_status"],conflicts=required.filter(key=>isConflict(deps[key]));
    if(conflicts.length)return {resolution_state:"CONFLICT",conflicting_dependencies:conflicts};
    const missing=required.filter(key=>!(key in deps));if(missing.length)return {resolution_state:"INCOMPLETE",missing_dependencies:missing};
    if(profileId!=="ADMISSIBILITY_STANDARD")return {resolution_state:"UNSUPPORTED",reason:"UNSUPPORTED_ADMISSIBILITY_PROFILE"};
    if(!new Set(["VERIFIED","ATTESTED"]).has(deps.evidence_status))return {resolution_state:"ABSTAIN",reason:"EVIDENCE_STATUS_NOT_ADMITTED"};
    let outcome;if(deps.eligibility_class==="STANDARD")outcome="ADMITTED";else if(deps.eligibility_class==="BLOCKED")outcome="REFUSED";else return {resolution_state:"UNSUPPORTED",reason:"UNSUPPORTED_ELIGIBILITY_CLASS"};
    return {resolution_state:RESOLVED_STATE,outcome,decision_scope:"BOUNDED_SYNTHETIC_ADMISSIBILITY",execution_authority:"NONE"};
  }

  function resolveAdapter(domainId,subject,dependencies,profileId){
    if(domainId==="CENTRE")return resolveCentreAdapter(subject,dependencies,profileId);
    if(domainId==="ADMISSIBILITY")return resolveAdmissibilityAdapter(subject,dependencies,profileId);
    return {resolution_state:"UNSUPPORTED",reason:"UNKNOWN_DOMAIN_ADAPTER"};
  }
  function adapterProfileId(domainId){if(domainId==="CENTRE")return CENTRE_ADAPTER_PROFILE;if(domainId==="ADMISSIBILITY")return ADMISSIBILITY_ADAPTER_PROFILE;throw new Error("UNKNOWN_DOMAIN_ADAPTER");}

  function evaluateVector(vector){
    const operation=vector.operation,data=vector.input||{};
    if(operation==="CLAIM_RELATION")return buildClaimRelation(data.left,data.right);
    if(operation==="RESULT_SPECTRUM")return buildResultSpectrum(data.claims);
    if(operation==="RESOLUTION_FRONTIER"){
      const resolver=dependencies=>resolveAdapter(data.domain_id,data.subject,dependencies,data.profile_id);
      return buildResolutionFrontier(data.current_dependencies,{repairOptions:data.repair_options,resolver,domainId:data.domain_id,adapterProfileId:adapterProfileId(data.domain_id)});
    }
    if(operation==="RESOLUTION_CERTIFICATE")return buildResolutionCertificate(data.claim,data.result,{adapterProfileId:adapterProfileId(data.domain_id),evidenceId:data.evidence_id});
    if(operation==="DOMAIN_RESOLVE")return resolveAdapter(data.domain_id,data.subject,data.dependencies,data.profile_id);
    throw new Error("UNKNOWN_PORTABILITY_OPERATION");
  }

  function buildPortabilityCertificate(corpus,portabilityProfile,genericProfile,centreAdapterProfile,admissibilityAdapterProfile){
    const body={schema:PORTABILITY_CERTIFICATE_SCHEMA,system_version:SYSTEM_VERSION,portability_profile_id:PORTABILITY_PROFILE,portability_profile_hash:portabilityProfile.profile_hash,generic_kernel_profile_id:GENERIC_KERNEL_PROFILE,generic_kernel_profile_hash:genericProfile.profile_hash,adapter_profiles:[
      {domain_id:"ADMISSIBILITY",adapter_profile_id:ADMISSIBILITY_ADAPTER_PROFILE,adapter_profile_hash:admissibilityAdapterProfile.profile_hash},
      {domain_id:"CENTRE",adapter_profile_id:CENTRE_ADAPTER_PROFILE,adapter_profile_hash:centreAdapterProfile.profile_hash}
    ],vector_set_id:corpus.vector_set_id,vector_corpus_id:corpus.vector_corpus_id,proof_scope:"SHARED_GENERIC_PRIMITIVES_ACROSS_TWO_BOUNDED_DOMAIN_ADAPTERS"};
    return {...body,portability_certificate_id:structuralHash(body)};
  }

  function auditVectorCorpus(corpus,profiles,{verbose=false}={}){
    const checks=[];const add=(check_id,pass,detail)=>{checks.push({check_id,pass:!!pass,detail});if(verbose)console.log(pass?"PASS":"FAIL",check_id,detail);};
    const profileList=[profiles.portability,profiles.generic,profiles.centre,profiles.admissibility];
    add("PROFILE_IDENTITIES",profileList.every(profile=>verifySelfHash(profile,"profile_hash")),profileList.map(profile=>profile.profile_hash));
    add("CORPUS_ID",verifySelfHash(corpus,"vector_corpus_id"),corpus.vector_corpus_id);
    const actualSet="secport_"+sha256Hex(canonicalStringify((corpus.vectors||[]).map(vector=>vector.vector_hash)));
    add("VECTOR_SET_ID",actualSet===corpus.vector_set_id,actualSet);
    const vectorMap={};
    for(const vector of corpus.vectors||[]){
      vectorMap[vector.vector_id]=vector;const actual=evaluateVector(vector),pass=verifySelfHash(vector,"vector_hash")&&canonicalStringify(actual)===canonicalStringify(vector.expected);
      const detail=actual.claim_relation||actual.spectrum_state||actual.frontier_state||actual.resolution_state||"CERTIFICATE";add(vector.vector_id,pass,detail);
    }
    [["SEC-PORT-RC001","SEC-PORT-RA001"],["SEC-PORT-RC002","SEC-PORT-RA002"],["SEC-PORT-RC003","SEC-PORT-RA003"],["SEC-PORT-RC004","SEC-PORT-RA004"]].forEach((pair,index)=>{
      const left=evaluateVector(vectorMap[pair[0]]),right=evaluateVector(vectorMap[pair[1]]);add(`RELATION_SEMANTICS_DOMAIN_INVARIANT_${index+1}`,left.claim_relation===right.claim_relation,[left.claim_relation,right.claim_relation]);
    });
    [["SEC-PORT-SC001","SEC-PORT-SA001"],["SEC-PORT-SC002","SEC-PORT-SA002"],["SEC-PORT-SC003","SEC-PORT-SA003"]].forEach((pair,index)=>{
      const left=evaluateVector(vectorMap[pair[0]]),right=evaluateVector(vectorMap[pair[1]]);add(`SPECTRUM_SEMANTICS_DOMAIN_INVARIANT_${index+1}`,left.spectrum_state===right.spectrum_state,[left.spectrum_state,right.spectrum_state]);
    });
    [["SEC-PORT-FC001","SEC-PORT-FA001"],["SEC-PORT-FC002","SEC-PORT-FA002"],["SEC-PORT-FC003","SEC-PORT-FA003"]].forEach((pair,index)=>{
      const left=evaluateVector(vectorMap[pair[0]]),right=evaluateVector(vectorMap[pair[1]]);add(`FRONTIER_SEMANTICS_DOMAIN_INVARIANT_${index+1}`,left.frontier_state===right.frontier_state&&left.minimal_repair_size===right.minimal_repair_size,[left.frontier_state,right.frontier_state,left.minimal_repair_size,right.minimal_repair_size]);
    });
    const certificateVector=vectorMap["SEC-PORT-CA001"],certificate=evaluateVector(certificateVector),tamperedInput=clone(certificateVector.input);tamperedInput.result.outcome="REFUSED";const tampered=evaluateVector({...certificateVector,input:tamperedInput});
    add("CERTIFICATE_TAMPER_SENSITIVITY",certificate.certificate_id!==tampered.certificate_id,tampered.certificate_id);
    const genericOps=new Set(profiles.generic.generic_operations||[]),adapterOps=new Set([...(profiles.centre.domain_operations||[]),...(profiles.admissibility.domain_operations||[])]);
    add("GENERIC_KERNEL_ADAPTER_SEPARATION",canonicalStringify(Array.from(genericOps).sort())===canonicalStringify(["CLAIM_RELATION","RESOLUTION_CERTIFICATE","RESOLUTION_FRONTIER","RESULT_SPECTRUM"])&&adapterOps.has("DOMAIN_RESOLVE")&&!genericOps.has("CENTRE_EXACT_MEAN")&&!genericOps.has("SYNTHETIC_ADMISSIBILITY"),Array.from(genericOps).sort());
    const portabilityCertificate=buildPortabilityCertificate(corpus,profiles.portability,profiles.generic,profiles.centre,profiles.admissibility),certificateBody=omit(portabilityCertificate,"portability_certificate_id");
    add("PORTABILITY_CERTIFICATE_RECONSTRUCTS",structuralHash(certificateBody)===portabilityCertificate.portability_certificate_id,portabilityCertificate.portability_certificate_id);
    const passed=checks.filter(check=>check.pass).length,total=checks.length;
    const core={schema:"SEC-STRUCTURAL-PORTABILITY-AUDIT-1-D01",system_version:SYSTEM_VERSION,status:passed===total?"PASS":"FAIL",passed,total,portability_profile_id:PORTABILITY_PROFILE,generic_kernel_profile_id:GENERIC_KERNEL_PROFILE,vector_set_id:corpus.vector_set_id,vector_corpus_id:corpus.vector_corpus_id,portability_certificate:portabilityCertificate,checks};
    return {...core,evidence_id:structuralHash(core)};
  }

  const api={SYSTEM_VERSION,PORTABILITY_PROFILE,GENERIC_KERNEL_PROFILE,CENTRE_ADAPTER_PROFILE,ADMISSIBILITY_ADAPTER_PROFILE,canonicalStringify,structuralHash,genericClaimMaterial,genericClaimId,genericResultId,buildClaimRelation,buildResultSpectrum,buildResolutionFrontier,buildResolutionCertificate,resolveCentreAdapter,resolveAdmissibilityAdapter,resolveAdapter,evaluateVector,buildPortabilityCertificate,auditVectorCorpus};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  global.SEC_PORTABILITY_CORE=api;
})(typeof globalThis!=="undefined"?globalThis:this);
