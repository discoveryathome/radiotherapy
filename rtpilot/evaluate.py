"""Independent evaluator: reads raw MAT files and accumulates columns.

Does not import optimizer, its data loader, dose multiplication, or objective code.
Physical dose model remains CORT's QIB model; this is numerical independence only.
"""
from pathlib import Path
import hashlib
import json
import argparse
import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
ANGLES = (0,72,144,216,288)
COUNTS = (98,70,90,90,70)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class Evaluator:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        manifest = json.loads((self.root/'data/manifest.json').read_text())
        for f in manifest['files']:
            if sha(self.root/f['path']) != f['sha256']:
                raise ValueError('Data SHA256 mismatch: '+f['path'])
        self.matrices=[]
        for a,n in zip(ANGLES,COUNTS):
            m=loadmat(self.root/f'data/raw/Gantry{a}_Couch0_D.mat')['D'].tocsc()
            if m.shape != (167*167*129,n) or not m.has_canonical_format:
                raise ValueError('Unexpected matrix shape or duplicate entries')
            self.matrices.append(m)
        self.vois={}
        for name in ('OuterTarget','Core','BODY'):
            raw=loadmat(self.root/f'data/raw/{name}_VOILIST.mat')['v'].reshape(-1)
            if not np.array_equal(raw,raw.astype(np.int64)):
                raise ValueError('Non-integral voxel index')
            ids=raw.astype(np.int64)-1
            if len(set(ids))!=len(ids) or ids.min()<0 or ids.max()>=167*167*129:
                raise ValueError('Invalid structure indices')
            self.vois[name]=ids
        self.vois['HealthyBody']=np.array(sorted(set(self.vois['BODY'])-set(self.vois['Core'])-set(self.vois['OuterTarget'])),dtype=np.int64)
        self.manifest_sha=sha(self.root/'data/manifest.json')

    def dose(self,x):
        x=np.asarray(x,dtype=float)
        if x.shape != (418,) or not np.isfinite(x).all():
            raise ValueError('Fluence must be 418 finite numbers')
        # Reverse column order and use extended accumulation when platform supports it.
        # No scipy sparse matrix-vector multiplication in this path.
        d=np.zeros(167*167*129,dtype=np.longdouble)
        offset=418
        for m in reversed(self.matrices):
            offset-=m.shape[1]
            for j in range(m.shape[1]-1,-1,-1):
                if x[offset+j] == 0: continue
                lo,hi=m.indptr[j:j+2]
                d[m.indices[lo:hi]] += m.data[lo:hi].astype(np.longdouble)*np.longdouble(x[offset+j])
        return np.asarray(d,dtype=np.float64)

    def read_plan(self,path):
        plan=json.loads(Path(path).read_text())
        if plan['schema']!='cort-plan/v1' or plan['data_sha256']!=self.manifest_sha:
            raise ValueError('Plan schema or dataset mismatch')
        config_path=self.root/'config'/f"{plan['profile']}.json"
        if plan['profile'] not in ('paper','research') or plan['config_sha256']!=sha(config_path):
            raise ValueError('Planning profile mismatch')
        if plan['angles']!=list(ANGLES): raise ValueError('Wrong angle order')
        if type(plan['beam_budget']) is not int or not 1<=plan['beam_budget']<=5:
            raise ValueError('Invalid beam budget')
        x=np.asarray(plan['fluence_mu'],dtype=float)
        d=self.dose(x)
        return plan,x,d,json.loads(config_path.read_text())

    def assess(self,x,d,cfg,budget):
        t=d[self.vois['OuterTarget']]; core=d[self.vois['Core']]
        h=d[self.vois['HealthyBody']]; body=d[self.vois['BODY']]
        metrics={name: dose_metrics(d[ids],cfg['prescription_gy']) for name,ids in self.vois.items()}
        active=[]; start=0
        for a,n in zip(ANGLES,COUNTS):
            if np.max(np.abs(x[start:start+n]))>cfg['active_mu_tolerance']: active.append(a)
            start+=n
        violations={
            'target_min_gy':max(0.,cfg['target_min_gy']-float(t.min())),
            'target_max_gy':max(0.,float(t.max())-cfg['target_max_gy']),
            'core_max_gy':max(0.,float(core.max())-cfg['core_max_gy']),
            'negative_fluence_mu':max(0.,-float(x.min())),
            'beam_budget':max(0,len(active)-budget)}
        if cfg.get('max_beamlet_mu') is not None:
            violations['max_beamlet_mu']=max(0.,float(x.max())-cfg['max_beamlet_mu'])
        if cfg.get('max_total_beamlet_mu') is not None:
            violations['total_beamlet_mu']=max(0.,float(x.sum())-cfg['max_total_beamlet_mu'])
        if cfg.get('core_mean_max_gy') is not None:
            violations['core_mean_gy']=max(0.,float(core.mean())-cfg['core_mean_max_gy'])
        if cfg.get('healthy_mean_max_gy') is not None:
            violations['healthy_mean_gy']=max(0.,float(h.mean())-cfg['healthy_mean_max_gy'])
        feasible=all(v <= (0 if k=='beam_budget' else cfg['fluence_tolerance_mu'] if k.endswith('_mu') else cfg['dose_tolerance_gy']) for k,v in violations.items())
        score=sum(w*metrics[name]['mean_gy'] for name,w in cfg['objective_weights'].items())
        # Dp is an empirical upper-tail order statistic: dose received by >=p% volume.
        ref=cfg.get('tg119_reference')
        reference_pass=None
        if ref:
            reference_pass=bool(metrics['OuterTarget']['D95_gy']>=ref['target_d95_min_gy']-cfg['dose_tolerance_gy'] and metrics['OuterTarget']['D10_gy']<=ref['target_d10_max_gy']+cfg['dose_tolerance_gy'] and metrics['Core']['D5_gy']<=ref['core_d5_max_gy']+cfg['dose_tolerance_gy'])
        return {'feasible':feasible,'objective_gy':score,'metrics':metrics,'active_angles':active,'beam_budget':budget,'violations':violations,'tg119_reference_goals_pass':reference_pass,'max_fluence_mu':float(x.max()),'sum_beamlet_fluence_mu':float(x.sum())}

    def evaluate(self,path):
        plan,x,d,cfg=self.read_plan(path)
        r=self.assess(x,d,cfg,plan['beam_budget'])
        return r,d

def dose_metrics(values,rx):
    a=np.sort(np.asarray(values,dtype=float))
    out={'min_gy':float(a[0]),'mean_gy':float(a.mean()),'max_gy':float(a[-1]),'voxels':len(a)}
    for p in (2,5,10,50,95,98):
        # ceil(p*n/100) highest-dose voxels have at least this dose.
        out[f'D{p}_gy']=float(a[len(a)-int(np.ceil(p*len(a)/100))])
    for pct in (95,100,110,120):
        out[f'V{pct}_pct']=float(100*np.count_nonzero(a>=rx*pct/100)/len(a))
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('plan');ap.add_argument('--output');ap.add_argument('--require-feasible',action='store_true')
    args=ap.parse_args(); r,_=Evaluator().evaluate(args.plan)
    text=json.dumps(r,indent=2,allow_nan=False)
    if args.output: Path(args.output).write_text(text+'\n')
    print(text)
    if args.require_feasible and not r['feasible']: raise SystemExit(2)
if __name__=='__main__': main()
