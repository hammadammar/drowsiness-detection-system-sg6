"""Package committed source only; never includes desktop venv, models or secrets."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    destination = ROOT.parent/'SG6_Jetson_Handoff.zip'
    subprocess.run(['git','archive','--format=zip','--prefix=SG6_Jetson_Handoff/',
                    '-o',str(destination),'HEAD'],cwd=ROOT,check=True)
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert not any('/.venv/' in name or '/.git/' in name or name.endswith('.task') for name in names)
        assert 'SG6_Jetson_Handoff/START_HERE_JETSON.md' in names
        for name in ('setup_jetson.sh','run_jetson.sh','test_jetson.sh'):
            assert b'\r' not in archive.read('SG6_Jetson_Handoff/'+name)
    manifest = dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                    branch='integration/jetson-sg6',file=destination.name,
                    sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),bytes=destination.stat().st_size)
    destination.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__ == '__main__':
    main()
