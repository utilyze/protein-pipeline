"""Optional, explicitly authorized fixed-host RFD4 HTTP adapter.

No inference occurs on import or from ordinary validation commands.
The hosted service has independent legal terms and may consume quota.
"""
from __future__ import annotations
import http.client
import json
import os
from pathlib import Path
import re
import ssl
from .molecules import sha256
HOST='health.api.nvidia.com'
PATH='/v1/biology/ipd/rfd4-proteina/generative'
MAX_REQUEST=12*1024*1024
MAX_RESPONSE=25*1024*1024

def prepare_request(annotated_cif:bytes,replicates:int=1)->bytes:
    if type(replicates)!=int or not 1<=replicates<=4:
        raise ValueError('Supported sample count 1 to 4')
    if not isinstance(annotated_cif,bytes) or not 0<len(annotated_cif)<=MAX_REQUEST:
        raise ValueError('Invalid conditioning input')
    text=annotated_cif.decode('utf-8')
    # Caller must independently establish semantic correctness and legal rights.
    body={'task':'generation','input':{'format':'annotated_cif','file':{'filename':'authorized_target.cif','content':text}},
          'sampling':{'num_replicates':replicates}}
    raw=json.dumps(body,sort_keys=True,separators=(',',':')).encode('utf-8')
    if len(raw)>MAX_REQUEST:raise ValueError('Encoded request exceeds size cap')
    return raw

def post_one_authorized(payload:bytes,destination:Path,*,confirm_terms:bool=False,
                        confirm_entitlement:bool=False,confirm_upload_rights:bool=False,
                        token:str|None=None)->dict:
    if not all((confirm_terms,confirm_entitlement,confirm_upload_rights)):
        raise ValueError('Explicit terms, entitlement and upload rights confirmations required')
    if not isinstance(payload,bytes) or not 0<len(payload)<=MAX_REQUEST:
        raise ValueError('Invalid payload')
    key=token or os.environ.get('NVIDIA_API_KEY','')
    if not re.fullmatch(r'nvapi-[A-Za-z0-9_+./=-]{10,4080}',key):
        raise ValueError('NVIDIA API key missing/malformed')
    dest=Path(destination)
    # No output directory can be silently overwritten.
    dest.mkdir(mode=0o700,parents=False,exist_ok=False)
    conn=http.client.HTTPSConnection(HOST,timeout=480,context=ssl.create_default_context())
    try:
        conn.request('POST',PATH,payload,{'Authorization':'Bearer '+key,
                       'Content-Type':'application/json','Accept':'application/json'})
        response=conn.getresponse()
        raw=response.read(MAX_RESPONSE+1)
        status=response.status
    finally:
        conn.close()
    if status!=200 or len(raw)>MAX_RESPONSE or not raw:
        raise RuntimeError('Provider response unsuccessful; no automatic retry')
    f=dest/'original_provider_response.json'
    with f.open('xb') as stream:stream.write(raw)
    os.chmod(f,0o600)
    return {'http_status':status,'response_sha256':sha256(raw),
           'response_bytes':len(raw),'original_response_saved':True,
           'biological_binding_verified':False}
