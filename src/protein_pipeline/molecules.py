"""Strict molecular chain and heavy-atom extraction for PDB/mmCIF.

Numbering in coordinates may differ from biological sequence positions.
All mutation-position calculations explicitly use 1-based sequence ordinal.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import math
from typing import Literal
import gemmi

AA=set("ACDEFGHIKLMNPQRSTVWY")
MAX_STRUCTURE_BYTES=20*1024*1024

@dataclass(frozen=True)
class Atom:
    chain: str
    residue_ordinal: int
    auth_residue_number: int
    atom_name: str
    element: str
    xyz: tuple[float,float,float]

@dataclass(frozen=True)
class Molecule:
    sha256: str
    format: str
    chain_sequences: dict[str,str]
    atoms: dict[str,tuple[Atom,...]]
    model_count: int
    number_of_skipped_altloc_atoms: int


def sha256(data: bytes)->str:
    return hashlib.sha256(data).hexdigest()


def parse_structure(data:bytes, fmt:Literal['cif','pdb']='cif')->Molecule:
    if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_STRUCTURE_BYTES:
        raise ValueError('Structure must be nonempty bytes within 20 MiB')
    if fmt not in ('cif','pdb'):
        raise ValueError('Unsupported coordinate format')
    try:
        text=data.decode('utf-8')
        if '\x00' in text: raise ValueError('NUL byte in source')
        if fmt=='cif':
            block=gemmi.cif.read_string(text).sole_block()
            st=gemmi.make_structure_from_block(block)
        else:
            st=gemmi.read_pdb_string(text)
    except (UnicodeError, RuntimeError, ValueError) as exc:
        raise ValueError('Structure format cannot be parsed') from exc
    if len(st)!=1: raise ValueError('Expected exactly one coordinate model')
    chains={}; atoms={}; skipped=0
    for ch in st[0]:
        residues=[]; records=[]; residue_ids=set()
        for res in ch:
            code=gemmi.find_tabulated_residue(res.name).one_letter_code
            if not len(res): continue
            if code not in AA:
                if res.het_flag == 'A' or {'N','CA','C','O'}.issubset({atom.name for atom in res}):
                    raise ValueError('Unsupported polymer residue detected')
                continue
            residue_key=(res.seqid.num,res.seqid.icode)
            if residue_key in residue_ids:
                raise ValueError('Duplicate polymer residue numbering')
            residue_ids.add(residue_key)
            residues.append(code)
            ordinal=len(residues)
            names=set()
            for at in res:
                alt=str(at.altloc).strip('\x00 ').upper()
                if alt not in ('','A'):
                    skipped+=1
                    continue
                element=at.element.name.upper()
                if element in ('H','D'):continue
                pos=(at.pos.x,at.pos.y,at.pos.z)
                if not all(math.isfinite(v) for v in pos):
                    raise ValueError('Nonfinite coordinate')
                # Duplicate atom names with the accepted altloc are ambiguous.
                if at.name in names: raise ValueError('Duplicate selected atom name')
                names.add(at.name)
                records.append(Atom(ch.name,ordinal,res.seqid.num,at.name,element,pos))
        if residues:
            if ch.name in chains:raise ValueError('Duplicate polymer chain identifier')
            chains[ch.name]=''.join(residues)
            atoms[ch.name]=tuple(records)
    if not chains: raise ValueError('No supported protein polymer chains')
    return Molecule(sha256(data),fmt,chains,atoms,1,skipped)


def read_structure(path:Path)->Molecule:
    p=Path(path)
    if not p.is_file() or p.stat().st_size>MAX_STRUCTURE_BYTES:
        raise ValueError('Missing or oversized coordinate file')
    return parse_structure(p.read_bytes(), 'pdb' if p.suffix.lower()=='.pdb' else 'cif')
