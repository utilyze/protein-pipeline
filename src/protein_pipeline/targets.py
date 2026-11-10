"""Explicit source-scoped identity fingerprints; no embedded private structures."""
from __future__ import annotations
from dataclasses import dataclass
import json
import re
from pathlib import Path
from .molecules import Molecule,parse_structure,sha256
SHA=re.compile(r'^[0-9a-f]{64}$')

@dataclass(frozen=True)
class TargetProfile:
    source_id:str
    source_sha256:str
    chain_sequence_sha256:dict[str,str]
    chain_lengths:dict[str,int]
    expected_peptide:str|None
    peptide_chain:str|None
    binder_chain:str
    provenance_status:str='self_asserted'

    def to_json(self)->str:
        return json.dumps(self.__dict__,sort_keys=True,indent=2)+'\n'
    @classmethod
    def from_json(cls,text:str):
        data=json.loads(text)
        if not isinstance(data,dict):raise ValueError('Target profile must be an object')
        keys={'source_id','source_sha256','chain_sequence_sha256','chain_lengths',
              'expected_peptide','peptide_chain','binder_chain','provenance_status'}
        if set(data)!=keys:raise ValueError('Incorrect target profile schema')
        if not isinstance(data['source_id'],str) or not 1<=len(data['source_id'])<=120:
            raise ValueError('Invalid target source name')
        if not isinstance(data['source_sha256'],str) or not SHA.fullmatch(data['source_sha256']):
            raise ValueError('Invalid source digest')
        digs=data['chain_sequence_sha256']; lengths=data['chain_lengths']
        if not isinstance(digs,dict) or not 1<=len(digs)<=12 or not isinstance(lengths,dict) or set(digs)!=set(lengths):
            raise ValueError('Invalid chain fingerprints')
        if any(not isinstance(k,str) or not k or not isinstance(v,str) or not SHA.fullmatch(v) for k,v in digs.items()):
            raise ValueError('Invalid chain fingerprint')
        if any(type(v)!=int or not 1<=v<=10000 for v in lengths.values()):
            raise ValueError('Invalid sequence length')
        if data['provenance_status'] != 'self_asserted':
            # A JSON field is not evidence that original source bytes were checked.
            raise ValueError('Provenance cannot be elevated through profile JSON')
        if not isinstance(data['binder_chain'],str) or not data['binder_chain'] or data['binder_chain'] in digs:
            raise ValueError('Invalid binder identifier')
        if data['peptide_chain'] is not None:
            if (data['peptide_chain'] not in digs or not isinstance(data['expected_peptide'],str)
                    or not 1 <= len(data['expected_peptide']) <= 10000
                    or not data['expected_peptide'].isupper()):
                raise ValueError('Invalid peptide chain')
        elif data['expected_peptide'] is not None:raise ValueError('Peptide without chain ID')
        return cls(**data)


def make_profile(source:Molecule,source_id:str,targets:tuple[str,...],binder_chain:str,
                 peptide_chain:str|None=None,expected_peptide:str|None=None)->TargetProfile:
    if not targets or len(set(targets))!=len(targets) or binder_chain in targets:
        raise ValueError('Invalid target selection')
    if not set(targets).issubset(source.chain_sequences):
        raise ValueError('Required chains missing from source')
    if peptide_chain is not None and (peptide_chain not in targets or source.chain_sequences[peptide_chain]!=expected_peptide):
        raise ValueError('Expected peptide does not match reference')
    # Extra chains in a public reference may be TCR chains; only selected target
    # chains are pinned. The generated binder is checked separately.
    data=TargetProfile(source_id,source.sha256,
         {c:sha256(source.chain_sequences[c].encode()) for c in targets},
         {c:len(source.chain_sequences[c]) for c in targets},expected_peptide,
         peptide_chain,binder_chain,'self_asserted')
    return TargetProfile.from_json(data.to_json())


def validate_output(output:Molecule,profile:TargetProfile)->dict:
    required=set(profile.chain_sequence_sha256)|{profile.binder_chain}
    if set(output.chain_sequences)!=required:
        raise ValueError('Generated chain set differs from expected target plus binder')
    for c,fp in profile.chain_sequence_sha256.items():
        sequence=output.chain_sequences[c]
        if sha256(sequence.encode())!=fp or len(sequence)!=profile.chain_lengths[c]:
            raise ValueError(f'Generated target chain {c} differs from source')
    if profile.peptide_chain is not None and output.chain_sequences[profile.peptide_chain]!=profile.expected_peptide:
        raise ValueError('Incorrect target peptide')
    # Sequence equality alone cannot certify that every modeled target residue
    # has the basic backbone coordinates needed for interpretable screening.
    for chain in required:
        sequence=output.chain_sequences[chain]
        by_residue={}
        for atom in output.atoms[chain]:
            by_residue.setdefault(atom.residue_ordinal,set()).add(atom.atom_name)
        if len(by_residue)!=len(sequence) or any(
                not {'N','CA','C','O'}.issubset(names) for names in by_residue.values()):
            raise ValueError(f'Incomplete N/CA/C/O backbone in chain {chain}')
    binder=output.chain_sequences[profile.binder_chain]
    return {'status':'SOURCE_CHAIN_IDENTITY_PASSED','source_id':profile.source_id,
      'source_sha256':profile.source_sha256,'candidate_structure_sha256':output.sha256,
      'binder_chain':profile.binder_chain,'binder_length':len(binder),
      'binder_sequence_sha256':sha256(binder.encode()),
      'source_provenance':profile.provenance_status,
      'provider_origin_authenticated':False,'experimental_binding_verified':False,
      'scientific_warning':'Chain identity and byte integrity are not binding or stereochemical certification.'}


def check_profile_source(profile:TargetProfile,source_bytes:bytes,fmt:str='cif')->None:
    if sha256(source_bytes)!=profile.source_sha256:
        raise ValueError('Actual source bytes do not match profile')
    obj=parse_structure(source_bytes,fmt)
    for c,fp in profile.chain_sequence_sha256.items():
        if c not in obj.chain_sequences or sha256(obj.chain_sequences[c].encode())!=fp:
            raise ValueError('Source profile chain identity not verified')
