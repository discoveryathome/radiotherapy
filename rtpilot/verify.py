"""Verify source controls and replay saved candidate claims without optimizing."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from .evaluate import Evaluator,sha,ANGLES

ROOT=Path(__file__).resolve().parents[1]

def assert_equivalent(actual,stored):
    if isinstance(actual,dict):
        if set(actual)!=set(stored):raise AssertionError('Evaluation fields differ')
        for key,value in actual.items():assert_equivalent(value,stored[key])
    elif isinstance(actual,list):
        if len(actual)!=len(stored):raise AssertionError('Evaluation list length')
        for a,b in zip(actual,stored):assert_equivalent(a,b)
    elif actual is None or isinstance(actual,bool):
        if actual!=stored:raise AssertionError('Evaluation verdict differs')
    elif isinstance(actual,(int,float)):
        if not np.isfinite(stored) or abs(actual-stored)>1e-7:raise AssertionError('Evaluation number differs')
    elif actual!=stored:raise AssertionError('Evaluation value differs')

def controls(ev):
    d=ev.dose(np.ones(418)); details={}
    expected={'Core':[.026798,.050724,.053313],'OuterTarget':[.049379,.051067,.052702]}
    for name,ref in expected.items():
        a=d[ev.vois[name]]; actual=[float(a.min()),float(a.mean()),float(a.max())]
        if not np.allclose(actual,ref,rtol=0,atol=5.1e-7):
            raise AssertionError(f'Published all-ones mismatch: {name} {actual}')
        details[name]=actual
    x=np.concatenate([loadmat(ROOT/f'data/raw/Gantry{a}_Couch0_beamletSol.mat')['beamx'].ravel() for a in ANGLES])
    d=ev.dose(x); cfg=json.loads((ROOT/'config/paper.json').read_text()); r=ev.assess(x,d,cfg,5)
    if not r['feasible']: raise AssertionError('Published witness infeasible: '+str(r['violations']))
    for name,v in [('Core',.2489),('BODY',.1021)]:
        if abs(r['metrics'][name]['mean_gy']-v)>0.000051: raise AssertionError('Published LP means mismatch')
    return {'all_ones':details,'published_lp':r}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--controls-only',action='store_true');ap.add_argument('--results',default='results');args=ap.parse_args()
    ev=Evaluator();r=controls(ev)
    print('PASS published all-ones values and original LP witness')
    if args.controls_only: return
    result_path=ROOT/args.results/'comparison.json'
    payload=json.loads(result_path.read_text());n=0
    for row in payload['plans']:
        actual,_=ev.evaluate(ROOT/row['path'])
        old=row['evaluation']
        assert_equivalent(actual,old)
        if actual['feasible']!=old['feasible'] or actual['active_angles']!=old['active_angles'] or actual['tg119_reference_goals_pass']!=old['tg119_reference_goals_pass']:
            raise AssertionError('Verdict drift: '+row['name'])
        if abs(actual['objective_gy']-old['objective_gy'])>1e-7: raise AssertionError('Score drift')
        for name,m in actual['metrics'].items():
            for key,v in m.items():
                if abs(v-old['metrics'][name][key])>1e-7: raise AssertionError('Metric drift')
        n+=1
    print(f'PASS independent full-grid evaluation of {n} plans')
    indexed={r['name']:r for r in payload['plans']}
    for sc in payload['sensitivity']:
        p,x,_,cfg=ev.read_plan(ROOT/indexed[sc['plan']]['path'])
        if sc['kind']!='output_gain' or sc['value'] not in cfg['sensitivity']['output_gains']:raise AssertionError('Unexpected scenario')
        actual=ev.assess(x,ev.dose(x*sc['value']),cfg,p['beam_budget'])
        assert_equivalent(actual,sc['evaluation'])
    print('PASS all saved global-gain sensitivity metrics')
    if not payload['paper_lp_reproduced']: raise AssertionError('Missing baseline reproduction')
    print('PASS baseline reproduction claim; optimizer re-solve is available via rtpilot.run')
    extra=ROOT/args.results/'robust-five.json'
    if extra.exists():
        rr=json.loads(extra.read_text())
        if 'path' in rr:
            ee,_=ev.evaluate(ROOT/rr['path'])
            if ee['feasible']!=rr['evaluation']['feasible'] or abs(ee['objective_gy']-rr['evaluation']['objective_gy'])>1e-7:raise AssertionError('Robust witness drift')
            assert_equivalent(ee,rr['evaluation'])
            p,x,_,cfg=ev.read_plan(ROOT/rr['path'])
            if [sc['gain'] for sc in rr['scenarios']]!=cfg['sensitivity']['output_gains']:raise AssertionError('Robust scenario list')
            for sc in rr['scenarios']:
                assert_equivalent(ev.assess(x,ev.dose(x*sc['gain']),cfg,p['beam_budget']),sc['evaluation'])
            print('PASS extra five-beam robust witness and all scenarios')
    cert=ROOT/args.results/'infeasibility.json'
    if cert.exists():
        from .certify import check
        cfg=json.loads((ROOT/'config/research.json').read_text())
        doc=json.loads(cert.read_text())
        import itertools
        expected=set(itertools.combinations(ANGLES,3))
        if len(doc['cases'])!=10 or {tuple(item['solver']['angles']) for item in doc['cases']}!=expected:raise AssertionError('Incomplete infeasibility cases')
        if doc['data_sha256']!=sha(ROOT/'data/manifest.json') or doc['config_sha256']!=sha(ROOT/'config/research.json'):raise AssertionError('Certificate pins')
        for item in doc['cases']:
            if not check(item['solver'],ev,cfg)['verified_numerically']:raise AssertionError('Bad infeasibility ray')
        print('PASS all ten independent numerical three-beam infeasibility checks')
if __name__=='__main__': main()
