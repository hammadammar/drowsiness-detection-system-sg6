"""Explicit opt-in download from the upstream versioned MediaPipe source."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'

def main():
    path = Path('models/face_landmarker.task')
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        raise SystemExit(f'{path} already exists; refusing to overwrite')
    temporary = path.with_suffix('.download')
    try:
        with urllib.request.urlopen(URL, timeout=60) as response, temporary.open('wb') as out:
            while chunk := response.read(65536):
                out.write(chunk)
        if not zipfile.is_zipfile(temporary):
            raise ValueError('Downloaded model is not a MediaPipe task ZIP bundle')
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('Corrupt model bundle')
        digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
        temporary.rename(path)
        path.with_suffix('.provenance.json').write_text(json.dumps(dict(url=URL,sha256=digest,bytes=path.stat().st_size,
            license='Apache-2.0 per upstream component model cards', publisher_checksum_verified=False,
            guide='https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker'),indent=2)+'\n')
        print(f'{path}: SHA256 {digest}; loading compatibility is verified at application initialization')
    finally:
        temporary.unlink(missing_ok=True)

if __name__ == '__main__':
    main()
