"""Evidence-based progress chart for the discrete contributor trial."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .data import ROOT

def main():
    rr=json.loads((ROOT/'trial/rounding/comparison.json').read_text());local=json.loads((ROOT/'trial/extended-pairs.json').read_text());dec=json.loads((ROOT/'trial/decrement-only.json').read_text());main=json.loads((ROOT/'results/comparison.json').read_text())
    four={r['guard_fraction']:r for r in rr['plans'] if len(r['angles'])==4}
    bound=next(r['evaluation']['objective_gy'] for r in main['plans'] if r['name']=='best_nominal')
    stages=[four[1.]['evaluation']['objective_gy'],four[.5]['evaluation']['objective_gy'],dec['evaluation']['objective_gy'],local['evaluation']['objective_gy']]
    fig,axs=plt.subplots(1,2,figsize=(12.5,5.0),layout='constrained')
    axs[0].plot(range(4),stages,'o-',color='#146d9a',lw=2,ms=7)
    for i,v in enumerate(stages):axs[0].annotate(f'{v:.4f}',(i,v),xytext=(0,9),textcoords='offset points',ha='center')
    axs[0].set(xticks=range(4),xticklabels=['Full dose\nerror guard','Half guard\nverified','Single\ndecrements','Pair\nexchanges'],title='Accepted plans: same 4 beams, 10-MU grid')
    h=local['history'];axs[1].plot([r['step'] for r in h],[r['objective_gy'] for r in h],color='#146d9a',lw=2)
    axs[1].set(xlabel='Accepted discrete move',title='Local search reaches a plateau')
    for ax in axs:
        ax.axhline(bound,color='#555555',ls='--',label='continuous relaxation lower bound')
        ax.set(ylabel='Core mean + healthy-body mean dose (Gy)',ylim=(20.45,21.65));ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False)
    axs[1].legend(fontsize=9,loc='upper right')
    improvement=100*(stages[0]-stages[-1])/stages[0]
    fig.suptitle(f'{improvement:.2f}% computational improvement • synthetic phantom • research only',fontsize=15)
    fig.savefig(ROOT/'results/contributor_progress.png',dpi=160);fig.savefig(ROOT/'results/contributor_progress.svg');plt.close(fig)
    print('Wrote contributor progress figures')
if __name__=='__main__':main()
