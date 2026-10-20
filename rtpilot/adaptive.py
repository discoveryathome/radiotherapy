"""Constraint generation: reduced LPs, with exhaustive full-constraint separation."""
import time
import warnings
import numpy as np
from scipy.optimize import linprog

def solve(c,A,b,bound,*,tol=1e-7,initial_rows=128,add_rows=128,max_rounds=60,time_limit=90):
    start=time.perf_counter();m=A.shape[0]
    selected=np.unique(np.r_[np.linspace(0,m-1,min(initial_rows,m),dtype=int),np.arange(max(0,m-3),m)])
    history=[];last=None
    for iteration in range(max_rounds):
        remaining=time_limit-(time.perf_counter()-start)
        if remaining<=0:break
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Unrecognized options detected')
            r=linprog(c,A_ub=A[selected],b_ub=b[selected],bounds=(0,bound),method='highs-ipm',
                options={'primal_feasibility_tolerance':tol,'dual_feasibility_tolerance':tol,'ipm_optimality_tolerance':1e-10,'time_limit':remaining,'threads':1})
        last=r
        if not r.success:
            return None,{'status':int(r.status),'message':r.message,'history':history,'seconds':time.perf_counter()-start}
        violation=np.asarray(A@r.x-b)
        maximum=float(max(0,violation.max()))
        history.append({'round':iteration,'rows':len(selected),'objective':float(c@r.x),'full_max_violation':maximum})
        if maximum<=max(1e-8,5*tol):
            dual=float(b[selected]@r.ineqlin.marginals)
            if bound is not None:dual+=float(bound*r.upper.marginals.sum())
            stationarity=c-A[selected].T@r.ineqlin.marginals-r.lower.marginals-r.upper.marginals
            return r.x,{'status':0,'message':'Reduced LP optimal; all original constraints checked','iterations':int(r.nit),'history':history,
                'seconds':time.perf_counter()-start,'objective':float(c@r.x),'dual_objective':dual,
                'numerical_duality_gap':float(c@r.x-dual),'stationarity_residual':float(np.abs(stationarity).max()),'primal_residual':maximum,'final_rows':len(selected),'full_rows':m}
        # Only unseen rows can add information. Violations in selected rows beyond
        # tolerance indicate a numerical failure, not a successful separation.
        violation[selected]=-np.inf
        new=np.flatnonzero(violation>max(1e-8,5*tol))
        if not len(new):
            return None,{'status':4,'message':'Selected constraints violate full-grid tolerance','history':history,'seconds':time.perf_counter()-start}
        order=np.argsort(-violation[new]/np.maximum(1,np.abs(b[new])),kind='stable')
        selected=np.union1d(selected,new[order[:add_rows]])
    return None,{'status':1,'message':'Constraint-generation budget exhausted','history':history,'seconds':time.perf_counter()-start}
