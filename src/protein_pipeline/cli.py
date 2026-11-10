"""Read-only molecular validation and scientific screening command line."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .molecules import read_structure,parse_structure,sha256
from .targets import TargetProfile,make_profile,validate_output,check_profile_source
from .geometry import screen_model
from .provenance import examine_response


def main(argv=None):
    p=argparse.ArgumentParser(prog='protein-pipeline',description='CPU-only molecular evidence checks; no model inference')
    sub=p.add_subparsers(dest='cmd',required=True)
    x=sub.add_parser('inspect',help='List polymer chain lengths and fingerprints (no sequences printed)')
    x.add_argument('structure',type=Path)
    x=sub.add_parser('profile',help='Create self-asserted source-specific profile')
    x.add_argument('source',type=Path);x.add_argument('--id',required=True)
    x.add_argument('--targets',default='A,B,C');x.add_argument('--binder',default='D')
    x.add_argument('--peptide-chain',default=None);x.add_argument('--peptide',default=None)
    x.add_argument('--output',required=True,type=Path)
    x=sub.add_parser('validate',help='Verify output structure against its selected reference profile')
    x.add_argument('candidate',type=Path);x.add_argument('--profile',required=True,type=Path)
    x.add_argument('--source',required=True,type=Path,help='Original reference bytes required for checking source profile')
    x=sub.add_parser('screen',help='Screen geometry on a candidate with source identity checks')
    x.add_argument('candidate',type=Path);x.add_argument('--profile',required=True,type=Path)
    x.add_argument('--source',required=True,type=Path)
    x.add_argument('--mutation-chain',default=None);x.add_argument('--mutation-position',type=int,default=None)
    x=sub.add_parser('response',help='Offline validation of user-provided provider JSON, no authenticity attestation')
    x.add_argument('response',type=Path);x.add_argument('--profile',type=Path,required=True)
    x.add_argument('--source',type=Path,required=True)
    x=sub.add_parser('replay',help='Replay a privately supplied original evidence archive')
    x.add_argument('archive',type=Path)
    args=p.parse_args(argv)
    try:
        if args.cmd=='inspect':
            obj=read_structure(args.structure)
            result={'sha256':obj.sha256,'chains':{c:{'length':len(seq),'sequence_sha256':sha256(seq.encode())}
                     for c,seq in obj.chain_sequences.items()},'model_count':obj.model_count,
                     'skipped_altloc_atoms':obj.number_of_skipped_altloc_atoms}
        elif args.cmd=='profile':
            obj=read_structure(args.source)
            data=make_profile(obj,args.id,tuple(args.targets.split(',')),args.binder,args.peptide_chain,args.peptide)
            with args.output.open('x',encoding='utf-8') as fp:fp.write(data.to_json())
            result={'profile_written':str(args.output),'source_id':data.source_id,'status':'SELF_ASSERTED_NOT_PROVIDER_VERIFIED'}
        elif args.cmd=='replay':
            from .replay import inspect_archive
            result=inspect_archive(args.archive)
        else:
            profile=TargetProfile.from_json(args.profile.read_text(encoding='utf-8'))
            source=args.source.read_bytes()
            check_profile_source(profile,source,'pdb' if args.source.suffix.lower()=='.pdb' else 'cif')
            if args.cmd=='response':
                result=examine_response(args.response.read_bytes(),profile)
            else:
                obj=read_structure(args.candidate)
                result=validate_output(obj,profile)
                if args.cmd=='screen':
                    result['geometry']=screen_model(obj,profile.binder_chain,tuple(profile.chain_sequence_sha256),
                                 args.mutation_chain,args.mutation_position)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    except (OSError,ValueError,RuntimeError,KeyError) as exc:
        p.exit(2,'Protein Pipeline rejected input: '+str(exc)+'\n')

if __name__=='__main__':raise SystemExit(main())
