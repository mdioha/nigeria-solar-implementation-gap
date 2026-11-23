#!/usr/bin/env python3
"""Read-only consistency check of the delivered workbooks and generated JSON results.

Runs with only the Python standard library plus openpyxl (pip install openpyxl).
Not an external-source verification and not a test of scientific causal validity.

Checked:
  - LCOE Europe value (workbook) matches results_summary.json, Europe WACC = 4.2%
  - AFSIA May-primary / January-sensitivity columns reconcile with JSON
    (access-relevant stock, five-category totals, residuals, investments,
    DARES shares, invariant no-stock-credit figure)
  - Access gap preferred (no stock credit) and full-credit sensitivity
  - PIGI preferred six-indicator mean and five-indicator sensitivity (supplementary sheet and standalone file)
  - Diesel-parity 11 GW midpoint and gross cost differential
  - 2030 scenario capacity path endpoints
  - No input cell in the supplementary workbook is a constant written as a formula
  - No cached Excel error values anywhere in the 14-sheet supplementary workbook
"""
import json
import pathlib
import sys

try:
    import openpyxl
except ImportError:
    sys.exit("openpyxl is required: pip install openpyxl")

here = pathlib.Path(__file__).resolve().parent
root = here / "data"
jsrc = here / "results_summary.json"
if not jsrc.exists():
    jsrc = here / "expected_outputs" / "results_summary.json"
j = json.loads(jsrc.read_text())
w = openpyxl.load_workbook(root / "Nigeria_Solar_Supplementary_File.xlsx", data_only=True)
p = openpyxl.load_workbook(root / "Nigeria_Solar_PIGI_Revised.xlsx", data_only=True)

checks = []


def ck(name, a, b, tol=1e-6):
    ok = a is not None and b is not None and abs(a - b) < tol
    checks.append((name, ok, a, b))
    if not ok:
        print(f"FAIL {name}: workbook={a!r} expected={b!r}")


lcoe = w["LCOE Analysis"]
ck("Europe WACC 4.2%", lcoe["E8"].value, 0.042, 1e-12)
ck("Europe LCOE vs JSON", lcoe["E19"].value, j["lcoe"]["Europe PV"]["LCOE_USD_per_kWh"], 1e-9)

cap = w["Capacity Reconciliation"]
ck("May access-relevant stock 831.48", cap["B11"].value, 831.48)
ck("May five-category total 4814.44", cap["B13"].value, 4814.44)

ver = w["AFSIA Version Sensitivity"]  # column B = May 2026 final (primary), C = January build (superseded)
ck("May stock (version sheet)", ver["B9"].value, 831.48)
ck("January stock (version sheet)", ver["C9"].value, 885.58)
ck("May total (version sheet)", ver["B10"].value, 4814.44)
ck("January total (version sheet)", ver["C10"].value, 1191.41)
ck("May full-credit investment vs JSON", ver["B13"].value,
   j["afsia_version_sensitivity"]["may_final_primary"]["optimistic_full_credit_investment_usd_bn"])
ck("January full-credit investment vs JSON", ver["C13"].value,
   j["afsia_version_sensitivity"]["january_build_superseded"]["optimistic_full_credit_investment_usd_bn"])
ck("May DARES share vs JSON", ver["B14"].value * 100,
   j["access_gap"]["dares_public_finance_share_full_credit_pct"])
ck("No-credit figure invariant across builds", ver["B15"].value, ver["C15"].value, 1e-8)

acc = w["Access Gap"]
ck("Full-credit investment vs JSON", acc["C18"].value,
   j["access_gap"]["optimistic_full_stock_credit_investment_usd_bn"])
ck("Preferred no-credit investment vs JSON", acc["C25"].value,
   j["access_gap"]["preferred_no_stock_credit_investment_usd_bn"])

ck("PIGI preferred six-indicator mean vs JSON", w["PIGI Index"]["D29"].value,
   j["pigi"]["preferred_six_indicator_mean"], 1e-9)
ck("PIGI five-indicator sensitivity vs JSON", w["PIGI Index"]["D33"].value,
   j["pigi"]["five_indicator_excluding_grid_solar_row_mean"], 1e-9)
ck("Grid-connected solar numerator is AFSIA utility-scale", w["PIGI Index"]["D12"].value, 12.8, 1e-12)
ck("Standalone PIGI matches", p["PIGI_Revised"]["D29"].value,
   j["pigi"]["preferred_six_indicator_mean"], 1e-9)

dsl = w["Diesel Parity"]
ck("Fleet-consistent unit cost vs JSON", dsl["C38"].value,
   j["diesel_parity"]["fleet_consistent_unit_cost_usd_per_kwh"], 1e-9)
ck("Fleet-consistent gross contrast vs JSON", dsl["C39"].value,
   j["diesel_parity"]["fleet_consistent_gross_contrast_usd_bn_NOT_net_savings"], 1e-9)
ck("In-progress interim mean", w["PIGI Index"]["D18"].value, 0.588717608225395, 1e-9)
ck("In-progress full mean", w["PIGI Index"]["D19"].value, 0.622776666666667, 1e-9)
ck("AFSIA May stock derives from inputs", w["AFSIA Version Sensitivity"]["B9"].value, 831.48)
ck("Access_Gap stock links to reconciliation", w["Access Gap"]["C15"].value, 831.48)
ck("Generator midpoint 11 GW", dsl["C24"].value, 11, 1e-9)
ck("Gross differential vs JSON", dsl["C27"].value,
   j["diesel_parity"]["theoretical_cost_difference_usd_bn_NOT_net_savings"])

scen = w["Scenarios_2030"]
for scenario, row in [("BAU", 14), ("Partial Reform", 15), ("Full Reform", 16)]:
    ck(f"2030 endpoint {scenario}", scen[f"I{row}"].value,
       j["scenarios"]["capacity_paths_mwp"][scenario][-1])

# Input cells must hold literal values; a constant written as a formula (e.g. "=12.8")
# would hide where an input comes from.
import re as _re
wf = openpyxl.load_workbook(root / "Nigeria_Solar_Supplementary_File.xlsx")
const_formulas = [f"{ws.title}!{c.coordinate}" for ws in wf.worksheets for row in ws.iter_rows()
                  for c in row if isinstance(c.value, str) and _re.fullmatch(r"=\s*-?[\d.]+\s*", c.value)]
checks.append(("Input cells are literal values, not constant formulas", not const_formulas, len(const_formulas), 0))
if const_formulas:
    print("FAIL constant-valued formulas:", const_formulas)

ERRS = {"#VALUE!", "#REF!", "#DIV/0!", "#NUM!", "#NAME?", "#N/A", "#NULL!"}
errors = []
for ws in w.worksheets:
    for row in ws.iter_rows(min_row=1, max_row=65, min_col=1, max_col=15):
        for cell in row:
            if isinstance(cell.value, str) and cell.value in ERRS:
                errors.append((ws.title, cell.coordinate, cell.value))
if errors:
    for e in errors:
        print("FAIL cached error value:", e)

failed = [c for c in checks if not c[1]]
if failed or errors:
    sys.exit(f"{len(failed)} value check(s) and {len(errors)} error-cell(s) failed.")
print(f"PASS: {len(checks)}/{len(checks)} value checks; no cached Excel error values in the "
      f"{len(w.sheetnames)}-sheet supplementary workbook; standalone PIGI consistent.")
print("NOTE: source provenance, structural model uncertainty, expert elicitation and "
      "observed dispatch are not validated by this script.")
