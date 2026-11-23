# Policies without Power? Quantifying Nigeria's Solar Energy Implementation Gap

Reproducibility code and data for:

> Dioha, I.J., Ekene, C., Dioha, M.O. *Policies without Power? Quantifying Nigeria's
> Solar Energy Implementation Gap.* Solar Compass (revised manuscript under review,
> SOLCOM-D-26-00123).

This repository regenerates every computed result, figure and machine-readable
output in the paper from a single input file, and verifies the delivered
supplementary workbooks against those outputs.

## Quick start

```bash
pip install -r requirements.txt
python nigeria_solar_calcs.py        # all 7 figures + results_summary.json
python lcoe_monte_carlo.py           # Monte Carlo LCOE percentiles
python ahp_sensitivity_reproduce.py  # 729-case AHP perturbation analysis
python validate_package.py           # 30 checks against the workbooks
```

## Contents

| Path | Description |
|---|---|
| `model_inputs.json` | Single source of truth: every model input with provenance notes |
| `nigeria_solar_calcs.py` | Regenerates all 7 figures (`figures/`) and `results_summary.json` (LCOE, diesel parity, grid losses, access gap, PIGI, AHP, 2030 scenarios) |
| `lcoe_monte_carlo.py` | Seeded Monte Carlo (10,000 draws, triangular +/-20% on CAPEX, WACC, capacity factor) for the LCOE uncertainty bands |
| `ahp_sensitivity_reproduce.py` | Enumerates all 729 one-step perturbations of the AHP judgment matrix; writes `AHP_sensitivity_cases.csv` |
| `validate_package.py` | Read-only consistency check: 30 assertions tying the workbooks in `data/` to `results_summary.json`, plus a cached-error scan |
| `data/` | The analysis workbooks published with the article: the 14-sheet supplementary file, the standalone PIGI extract, and the AHP Judgment Audit (`AHP_Judgment_Audit.xlsx`: the provenance and rationale for each of the six pairwise judgments, and all 729 perturbed matrices with their weights, consistency ratios and rankings) |
| `expected_outputs/` | Reference copies of `results_summary.json`, `AHP_sensitivity_cases.csv` and the 7 published figures, for diffing against your regenerated outputs |

## What to expect when reproducing

- `results_summary.json` regenerates **byte-identical** to
  `expected_outputs/results_summary.json`.
- The portability test is **numerical and visual equivalence**, not bitwise
  identity: every computed value must match, and each figure must show the
  same data and labels as `expected_outputs/figures/`. In the tested
  environment below (installed with the pinned `requirements.txt`) all 7
  figures also regenerate pixel-identically. The script pins matplotlib's
  bundled DejaVu Sans font so that results do not depend on system fonts;
  other matplotlib, FreeType or Pillow builds can still change glyph
  anti-aliasing slightly, which is not a content difference.
- `lcoe_monte_carlo.py` is seeded (`numpy` seed 42) and prints
  `P10=0.1563  P50=0.1863  P90=0.2213  mean=0.1879` (rounded in the paper to
  0.156/0.186/0.221).
- `ahp_sensitivity_reproduce.py` reports 710 of 729 perturbed matrices with
  CR < 0.10, with the finance criterion ranked first in 689 (97.0%). The
  consistency-ratio column of the CSV may differ from the reference copy in
  the last one or two decimal digits across platforms (floating-point
  rounding); every weight, flag and count is unaffected.

Developed and tested with Python 3.13.18, numpy 2.5.3, matplotlib 3.11.2,
openpyxl 3.1.5 and Pillow 12.3.0 (pinned in `requirements.txt`).

## Scope

The scripts reproduce the paper's computed quantities. They do not re-derive
the externally sourced inputs (NERC, AFSIA, Ember/statistical, ESMAP, IRENA,
World Bank values), whose provenance is recorded in `model_inputs.json` and in
the article's supplementary reference tracker. The analysis is descriptive and
scenario-based, not causal; see Section 5.4 of the paper for limitations.

## License

Code is released under the MIT License (see `LICENSE`). The workbooks in
`data/` and the reference outputs are part of the article's supplementary
material; please cite the paper when using them.
