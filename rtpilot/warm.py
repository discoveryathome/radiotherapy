"""Incremental row generation with retained HiGHS simplex basis."""
import time
import highspy
import numpy as np

def solve(c,A,b,bound,*,tol=1e-7,time_limit=180,initial_rows=256,add_rows=256):
    start=time.perf_counter();cpu=time.process_time();m,n=A.shape
    A=A.tocsr();selected=np.unique(np.r_[np.linspace(0,m-1,min(initial_rows,m),dtype=int),np.arange(max(0,m-3),m)])
    h=highspy.Highs();h.setOptionValue('output_flag',False);h.setOptionValue('threads',1)
    h.setOptionValue('solver','simplex');h.setOptionValue('primal_feasibility_tolerance',tol);h.setOptionValue('dual_feasibility_tolerance',tol)
    h.addVars(n,np.zeros(n),np.full(n,highspy.kHighsInf) if bound is None else np.broadcast_to(bound,(n,)).copy())
    h.changeColsCost(n,np.arange(n,dtype=np.int32),c)
    def add(ids):
        rows=A[ids]
        h.addRows(len(ids),np.full(len(ids),-highspy.kHighsInf),b[ids],rows.nnz,rows.indptr.astype(np.int32),rows.indices.astype(np.int32),rows.data)
    add(selected);order=list(selected);history=[]
    for iteration in range(80):
        remaining=time_limit-(time.perf_counter()-start)
        if remaining<=0:break
        h.setOptionValue('time_limit',remaining);h.run();status=h.getModelStatus()
        if status!=highspy.HighsModelStatus.kOptimal:
            info={'status':2 if status==highspy.HighsModelStatus.kInfeasible else 1,'message':str(status),'history':history,'seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu}
            if status==highspy.HighsModelStatus.kInfeasible:
                _,exists,ray=h.getDualRay()
                if exists:
                    raw=-np.asarray(ray);lam=np.maximum(raw,0);norm=np.max(np.abs(lam))
                    info['farkas']={'rows':list(map(int,order)),'multipliers':(lam/norm).tolist(),'negative_ray_projection_max':float(np.maximum(-raw,0).max())}
            return None,info
        sol=h.getSolution();x=np.array(sol.col_value);v=A@x-b;maximum=float(max(0,v.max()))
        history.append({'round':iteration,'rows':len(order),'objective':float(c@x),'full_max_violation':maximum})
        if maximum<=max(1e-8,5*tol):
            lam=np.array(sol.row_dual);rc=np.array(sol.col_dual)
            dual=float(b[order]@lam)
            if bound is not None:dual+=float((np.broadcast_to(bound,(n,))*np.minimum(rc,0)).sum())
            return x,{'status':0,'message':'Warm-start row-generation LP; full constraint scan passed','history':history,'objective':float(c@x),
                'dual_objective':dual,'numerical_duality_gap':float(c@x-dual),'stationarity_residual':float(np.abs(c-A[order].T@lam-rc).max()),'primal_residual':maximum,
                'final_rows':len(order),'full_rows':m,'seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu,'solver':'highspy '+h.version()}
        v[np.array(order)]=-np.inf
        bad=np.flatnonzero(v>max(1e-8,5*tol))
        if not len(bad):break
        new=bad[np.argsort(-v[bad]/np.maximum(1,np.abs(b[bad])),kind='stable')[:add_rows]]
        add(new);order.extend(new.tolist())
    return None,{'status':1,'message':'Warm separation budget exhausted','history':history,'seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu}
