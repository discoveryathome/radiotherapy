"""Independent numerical infeasibility-ray checker, rebuilt from raw matrices.

For inequalities A*x<=b and box 0<=x<=u, nonnegative multipliers lambda
imply lambda*b >= min_{box} (A.T*lambda)*x. A strict contradiction establishes
numerical infeasibility. This is floating-point evidence, not a formal certificate.
"""
import json
import itertools
import argparse
import numpy as np
from scipy import sparse
from .evaluate import Evaluator,ROOT,ANGLES,COUNTS,sha

def check(info,ev,cfg):
    cols=np.flatnonzero(np.isin(np.repeat(ANGLES,COUNTS),info['angles']))
    D=sparse.hstack(ev.matrices,format='csr')[:,cols]
    target=D[ev.vois['OuterTarget']];core=D[ev.vois['Core']]
    gains=info.get('gains',[1.]);lo=min(gains);hi=max(gains)
    aa=[-target,target,core]
    bb=[np.full(target.shape[0],-cfg['target_min_gy']/lo),np.full(target.shape[0],cfg['target_max_gy']/hi),np.full(core.shape[0],cfg['core_max_gy']/hi)]
    for key,name in [('core_mean_max_gy','Core'),('healthy_mean_max_gy','HealthyBody')]:
        if cfg.get(key) is not None:
            aa.append(sparse.csr_matrix(np.asarray(D[ev.vois[name]].mean(axis=0))));bb.append(np.array([cfg[key]/hi]))
    if cfg.get('max_total_beamlet_mu') is not None:
        aa.append(sparse.csr_matrix(np.ones((1,len(cols)))));bb.append(np.array([cfg['max_total_beamlet_mu']]))
    A=sparse.vstack(aa,format='csc');b=np.concatenate(bb)
    rows=np.asarray(info['farkas']['rows'],dtype=int);lam=np.asarray(info['farkas']['multipliers'],dtype=np.longdouble)
    if rows.shape!=lam.shape or rows.min()<0 or rows.max()>=len(b) or len(set(rows))!=len(rows) or not np.isfinite(lam).all() or lam.min()<0:
        raise ValueError('Invalid infeasibility multipliers')
    Ar=A[rows].tocsc();g=[];err=[]
    eps=np.finfo(float).eps
    for j in range(Ar.shape[1]):
        l,h=Ar.indptr[j:j+2];terms=Ar.data[l:h].astype(np.longdouble)*lam[Ar.indices[l:h]]
        g.append(float(terms.sum(dtype=np.longdouble)))
        # Conservative numerical allowance for coefficient construction and sums.
        err.append(float(np.abs(terms).sum(dtype=np.longdouble))*eps*10000)
    g=np.array(g);err=np.array(err);upper=cfg['max_beamlet_mu']
    if upper is None:raise ValueError('This checker requires finite fluence boxes')
    box_lower=float(upper*np.minimum(g-err,0).sum())
    terms=b[rows].astype(np.longdouble)*lam
    rhs=float(terms.sum(dtype=np.longdouble));rhs_allowance=float(np.abs(terms).sum(dtype=np.longdouble))*eps*10000
    gap=box_lower-rhs-rhs_allowance
    return {'verified_numerically':bool(gap>1e-7),'contradiction_margin':gap,'box_lower_bound':box_lower,'weighted_rhs':rhs,'roundoff_allowance_rhs':rhs_allowance,'max_coefficient_allowance':float(err.max()),'formal_certificate':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--path',default='results/infeasibility.json');args=ap.parse_args()
    ev=Evaluator();cfg=json.loads((ROOT/'config/research.json').read_text());doc=json.loads((ROOT/args.path).read_text())
    if doc['data_sha256']!=sha(ROOT/'data/manifest.json') or doc['config_sha256']!=sha(ROOT/'config/research.json'):raise AssertionError('Certificate pin mismatch')
    expected=set(itertools.combinations(ANGLES,3))
    observed={tuple(item['solver']['angles']) for item in doc['cases']}
    if observed!=expected:raise AssertionError('Missing or duplicated angle cases')
    for item in doc['cases']:
        result=check(item['solver'],ev,cfg)
        if not result['verified_numerically']:raise AssertionError(result)
        print('PASS numerical infeasibility ray',item['solver']['angles'],result['contradiction_margin'])
    if len(doc['cases'])!=10:raise AssertionError('Need all ten 3-beam subsets')
if __name__=='__main__':main()
