# %%

import pandas as pd
from lifelines import KaplanMeierFitter,CoxPHFitter

cont=pd.read_csv('cont.csv')
cont_un = pd.read_csv('cont_un.csv')

cont['outcome']= cont['outcomeCount']>1
cont_un['outcome']= cont_un['outcomeCount']>1

kmf = CoxPHFitter()
kmf.fit(cont[['survivalTime','outcome','treatment']], 'survivalTime', event_col='outcome')  
kmf.print_summary()
fig=kmf.plot(hazard_ratios=True)
# %%
cont_un