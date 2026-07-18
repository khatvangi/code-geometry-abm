import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.getcwd(), "src"))
from regime_classifier import classify_dataframe
df = pd.read_csv("recon/exogenous_delta/sweep_seed_results.csv")
d0   = next(c for c in ["delta0","delta_outside_degrade","delta_baseline"] if c in df.columns)
pcol = next(c for c in ["max_punish","max_punish_intensity_step"] if c in df.columns)
dfc = classify_dataframe(df, schema="hierarchical", exit_col="final_exit_rate",
                         punish_col=pcol, enforcer_col="enforcer_punish_share")
reg = "regime_hierarchical"
print("capture rate by imposed delta (pooled):")
print(dfc.groupby(d0)[reg].apply(lambda s:(s=="CAPTURE").mean()).round(3).to_string())
print("\nmedian final_exit_rate by imposed delta:")
print(dfc.groupby(d0)["final_exit_rate"].median().round(3).to_string())
cells = dfc.groupby([d0,"sigma","pi_reward"])[reg].apply(lambda s:(s=="CAPTURE").mean())
print(f"\ncells={len(cells)}  ==0:{(cells==0).sum()}  ==1:{(cells==1).sum()}  INTERMEDIATE:{((cells>0)&(cells<1)).sum()}")
print("\ncapture rate by (imposed delta rows x sigma cols) at pi=0.25:")
sub = dfc[dfc["pi_reward"]==0.25]
print(sub.groupby([d0,"sigma"])[reg].apply(lambda s:(s=="CAPTURE").mean()).round(2).unstack().to_string())
