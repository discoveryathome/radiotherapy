"""Second LP solver with constraint/bound scaling and explicit dual diagnostics."""
import time
import numpy as np
from scipy import sparse
import clarabel

def solve(c,A,b,bound,tol=1e-9):
    start=time.perf_counter();n=A.shape[1]
    # Rescale fluence to roughly O(1) and normalize every row by RHS magnitude.
    scale=1000. if np.max(np.abs(b[:min(100,len(b))]))>10 else 20.
    AA=sparse.vstack([A*scale,-sparse.eye(n)],format='csc');bb=np.r_[b,np.zeros(n)]
    if bound is not None:
        AA=sparse.vstack([AA,sparse.eye(n)],format='csc');bb=np.r_[bb,np.full(n,bound/scale)]
    norm=np.maximum(1,np.abs(bb));AA=sparse.diags(1/norm)@AA;bb=bb/norm
    settings=clarabel.DefaultSettings();settings.verbose=False;settings.max_iter=100;settings.time_limit=120.
    settings.max_threads=1;settings.tol_gap_abs=tol;settings.tol_gap_rel=tol;settings.tol_feas=tol
    solver=clarabel.DefaultSolver(sparse.csc_matrix((n,n)),c*scale,AA.tocsc(),bb,[clarabel.NonnegativeConeT(len(bb))],settings)
    r=solver.solve();status=str(r.status)
    info={'status':0 if status=='Solved' else 2 if status=='PrimalInfeasible' else 4,'message':status,'iterations':r.iterations,'seconds':time.perf_counter()-start,'solver':'Clarabel '+clarabel.__version__}
    if status!='Solved':return None,info
    raw=np.array(r.x)*scale
    # Projection of tiny negative roundoff is explicit; final evaluation uses projected x.
    x=np.maximum(raw,0)
    dual=-float(bb@np.array(r.z))
    info.update(objective=float(c@x),dual_objective=dual,numerical_duality_gap=float(c@x-dual),
        stationarity_residual=float(np.abs(c*scale+AA.T@np.array(r.z)).max()),
        primal_residual=float(max(0,(A@x-b).max())),projection_max_mu=float(np.abs(x-raw).max()))
    return x,info
