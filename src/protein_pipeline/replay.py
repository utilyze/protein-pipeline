"""Read-only reproducibility audit of a privately supplied NVIDIA response archive.

No inference or network; no source data modified; never prints candidate sequences.
Not a provider-authenticity attestation, structural certification, or binding test.
Dependencies: gemmi and numpy. All outputs are aggregate, public-safe counts.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, zipfile
from pathlib import Path
import numpy as np
import gemmi

PEPTIDE = "VVVGADGVGK"     # published challenge target, not a private binder sequence
AA = set("ACDEFGHIKLMNPQRSTVWY")
MAX_ZIP_MEMBER=30*1024*1024
MAX_ZIP_TOTAL=190*1024*1024
MAX_ZIP_ENTRIES=120

def digest(blob:bytes)->str:
    return hashlib.sha256(blob).hexdigest()

def safe_members(z:zipfile.ZipFile):
    entries=z.infolist()
    if len(entries)>MAX_ZIP_ENTRIES or sum(x.file_size for x in entries)>MAX_ZIP_TOTAL:
        raise ValueError('Archive exceeds bounded total size/count')
    seen=set()
    for entry in entries:
        name=entry.filename
        if (entry.file_size>MAX_ZIP_MEMBER or name.startswith('/')
                or '\\' in name or '..' in Path(name).parts or not name):
            raise ValueError('Disallowed archive member')
        if name in seen:
            raise ValueError('Duplicate archive member name')
        seen.add(name)
        # Only regular files and directories are expected. Do not interpret
        # symlink/device archive entries as trusted evidence containers.
        mode=(entry.external_attr >> 16) & 0o170000
        if mode not in (0,0o100000,0o040000):
            raise ValueError('Nonregular archive member')
        if entry.flag_bits & 1:
            raise ValueError('Encrypted archive entry not supported')
    if z.testzip() is not None:
        raise ValueError('Corrupted ZIP member')

def inspect_sequence(seq:str)->bool:
    return isinstance(seq,str) and 70 <= len(seq)<=100 and set(seq)<=AA

def inspect_structure(cif_text:str):
    st=gemmi.make_structure_from_block(gemmi.cif.read_string(cif_text).sole_block())
    if len(st)!=1: raise ValueError("Expected exactly one coordinate model")
    chains={}
    groups={}
    for ch in st[0]:
        residues=[]; atoms=[]
        for res in ch:
            code=gemmi.find_tabulated_residue(res.name).one_letter_code
            if len(res)>0 and code in AA:
                residues.append(code)
                for at in res:
                    if at.element.name.upper() not in ("H","D"):
                        vec=np.array([at.pos.x,at.pos.y,at.pos.z],dtype=float)
                        if not np.isfinite(vec).all(): raise ValueError("Nonfinite coordinate")
                        atoms.append((res.seqid.num,at.name,vec))
        if residues:
            if ch.name in chains: raise ValueError("Duplicate chain name")
            chains[ch.name]="".join(residues)
            groups[ch.name]=atoms
    if set(chains)!={"A","B","C","D"}: raise ValueError("Missing or extra target/binder chain")
    return chains,groups

def source_target_sequences(source_cif:str):
    st=gemmi.make_structure_from_block(gemmi.cif.read_string(source_cif).sole_block())
    if len(st)!=1: raise ValueError("Invalid source target model")
    out={}
    for ch in st[0]:
        residues=[]
        for res in ch:
            code=gemmi.find_tabulated_residue(res.name).one_letter_code
            if len(res)>0 and code in AA:residues.append(code)
        if residues:out[ch.name]="".join(residues)
    if set(out)!={"A","B","C"} or len(out["A"])!=276 or len(out["B"])!=99 or out["C"]!=PEPTIDE:
        raise ValueError("Conditioned public target has unexpected chains")
    return out

def validate_design(design:dict,reference:dict):
    if not isinstance(design,dict): raise ValueError("Malformed design record")
    struct=design.get("structure")
    if not isinstance(struct,dict) or struct.get("format") not in ("cif","mmcif") or not isinstance(struct.get("content"),str):
        raise ValueError("Missing molecular structure")
    chains,groups=inspect_structure(struct["content"])
    binder=chains["D"]
    full="".join(chains[k] for k in ("A","B","C","D"))
    if design.get("sequence") not in (binder,full): raise ValueError("Model sequence-structure mismatch")
    good=all(chains[k]==reference[k] for k in ("A","B","C"))
    if not inspect_sequence(binder): raise ValueError("Invalid binder residues or length")
    return {"target_preserved":good,"binder_sha256":digest(binder.encode()),
            "structure_sha256":digest(struct["content"].encode()),"groups":groups,"length":len(binder)}

def atom_distances(d_atoms, t_atoms):
    if not d_atoms or not t_atoms: return math.inf,0,0
    d=np.array([a[2] for a in d_atoms]);t=np.array([a[2] for a in t_atoms]);
    distances=np.linalg.norm(d[:,None,:]-t[None,:,:],axis=2)
    return float(np.min(distances)),int(np.sum(distances<2.5)),int(np.sum(distances<=5.0))

def geometry_metrics(groups):
    binder=groups["D"]
    out={}
    for ch in ("A","B","C"):
        min_d,clashes,pairs=atom_distances(binder,groups[ch])
        out[ch]={"min_A":round(min_d,3),"pairs_lt_2p5A":clashes,"pairs_lte_5A":pairs}
    pos6=[a for a in groups["C"] if a[0]==6]
    backbone=[a for a in pos6 if a[1] in {"N","CA","C","O"}]
    sidechain=[a for a in pos6 if a[1] in {"CB","CG","OD1","OD2"}]
    if not backbone or not sidechain: raise ValueError("Expected mutated Asp6 atom groups")
    for k,atoms in (("d6_backbone",backbone),("d6_sidechain",sidechain)):
        min_d,_,pairs=atom_distances(binder,atoms)
        out[k]={"min_A":round(min_d,3),"pairs_lte_5A":pairs}
    out["any_clash"] = any(out[ch]["pairs_lt_2p5A"]>0 for ch in ("A","B","C"))
    out["hla_or_peptide_clash"] = any(out[ch]["pairs_lt_2p5A"]>0 for ch in ("A","C"))
    return out

def verify_provider(obj):
    if not isinstance(obj,dict) or obj.get("task")!="generation": raise ValueError("Not a generation response")
    model=obj.get("model")
    if not isinstance(model,dict) or "rfd4" not in str(model.get("model_name","")).lower():
        raise ValueError("Unexpected model identity")
    if not isinstance(obj.get("designs"),list) or not obj["designs"]:
        raise ValueError("No designs")
    # Request ID/model name are metadata, not cryptographic proof of provider origin.
    return obj["designs"]

def inspect_archive(path:Path, include_private_audit:bool=False):
    with zipfile.ZipFile(path) as outer:
        safe_members(outer)
        names=outer.namelist(); archive_names=sorted(x for x in names if x.startswith("original_provider_archives/") and x.endswith(".zip"))
        if not archive_names:raise ValueError("Original response archives absent")
        entries=[]
        reference_digests=set()
        for name in archive_names:
            with zipfile.ZipFile(io.BytesIO(outer.read(name))) as inner:
                safe_members(inner)
                if "original_provider_response.json" not in inner.namelist():raise ValueError("Missing original response")
                raw=inner.read("original_provider_response.json")
                reference=source_target_sequences(inner.read("PUBLIC_7OW6_conditioned.cif").decode("utf-8"))
                reference_digests.add(tuple(digest(reference[k].encode()) for k in ("A","B","C")))
                for index,design in enumerate(verify_provider(json.loads(raw)),1):
                    r=validate_design(design,reference)
                    r["archive"]=Path(name).name;r["index"]=index
                    if r["target_preserved"]:r["geometry"]=geometry_metrics(r["groups"])
                    del r["groups"]
                    entries.append(r)
        if len(reference_digests)!=1:raise ValueError("Original conditioned source chain sequences differ among the seven response archives")
        count_valid=sum(x["target_preserved"] for x in entries)
        valid=[x for x in entries if x["target_preserved"]]
        with zipfile.ZipFile(path) as outer2:
            manifest=json.loads(outer2.read("review/KRAS_DRAFT_20_REVIEW_MANIFEST.json"))
            csv_raw=outer2.read("review/KRAS_DRAFT_20_NOT_SUBMISSION_READY.csv")
            rows=list(csv.DictReader(io.StringIO(csv_raw.decode())))
        if len({v["binder_sha256"] for v in valid})!=len(valid):raise ValueError("Duplicate target-preserving binder")
        seen=set();chosen=[]
        for row in rows:
            if row["name"] in seen:raise ValueError("Duplicate shortlist name")
            seen.add(row["name"])
            sha=digest(row["sequence"].encode())
            matches=[r for r in valid if r["binder_sha256"]==sha]
            if len(matches)!=1:raise ValueError("Shortlist design not in exactly one original response")
            entry=matches[0]
            records=[m for m in manifest["shortlist"] if m["candidate_id"]==row["name"]]
            if len(records)!=1 or records[0]["structure_sha256"]!=entry["structure_sha256"]:
                raise ValueError("Manifest structure fingerprint mismatch")
            chosen.append(entry)
        if len(chosen)!=20:raise ValueError("Expected 20 shortlisted rows")
        out={
            "source_archive_sha256":digest(path.read_bytes()),"provider_response_files":len(archive_names),
            "provider_output_records":len(entries),"target_preserving_unique":count_valid,
            "target_altered":len(entries)-count_valid,"shortlist_count":len(chosen),
            "shortlist_source_match":len(chosen),
            "shortlist_lengths_min_max":[min(x["length"] for x in chosen),max(x["length"] for x in chosen)],
            "shortlist_geometry":{"lt_2p5A_hla_or_peptide":sum(x["geometry"]["hla_or_peptide_clash"] for x in chosen),
             "lt_2p5A_any_target_chain":sum(x["geometry"]["any_clash"] for x in chosen),
             "asp6_backbone_lte_5A":sum(x["geometry"]["d6_backbone"]["pairs_lte_5A"]>0 for x in chosen),
             "asp6_sidechain_lte_5A":sum(x["geometry"]["d6_sidechain"]["pairs_lte_5A"]>0 for x in chosen)},
            "analysis_scope":"Original provider files plus modeled structure consistency and simple distances; no authenticated server attestation or binding conclusion",
            "experimental_binding_verified":False,
        }
        if include_private_audit:
            out["per_shortlist_privately"]= [{"candidate":row["name"],"archive":x["archive"],"index":x["index"],"geometry":x["geometry"]} for row,x in zip(rows,chosen)]
        return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("original_private_zip",type=Path,help="private raw evidence package, not redistributed")
    parser.add_argument("--private-details",action="store_true")
    parser.add_argument("--output",type=Path,help="summary JSON output")
    args=parser.parse_args()
    result=inspect_archive(args.original_private_zip,include_private_audit=args.private_details)
    rendered=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if args.output:args.output.write_text(rendered)
    else:print(rendered)
if __name__=="__main__":main()
