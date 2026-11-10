"""Synthetic-only offline scientific integrity tests. No private binder data."""
import io, json, os, subprocess, sys, zipfile
from pathlib import Path
import numpy as np
import pytest
from protein_pipeline.fixtures import make_synthetic_cif
from protein_pipeline.molecules import parse_structure,sha256,Atom
from protein_pipeline.targets import TargetProfile,make_profile,validate_output,check_profile_source
from protein_pipeline.geometry import distances,screen_model
from protein_pipeline.provenance import examine_response
from protein_pipeline.transport import prepare_request,post_one_authorized
from protein_pipeline.replay import safe_members


def setup_source():
    raw=make_synthetic_cif(False)
    source=parse_structure(raw)
    profile=make_profile(source,'synthetic-fixture',('A','B','C'),'D','C','VVVGADGVGK')
    return raw,profile


def test_fixture_parses_all_chains():
    obj=parse_structure(make_synthetic_cif())
    assert obj.chain_sequences['C']=='VVVGADGVGK'
    assert set(obj.chain_sequences)=={'A','B','C','D'}
    assert obj.model_count==1


def test_valid_source_profile_and_output():
    raw,profile=setup_source()
    check_profile_source(profile,raw)
    r=validate_output(parse_structure(make_synthetic_cif()),profile)
    assert r['status']=='SOURCE_CHAIN_IDENTITY_PASSED'
    assert r['experimental_binding_verified'] is False
    assert r['provider_origin_authenticated'] is False


def test_profile_roundtrip():
    _,profile=setup_source()
    assert TargetProfile.from_json(profile.to_json())==profile


def test_wrong_source_bytes_fail():
    _,profile=setup_source()
    with pytest.raises(ValueError,match='source bytes'):
        check_profile_source(profile,make_synthetic_cif())


def test_wrong_hla_fails():
    _,profile=setup_source()
    with pytest.raises(ValueError,match='chain A'):
        validate_output(parse_structure(make_synthetic_cif(altered_a=True)),profile)


def test_wrong_b2m_fails():
    _,profile=setup_source()
    with pytest.raises(ValueError,match='chain B'):
        validate_output(parse_structure(make_synthetic_cif(altered_b=True)),profile)


def test_mutant_to_wt_fails():
    _,profile=setup_source()
    with pytest.raises(ValueError):validate_output(parse_structure(make_synthetic_cif(altered_c=True)),profile)


def test_missing_chain_fails():
    _,profile=setup_source()
    with pytest.raises(ValueError,match='chain set'):
        validate_output(parse_structure(make_synthetic_cif(missing_a=True)),profile)


def test_rogue_extra_chain_fail():
    _,profile=setup_source()
    # Pass through duplicate binder in original reference case is not allowed.
    obj=parse_structure(make_synthetic_cif(False))
    with pytest.raises(ValueError):validate_output(obj,profile)


def test_profile_binder_same_as_target_fails():
    obj=parse_structure(make_synthetic_cif(False))
    with pytest.raises(ValueError):make_profile(obj,'bad',('A','B','C'),'C','C','VVVGADGVGK')


def test_profile_cross_source_fail_even_if_sequences_same():
    raw,profile=setup_source()
    other=make_synthetic_cif(False)
    assert raw==other
    modified=raw.replace(b'_SYNTHETIC_NOT_BIOLOGICAL',b'_REPLACED_SYNTHETIC_SOURCE')
    assert modified!=raw
    with pytest.raises(ValueError,match='source bytes'):check_profile_source(profile,modified)


def test_geometry_numeric_thresholds():
    d=(Atom('D',1,1,'CA','C',(0.,0.,0.)),)
    t=(Atom('C',1,1,'CA','C',(5.,0.,0.)),)
    assert distances(d,t)['pairs_lte_5A']==1
    assert distances(d,t)['pairs_lt_2p5A']==0
    t2=(Atom('C',1,1,'CA','C',(2.49,0.,0.)),)
    assert distances(d,t2)['pairs_lt_2p5A']==1


def test_geometry_mutation_ordinal():
    obj=parse_structure(make_synthetic_cif())
    r=screen_model(obj,'D',('A','B','C'),'C',6)
    assert 'mutation_backbone' in r and 'mutation_sidechain' in r
    assert r['experimental_binding_verified'] is False


def test_geometry_wrong_chain_fails():
    obj=parse_structure(make_synthetic_cif())
    with pytest.raises(ValueError):screen_model(obj,'D',('A','B','C'),'E',6)


def test_geometry_missing_mutation_atom_fails():
    obj=parse_structure(make_synthetic_cif())
    with pytest.raises(ValueError):screen_model(obj,'D',('A','B','C'),'C',5)


def test_reject_nonfinite_distance():
    a=(Atom('A',1,1,'CA','C',(float('nan'),0,0)),)
    b=(Atom('D',1,1,'CA','C',(0,0,0)),)
    with pytest.raises(ValueError):distances(a,b)


