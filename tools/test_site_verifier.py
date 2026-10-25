#!/usr/bin/env python3
"""Run the real verifier against signed fixtures; never extract attack archives."""
import argparse
import base64
import textwrap
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def read_pack(path):
    with tarfile.open(path) as archive:
        return {m.name: archive.extractfile(m).read() for m in archive if m.isfile()}

def write_pack(path, files, extra=()):
    with tarfile.open(path, 'w', format=tarfile.USTAR_FORMAT) as archive:
        for name, data in files.items():
            member = tarfile.TarInfo(name); member.size = len(data); member.mode = 0o644
            archive.addfile(member, io.BytesIO(data))
        for member, data in extra:
            archive.addfile(member, io.BytesIO(data) if data is not None else None)

def rebind_identity(files):
    """Keep unsigned hash bindings consistent while invalidating the manifest signature."""
    manifest = 'content_manifest.sha256'
    ci_path = 'artifacts/ci_report.json'
    lines = files[manifest].decode().splitlines()
    no_ci = ''.join(line + '\n' for line in lines if 'ci_report.json' not in line)
    content_hash = hashlib.sha256(no_ci.encode()).hexdigest()
    ci = json.loads(files[ci_path])
    stripped = {k:v for k,v in ci.items() if k not in ('pack_hash','meta_hash','content_hash')}
    meta_hash = hashlib.sha256(json.dumps(stripped, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode()).hexdigest()
    ci['content_hash'] = content_hash; ci['meta_hash'] = meta_hash
    ci['pack_hash'] = hashlib.sha256(bytes.fromhex(meta_hash + content_hash)).hexdigest()
    files[ci_path] = json.dumps(ci, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode()
    ci_hash = hashlib.sha256(files[ci_path]).hexdigest()
    files[manifest] = ''.join((ci_hash + '  ' + ci_path if line.endswith('  ' + ci_path) else line) + '\n' for line in lines).encode()

def run_suite(binary, report_dir=None):
    binary = Path(binary).resolve()
    fixtures = ROOT / 'demos/site_v1' if (ROOT / 'demos/site_v1/evidence_pack.tar').exists() else ROOT
    original = read_pack(fixtures / 'evidence_pack.tar')
    trust = fixtures / 'trusted_signers'
    cases = []
    cases.append(('valid', original.copy(), [], trust, 'PACK VERIFIED', 0))
    changed = original.copy(); changed['artifacts/demo/request.json'] += b' '
    cases.append(('changed-content', changed, [], trust, 'HASH_MISMATCH', 1))
    missing = original.copy(); missing.pop('artifacts/demo/request.json')
    cases.append(('missing-file', missing, [], trust, 'MISSING_FILE', 1))
    missing_sig = original.copy(); missing_sig.pop('artifacts/manifest.sig')
    cases.append(('missing-signature', missing_sig, [], trust, 'SIGNATURE_MISSING', 1))
    rewritten = original.copy(); rewritten['content_manifest.sha256'] += b'# changed manifest\n'; rebind_identity(rewritten)
    cases.append(('rewritten-manifest', rewritten, [], trust, 'SIGNATURE_INVALID', 1))
    with tempfile.TemporaryDirectory(prefix='isc-verifier-regression-') as temporary:
        temp = Path(temporary)
        # A genuinely valid original signature is established by the positive case.
        # Supply a different, syntactically valid Ed25519 trust key without changing the pack.
        subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-f',str(temp/'other-key')], check=True)
        other = temp/'other-signers'
        other.write_text('unrelated ' + (temp/'other-key.pub').read_text())
        cases.append(('untrusted-signer', original.copy(), [], other, 'UNTRUSTED_SIGNER', 1))
        damaged = original.copy()
        raw = bytearray(base64.b64decode(b''.join(damaged['artifacts/manifest.sig'].splitlines()[1:-1])))
        raw[-1] ^= 1
        encoded = '\n'.join(textwrap.wrap(base64.b64encode(raw).decode(),70))
        damaged['artifacts/manifest.sig'] = ('-----BEGIN SSH SIGNATURE-----\n'+encoded+'\n-----END SSH SIGNATURE-----\n').encode()
        cases.append(('invalid-signature', damaged.copy(), [], trust, 'SIGNATURE_INVALID', 1))
        cases.append(('invalid-signature-untrusted-key', damaged, [], other, 'SIGNATURE_INVALID', 1))
        extra = original.copy(); extra['artifacts/unlisted.txt'] = b'not in signed manifest'
        cases.append(('unlisted-file', extra, [], trust, 'UNEXPECTED_FILE', 1))
        for name, tar_path, kind, link in [
            ('path-traversal', '../isc-path-traversal-test', tarfile.REGTYPE, ''),
            ('absolute-path', '/tmp/isc-absolute-path-test', tarfile.REGTYPE, ''),
            ('symlink', 'artifacts/unsafe-link', tarfile.SYMTYPE, '../outside'),
            ('hardlink', 'artifacts/unsafe-hardlink', tarfile.LNKTYPE, 'artifacts/demo/request.json'),
            ('duplicate-entry', 'artifacts/demo/request.json', tarfile.REGTYPE, ''),
        ]:
            member = tarfile.TarInfo(tar_path); member.type = kind; member.linkname = link
            data = b'test' if kind == tarfile.REGTYPE else None
            member.size = len(data) if data is not None else 0
            cases.append((name, original.copy(), [(member,data)], trust, 'UNSAFE_ARCHIVE', 1))
        for name, contents, expected in [
            ('malformed-manifest', b'not-a-manifest\n', 'PARSE_ERROR'),
            ('empty-manifest', b'# no files\n', 'PARSE_ERROR'),
            ('bad-manifest-digest', b'z'*64 + b'  artifacts/demo/request.json\n', 'PARSE_ERROR'),
            ('manifest-traversal', b'0'*64 + b'  ../outside\n', 'UNSAFE_ARCHIVE'),
            ('duplicate-manifest-path', original['content_manifest.sha256'] + original['content_manifest.sha256'].splitlines(keepends=True)[0], 'PARSE_ERROR'),
        ]:
            files = original.copy(); files['content_manifest.sha256'] = contents
            cases.append((name,files,[],trust,expected,1))
        results=[]
        for name, files, additions, signers, expected, expected_exit in cases:
            path = temp/(name+'.tar'); write_pack(path,files,additions)
            proc = subprocess.run([str(binary),str(path),'--trusted-signers',str(signers)],capture_output=True,text=True,timeout=30)
            output=proc.stdout+proc.stderr
            match=re.search(r'^Code:\s+(\S+)',output,re.M)
            actual='PACK VERIFIED' if proc.returncode==0 and '\nPACK VERIFIED\n' in output else (match.group(1) if match else 'NO_RESULT_CODE')
            passed=proc.returncode==expected_exit and actual==expected
            results.append({'case':name,'expected':expected,'actual':actual,'exit_code':proc.returncode,'passed':passed,'output':output})
            print(('PASS' if passed else 'FAIL') + ': ' + name + ' → ' + actual)
        report={'profile':'isc-site-demo-v1','verifier_version':'0.2.1','tests':results}
        if report_dir:
            dest=Path(report_dir);dest.mkdir(parents=True,exist_ok=True)
            (dest/'report.json').write_text(json.dumps(report,indent=2)+'\n')
            for item in results:(dest/(item['case']+'.txt')).write_text(item['output'])
        if not all(item['passed'] for item in results):raise SystemExit('Verifier regression failed')
        return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--binary',required=True);parser.add_argument('--report-dir')
    args=parser.parse_args();run_suite(args.binary,args.report_dir)
