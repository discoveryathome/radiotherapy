"""Standalone scientific figures from independently recomputed dose."""
import argparse
import json
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .data import ROOT
from .evaluate import Evaluator

COLORS={'OuterTarget':'#b03b3b','Core':'#146d9a','HealthyBody':'#4b8b55'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',default='results');args=ap.parse_args()
    folder=ROOT/args.results;payload=json.loads((folder/'comparison.json').read_text());ev=Evaluator()
    allrows={r['name']:r for r in payload['plans']}
    extra=folder/'robust-five.json'
    if extra.exists():
        rr=json.loads(extra.read_text())
        if 'path' in rr:allrows['robust_five']={'name':'robust_five','path':rr['path']}
    labels={'uniform':'uniform (infeasible)','quadratic_penalty':'quadratic penalty (infeasible)','subset_0_72_144_216_288':'five-beam LP','best_nominal':'best four-beam LP','robust_five':'five-beam gain-robust LP'}
    names=[n for n in ['uniform','quadratic_penalty','subset_0_72_144_216_288','best_nominal','robust_five'] if n in allrows]
    doses={n:ev.evaluate(ROOT/allrows[n]['path'])[1] for n in names}
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(1,3,figsize=(14,4.6),layout='constrained')
    for ax,structure in zip(axs,COLORS):
        for name,d in doses.items():
            values=np.sort(d[ev.vois[structure]])
            thresholds=np.linspace(0,70,701)
            volume=100*(len(values)-np.searchsorted(values,thresholds,side='left'))/len(values)
            ax.plot(thresholds,volume,label=labels.get(name,name.replace('_',' ')),lw=1.6)
        ax.set(title=structure,xlabel='Dose (Gy)',ylabel='Volume receiving at least dose (%)',ylim=(0,101),xlim=(0,70));ax.grid(alpha=.2)
    axs[0].axvline(50,color='black',alpha=.4,ls=':');axs[0].axvline(55,color='black',alpha=.4,ls='--');axs[1].axvline(25,color='black',alpha=.4,ls='--');axs[0].legend(fontsize=8)
    fig.suptitle('CORT synthetic phantom • dose-volume histograms • research only',fontsize=14)
    fig.savefig(folder/'dvh.png',dpi=160);fig.savefig(folder/'dvh.svg');plt.close(fig)
    # Choose the slice with most target voxels by a fixed geometry rule.
    target=ev.vois['OuterTarget'];sl=int(np.argmax(np.bincount(target//(167*167),minlength=129)))
    show=[n for n in ['subset_0_72_144_216_288','best_nominal','robust_five'] if n in doses]
    fig,axs=plt.subplots(1,len(show),figsize=(5*len(show),4.7),layout='constrained',squeeze=False)
    for ax,name in zip(axs[0],show):
        plane=doses[name].reshape((167,167,129),order='F')[:,:,sl]
        im=ax.imshow(plane,vmin=0,vmax=65,cmap='inferno',origin='upper')
        for structure,color in COLORS.items():
            if structure=='HealthyBody':continue
            mask=np.zeros(167*167*129,dtype=np.uint8);mask[ev.vois[structure]]=1
            ax.contour(mask.reshape((167,167,129),order='F')[:,:,sl],levels=[.5],colors=[color],linewidths=1.3)
        ax.set(xlim=(45,120),ylim=(120,45),xlabel='LR voxel index',ylabel='AP voxel index',title=labels.get(name,name.replace('_',' ')))
    fig.colorbar(im,ax=list(axs[0]),label='Dose (Gy)',shrink=.8)
    fig.suptitle(f'Synthetic phantom dose • axial slice {sl} (zero-based) • common color scale',fontsize=13)
    fig.savefig(folder/'dose_maps.png',dpi=160);plt.close(fig)
    rows=[]
    for r in payload['plans']:
        m=r['evaluation'];t=m['metrics']['OuterTarget'];c=m['metrics']['Core']
        rows.append({'name':r['name'],'profile':r['profile'],'budget':m['beam_budget'],'feasible':m['feasible'],'score_gy':m['objective_gy'],'target_D95_gy':t['D95_gy'],'target_D2_gy':t['D2_gy'],'core_mean_gy':c['mean_gy'],'core_D5_gy':c['D5_gy'],'healthy_mean_gy':m['metrics']['HealthyBody']['mean_gy'],'tg119_reference_goals_pass':m['tg119_reference_goals_pass']})
    with (folder/'comparison.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    subset=[r for r in rows if r['name'].startswith('subset')]
    fig,ax=plt.subplots(figsize=(7,4.5),layout='constrained')
    for k in range(1,6):
        rr=[r for r in subset if r['budget']==k and r['feasible']]
        if rr: ax.scatter([k]*len(rr),[r['score_gy'] for r in rr],color='#146d9a',alpha=.6,s=40)
    best=[min((r for r in subset if r['budget']==k and r['feasible']),key=lambda r:r['score_gy'],default=None) for k in range(1,6)]
    ax.plot([r['budget'] for r in best if r],[r['score_gy'] for r in best if r],color='#b03b3b',marker='o',label='best enumerated feasible subset')
    ax.set(xlabel='Allowed beam directions',ylabel='Core mean + healthy-body mean dose (Gy)',title='How much healthy-tissue dose does a beam budget cost?',xticks=range(1,6));ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.savefig(folder/'beam_tradeoff.png',dpi=160);plt.close(fig)
    print('Wrote DVHs, dose maps, beam tradeoff, and comparison CSV')
if __name__=='__main__':main()
