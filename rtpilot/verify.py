"""Verify source controls and replay saved candidate claims without optimizing."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.io import loadmat
from .evaluate import Evaluator,sha,ANGLES

ROOT=Path(__file__).resolve().parents[1]

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
        if actual['feasible']!=old['feasible'] or actual['active_angles']!=old['active_angles'] or actual['tg119_reference_goals_pass']!=old['tg119_reference_goals_pass']:
            raise AssertionError('Verdict drift: '+row['name'])
        if abs(actual['objective_gy']-old['objective_gy'])>1e-7: raise AssertionError('Score drift')
        for name,m in actual['metrics'].items():
            for key,v in m.items():
                if abs(v-old['metrics'][name][key])>1e-7: raise AssertionError('Metric drift')
        n+=1
    print(f'PASS independent full-grid evaluation of {n} plans')
    if not payload['paper_lp_reproduced']: raise AssertionError('Missing baseline reproduction')
    print('PASS baseline reproduction claim; optimizer re-solve is available via rtpilot.run')
if __name__=='__main__': main()
