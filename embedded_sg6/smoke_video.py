"""Generate explicitly synthetic no-face video and check actual model execution."""
import json
from pathlib import Path

def main():
    import cv2
    import numpy as np
    from .app import main as run
    directory = Path('evaluation')
    directory.mkdir(exist_ok=True)
    fixture = directory/'no_face_fixture.avi'
    writer = cv2.VideoWriter(str(fixture), cv2.VideoWriter_fourcc(*'MJPG'), 10, (320,240))
    if not writer.isOpened():
        raise RuntimeError('MJPG VideoWriter unavailable')
    try:
        for _ in range(30):
            writer.write(np.zeros((240,320,3),np.uint8))
    finally:
        writer.release()
    output = directory/'sg6_no_face_output.jsonl'
    code = run(['--video',str(fixture),'--headless','--output',str(output),
                '--metrics',str(directory/'sg6_no_face_metrics.json')])
    if code:
        raise SystemExit(code)
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    if len(rows) != 30 or any(row['decision']['decision_valid'] or row['software_alert'] for row in rows):
        raise AssertionError('No-face smoke did not produce 30 invalid, non-alert observations')
    print('PASS: 30 synthetic blank frames through actual SG1 model; no confirmed drowsiness or alerts. This is not driver validation.')

if __name__ == '__main__':
    main()
