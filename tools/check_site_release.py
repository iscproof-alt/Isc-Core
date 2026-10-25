#!/usr/bin/env python3
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(args):return subprocess.run(args,cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check-remotes',action='store_true');args=parser.parse_args()
 downloads=ROOT/'site-public/downloads';report=json.loads((downloads/'report.json').read_text())
 for line in (downloads/'checksums.txt').read_text().splitlines():
  expected,name=line.split('  ',1);actual=hashlib.sha256((downloads/name).read_bytes()).hexdigest();assert actual==expected,name
 binary=downloads/'isc_verify-linux-x86_64';h=hashlib.sha256(binary.read_bytes()).hexdigest()
 assert h==report['verifier_sha256']
 version_data=run(['objdump','-T',str(binary)])
 versions=sorted(set(re.findall(r'GLIBC_(\d+(?:\.\d+)+)',version_data)),key=lambda v:tuple(map(int,v.split('.'))))
 glibc=versions[-1] if versions else None
 assert glibc and report['platform']=='GLIBC symbol versions through '+glibc
 release_note=(ROOT/'docs/releases/isc-site-demo-v1.md').read_text();assert h in release_note
 source=report['source_commit'];assert run(['git','rev-parse',source])==source
 assert (ROOT/'index.html').read_bytes()==(ROOT/'site-public/index.html').read_bytes()
 for filename in ['index.html','site-public/index.html']:
  text=(ROOT/filename).read_text();assert h in text and ('GLIBC symbol versions through '+glibc) in text
  assert source in text and ('tree/'+source+'/demos/site_v1/verifier-source') in text
  assert '<th>Status</th>' in text
  assert text.index(h)<text.index('chmod +x isc_verify-linux-x86_64')
  assert 'reproducible-build guarantee' not in text or 'not a guarantee' in text
 cases={test['case']:test for test in report['tests']}
 assert all(test['passed'] for test in cases.values())
 assert cases['untrusted-signer']['actual']=='UNTRUSTED_SIGNER'
 assert cases['invalid-signature']['actual']=='SIGNATURE_INVALID'
 assert cases['invalid-signature-untrusted-key']['actual']=='SIGNATURE_INVALID'
 metadata=json.loads((downloads/'build-metadata.json').read_text())
 assert metadata['source_commit']==source and metadata['published_binary_sha256']==h
 for relative in ['Cargo.toml','Cargo.lock','src/main.rs']:
  committed=subprocess.run(['git','show',source+':isc_verify/'+relative],cwd=ROOT,check=True,capture_output=True).stdout
  assert (ROOT/'demos/site_v1/verifier-source'/relative).read_bytes()==committed
 if args.check_remotes:
  for label,url in [('GitHub','https://github.com/iscproof-alt/Isc-Core.git'),('Codeberg','https://codeberg.org/Buildseal/Isc-Core.git')]:
   refs=run(['git','ls-remote',url,'refs/tags/isc-verify-v0.2.1-source'])
   assert refs.split()[0]==source,label+': source tag does not match source_commit'
   print('PASS: Source commit tag is available on '+label)
 print('PASS: Binary hash matches both pages, the report, release notes and checksums.')
 print('PASS: objdump confirms '+report['platform']+'.')
 print('PASS: Source snapshot matches the recorded source commit; signer error codes are distinct.')
 print('Fresh-directory rebuild hash match:',metadata['fresh_rebuild_matches'])
 print('Source commit:',source)
if __name__=='__main__':main()
