import copy
import json
from pathlib import Path

import pytest
from embedded_sg6.pipeline import ROOT, Pipeline, SoftwareAlert, temporal_input, validate_observation, mouth_points

def observation():
    return json.loads((ROOT/'interfaces/sg2/examples/eb8_09_real_sg1.jsonl').read_text().splitlines()[0])

def pipeline():
    return Pipeline(ROOT/'module_sg2/configs/backup.yaml', alert_sink=lambda e: None)

def test_real_sample_pipeline_alignment():
    p = pipeline()
    for line in (ROOT/'interfaces/sg2/examples/eb8_09_real_sg1.jsonl').read_text().splitlines():
        b = json.loads(line)
        r = p.process(b)
        for name in ('eyes','mouth','temporal','decision'):
            assert r[name]['frame_id'] == b['frame_id']
            expected = int(b['timestamp_ms']) if name in ('temporal','decision') else b['timestamp_ms']
            assert r[name]['timestamp_ms'] == expected
        json.dumps(r, allow_nan=False)

@pytest.mark.parametrize('change', [{'frame_id':True},{'timestamp_ms':-1},{'face_valid':1},{'left_eye_pts':[[float('nan'),0]]*6},{'right_eye_pts':None}])
def test_reject_incompatible(change):
    b = observation()
    b.update(change)
    with pytest.raises(ValueError):
        validate_observation(b)

def test_duplicate_timestamp_rejected():
    p, b = pipeline(), observation()
    p.process(b)
    with pytest.raises(ValueError, match='increase'):
        p.process(b)

def test_no_face_never_blink_or_alert():
    p, b = pipeline(), observation()
    for t in range(0,10000,50):
        b.update(timestamp_ms=t, frame_id=t//50, face_valid=False, face_detected=False)
        r = p.process(b)
        assert not r['software_alert'] and not r['decision']['decision_valid']
        assert r['eyes']['eye_state'] == 'unknown' and r['eyes']['blink_event'] is None

def test_no_face_after_closure_does_not_create_blink():
    p, b = pipeline(), observation()
    closed = [[0,0],[3,0],[7,0],[10,0],[7,0],[3,0]]
    b.update(left_eye_pts=closed, right_eye_pts=closed)
    for t in (0,50,100):
        b.update(timestamp_ms=t, frame_id=t//50)
        p.process(b)
    b.update(timestamp_ms=150,frame_id=3,face_valid=False,face_detected=False)
    assert p.process(b)['eyes']['blink_event'] is None

def test_sustained_closure_and_recovery():
    p, b = pipeline(), observation()
    open_pts = [[0,0],[3,-2],[7,-2],[10,0],[7,2],[3,2]]
    closed = [[0,0],[3,0],[7,0],[10,0],[7,0],[3,0]]
    states = []
    for t in range(0,45000,50):
        pts = closed if 6000 <= t < 9000 else open_pts
        b.update(frame_id=t//50,timestamp_ms=t,left_eye_pts=pts,right_eye_pts=pts)
        states.append(p.process(b)['decision']['state'])
    assert 'DROWSY' in states and states[-1] == 'NORMAL'

def test_adapter_alignment_and_unknown():
    b = observation()
    e = dict(frame_id=b['frame_id'],timestamp_ms=b['timestamp_ms'],eye_valid=False,eye_state='unknown')
    m = dict(frame_id=b['frame_id'],timestamp_ms=b['timestamp_ms'],mouth_valid=False,yawn_prob=None)
    assert temporal_input(b,e,m)['eyes_closed'] is None
    e['frame_id'] += 1
    with pytest.raises(ValueError,match='alignment'):
        temporal_input(b,e,m)

def test_four_mouth_points_not_fabricated():
    b = observation()
    b['landmarks'] = None
    assert mouth_points(b) is None
    b['landmarks'] = [[i,0] for i in range(478)]
    assert mouth_points(b) == [[i,0] for i in (78,82,13,312,308,317,14,87)]

def test_alert_cooldown_and_failure():
    events = []
    a = SoftwareAlert(1000, events.append)
    d = dict(decision_valid=True,alarm_flag=True,state='DROWSY')
    assert a.update(d,0) and not a.update(d,999) and a.update(d,1000)
    assert len(events) == 2
    assert not a.update(dict(d, decision_valid=False),2000)

def test_missing_optional_fields_safe():
    b = observation()
    b.pop('landmarks',None)
    b.pop('head_pose',None)
    assert not pipeline().process(b)['mouth']['mouth_valid']

def test_yawn_from_full_landmarks_to_temporal():
    p, b = pipeline(), observation()
    indices = (78,82,13,312,308,317,14,87)
    for t in range(0,11000,50):
        height = 60 if 6000 <= t < 8500 else 0
        pts = [[0,0],[25,-height/2],[50,-height/2],[75,-height/2],
               [100,0],[75,height/2],[50,height/2],[25,height/2]]
        lm = [[0,0] for _ in range(478)]
        for i, xy in zip(indices,pts):
            lm[i] = xy
        b.update(timestamp_ms=t,frame_id=t//50,landmarks=lm)
        r = p.process(b)
    assert r['mouth']['mouth_valid'] and r['temporal']['yawn_count'] == 1

@pytest.mark.parametrize('method',['rule','weighted'])
def test_decision_thresholds_and_invalid(method):
    from module_sg5.decision_rules import make_decision
    from module_sg5.weighted_fusion import weighted_decision
    fn = make_decision if method == 'rule' else weighted_decision
    b = dict(frame_id=0,timestamp_ms=0,valid=True,window_valid_fraction=.9,
             perclos=.1,longest_closure_ms=0,current_closure_ms=0,yawn_count=0)
    assert fn(b)['state'] == 'NORMAL'
    assert fn(dict(b,current_closure_ms=2000))['state'] == 'DROWSY'
    assert not fn(dict(b,valid=False))['decision_valid']
    assert not fn(dict(b,window_valid_fraction=.69))['alarm_flag']
