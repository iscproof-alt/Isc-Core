#!/usr/bin/env python3
"""Build, test and stage website artifacts locally; never deploy or push."""
from pathlib import Path
import datetime
import hashlib
import html
import importlib.util
import json
import platform
import os
import tomllib
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def command(args):return subprocess.run(args,cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
def main():
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64'):
        raise SystemExit('Published binary generation is currently supported only on Linux x86-64; source builds remain possible elsewhere.')
    command(['git','diff','--exit-code','HEAD','--','isc_verify','demos/site_v1/verifier-source'])
    revision=command(['git','rev-parse','HEAD'])
    command(['cargo','build','--release','--locked','--manifest-path','isc_verify/Cargo.toml'])
    binary=ROOT/'isc_verify/target/release/isc_verify'
    assert command([str(binary),'--version'])=='isc_verify 0.2.1'
    src=ROOT/'isc_verify';snapshot=ROOT/'demos/site_v1/verifier-source'
    for relative in ['Cargo.toml','Cargo.lock','src/main.rs']:
        if (src/relative).read_bytes()!=(snapshot/relative).read_bytes():raise SystemExit('Verifier source snapshots disagree: '+relative)
    versions=command(['readelf','--version-info',str(binary)])
    glibc=sorted(set(re.findall(r'GLIBC_(\d+(?:\.\d+)+)',versions)),key=lambda x:tuple(map(int,x.split('.'))))
    requirement='GLIBC symbol versions through '+glibc[-1] if glibc else 'GLIBC requirement not established'
    spec=importlib.util.spec_from_file_location('fixture_tests',ROOT/'tools/test_site_verifier.py');tests=importlib.util.module_from_spec(spec);spec.loader.exec_module(tests)
    with tempfile.TemporaryDirectory(prefix='isc-site-release-') as temp:
        stage=Path(temp);download=stage/'downloads';download.mkdir()
        report=tests.run_suite(binary,download)
        old=ROOT/'demos/site_v1'
        for name in ['evidence_pack.tar','trusted_signers','records.json']:shutil.copy2(old/name,download/name)
        shutil.copy2(binary,download/'isc_verify-linux-x86_64')
        source_hash=hashlib.sha256(b''.join((snapshot/p).read_bytes() for p in ['Cargo.toml','Cargo.lock','src/main.rs'])).hexdigest()
        # Rebuild exactly the committed source in a different, fresh directory.
        clean=stage/'clean-source';clean.mkdir()
        for relative in ['Cargo.toml','Cargo.lock','src/main.rs']:
            target=clean/relative;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(subprocess.run(['git','show',revision+':isc_verify/'+relative],cwd=ROOT,check=True,capture_output=True).stdout)
        rebuild_command=['cargo','build','--release','--locked','--manifest-path',str(clean/'Cargo.toml'),'--target-dir',str(clean/'target')]
        subprocess.run(rebuild_command,cwd=ROOT,check=True)
        rebuilt=clean/'target/release/isc_verify'
        assert command([str(rebuilt),'--version'])=='isc_verify 0.2.1'
        build_metadata={
            'source_commit':revision,
            'rustc':command(['rustc','-vV']),
            'cargo':command(['cargo','--version']),
            'release_profile':tomllib.loads((src/'Cargo.toml').read_text()).get('profile',{}).get('release',{}),
            'rustflags':os.environ.get('RUSTFLAGS',''),
            'cargo_encoded_rustflags':os.environ.get('CARGO_ENCODED_RUSTFLAGS',''),
            'published_binary_sha256':digest(binary),
            'fresh_directory_rebuild_sha256':digest(rebuilt),
            'fresh_rebuild_matches':digest(binary)==digest(rebuilt),
            'rebuild_source':'git show of the three source files at source_commit; separate target directory',
            'claim':'One recorded rebuild comparison; no general reproducible-build guarantee.'
        }
        (download/'build-metadata.json').write_text(json.dumps(build_metadata,indent=2)+'\n')
        report.update({'build_metadata':build_metadata,'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':revision,'package_sha256':digest(download/'evidence_pack.tar'),'verifier_sha256':digest(download/'isc_verify-linux-x86_64'),'source_sha256':source_hash,'platform':requirement,'scope':'Project-run signed fixture and archive rejection tests. No decision-correctness or semantic chain validation.','timestamp':'No RFC 3161 timestamp in the ISC website demo.'})
        (download/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        instructions=f'''ISC website verifier 0.2.1
Source commit: {revision}
Source tree: https://github.com/iscproof-alt/Isc-Core/tree/{revision}/demos/site_v1/verifier-source

This version replaces the earlier v0.2.0-based snapshot for the website fixture.
This is not the BuildSeal hosted 5.1 verifier. Compatibility is not established.

Prebuilt executable: Linux x86-64; {requirement}; compatible loader and system libraries required.
This does not establish portability to every distribution or native Windows/macOS.
Build from reviewed source using Rust and Cargo:
  cargo build --release --locked --manifest-path verifier-source/Cargo.toml
  ./verifier-source/target/release/isc_verify evidence_pack.tar --trusted-signers trusted_signers

Before chmod/execution, check the executable, package and trust-list SHA-256
against the release note in the source repository and the website.
The same operator controls both channels; these are not independent certification.
Inspect the source and choose whether to trust the externally supplied signer key.

The kit excludes the prebuilt executable. --locked locks dependency resolution;
it is not a reproducible-build or software-correctness guarantee.
No RFC3161 TSA, decision correctness, or semantic record-chain guarantee is provided.

The regression suite rejects an unchanged, genuinely signed original package
when its signing key is excluded from the external trust list. It also checks
unlisted files, traversal, symlinks, hardlinks, duplicate entries and malformed manifests.
Only manifest files and the detached manifest signature are envelope exceptions;
other regular files must be explicitly listed and hash-checked.
'''
        (download/'README.txt').write_text(instructions)
        source_revision={'verifier_version':'0.2.1','source_commit':revision,'source_tree_sha256':source_hash}
        (download/'source-revision.json').write_text(json.dumps(source_revision,indent=2)+'\n')
        kit=download/'isc-demo-kit.zip'
        with zipfile.ZipFile(kit,'w',zipfile.ZIP_DEFLATED) as archive:
            for name in ['README.txt','source-revision.json','build-metadata.json','evidence_pack.tar','trusted_signers','records.json','report.json']:
                archive.write(download/name,name)
            for p in sorted((snapshot/'src').rglob('*')):
                if p.is_file():archive.write(p,'verifier-source/'+p.relative_to(snapshot).as_posix())
            for name in ['Cargo.toml','Cargo.lock']:archive.write(snapshot/name,'verifier-source/'+name)
            for item in report['tests']:archive.write(download/(item['case']+'.txt'),item['case']+'.txt')
            archive.write(ROOT/'tools/test_site_verifier.py','tools/test_site_verifier.py')
        checksums=''.join(digest(p)+'  '+p.name+'\n' for p in sorted(download.iterdir()) if p.is_file())
        (download/'checksums.txt').write_text(checksums)
        binary_hash=digest(download/'isc_verify-linux-x86_64');pack_hash=digest(download/'evidence_pack.tar');key_hash=digest(download/'trusted_signers')
        def verification_cmd(prefix=''):
            return '\n'.join([f"echo '{binary_hash}  {prefix}isc_verify-linux-x86_64' | sha256sum -c -",f"echo '{pack_hash}  {prefix}evidence_pack.tar' | sha256sum -c -",f"echo '{key_hash}  {prefix}trusted_signers' | sha256sum -c -"])
        # Stage all changes only after the actual binary passes every case.
        pages={}
        table=''.join('<tr><td>'+html.escape(t['case'])+'</td><td>'+html.escape(t['actual'])+'</td><td>'+str(t['exit_code'])+'</td><td class="pass">PASS</td></tr>' for t in report['tests'])
        for filename in ['index.html']:
            text=(ROOT/filename).read_text()
            text=re.sub(r'<b>Verifier snapshot</b>.*?</div>', f'<b>Verifier snapshot</b>isc_verify v0.2.1. Source snapshot: <a href="https://github.com/iscproof-alt/Isc-Core/tree/{revision}/demos/site_v1/verifier-source"><code>{revision}</code></a>. <a href="https://codeberg.org/Buildseal/Isc-Core/src/commit/{revision}/demos/site_v1/verifier-source">Same source commit on Codeberg</a>.</div>',text,count=1,flags=re.S)
            text=text.replace('Based on isc_verify v0.2.0, with local fixes and an explicit trusted-signer option. The exact demo source is included in the kit; this is not a claim that the older v0.2.0 release binary is identical.',f'isc_verify v0.2.1. Exact source snapshot: <a href="https://github.com/iscproof-alt/Isc-Core/tree/{revision}/demos/site_v1/verifier-source"><code>{revision}</code></a>.')
            text=text.replace('It is based on v0.2.0 with local fixes and\n      <code>--trusted-signers</code> support.','It is version 0.2.1, with\n      <code>--trusted-signers</code> support.')
            kit_hash=digest(kit)
            source_block=f"echo '{kit_hash}  isc-demo-kit.zip' | sha256sum -c -\nunzip isc-demo-kit.zip\ncargo build --release --locked --manifest-path verifier-source/Cargo.toml\n./verifier-source/target/release/isc_verify evidence_pack.tar --trusted-signers trusted_signers"
            text=re.sub(r'<pre>[^<]*cargo build --release --locked --manifest-path verifier-source/Cargo.toml[^<]*</pre>',lambda _: '<pre>'+source_block+'</pre>',text,count=1)
            text=text.replace('<p class="small">Start here if you are exploring ISC for the first time.</p>','').replace('<p class="small">Use this example when evaluating BuildSeal hosted records.</p>','')
            text=text.replace('<h3>ISC website demonstration</h3>','<h3>ISC website demonstration</h3><p class="small">Start here if you are exploring ISC for the first time.</p>')
            text=text.replace('<h3>BuildSeal hosted 5.1 example</h3>','<h3>BuildSeal hosted 5.1 example</h3><p class="small">Use this example when evaluating BuildSeal hosted records.</p>')
            text=text.replace('<th>Exit</th><th>Test</th>','<th>Exit</th><th>Status</th>')
            text=re.sub(r'(?:Five|[0-9]+) local fixture checks.*?not an external audit\.',f'{len(report["tests"])} local fixture checks exercise acceptance, signer trust and malformed archive rejection. These are project-run checks, not an external audit.',text,count=1,flags=re.S)
            text=re.sub(r'[0-9]+ package cases passed: one acceptance case and [0-9]+ rejection cases\.',f'{len(report["tests"])} package cases passed: one acceptance case and {len(report["tests"])-1} rejection cases.',text)
            text=text.replace('Five local fixture checks exercise acceptance and rejection. These are project-run checks, not an external audit.',f'{len(report["tests"])} local fixture checks exercise acceptance, external signer trust and rejection of malformed or unexpected archive content. These are project-run checks, not an external audit.')
            text=text.replace('Acceptance and rejection in the five published test cases: valid, changed-content, missing-file, missing-signature and rewritten-manifest.','Acceptance and rejection in the published fixture tests, including an untrusted signer, unlisted content, unsafe archive entries and malformed manifests.')
            text=text.replace('Five package cases passed: one acceptance case and four rejection cases.',f'{len(report["tests"])} package cases passed: one acceptance case and {len(report["tests"])-1} rejection cases.')
            text=re.sub(r'valid → PACK VERIFIED \(exit 0\); changed-content.*?rewritten-manifest → SIGNATURE_INVALID \(exit 1\)', 'See the versioned report for each case, exact result code and process exit status.',text)
            text=re.sub(r'<tbody>.*?</tbody>','<tbody>'+table+'</tbody>',text,count=1,flags=re.S)
            run_block=verification_cmd()+'\nchmod +x isc_verify-linux-x86_64\n./isc_verify-linux-x86_64 evidence_pack.tar --trusted-signers trusted_signers'
            text=re.sub(r'<pre>[^<]*chmod \+x isc_verify-linux-x86_64\n\./isc_verify-linux-x86_64 evidence_pack.tar --trusted-signers trusted_signers</pre>',lambda _: '<pre>'+run_block+'</pre>',text,count=1)
            text=re.sub(r'Prebuilt binary: Linux x86-64, dynamically linked;[^<]*compatible system libraries(?: are required)?\.',f'Prebuilt binary: Linux x86-64, dynamically linked; {requirement}; compatible system libraries are required.',text)
            text=re.sub(r'(?<=Linux verifier SHA-256<br>)[a-f0-9]{64}',binary_hash,text)
            text=re.sub(r'(?<=TAR archive SHA-256<br>)[a-f0-9]{64}',pack_hash,text)
            text=re.sub(r'<p class="hash">Demo signer<br>', '<p class="hash">Demo signer · OpenSSH SHA-256 fingerprint (base64)<br>',text)
            text=text.replace('<b>Demo signer</b>','<b>Demo signer · OpenSSH SHA-256 fingerprint (base64)</b>')
            text=re.sub(r'(?<=Captured during an internal fixture test\. It is not recomputed by this page\. Run the verifier to obtain your own result\.</p><pre>).*?(?=</pre>)',html.escape(report['tests'][0]['output']),text,flags=re.S)
            text=re.sub(r'https://github.com/iscproof-alt/Isc-Core/blob/[a-f0-9]+/docs/releases/isc-site-demo-v1.md','https://github.com/iscproof-alt/Isc-Core/blob/main/docs/releases/isc-site-demo-v1.md',text)
            text=text.replace('href="https://codeberg.org/Buildseal/Isc-Core">Technical questions and integration discussions','href="https://www.iscproof.io/contact.html">Technical questions and integration discussions')
            text=text.replace('href="https://codeberg.org/Buildseal/Isc-Core">Discuss an integration','href="https://www.iscproof.io/contact.html">Discuss an integration')
            if digest(binary) not in text or '<th>Status</th>' not in text or revision not in text:
                raise SystemExit('Generated page is inconsistent; no artifacts written.')
            pages[filename]=text
        pages['site-public/index.html']=pages['index.html']
        note='# ISC website verifier v0.2.1\n\nSource commit: `'+revision+'`\n\nSource snapshot SHA-256 (Cargo.toml + Cargo.lock + src/main.rs, in this order): `'+source_hash+'`\n\n| File | SHA-256 |\n| --- | --- |\n'+''.join('| '+line.split('  ',1)[1]+' | `'+line.split('  ',1)[0]+'` |\n' for line in checksums.splitlines())+'\nTests: '+str(len(report['tests']))+' passed. See `demos/site_v1/report.json`.\n\nNo RFC3161 timestamp in this fixture. The BuildSeal 5.1 verifier and scope are separate.\nThese are project-run tests and operator-controlled publication channels.\n'
        readme=(ROOT/'README.md').read_text()
        readme=readme.replace('based on **v0.2.0 with local fixes and `--trusted-signers` support**','**v0.2.1 with `--trusted-signers` support**')
        readme=readme.replace('rather than assuming that another v0.2.0 executable is identical','for this versioned fixture')
        readme=readme.replace('It rejects the four tested forms of incomplete or modified evidence below.','Its published fixture suite checks signer trust and rejects the malformed or unexpected evidence cases below.')
        readme=readme.replace('chmod +x site-public/downloads/isc_verify-linux-x86_64',verification_cmd('site-public/downloads/')+'\nchmod +x site-public/downloads/isc_verify-linux-x86_64')
        readme=re.sub(r'(?<=\| --- \| --- \| --- \|\n).*?(?=\n\nThese are)', '\n'.join('| `'+t['case']+'` | `'+t['actual']+'` | '+str(t['exit_code'])+' |' for t in report['tests']),readme,count=1,flags=re.S)
        readme=re.sub(r'These are [0-9]+ project-run fixture cases: one acceptance case and [0-9]+ rejection cases\.',f'These are {len(report["tests"])} project-run fixture cases: one acceptance case and {len(report["tests"])-1} rejection cases.',readme)
        readme=readme.replace('These are five project-run fixture cases: one acceptance case and four rejection cases.',f'These are {len(report["tests"])} project-run fixture cases: one acceptance case and {len(report["tests"])-1} rejection cases.')
        readme=re.sub(r'requires \*\*glibc 2\.34 or later\*\*',requirement,readme)
        readme=re.sub(r'\nVerifier v0\.2\.1 source commit: `[^`]+`\.\n','\n',readme)
        readme += '\nVerifier v0.2.1 source commit: `'+revision+'`.\n'
        readme=re.sub(r'\nBuild metadata and fresh-directory rebuild comparison:[^\n]*\n','\n',readme)
        readme += '\nBuild metadata and fresh-directory rebuild comparison: `site-public/downloads/build-metadata.json`. No general reproducible-build claim.\n'
        # No invented mailbox: the domain contact page leads to the actual issue channel.
        contact='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ISCProof technical contact</title></head><body><main style="max-width:720px;margin:60px auto;padding:24px;font:18px/1.7 system-ui"><a href="/">ISCProof</a><h1>Technical questions and integrations</h1><p>Maintained by Hakan Ünal. For a technical question, include the verifier version, package profile and error code. Do not post private evidence, customer inputs or secret keys.</p><p><a href="https://github.com/iscproof-alt/Isc-Core/issues">Open a technical question in the source repository</a></p><p><a href="https://buildseal.io/experience.html">Try the BuildSeal hosted example</a></p></main></body></html>'''
        output=ROOT/'site-public/downloads'
        for p in download.iterdir():shutil.copy2(p,output/p.name)
        for p in download.iterdir():
            if p.suffix=='.txt' and p.name not in ('checksums.txt',):shutil.copy2(p,old/p.name)
        shutil.copy2(download/'report.json',old/'report.json')
        (ROOT/'docs/releases/isc-site-demo-v1.md').write_text(note)
        for filename,text in pages.items():(ROOT/filename).write_text(text)
        (ROOT/'README.md').write_text(readme)
        for filename in ['contact.html','site-public/contact.html']:(ROOT/filename).write_text(contact)
        print('Staged v0.2.1 binary, source snapshot, kit, checksums, '+str(len(report['tests']))+'-case report and both pages.')
        print('No commit, push or deployment was performed.')
if __name__=='__main__':main()
