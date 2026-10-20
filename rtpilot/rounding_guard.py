"""Quantization-aware LP: reserve a rowwise rounding-error envelope, then round.

For |delta x_j| <= q/2, A_i delta x <= (q/2)*sum_j |A_ij|.
Alpha=1 is a sufficient guard; smaller guards are heuristic candidates accepted
only if the unchanged independent evaluator passes their actual rounded doses.
"""
import json,time
import numpy as np
from .data import ROOT,load,write_json,ANGLES
from .evaluate import Evaluator
from .optimize import Planner,save_plan
from .warm import solve

def main():
    start=time.perf_counter();cpu=time.process_time();D,V,B=load();ev=Evaluator();cfg=json.loads((ROOT/'config/research.json').read_text());pl=Planner(D,V,B,cfg);q=10.
    folder=ROOT/'trial/rounding';folder.mkdir(parents=True,exist_ok=True);rows=[]
    for angles in [(0,72,144,216),ANGLES]:
        c,A,b,cols=pl.formulation(angles);guard=q/2*np.asarray(abs(A).sum(axis=1)).ravel()
        for alpha in [1.,.5,.25]:
            x,info=solve(c,A,b-alpha*guard,cfg['max_beamlet_mu'],time_limit=120)
            item={'angles':list(angles),'guard_fraction':alpha,'quantum_mu':q,'optimizer':info}
            if x is not None:
                xx=np.zeros(418);xx[cols]=np.rint(x/q)*q
                path=folder/f'budget{len(angles)}_guard{alpha}.json';save_plan(path,xx,'research',len(angles),{'method':'dose-error guard then round','guard_fraction':alpha,'quantum_mu':q})
                r,d=ev.evaluate(path);item.update(evaluation=r,path=str(path.relative_to(ROOT)),dose_recomputation_max_error_gy=float(np.abs(d-D@xx).max()),grid_residual_mu=float(np.abs(xx/q-np.rint(xx/q)).max()),bound_max_gy=float(guard[:2*len(V['OuterTarget'])+len(V['Core'])].max()))
                print('budget',len(angles),'guard',alpha,'feasible',r['feasible'],'objective',r['objective_gy'],flush=True)
            else: print('budget',len(angles),'guard',alpha,'status',info['status'],flush=True)
            rows.append(item);write_json(folder/'comparison.json',{'plans':rows,'elapsed_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu,'note':'Explicit new discrete subtrack using the predeclared 10-MU grid, with unchanged primary feasibility and score; not MLC delivery validation.'})
if __name__=='__main__':main()
