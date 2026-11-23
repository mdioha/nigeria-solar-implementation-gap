"""Reproduce AHP Judgment Audit 729-case author-defined robustness calculation.
Not an elicited expert panel or probabilistic confidence interval.
Requires numpy; Python 3.10+.
"""
import itertools, csv, numpy as np
from pathlib import Path
base=[(0,1,2),(0,2,3),(0,3,4),(1,2,2),(1,3,3),(2,3,2)]
rows=[]
for scenario,inputs in enumerate(itertools.product(*[(max(1,v-1),v,v+1) for _,_,v in base]),1):
    a=np.ones((4,4))
    for (i,j,_),value in zip(base,inputs):
        a[i,j]=value;a[j,i]=1/value
    g=np.exp(np.log(a).mean(axis=1)); w=g/g.sum()
    eigenvalue=max(np.linalg.eigvals(a).real)
    cr=((eigenvalue-4)/3)/0.9
    rows.append([scenario,*inputs,*map(float,w),float(cr),int(np.argmax(w)==0),int(cr<0.1)])
valid=[row for row in rows if row[-1]==1]
print(f'Total = {len(rows)}; consistent CR<0.10 = {len(valid)}; finance first among consistent = {sum(x[-2] for x in valid)}')
print('Financing priority range among consistent: ', min(x[7] for x in valid),max(x[7] for x in valid))
with open(Path(__file__).with_name('AHP_sensitivity_cases.csv'),'w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['id','F/R','F/I','F/T','R/I','R/T','I/T','F weight','R weight','I weight','T weight','CR','F first','CR<.10']);writer.writerows(rows)
