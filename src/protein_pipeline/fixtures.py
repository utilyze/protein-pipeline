"""Synthetic test fixture; never model output, not biological evidence."""
from pathlib import Path
import gemmi

def make_synthetic_cif(include_binder:bool=True, altered_b:bool=False,
                       altered_c:bool=False,missing_a:bool=False,altered_a:bool=False)->bytes:
    doc=gemmi.cif.Document();block=doc.add_new_block('SYNTHETIC_NOT_BIOLOGICAL')
    loop=block.init_loop('_atom_site.', ['group_PDB','id','type_symbol','label_atom_id',
       'label_alt_id','label_comp_id','label_asym_id','label_entity_id','label_seq_id',
       'pdbx_PDB_ins_code','Cartn_x','Cartn_y','Cartn_z','occupancy','B_iso_or_equiv',
       'auth_seq_id','auth_comp_id','auth_asym_id','auth_atom_id','pdbx_PDB_model_num'])
    components={}
    if not missing_a:components['A']=['ALA','SER' if altered_a else 'GLY','LEU']
    components['B']=['CYS' if altered_b else 'ALA','SER']
    components['C']=['VAL','VAL','VAL','GLY','ALA','GLU' if altered_c else 'ASP','GLY','VAL','GLY','LYS']
    if include_binder:components['D']=['ARG','GLY','SER']
    n=0
    for ch,residues in components.items():
        for i,comp in enumerate(residues,1):
            for atom,element,dx in [('N','N',0.0),('CA','C',0.5),('C','C',1.0),('O','O',1.5)]:
                n+=1; y=0 if ch=='A' else 8 if ch=='B' else 16 if ch=='C' else 20
                loop.add_row(['ATOM',str(n),element,atom,'.',comp,ch,str(ord(ch)-64),str(i),'.',
                       str(round(i*3.4+dx,3)),str(y), '0','1','20',str(i),comp,ch,atom,'1'])
            if ch=='C' and i==6:
                for atom,dx in [('CB',2.0),('CG',2.5),('OD1',3.0),('OD2',3.5)]:
                    n+=1
                    loop.add_row(['ATOM',str(n),'O' if atom.startswith('OD') else 'C',atom,'.',comp,ch,'3',str(i),'.',
                              str(round(i*3.4+dx,3)),'16','0','1','20',str(i),comp,ch,atom,'1'])
    return doc.as_string().encode('utf-8')
