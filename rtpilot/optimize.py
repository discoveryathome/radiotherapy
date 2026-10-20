"""Conventional LP/QP and discrete beam-subset search. Research use only."""
import time
import json
import numpy as np
from scipy import sparse
from scipy.optimize import linprog, minimize
from .data import ROOT,ANGLES,digest,write_json

class Planner:
    def __init__(self,D,vois,beam_ids,cfg):
        self.D=D;self.vois=vois;self.beam_ids=beam_ids;self.cfg=cfg
        self.T=D[vois['OuterTarget']];self.C=D[vois['Core']]
        self.means={name:np.asarray(D[ids].mean(axis=0)).ravel() for name,ids in vois.items()}

    def formulation(self,angles,gains=(1.,),core_weight=None):
        cfg=self.cfg;cols=np.flatnonzero(np.isin(self.beam_ids,angles))
        low=min(gains);high=max(gains)
        A=[-self.T,self.T,self.C]
        b=[np.full(self.T.shape[0],-cfg['target_min_gy']/low),np.full(self.T.shape[0],cfg['target_max_gy']/high),np.full(self.C.shape[0],cfg['core_max_gy']/high)]
        for key,name in [('core_mean_max_gy','Core'),('healthy_mean_max_gy','HealthyBody')]:
            if cfg.get(key) is not None:
                A.append(sparse.csr_matrix(self.means[name][None,:]));b.append(np.array([cfg[key]/high]))
        if cfg.get('max_total_beamlet_mu') is not None:
            A.append(sparse.csr_matrix(np.ones((1,418))));b.append(np.array([cfg['max_total_beamlet_mu']]))
        weights=dict(cfg['objective_weights'])
        if core_weight is not None: weights['Core']=core_weight
        c=sum(w*self.means[name] for name,w in weights.items())
        return c[cols],sparse.vstack(A,format='csr')[:,cols],np.concatenate(b),cols

    def solve(self,angles,*,gains=(1.,),core_weight=None,method='warm',tol=1e-7):
        t=time.perf_counter();c,A,b,cols=self.formulation(angles,gains,core_weight)
        if method=='warm':
            from .warm import solve
            xx,info=solve(c,A,b,self.cfg.get('max_beamlet_mu'),tol=tol)
            info.update(angles=list(angles),gains=list(gains),core_weight=core_weight,method=method)
            if xx is None:return None,info
            x=np.zeros(418);x[cols]=xx
            return x,info
        if method=='clarabel':
            from .conic import solve
            xx,info=solve(c,A,b,self.cfg.get('max_beamlet_mu'),tol=min(tol,1e-9))
            info.update(angles=list(angles),gains=list(gains),core_weight=core_weight,method=method)
            if xx is None:return None,info
            x=np.zeros(418);x[cols]=xx
            return x,info
        if method=='adaptive':
            from .adaptive import solve
            xx,info=solve(c,A,b,self.cfg.get('max_beamlet_mu'),tol=tol)
            info.update(angles=list(angles),gains=list(gains),core_weight=core_weight,method=method)
            if xx is None:return None,info
            x=np.zeros(418);x[cols]=xx
            return x,info
        result=linprog(c,A_ub=A,b_ub=b,bounds=(0,self.cfg.get('max_beamlet_mu')),method=method,
            options={'dual_feasibility_tolerance':tol,'primal_feasibility_tolerance':tol,'time_limit':300,'threads':1})
        info={'angles':list(angles),'status':int(result.status),'message':result.message,'seconds':time.perf_counter()-t,'iterations':int(result.nit),'gains':list(gains),'core_weight':core_weight,'method':method}
        if result.success:
            x=np.zeros(418);x[cols]=result.x
            # Numerical LP bound derived from marginals, not an exact mathematical certificate.
            dual=float(b@result.ineqlin.marginals)
            if self.cfg.get('max_beamlet_mu') is not None:
                dual+=float(self.cfg['max_beamlet_mu']*result.upper.marginals.sum())
            stationarity=c-A.T@result.ineqlin.marginals-result.lower.marginals-result.upper.marginals
            info.update(objective=float(c@result.x),dual_objective=dual,
                numerical_duality_gap=float(c@result.x-dual),stationarity_residual=float(np.max(np.abs(stationarity))),
                primal_residual=float(max(0,np.max(A@result.x-b))))
            return x,info
        return None,info

    def quadratic(self):
        # Standard nonnegative weighted squared-dose-error baseline, not hard-constrained.
        cfg=self.cfg;t=time.perf_counter();rx=cfg['prescription_gy']
        H=np.zeros((418,418));g=np.zeros(418)
        for name,w in [('OuterTarget',100.),('Core',1.),('HealthyBody',.1)]:
            A=self.D[self.vois[name]]
            H+=w*(A.T@A).toarray()/A.shape[0]
            if name=='OuterTarget': g+=w*rx*self.means[name]
        scale=rx*rx
        def fun(x):
            return (float(x@H@x-2*g@x)/scale,(2*H@x-2*g)/scale)
        r=minimize(fun,np.full(418,rx/.051067),jac=True,method='L-BFGS-B',bounds=[(0,cfg['max_beamlet_mu'])]*418,
            options={'ftol':1e-13,'gtol':1e-9,'maxiter':3000,'maxls':40})
        return r.x,{'method':'L-BFGS-B quadratic penalty','success':bool(r.success),'iterations':r.nit,'seconds':time.perf_counter()-t,'message':r.message,'weights':{'target_squared_error':100,'core_squared_dose':1,'healthy_squared_dose':.1}}

def save_plan(path,x,profile,budget,method):
    write_json(path,{'schema':'cort-plan/v1','profile':profile,'config_sha256':digest(ROOT/f'config/{profile}.json'),
        'data_sha256':digest(ROOT/'data/manifest.json'),'angles':list(ANGLES),'beam_budget':budget,
        'fluence_mu':np.asarray(x).tolist(),'method':method,'research_only':True})
