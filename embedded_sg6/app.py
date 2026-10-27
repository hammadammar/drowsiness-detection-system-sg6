"""Canonical CLI: raw camera/video or explicitly labelled SG1 observation replay."""
import argparse
import contextlib
import json
import math
import sys
import time
from pathlib import Path

from .pipeline import Pipeline, ROOT

def parser():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--sg1-jsonl', type=Path)
    source.add_argument('--video', type=Path)
    source.add_argument('--camera', type=int)
    source.add_argument('--csi-pipeline', help='Explicit OpenCV GStreamer pipeline (requires GStreamer build)')
    p.add_argument('--model', type=Path, default=Path('models/face_landmarker.task'))
    p.add_argument('--config', type=Path, default=ROOT / 'embedded_sg6/config.json')
    p.add_argument('--headless', action='store_true', help='Default; never opens a GUI')
    p.add_argument('--display', action='store_true')
    p.add_argument('--output', type=Path, default=Path('evaluation/sg6_output.jsonl'))
    p.add_argument('--metrics', type=Path, default=Path('evaluation/sg6_metrics.json'))
    p.add_argument('--benchmark', action='store_true', help='Collect stage and process resource measurements')
    p.add_argument('--max-frames', type=int, default=0)
    return p

def observations(args, cfg, resources):
    if args.sg1_jsonl:
        with args.sg1_jsonl.open(encoding='utf-8') as fh:
            for line in fh:
                if line.strip():
                    b = json.loads(line)
                    if 'face' in b:
                        b = dict(b['face'], frame_id=b['frame_id'], timestamp_ms=b['timestamp_ms'])
                    yield b, None, {'input_kind': 'SG1_OBSERVATION_REPLAY', 'capture_ms': None, 'sg1_ms': None}, None
        return
    if not args.model.is_file() or args.model.stat().st_size == 0:
        raise ValueError(f'Missing or empty SG1 model: {args.model}; see deployment documentation')
    import cv2
    from module_sg1 import Sg1_Pipeline as sg1
    sg1.MODEL_PATH = str(args.model.resolve())
    detector = sg1.create_detector(sg1.vision.RunningMode.VIDEO, max_faces=3)
    resources.callback(detector.close)
    source = str(args.video) if args.video else args.camera
    cap = cv2.VideoCapture(args.csi_pipeline, cv2.CAP_GSTREAMER) if args.csi_pipeline else cv2.VideoCapture(source)
    resources.callback(cap.release)
    if not cap.isOpened():
        raise ValueError(f'Input initialization failed: {source or args.csi_pipeline}')
    if not args.video:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg['width'])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg['height'])
        cap.set(cv2.CAP_PROP_FPS, cfg['fps'])
    fps = cap.get(cv2.CAP_PROP_FPS)
    if args.video and (not math.isfinite(fps) or fps <= 0 or fps > 1000):
        raise ValueError('Video requires a finite, credible container FPS for timeline reconstruction')
    fid, previous = 0, -1
    while True:
        start = time.perf_counter_ns()
        ok, frame = cap.read()
        acquired = time.monotonic_ns()
        capture_ms = (time.perf_counter_ns() - start) / 1e6
        if not ok:
            if args.video and fid > 0 and cap.get(cv2.CAP_PROP_FRAME_COUNT) <= fid:
                return
            raise RuntimeError('Frame read failed/disconnected or truncated input; driver state UNKNOWN')
        ts = round(fid * 1000 / fps) if args.video else acquired // 1000000
        ts = max(previous + 1, ts)
        previous = ts
        start = time.perf_counter_ns()
        result = detector.detect_for_video(sg1.to_mp_image(frame), ts)
        # Single-face region policy: ambiguity becomes unknown instead of switching drivers.
        candidates = sum(sg1.select_driver_face(type('R', (), {'face_landmarks': [lm]})(), frame.shape[1], frame.shape[0], cfg['driver_region']) is not None for lm in result.face_landmarks)
        if candidates > 1:
            result = type('R', (), {'face_landmarks': []})()
        record, _rois = sg1.build_sg1_packet(result, frame, fid, ts, cfg['driver_region'], include_landmarks=True)
        problems = sg1.check_face_block(record['face'])
        if problems:
            raise ValueError(f'SG1 contract violation: {problems}')
        yield dict(record['face'], frame_id=fid, timestamp_ms=ts), frame, dict(input_kind='VIDEO' if args.video else 'CAMERA', source_width=frame.shape[1], source_height=frame.shape[0], reported_source_fps=fps if math.isfinite(fps) else None, capture_ms=capture_ms, sg1_ms=(time.perf_counter_ns()-start)/1e6), acquired
        fid += 1

