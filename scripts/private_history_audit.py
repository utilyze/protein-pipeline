#!/usr/bin/env python3
"""Read-only Git history and disclosure audit. Prints counts only, never secret values."""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

PATTERNS = {
    'github_token': re.compile(rb'(?:gh[pousr]_[a-zA-Z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,})'),
    'nvidia_key': re.compile(rb'nvapi-[A-Za-z0-9_+/=-]{16,}'),
    'aws_key': re.compile(rb'AKIA[0-9A-Z]{16}'),
    'pem_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'stripe_secret': re.compile(rb'sk_(?:live|test)_[A-Za-z0-9]{20,}'),
    'long_protein_sequence': re.compile(rb'(?<![A-Z])[ACDEFGHIKLMNPQRSTVWY]{70,}(?![A-Z])'),
}
SENSITIVE_PATH = re.compile(r'(?i)(?:^|[/._-])(?:\.env|private|secret|token|credentials|h1|binder|candidate|response)(?:[/._-]|$)')
SENSITIVE_SUFFIX = {'.pdb','.cif','.mmcif','.fasta','.fa','.pkl','.pickle','.zip','.tar','.gz','.npz','.npy','.pt','.pth','.safetensors'}
MAX_BLOB=20_000_000

def git(*args, check=True):
    return subprocess.run(['git', *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)

def audit():
    refs = git('for-each-ref', '--format=%(refname)').stdout.decode('utf8','replace').splitlines()
    remote = git('ls-remote', '--heads', '--tags', 'origin', check=False)
    remote_refs = {line.split('\t')[-1] for line in remote.stdout.decode('utf8','replace').splitlines() if '\t' in line}
    local_headstags={r.replace('refs/remotes/origin/','refs/heads/') if r.startswith('refs/remotes/origin/') else r
                     for r in refs if r.startswith('refs/heads/') or r.startswith('refs/tags/') or r.startswith('refs/remotes/origin/')}
    local_headstags.discard('refs/heads/HEAD')
    missing_remote_refs = sorted(remote_refs-local_headstags)
    local_pr_refs=sum('/pr/' in r or r.startswith('refs/pull/') for r in refs)
    listed=git('rev-list','--objects','--all').stdout.decode('utf8','replace').splitlines()
    object_ids={line.split(' ',1)[0] for line in listed if line}
    kinds=Counter(); finds=Counter(); paths=Counter(); blobs_checked=0; oversized=0
    oid_to_paths={}
    for line in listed:
        if ' ' in line:
            sha,path=line.split(' ',1)
            oid_to_paths.setdefault(sha,set()).add(path)
    for sha in sorted(object_ids):
        typ=git('cat-file','-t',sha).stdout.decode().strip()
        kinds[typ]+=1
        if typ!='blob': continue
        blobs_checked+=1
        blob_paths=oid_to_paths.get(sha,set())
        if any(SENSITIVE_PATH.search(p) or Path(p).suffix.lower() in SENSITIVE_SUFFIX for p in blob_paths):
            paths['sensitive_path_or_extension']+=1
        sz=int(git('cat-file','-s',sha).stdout)
        if sz>MAX_BLOB:
            oversized+=1
            continue
        data=git('cat-file','blob',sha).stdout
        for name,pat in PATTERNS.items():
            matches=list(pat.finditer(data))
            if name=='nvidia_key':
                matches=[m for m in matches if m.group()!=b'nvapi-FAKEONLYNOTREAL']
            finds[name]+=len(matches)
        if b'\x00' in data[:4096]:
            paths['binary_blob']+=1
    fsck=git('fsck','--full','--no-reflogs','--unreachable',check=False)
    fsck_lines=(fsck.stdout+fsck.stderr).decode('utf8','replace').splitlines()
    dangling=sum('unreachable' in line or 'dangling' in line for line in fsck_lines)
    fsck_errors=sum(bool(re.search('error|fatal|missing',line,re.I)) for line in fsck_lines)
    return {
        'scan_type':'authenticated GitHub Actions clone - reachable refs and local cloned objects only',
        'git_head':git('rev-parse','HEAD').stdout.decode().strip(),
        'remote_ref_listing_status':'ok' if remote.returncode==0 else 'failed',
        'fetched_ref_count':len(refs),
        'remote_branch_tag_ref_count':len(remote_refs),
        'unfetched_branch_tag_ref_count':len(missing_remote_refs),
        'fetched_pr_ref_count':local_pr_refs,
        'reachable_object_count':len(object_ids),
        'reachable_commit_count':kinds['commit'],
        'reachable_tree_count':kinds['tree'],
        'unique_reachable_blob_count':kinds['blob'],
        'blobs_scanned_count':blobs_checked,
        'oversized_unscanned_blobs':oversized,
        'binary_blob_count':paths['binary_blob'],
        'suspicious_name_or_extension_count':paths['sensitive_path_or_extension'],
        'potential_sensitive_pattern_matches':dict(finds),
        'fsck_exit_code':fsck.returncode,
        'fsck_error_lines':fsck_errors,
        'locally_dangling_or_unreachable_objects':dangling,
        'scope_limitations':['Remote server-only unreachable objects are not downloadable via ordinary clone.',
                             'GitHub Actions logs, caches, packages and Pages must be checked separately.',
                             'Generic peptide patterns do not replace exact private-sequence matching.']
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='private_history_audit_results.json')
    args=p.parse_args()
    r=audit()
    Path(args.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ('scope_limitations',)},sort_keys=True))
    summary=os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a') as f:
            f.write('## Private history audit (redacted, counts only)\n\n')
            for k,v in r.items():
                if k!='scope_limitations':f.write(f'- **{k}**: {json.dumps(v)}\n')
            f.write('\nRemote-only unreachable Git objects and external GitHub disclosure surfaces are not certified by this workflow.\n')
    critical=sum(r['potential_sensitive_pattern_matches'].values()) + r['oversized_unscanned_blobs'] + r['fsck_error_lines'] + r['unfetched_branch_tag_ref_count']
    if r['remote_ref_listing_status']!='ok' or critical:
        print('AUDIT REVIEW REQUIRED: incomplete fetch, integrity defect or potential sensitive matches (redacted).')
        return 2
    print('AUDIT PASS FOR SCANNED REACHABLE OBJECTS. This is not server-unreachable-object certification.')
    return 0

if __name__=='__main__':sys.exit(main())
