"""Small synthetic CLI-independent demonstration, no actual protein design."""
from __future__ import annotations
import json
from protein_pipeline.fixtures import make_synthetic_cif
from protein_pipeline.molecules import parse_structure
from protein_pipeline.targets import make_profile,check_profile_source,validate_output
from protein_pipeline.geometry import screen_model

def main():
    source_bytes=make_synthetic_cif(include_binder=False)
    candidate_bytes=make_synthetic_cif(include_binder=True)
    source=parse_structure(source_bytes)
    candidate=parse_structure(candidate_bytes)
    profile=make_profile(source,'synthetic-not-biological',('A','B','C'),'D','C','VVVGADGVGK')
    check_profile_source(profile,source_bytes)
    identity=validate_output(candidate,profile)
    geometry=screen_model(candidate,'D',('A','B','C'),'C',6)
    report={
        'fixture':'SYNTHETIC_ONLY_NOT_PROVIDER_GENERATED',
        'identity':identity,
        'geometry':geometry,
        'biological_binding_demonstrated':False,
    }
    print(json.dumps(report,sort_keys=True,indent=2))
if __name__=='__main__':main()
