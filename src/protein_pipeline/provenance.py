"""Offline provider metadata validation. Never implies independent API attestation."""
from __future__ import annotations
import json
from .molecules import parse_structure,sha256
from .targets import TargetProfile,validate_output
MAX_RESPONSE=25*1024*1024


def examine_response(raw:bytes,profile:TargetProfile,expected:int|None=None)->dict:
    if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_RESPONSE:
        raise ValueError('Invalid provider response size')
    try: obj=json.loads(raw)
    except (UnicodeError,ValueError) as e:raise ValueError('Invalid response JSON') from e
    if not isinstance(obj,dict) or obj.get('task')!='generation':
        raise ValueError('Unexpected response task or shape')
    model=obj.get('model')
    if not isinstance(model,dict) or 'rfd4' not in str(model.get('model_name','')).lower():
        raise ValueError('Unexpected model metadata')
    rows=obj.get('designs')
    if not isinstance(rows,list) or not rows or (expected is not None and len(rows)!=expected):
        raise ValueError('Invalid design count')
    seen=set();records=[]
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Invalid design object')
        st=row.get('structure')
        if not isinstance(st,dict) or st.get('format') not in ('cif','mmcif') or not isinstance(st.get('content'),str):
            raise ValueError('Missing molecular structure')
        structure=parse_structure(st['content'].encode('utf-8'),'cif')
        result=validate_output(structure,profile)
        binder=structure.chain_sequences[profile.binder_chain]
        complete=''.join(structure.chain_sequences[c] for c in tuple(profile.chain_sequence_sha256)+(profile.binder_chain,))
        if row.get('sequence') not in (binder,complete):
            raise ValueError('Model sequence field differs from structural chains')
        if result['binder_sequence_sha256'] in seen:
            raise ValueError('Duplicate binder sequence within response')
        seen.add(result['binder_sequence_sha256'])
        records.append(result)
    return {'status':'SOURCE_INTEGRITY_CHECK_PASSED','response_sha256':sha256(raw),
            'model_name_reported':model['model_name'],'record_count':len(records),
            'records':records,'provider_origin_authenticated':False,
            'scientific_warning':'Response metadata may be copied or fabricated. No verified binding.'}
