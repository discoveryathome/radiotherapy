"""Reproducible full experiment; no changes to frozen benchmark inputs."""
import argparse
import itertools
import json
import platform
import time
from pathlib import Path
import numpy as np
import scipy
from .data import ROOT,load,write_json,ANGLES,digest
from .evaluate import Evaluator
from .verify import controls
from .optimize import Planner,save_plan

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results');ap.add_argument('--baseline-only',action='store_true');args=ap.parse_args()
    out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True);plans=out/'plans';plans.mkdir(exist_ok=True)
    started=time.perf_counter();D,V,B=load();ev=Evaluator();ctrl=controls(ev)
    cfg=json.loads((ROOT/'config/research.json').read_text());paper=json.loads((ROOT/'config/paper.json').read_text())
    records=[];solves=[];cache={}
    def record(name,x,profile,budget,info):
        path=plans/f'{name}.json';save_plan(path,x,profile,budget,info)
        r,d=ev.evaluate(path);optimized=np.asarray(D@x).ravel();err=float(np.max(np.abs(d-optimized)))
        if err>1e-9: raise AssertionError('Independent dose mismatch')
        rec={'name':name,'path':str(path.relative_to(ROOT)),'profile':profile,'evaluation':r,'dose_recomputation_max_error_gy':err,'optimizer':info}
        records.append(rec)
        print(name,'feasible=',r['feasible'],'score=',round(r['objective_gy'],6),'seconds=',round(info.get('seconds',0),2),flush=True)
        write_json(out/'partial.json',{'plans':records,'solves':solves})
        return rec
    pp=Planner(D,V,B,paper);x,pinfo=pp.solve(ANGLES)
    if x is None: raise RuntimeError(pinfo)
    pr=record('paper_lp',x,'paper',5,pinfo)
    for n,val in [('Core',.2489),('BODY',.1021)]:
        if abs(pr['evaluation']['metrics'][n]['mean_gy']-val)>.000051: raise AssertionError('New LP does not reproduce published result')
    if args.baseline_only:
        write_json(out/'baseline.json',{'controls':ctrl,'paper_lp':pr});return
    planner=Planner(D,V,B,cfg)
    # Simple all-beam uniform positive control. Dose lower bound met by construction;
    # it may fail OAR constraints, which the evaluator explicitly reports.
    ones=np.ones(418);dose=D@ones;uniform=ones*cfg['target_min_gy']/dose[V['OuterTarget']].min()
    record('uniform',uniform,'research',5,{'method':'uniform scaled to minimum target dose'})
    q,qi=planner.quadratic();record('quadratic_penalty',q,'research',5,qi)
    for k in (5,4,3,2,1):
        for angles in itertools.combinations(ANGLES,k):
            x,info=planner.solve(angles);solves.append(info);cache[angles]=(x,info)
            if x is not None: record('subset_'+'_'.join(map(str,angles)),x,'research',k,info)
            else: print('subset',angles,'status',info['status'],info['message'],flush=True)
    # Backward greedy removes one angle at each level; uses the same subproblem oracle.
    chosen=tuple(ANGLES);greedy=[]
    for k in (4,3,2,1):
        candidates=[(sub,cache[sub]) for sub in itertools.combinations(chosen,k) if cache[sub][0] is not None]
        if not candidates: break
        chosen,(x,info)=min(candidates,key=lambda t:t[1][1]['objective'])
        greedy.append({'budget':k,'angles':list(chosen),'objective_gy':info['objective']})
    feasible3=[(a,p) for a,p in cache.items() if len(a)==3 and p[0] is not None]
    best3=min(feasible3,key=lambda t:t[1][1]['objective']) if feasible3 else None
    sensitivity=[]
    if best3:
        angles,(x,info)=best3
        base=record('best_three',x,'research',3,{'method':'enumeration incumbent','angles':list(angles)})
        # Synthetic global output gain; not geometry/setup robustness.
        for gain in cfg['sensitivity']['output_gains']:
            dd=ev.dose(x*gain);r=ev.assess(x,dd,cfg,3)
            sensitivity.append({'kind':'output_gain','value':gain,'plan':'best_three','evaluation':r})
        for quantum in cfg['sensitivity']['rounding_mu']:
            xx=np.rint(x/quantum)*quantum
            record('rounded_'+str(int(quantum)),xx,'research',3,{'method':'nearest MU rounding','quantum_mu':quantum})
        for weight in cfg['sensitivity']['core_objective_weights']:
            xx,ii=planner.solve(angles,core_weight=weight)
            if xx is not None: record('weight_'+str(weight),xx,'research',3,ii)
        # Robust search uses same finite set, enforcing both predeclared gain endpoints.
        robust=[]
        for a in itertools.combinations(ANGLES,3):
            xx,ii=planner.solve(a,gains=tuple(cfg['sensitivity']['robust_training_gains']));solves.append(ii)
            if xx is not None: robust.append((xx,ii))
        if robust:
            xx,ii=min(robust,key=lambda p:p[1]['objective']);record('robust_three',xx,'research',3,ii)
            for gain in cfg['sensitivity']['output_gains']:
                r=ev.assess(xx,ev.dose(xx*gain),cfg,3)
                sensitivity.append({'kind':'output_gain','value':gain,'plan':'robust_three','evaluation':r})
        # Re-solve strongest candidate with another HiGHS algorithm and tighter tolerances.
        xx,ii=planner.solve(angles,method='highs-ipm',tol=1e-9)
        if xx is not None: record('tight_ipm_three',xx,'research',3,ii)
    payload={'schema':'cort-comparison/v1','paper_lp_reproduced':True,'data_sha256':digest(ROOT/'data/manifest.json'),
        'research_config_sha256':digest(ROOT/'config/research.json'),'controls':ctrl,'plans':records,'solves':solves,
        'greedy_path':greedy,'sensitivity':sensitivity,'elapsed_seconds':time.perf_counter()-started,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform(),'machine':platform.machine(),'timing_note':'Other heavy workloads were present. Timings are descriptive, not speedup evidence.'}}
    write_json(out/'comparison.json',payload)
    print('COMPLETE',len(records),'plans;',round(payload['elapsed_seconds'],1),'seconds',flush=True)
if __name__=='__main__':main()
