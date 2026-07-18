import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.getcwd(), "src"))
from regime_classifier import classify_dataframe

ARMS = {
    "legacy": "recon/factorial_shock_off/sweep_seed_results.csv",
    "k1.5":   "recon/decoupled_k1.5/sweep_seed_results.csv",
    "k3.0":   "recon/decoupled_k3.0/sweep_seed_results.csv",
    "k6.0":   "recon/decoupled_k6.0/sweep_seed_results.csv",
}

def find_col(df, cands):
    return next((c for c in cands if c in df.columns), None)

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k/n; d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (max(0,c-h), min(1,c+h))

for name, path in ARMS.items():
    df = pd.read_csv(path)
    eta = find_col(df, ["eta_delta_drift","eta","eta_drift"])
    d0  = find_col(df, ["delta0","delta_0","delta_baseline","delta_outside_degrade"])
    dcol= find_col(df, ["final_current_delta","final_delta","current_delta"])
    pcol= find_col(df, ["max_punish","max_punish_intensity_step","punish_intensity"])
    dfc = classify_dataframe(df, schema="hierarchical",
              exit_col="final_exit_rate", punish_col=pcol,
              enforcer_col="enforcer_punish_share")
    reg = "regime_hierarchical"
    don = dfc[dfc[eta] > 0]
    k, n = int((don[reg]=="CAPTURE").sum()), len(don)
    lo, hi = wilson(k, n)
    cells = don.groupby([eta, d0, "sigma", "pi_reward"])[reg].apply(lambda s: (s=="CAPTURE").mean())
    n0  = int((cells==0).sum()); n1 = int((cells==1).sum())
    mid = int(((cells>0) & (cells<1)).sum())
    print(f"\n=== {name} ===  (cols: eta={eta}, d0={d0}, punish={pcol}, delta={dcol})")
    print(f"drift-on CAPTURE: {k}/{n} = {k/n:.3f}  (95% CI {lo:.3f}-{hi:.3f})")
    print(f"cells={len(cells)}  rate==0:{n0}  rate==1:{n1}  INTERMEDIATE:{mid}")
    if dcol:
        cr = dfc[dfc[reg]=="CAPTURE"][dcol]
        print(f"median final delta in capture runs: {cr.median():.4f}" if len(cr) else "no capture runs")
    sp = don.groupby(["sigma","pi_reward"])[reg].apply(lambda s: (s=="CAPTURE").mean()).round(2)
    print("sigma x pi capture rate:\n" + sp.to_string())
