"""Secondary trial: hill-climb the extra DVH-goal feasibility margin.

Primary research constraints remain hard. The secondary objective is an explicit
uniform relaxation t of the two reference dose caps. A t>0 plan does NOT pass the
reference goals. Report original objective and metrics for every iterate.
"""
import json,time,argparse
import numpy as np
from scipy import sparse
from .data import ROOT,load,write_json
from .evaluate import Evaluator
from .optimize import Planner,save_plan
from .warm import solve

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scaled',action='store_true');args=ap.parse_args()
    start=time.perf_counter();cpu=time.process_time();D,V,B=load();ev=Evaluator();cfg=json.loads((ROOT/'config/research.json').read_text());pl=Planner(D,V,B,cfg)
    source=json.loads((ROOT/'trial/initial-comparison.json').read_text())
    base=next(r for r in source['plans'] if r['name']=='subset_0_72_144_216_288')
    bx=np.array(json.loads((ROOT/base['path']).read_text())['fluence_mu']);angles=base['evaluation']['active_angles'];c,A,b,cols=pl.formulation(angles)
    out=ROOT/('trial/repair-scaled' if args.scaled else 'trial/repair');out.mkdir(exist_ok=True,parents=True);rows=[]
    for strategy in ['convex_all_voxel','dose_volume_active_set']:
        x=bx.copy();old=None
        for i in range(1 if strategy=='convex_all_voxel' else 8):
            td=pl.T@x;cd=pl.C@x
            ti=np.arange(len(td));ci=np.arange(len(cd))
            if strategy=='dose_volume_active_set':
                ti=np.argsort(td,kind='stable')[:len(td)-(int(np.ceil(.1*len(td)))-1)]
                ci=np.argsort(cd,kind='stable')[:len(cd)-(int(np.ceil(.05*len(cd)))-1)]
            extras=sparse.vstack([pl.T[ti][:,cols],pl.C[ci][:,cols]],format='csr')
            AA=sparse.vstack([sparse.hstack([A,sparse.csr_matrix((A.shape[0],1))]),sparse.hstack([extras,-np.ones((extras.shape[0],1))])],format='csr')
            bb=np.r_[b,np.full(len(ti),55.-1e-5),np.full(len(ci),25.-1e-5)]
            cc=np.r_[c*1e-7,1.]
            if args.scaled:
                scales=np.r_[np.full(len(cols),1000.),1.]
                # Pure uniform-goal relaxation objective; no hidden primary reweighting.
                cc=np.r_[np.zeros(len(cols)),1.]
                y,info=solve(cc,AA@sparse.diags(scales),bb,np.r_[np.full(len(cols),cfg['max_beamlet_mu']/1000),100.],time_limit=120)
                if y is not None:y=y*scales
                info['secondary_objective']='minimize uniform DVH-goal relaxation only'
            else:
                y,info=solve(cc,AA,bb,cfg['max_beamlet_mu'],time_limit=120)
            item={'strategy':strategy,'iteration':i,'optimizer':info}
            if y is None:
                rows.append(item);print(strategy,'failed',info['message'],flush=True);break
            x=np.zeros(418);x[cols]=y[:-1];t=float(y[-1]);name=f'{strategy}_{i}';path=out/f'{name}.json'
            save_plan(path,x,'research',5,{'method':strategy,'secondary_goal_relaxation_gy':t})
            r,d=ev.evaluate(path);item.update(relaxation_gy=t,path=str(path.relative_to(ROOT)),evaluation=r,dose_recomputation_max_error_gy=float(np.abs(d-D@x).max()))
            rows.append(item);write_json(out/'comparison.json',{'plans':rows,'elapsed_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu,'note':'Secondary feasibility search, not a primary-score improvement.'})
            print(name,'relaxation',t,'research feasible',r['feasible'],'reference pass',r['tg119_reference_goals_pass'],'score',r['objective_gy'],flush=True)
            if old is not None and abs(old-t)<1e-6:break
            if t<1e-6:break
            old=t
    write_json(out/'comparison.json',{'plans':rows,'elapsed_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu})
if __name__=='__main__':main()
