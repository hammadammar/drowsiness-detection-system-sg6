"""Thin adapters for the audited subgroup contracts; no replacement inference."""
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for group in (2, 3, 4):
    sys.path.insert(0, str(ROOT / f'module_sg{group}'))

MOUTH_INDICES = (78, 82, 13, 312, 308, 317, 14, 87)

def validate_observation(block):
    if not isinstance(block, dict):
        raise ValueError('SG1 observation must be an object')
    if type(block.get('frame_id')) is not int or block['frame_id'] < 0:
        raise ValueError('SG1 frame_id must be a nonnegative integer')
    ts = block.get('timestamp_ms')
    if type(ts) not in (int,float) or not math.isfinite(ts) or ts < 0:
        raise ValueError('SG1 timestamp_ms must be finite nonnegative milliseconds')
    for key in ('face_valid', 'face_detected'):
        if type(block.get(key)) is not bool:
            raise ValueError(f'SG1 {key} must be boolean')
    if block['face_valid']:
        if not block['face_detected']:
            raise ValueError('valid face cannot be undetected')
        for key in ('left_eye_pts', 'right_eye_pts'):
            pts = block.get(key)
            if not isinstance(pts, list) or len(pts) != 6:
                raise ValueError(f'{key} requires six points')
            for p in pts:
                if not isinstance(p, (list, tuple)) or len(p) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in p):
                    raise ValueError(f'{key} requires finite numeric coordinates')

def mouth_points(block):
    """Use real optional full landmarks, never expand four points by invention."""
    landmarks = block.get('landmarks')
    if not block['face_valid'] or landmarks is None or len(landmarks) <= max(MOUTH_INDICES):
        return None
    return [landmarks[i] for i in MOUTH_INDICES]

def temporal_input(block, eyes, mouth):
    for cue in (eyes, mouth):
        if (cue['frame_id'], cue['timestamp_ms']) != (block['frame_id'], block['timestamp_ms']):
            raise ValueError('Cross-frame cue alignment rejected')
    return dict(frame_id=block['frame_id'], timestamp_ms=block['timestamp_ms'],
                face_detected=block['face_detected'] and block['face_valid'],
                eyes_valid=eyes['eye_valid'],
                eyes_closed=(eyes['eye_state'] == 'closed') if eyes['eye_valid'] else None,
                mouth_valid=mouth['mouth_valid'], yawn_prob=mouth['yawn_prob'])

class SoftwareAlert:
    """Rate-limited JSON console alert; no physical actuator implied."""
    def __init__(self, cooldown_ms=5000, sink=None):
        if cooldown_ms < 0:
            raise ValueError('cooldown_ms must be nonnegative')
        self.cooldown_ms, self.last = cooldown_ms, None
        self.sink = sink or (lambda event: print(json.dumps(event), file=sys.stderr))

    def update(self, decision, now_ms):
        if not decision['decision_valid'] or not decision['alarm_flag']:
            return False
        if self.last is not None and now_ms - self.last < self.cooldown_ms:
            return False
        self.sink(dict(type='SOFTWARE_ALERT', timestamp_ms=now_ms, state=decision['state']))
        self.last = now_ms
        return True

class Pipeline:
    def __init__(self, eye_config=None, temporal_config=None, decision_method='rule', cooldown_ms=5000, alert_sink=None):
        import jsonschema
        from sg2_eye import EyeStateModule
        from sg3 import SG3
        from sg4 import TemporalAnalyzer, SG4Config
        from module_sg5.decision_rules import make_decision
        from module_sg5.weighted_fusion import weighted_decision
        self.eye = EyeStateModule(eye_config or ROOT / 'module_sg2/configs/primary.yaml')
        self.mouth = SG3()
        self.temporal = TemporalAnalyzer(SG4Config.from_dict(temporal_config or {}))
        self.decide = {'rule': make_decision, 'weighted': weighted_decision}[decision_method]
        schema = json.loads((ROOT / 'interfaces/sg2/sg2_eye_state_v1.schema.json').read_text())
        self.validator = jsonschema.Draft202012Validator(schema)
        self.alert = SoftwareAlert(cooldown_ms, alert_sink)
        self.previous = None

    def process(self, block, frame=None):
        validate_observation(block)
        ts = block['timestamp_ms']
        if self.previous is not None and ts <= self.previous:
            raise ValueError('Observation timestamps must increase strictly')
        # SG2 permits frame-count gaps. At integration boundaries abandon any
        # pending blink across missing faces or long elapsed gaps, without a fake event.
        if not block['face_valid'] or (self.previous is not None and ts - self.previous > self.temporal.config.max_gap_ms):
            self.eye.blink.run_start = self.eye.blink.run_last = None
            self.eye.blink.run_frames = self.eye.blink.gap = 0
        self.previous = ts
        metrics = {}
        def stage(name, fn):
            start = time.perf_counter_ns()
            result = fn()
            metrics[name] = (time.perf_counter_ns() - start) / 1e6
            return result
        eyes = stage('sg2_ms', lambda: self.eye.process(block, frame))
        stage('validation_ms', lambda: self.validator.validate(eyes))
        # SG1's pose sign is unverified: do not assert head-nod evidence.
        mouth = stage('sg3_ms', lambda: self.mouth.process(block['frame_id'], ts, block['face_valid'], mouth_pts=mouth_points(block)).to_dict())
        temporal = stage('sg4_ms', lambda: self.temporal.update(temporal_input(block, eyes, mouth)))
        current_valid = block['face_valid'] and eyes['eye_valid']
        decision = stage('sg5_ms', lambda: self.decide(dict(temporal, valid=temporal['valid'] and current_valid)))
        alert_error = None
        try:
            alerted = stage('alert_ms', lambda: self.alert.update(decision, time.monotonic_ns() // 1000000))
        except Exception as exc:
            alerted, alert_error = False, str(exc)
        return dict(frame_id=block['frame_id'], timestamp_ms=ts, eyes=eyes, mouth=mouth,
                    temporal=temporal, decision=decision, software_alert=alerted,
                    eye_backend=self.eye.classifier.name,
                    cnn_available=getattr(self.eye.classifier,'cnn_available',None),
                    alert_error=alert_error, observation_status='AVAILABLE' if current_valid else 'UNKNOWN',
                    stage_latency_ms=metrics)