def test_bad_json_response_type_fails():
    _,profile=setup_source()
    for bad in (b'not json',b'[]',b'{"task":"generation","model":[],"designs":[]}',
                b'{"task":"generation","model":{"model_name":"rfd4"},"designs":{}}'):
        with pytest.raises(ValueError):examine_response(bad,profile)


def test_good_synthetic_response_not_authenticated():
    _,profile=setup_source()
    obj={'task':'generation','model':{'model_name':'rfd4-proteina'},'designs':[
       {'structure':{'format':'cif','content':make_synthetic_cif().decode()},
         'sequence': parse_structure(make_synthetic_cif()).chain_sequences['D']}]}
    res=examine_response(json.dumps(obj).encode(),profile,1)
    assert res['record_count']==1 and res['provider_origin_authenticated'] is False


def test_duplicate_designs_rejected():
    _,profile=setup_source()
    row={'structure':{'format':'cif','content':make_synthetic_cif().decode()},'sequence':'RGS'}
    data={'task':'generation','model':{'model_name':'rfd4-proteina'},'designs':[row,row]}
    with pytest.raises(ValueError,match='Duplicate binder'):
        examine_response(json.dumps(data).encode(),profile,2)


def test_provider_defaults_offline_prepared_request_has_no_network(monkeypatch):
    monkeypatch.delenv('NVIDIA_API_KEY',raising=False)
    payload=prepare_request(make_synthetic_cif())
    assert json.loads(payload)['task']=='generation'
    assert b'Authorization' not in payload


def test_provider_requires_all_consents(tmp_path):
    with pytest.raises(ValueError,match='confirmations'):
        post_one_authorized(b'{}',tmp_path/'output',token='nvapi-FAKEONLYNOTREAL',confirm_terms=True)
    assert not (tmp_path/'output').exists()


def test_zip_traversal_rejected():
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:z.writestr('../attack',b'not-ok')
    with zipfile.ZipFile(io.BytesIO(b.getvalue())) as z:
        with pytest.raises(ValueError):safe_members(z)


def test_zip_size_bomb_rejected():
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w') as z:
        for i in range(121):z.writestr(f'fixture_{i}',b'1')
    with zipfile.ZipFile(io.BytesIO(b.getvalue())) as z:
        with pytest.raises(ValueError):safe_members(z)


def test_truncated_mmcif_rejected():
    with pytest.raises(ValueError):parse_structure(b'data_broken\nloop_\n_atom_site.id\n1\n2')


def test_local_cli_inspect(tmp_path):
    p=tmp_path/'synthetic.cif';p.write_bytes(make_synthetic_cif(False))
    r=subprocess.run([sys.executable,'-m','protein_pipeline','inspect',str(p)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    obj=json.loads(r.stdout);assert 'chains' in obj and 'sequence' not in obj['chains']['C']


def test_local_cli_profile_validate_screen(tmp_path):
    source=tmp_path/'ref.cif';source.write_bytes(make_synthetic_cif(False))
    candidate=tmp_path/'out.cif';candidate.write_bytes(make_synthetic_cif())
    profile=tmp_path/'profile.json'
    base=[sys.executable,'-m','protein_pipeline']
    cmds=[base+['profile',str(source),'--id','fixture','--targets','A,B,C','--binder','D',
                '--peptide-chain','C','--peptide','VVVGADGVGK','--output',str(profile)],
          base+['validate',str(candidate),'--profile',str(profile),'--source',str(source)],
          base+['screen',str(candidate),'--profile',str(profile),'--source',str(source),
                '--mutation-chain','C','--mutation-position','6']]
    for cmd in cmds:
        r=subprocess.run(cmd,capture_output=True,text=True)
        assert r.returncode==0,(cmd,r.stderr)
        assert json.loads(r.stdout)


def test_public_synthetic_demo_script():
    path=Path(__file__).resolve().parents[1]/'examples'/'synthetic'/'run_demo.py'
    r=subprocess.run([sys.executable,str(path)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    x=json.loads(r.stdout)
    assert x['fixture']=='SYNTHETIC_ONLY_NOT_PROVIDER_GENERATED'
    assert x['identity']['experimental_binding_verified'] is False


def test_profile_unknown_sha_rejected():
    _,profile=setup_source()
    obj=json.loads(profile.to_json());obj['source_sha256']='0'*60
    with pytest.raises(ValueError):TargetProfile.from_json(json.dumps(obj))


def test_noncanonical_polymer_residue_rejected():
    text=make_synthetic_cif().decode('utf-8')
    assert 'GLY A 1 2' in text
    text=text.replace('GLY A 1 2','UNK A 1 2').replace(' 2 GLY A ', ' 2 UNK A ')
    with pytest.raises(ValueError):parse_structure(text.encode())