def main(argv=None):
    args = parser().parse_args(argv)
    if args.headless and args.display:
        parser().error('--headless and --display are mutually exclusive')
    if args.max_frames < 0:
        parser().error('--max-frames must be nonnegative')
    cfg = json.loads(args.config.read_text())
    if min(cfg['width'], cfg['height'], cfg['fps']) <= 0:
        raise ValueError('Resolution and FPS must be positive')
    region = cfg['driver_region']
    if len(region) != 4 or not (0 <= region[0] < region[2] <= 1 and 0 <= region[1] < region[3] <= 1):
        raise ValueError('driver_region must be normalized [x1,y1,x2,y2]')
    pipe = Pipeline(cfg['eye_config'], cfg.get('temporal'), cfg['decision_method'], cfg['alert_cooldown_ms'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    count, errors, consecutive_errors, totals, maxima = 0, 0, 0, {}, {}
    begin = time.perf_counter()
    status, error = 'COMPLETED', None
    input_metadata = None
    import psutil
    process = psutil.Process()
    cpu_begin = sum(process.cpu_times()[:2])
    peak_rss = process.memory_info().rss
    try:
        with contextlib.ExitStack() as resources:
            out = resources.enter_context(args.output.open('w', encoding='utf-8'))
            if args.display:
                import cv2
                resources.callback(cv2.destroyAllWindows)
            for block, frame, input_metrics, acquired in observations(args, cfg, resources):
                input_metadata = input_metrics
                tick = time.perf_counter_ns()
                try:
                    result = pipe.process(block, frame)
                    consecutive_errors = 0
                except Exception as exc:
                    errors += 1
                    consecutive_errors += 1
                    pipe.temporal.reset()
                    pipe.eye.reset()
                    # Explicit error record is not a fabricated algorithm result.
                    out.write(json.dumps(dict(observation_status='INVALID',decision=None,
                               software_alert=False,error=f'{type(exc).__name__}: {exc}'),allow_nan=False)+'\n')
                    if consecutive_errors >= 5:
                        raise RuntimeError('Five consecutive module/contract errors; stopping in UNKNOWN state') from exc
                    continue
                decision_at = time.monotonic_ns()
                result['input'] = input_metrics
                result['read_complete_to_decision_ms'] = None if acquired is None else (decision_at-acquired)/1e6
                result['stage_latency_ms']['pipeline_ms'] = (time.perf_counter_ns()-tick)/1e6
                for name in ('capture_ms','sg1_ms'):
                    if input_metrics[name] is not None:
                        result['stage_latency_ms'][name] = input_metrics[name]
                if args.display and frame is not None:
                    from module_sg1.Sg1_Pipeline import draw_sg1_output
                    tick = time.perf_counter_ns()
                    vis = draw_sg1_output(frame, {'face': block, 'frame_id': block['frame_id'], 'timestamp_ms': block['timestamp_ms']})
                    text = f"{result['decision']['state'] or 'UNKNOWN'} eye={result['eyes']['eye_state']} blink={result['eyes']['blink_count']} yawn={result['mouth']['yawn_prob']} alert={result['software_alert']}"
                    cv2.putText(vis, text, (10, 220), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,255,255), 1)
                    cv2.imshow('SG6', vis)
                    if cv2.waitKey(1) & 0xff == ord('q'):
                        break
                    result['stage_latency_ms']['visualization_ms'] = (time.perf_counter_ns()-tick)/1e6
                out.write(json.dumps(result, allow_nan=False)+'\n')
                count += 1
                for k, v in result['stage_latency_ms'].items():
                    totals[k] = totals.get(k, 0) + v
                    maxima[k] = max(maxima.get(k, 0), v)
                peak_rss = max(peak_rss, process.memory_info().rss)
                if args.max_frames and count >= args.max_frames:
                    break
    except KeyboardInterrupt:
        status = 'INTERRUPTED'
    except Exception as exc:
        errors, status, error = errors+1, 'FAILED', f'{type(exc).__name__}: {exc}'
    elapsed = time.perf_counter()-begin
    metrics = dict(status=status, error=error, frames=count, errors=errors, elapsed_s=elapsed,
                   processing_fps=count/elapsed, mean_stage_ms={k:v/count for k,v in totals.items()} if count else {},
                   max_stage_ms=maxima, peak_sampled_rss_bytes=peak_rss,
                   cpu_percent_one_core=100*(sum(process.cpu_times()[:2])-cpu_begin)/elapsed,
                   gpu_utilization=None, camera_to_alert_latency_ms=None, frame_drops=None,
                   verification=('NOT TESTED' if not count else 'VERIFIED ON RECORDED INPUT' if args.sg1_jsonl else 'RAW INPUT RUN; SEE STATUS'),
                   input=str(args.sg1_jsonl or args.video or (args.camera if args.camera is not None else args.csi_pipeline)), input_metadata=input_metadata, config=cfg)
    args.metrics.write_text(json.dumps(metrics, indent=2)+'\n')
    print(json.dumps(metrics), file=sys.stderr)
    return 1 if status == 'FAILED' else 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'SG6 initialization failed: {type(exc).__name__}: {exc}', file=sys.stderr)
        sys.exit(1)
