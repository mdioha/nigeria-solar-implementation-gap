"""Monte Carlo uncertainty analysis for the Nigerian utility-scale solar LCOE.
10,000 draws; independent triangular distributions (min/mode/max = -20%/base/+20%)
on CAPEX, WACC and capacity factor; O&M and project life held fixed.
Results reported in the Sensitivity sheet of the supplementary workbook."""
import numpy as np
np.random.seed(42)
N = 10000
def tri(base): return np.random.triangular(0.8*base, base, 1.2*base, N)
capex, wacc, cf = tri(1600.0), tri(0.18), tri(0.19)
om, life = 18.0, 25
crf = wacc*(1+wacc)**life/((1+wacc)**life-1)
lcoe = (capex*crf + om)/(8760*cf)
p10, p50, p90 = np.percentile(lcoe, [10, 50, 90])
print(f"P10={p10:.4f}  P50={p50:.4f}  P90={p90:.4f}  mean={lcoe.mean():.4f}")
