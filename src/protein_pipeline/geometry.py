"""Interchain heavy-atom geometry, not a MolProbity clashscore or binding model."""
from __future__ import annotations
import math
import numpy as np
from .molecules import Atom,Molecule


def distances(a:tuple[Atom,...],b:tuple[Atom,...],chunk:int=128)->dict:
    if not a or not b:raise ValueError('Missing atom coordinates for pairwise distance')
    if type(chunk)!=int or not 1<=chunk<=4096:raise ValueError('Unsafe distance chunk size')
    x=np.asarray([p.xyz for p in a],dtype=float)
    y=np.asarray([p.xyz for p in b],dtype=float)
    if not (np.isfinite(x).all() and np.isfinite(y).all()):raise ValueError('Nonfinite input')
    closest=math.inf; short=0; contacts=0
    for start in range(0,len(x),chunk):
        diff=x[start:start+chunk,None,:]-y[None,:,:]
        lengths=np.linalg.norm(diff,axis=-1)
        closest=min(closest,float(lengths.min()))
        short+=int(np.count_nonzero(lengths<2.5))
        contacts+=int(np.count_nonzero(lengths<=5.0))
    return {'min_A':round(closest,3),'pairs_lt_2p5A':short,'pairs_lte_5A':contacts}


def screen_model(model:Molecule,binder:str,targets:tuple[str,...],
                 mutation_chain:str|None=None,mutation_ordinal:int|None=None)->dict:
    needed=set(targets)|{binder}
    if len(needed)!=len(targets)+1 or not needed.issubset(model.atoms):
        raise ValueError('Missing target or binder coordinates')
    out={'model_sha256':model.sha256,'binder_chain':binder,'target_chains':{},
         'coordinate_units':'angstrom','hydrogen_atoms_included':False,
         'warning':'<2.5 A is a heuristic close-atom warning, not formal MolProbity or binding evidence',
         'experimental_binding_verified':False}
    for t in targets:
        out['target_chains'][t]=distances(model.atoms[binder],model.atoms[t])
    out['any_target_lt_2p5A']=any(v['pairs_lt_2p5A']>0 for v in out['target_chains'].values())
    if mutation_chain is not None:
        if mutation_chain not in targets or type(mutation_ordinal)!=int or mutation_ordinal<1:
            raise ValueError('Invalid mutation coordinates')
        atoms=[a for a in model.atoms[mutation_chain] if a.residue_ordinal==mutation_ordinal]
        bb=tuple(a for a in atoms if a.atom_name in {'N','CA','C','O'})
        sc=tuple(a for a in atoms if a.atom_name not in {'N','CA','C','O'})
        if not bb or not sc:raise ValueError('Mutation residue missing backbone or side-chain atoms')
        out['mutation_ordinal_1based']=mutation_ordinal
        out['mutation_backbone']=distances(model.atoms[binder],bb)
        out['mutation_sidechain']=distances(model.atoms[binder],sc)
    return out
