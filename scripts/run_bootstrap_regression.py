#!/usr/bin/env python3
"""experiment 4: bootstrap CIs on cross-national regression.

expects a CSV with columns: country, wvs_godimp, relleg, log_gdp_pc
for ~36 countries. path is set via --data or auto-detected.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
    from statsmodels.stats.power import FTestPower
except ImportError:
    print("ERROR: statsmodels not installed. run: pip install statsmodels")
    sys.exit(1)


def r2_ratio(y, x1, x2):
    """R² of y~x1 divided by R² of y~x2"""
    r2_1 = sm.OLS(y, sm.add_constant(x1)).fit().rsquared
    r2_2 = sm.OLS(y, sm.add_constant(x2)).fit().rsquared
    return r2_1 / r2_2 if r2_2 > 0 else np.inf


def find_data():
    """try to find cross-national data CSV"""
    candidates = [
        Path(__file__).resolve().parent.parent / "data" / "cross_national_data.csv",
        Path(__file__).resolve().parent.parent / "cross_national_data.csv",
        Path(__file__).resolve().parent.parent / "data" / "cross_national.csv",
        Path(__file__).resolve().parent.parent / "results" / "cross_national_data.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=str, default=None, help="path to cross-national CSV")
    ap.add_argument("--n_boot", type=int, default=10000)
    args = ap.parse_args()

    data_path = Path(args.data) if args.data else find_data()
    if data_path is None or not data_path.exists():
        print("ERROR: cross-national data CSV not found.")
        print("provide --data /path/to/cross_national_data.csv")
        print("expected columns: country, wvs_godimp, relleg, log_gdp_pc")
        sys.exit(1)

    df = pd.read_csv(data_path)
    print(f"loaded {len(df)} countries from {data_path}")

    # detect column names (flexible matching)
    col_map = {}
    for col in df.columns:
        cl = col.lower().strip()
        if "godimp" in cl or "wvs" in cl:
            col_map["y"] = col
        elif "relleg" in cl or "legislation" in cl:
            col_map["x_leg"] = col
        elif "gdp" in cl or "log_gdp" in cl:
            col_map["x_gdp"] = col

    if len(col_map) < 3:
        print(f"ERROR: could not detect all required columns. found: {col_map}")
        print(f"available columns: {list(df.columns)}")
        sys.exit(1)

    y = df[col_map["y"]].astype(float)
    x_gdp = df[col_map["x_gdp"]].astype(float)
    x_leg = df[col_map["x_leg"]].astype(float)

    # drop rows with any NaN
    mask = y.notna() & x_gdp.notna() & x_leg.notna()
    y, x_gdp, x_leg = y[mask], x_gdp[mask], x_leg[mask]
    print(f"after dropping NaN: {len(y)} countries")

    # original R² ratio
    original_ratio = r2_ratio(y, x_gdp, x_leg)
    print(f"\noriginal R² ratio (GDP/legislation): {original_ratio:.2f}")

    # OLS with HC3 robust SEs
    results = []
    out_lines = []

    model_gdp = sm.OLS(y, sm.add_constant(x_gdp)).fit(cov_type="HC3")
    model_leg = sm.OLS(y, sm.add_constant(x_leg)).fit(cov_type="HC3")
    x_combined = sm.add_constant(pd.DataFrame({
        col_map["x_gdp"]: x_gdp.values,
        col_map["x_leg"]: x_leg.values,
    }))
    model_combined = sm.OLS(y.values, x_combined).fit(cov_type="HC3")

    out_lines.append("--- GDP-only model (HC3) ---")
    out_lines.append(str(model_gdp.summary2().tables[1]))
    out_lines.append(f"R² = {model_gdp.rsquared:.4f}")

    out_lines.append("\n--- Legislation-only model (HC3) ---")
    out_lines.append(str(model_leg.summary2().tables[1]))
    out_lines.append(f"R² = {model_leg.rsquared:.4f}")

    out_lines.append("\n--- Combined model (HC3) ---")
    out_lines.append(str(model_combined.summary2().tables[1]))
    out_lines.append(f"R² = {model_combined.rsquared:.4f}")

    # bootstrap
    np.random.seed(42)
    ratios = []
    for i in range(args.n_boot):
        idx = np.random.choice(len(y), size=len(y), replace=True)
        y_b = y.iloc[idx].values
        x1_b = x_gdp.iloc[idx].values
        x2_b = x_leg.iloc[idx].values
        try:
            r2_1 = sm.OLS(y_b, sm.add_constant(x1_b)).fit().rsquared
            r2_2 = sm.OLS(y_b, sm.add_constant(x2_b)).fit().rsquared
            if r2_2 > 0.01:
                ratios.append(r2_1 / r2_2)
        except Exception:
            pass

    ratios = np.array(ratios)
    ci_low = np.percentile(ratios, 2.5)
    ci_high = np.percentile(ratios, 97.5)
    median_ratio = np.median(ratios)

    out_lines.append(f"\n--- Bootstrap (n={len(ratios)}) ---")
    out_lines.append(f"median R² ratio: {median_ratio:.2f}")
    out_lines.append(f"95% CI: [{ci_low:.2f}, {ci_high:.2f}]")
    out_lines.append(f"original: {original_ratio:.2f}")

    if ci_low > 1.0:
        out_lines.append("\nCI excludes 1.0: outside-option quality explains")
        out_lines.append("significantly more variance than enforcement intensity.")
    else:
        out_lines.append("\nCI includes 1.0: cannot claim significant difference.")
        out_lines.append("soften language to 'substantially more' without the 4.4x claim.")

    # power analysis
    r2_combined = model_combined.rsquared
    f2 = r2_combined / (1 - r2_combined)
    power_analysis = FTestPower()
    power = power_analysis.solve_power(
        effect_size=np.sqrt(f2),
        nobs=len(y),
        alpha=0.05,
        df_num=2,
        df_denom=len(y) - 3,
    )
    out_lines.append(f"\n--- Power analysis ---")
    out_lines.append(f"combined model R² = {r2_combined:.4f}")
    out_lines.append(f"Cohen's f² = {f2:.4f}")
    out_lines.append(f"power at N={len(y)}: {power:.3f}")

    # write output
    out_dir = Path(__file__).resolve().parent.parent / "results" / "bootstrap_regression"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "summary.txt"
    text = "\n".join(out_lines)
    out_path.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
