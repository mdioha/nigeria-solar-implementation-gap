#!/usr/bin/env python3
"""Recreate updated Nigeria solar results_summary.json and all seven figures.

Run from anywhere: python python_code/nigeria_solar_calcs.py
Inputs: model_inputs.json in this folder. No Excel/Word editing, no undocumented input overrides.
The 2025 Ember PV series is statistical and NOT verified as on-grid utility-scale.
All scenario outputs and generator contrasts are conditional, NOT measured savings/abatement.
"""
from __future__ import annotations
import json, math, pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.family']='DejaVu Sans'  # bundled with matplotlib; pinned so figures reproduce identically across systems

HERE=pathlib.Path(__file__).resolve().parent
inp=json.loads((HERE/'model_inputs.json').read_text())
FIG=HERE/'figures'; FIG.mkdir(exist_ok=True)

def crf(r,n):return r*(1+r)**n/((1+r)**n-1)
def pv_lcoe(a):return (a['capex_per_kW']*crf(a['wacc'],a['project_life_yr'])+a['om_per_kW_yr'])/(8760*a['capacity_factor'])
def save(fig,name):
 fig.tight_layout();fig.savefig(FIG/name,dpi=220);plt.close(fig)

results={'model_version':inp['model_version'], 'critical_qualification':inp['basis_note']}
results['lcoe']={k:dict(v,LCOE_USD_per_kWh=pv_lcoe(v)) for k,v in inp['lcoe'].items()}
nig=inp['lcoe']['Nigeria']; counter=dict(nig,wacc=0.12)
results['counterfactual_nigeria_lcoe']=pv_lcoe(counter)
fig,ax=plt.subplots(figsize=(7,4))
keys=list(inp['lcoe']);lv=[results['lcoe'][x]['LCOE_USD_per_kWh'] for x in keys]
ax.bar(keys,lv);ax.axhline(results['counterfactual_nigeria_lcoe'],ls='--',color='0.4',label='Nigeria at 12% WACC')
for i,y in enumerate(lv):ax.text(i,y+.004,f'${y:.3f}',ha='center')
ax.set_ylim(0,0.24);ax.set_ylabel('Modeled LCOE (US$/kWh)');ax.legend(fontsize=9);save(fig,'fig1_lcoe_comparison.png')

P=inp['pigi_full_target']; p5=[x for i,x in enumerate(P) if i!=4]
results['pigi']={'preferred_six_indicator_mean':float(np.mean(P)), 'five_indicator_excluding_grid_solar_row_mean':float(np.mean(p5)), 'six_indicator_median':float(np.median(P)), 'grid_solar_row_index':4, 'grid_solar_numerator':inp['pigi_grid_solar_numerator_source'], 'grid_solar_row_pigi_onGrid_upper_bound':float(1-inp['pigi_grid_solar_onGrid_upper_bound_mw']/5000)}
fig,ax=plt.subplots(figsize=(9,4.2)); colors=['C0']*6
ax.bar(range(6),P,color=colors);ax.set_xticks(range(6),inp['pigi_labels'],rotation=25,ha='right',fontsize=8);ax.axhline(.7,ls=':',color='0.5');ax.set_ylabel('Full-target PIGI (0 to 1)');save(fig,'fig2_pigi.png')

scores=inp['policy_scores']; countries=list(scores)
results['policy_scoring']={'score_totals':{k:sum(v) for k,v in scores.items()},'score_stress_ranges':{k:[sum(max(0,x-1) for x in v),sum(min(10,x+1) for x in v)] for k,v in scores.items()},'only_bottom_rank_robust_to_independent_perturbation':True}
fig=plt.figure(figsize=(7,6));ax=fig.add_subplot(111,polar=True)
labels=['Regulatory','Auction/FIT','Coordination','Finance','Grid','QA','Prosumer','Manufacturing']
a=np.linspace(0,2*np.pi,8,endpoint=False).tolist(); xx=a+[a[0]]
for country,values in scores.items(): ax.plot(xx,values+[values[0]],label=country)
ax.set_xticks(a,labels,fontsize=8);ax.set_ylim(0,10);ax.legend(loc='upper right',bbox_to_anchor=(1.32,1.16),fontsize=8);save(fig,'fig3_policy_radar.png')

import numpy as _np
_m=_np.asarray(inp['ahp_author_judgments'],dtype=float);_gm=_np.prod(_m,axis=1)**(1/len(_m));ahp=(_gm/_gm.sum()).tolist()
fig,ax=plt.subplots(figsize=(7,4));ax.barh(['Finance/Economic','Regulatory/Policy','Institutional/Governance','Technical/Infrastructure'][::-1],[100*x for x in ahp][::-1]);ax.set_xlabel('AHP weight (%)');save(fig,'fig4_ahp_weights.png')

sc=inp['scenario'];years=list(range(2024,2031)); paths={}; disp={}; invest={}
for name,cagr in sc['cagrs'].items():
 series=[sc['statistical_pv_2024_mwp'],sc['statistical_pv_2025_mwp']]
 for _ in range(5):series.append(series[-1]*(1+cagr))
 paths[name]=series
 mw_year=sum((series[j-1]+series[j])/2 for j in range(2,7))
 generation_twh=mw_year*sc['capacity_factor']*8760/1e6
 disp[name]=generation_twh*sc['average_grid_emissions_t_per_mwh']
 invest[name]=(series[-1]-series[1])*sc['unit_capex_usd_kw_assumed']/1e6
results['scenarios']={'years':years,'capacity_paths_mwp':paths,'gross_average_factor_displacement_mtco2_2026_2030':disp,'investment_usd_bn':invest,'boundary':'Ember national statistical PV, not verified on-grid; neither forecast nor marginal avoided emissions'}
fig,ax=plt.subplots(figsize=(7.8,4.6))
for name,values in paths.items():ax.plot(years,values,marker='o',label=name)
ax.plot([2025],[280],marker='o',color='black');ax.set_ylabel('Official-statistics PV series (MWp)');ax.set_xlabel('Year');ax.legend();save(fig,'fig5_scenarios.png')

from statistics import median
bas=pv_lcoe(nig)
sp={}
for key in ['capex_per_kW','wacc','capacity_factor','project_life_yr','om_per_kW_yr']:
 x=nig[key];lo=pv_lcoe(dict(nig,**{key:x*.8}));hi=pv_lcoe(dict(nig,**{key:x*1.2}));sp[key]={'lcoe_at_minus20':lo,'lcoe_at_plus20':hi,'swing':abs(hi-lo)}
results['sensitivity']=sp
fig,ax=plt.subplots(figsize=(7.6,4.5));skeys=sorted(sp,key=lambda k:sp[k]['swing'])
disp={'capex_per_kW':'CAPEX (US$/kW)','wacc':'WACC','capacity_factor':'Capacity factor','project_life_yr':'Project life (years)','om_per_kW_yr':'O&M (US$/kW per year)'}
ax.barh([disp[k] for k in skeys],[sp[k]['swing'] for k in skeys]);ax.set_xlabel('Absolute LCOE change between -20% and +20% assumptions (US$/kWh)');save(fig,'fig6_tornado.png')

names=list(inp['agency_counts']); agencies=[inp['agency_counts'][k] for k in names]; W=[inp['reported_pv_capacity_mwp_nonharmonized'][k]/inp['population_m'][k] for k in names]
results['fragmentation']={'agencies':inp['agency_counts'],'reported_pv_per_person_w':dict(zip(names,W)),'sample_n':4,'inference':'Descriptive; heterogeneous PV capacity boundaries, no causal inference'}
fig,ax=plt.subplots(figsize=(7,4.6));ax.scatter(agencies,W)
for k,x,y in zip(names,agencies,W):ax.annotate(k,(x,y),xytext=(5,4),textcoords='offset points',fontsize=9)
ax.set_yscale('log');ax.set_xlabel('Number of lead agencies');ax.set_ylabel('Solar PV per capita (W/person, log scale)');save(fig,'fig7_fragmentation.png')

S=inp['afsia_country_table_mwp'];distrib=sum(S[k] for k in ('mini_grid','solar_home_systems','residential'))
A=inp['access'];hh=A['people_without_access_m']/A['household_size'];gross=hh*1e6*A['tier3_kwh_hh_y']/(8760*A['pv_cf'])/1e3
net=gross-distrib
results['access_gap']={'gross_tier3_energy_equivalent_mwp':gross, 'preferred_no_stock_credit_investment_usd_bn':gross*A['mini_grid_capex_usd_kw_assumed']/1e6,'afsia_country_access_relevant_stock_mwp':distrib,'optimistic_full_stock_credit_gap_mwp':net,'optimistic_full_stock_credit_investment_usd_bn':net*A['mini_grid_capex_usd_kw_assumed']/1e6,'dares_public_finance_share_gross_pct':A['dares_public_credit_usd_m']/1000/(gross*A['mini_grid_capex_usd_kw_assumed']/1e6)*100,'dares_public_finance_share_full_credit_pct':A['dares_public_credit_usd_m']/1000/(net*A['mini_grid_capex_usd_kw_assumed']/1e6)*100,'all_afsia_country_table_categories_mwp':sum(S.values())}


# Source-version note: the May 2026 final build (publisher PDF held and inspected by the authors)
# is primary; the January 2026 build values are retained as a superseded-build sensitivity.
jan=inp['afsia_january_build_superseded_mwp']
jan_stock=sum(jan[k] for k in ('mini_grid','solar_home_systems','residential'))
jan_net=max(0,gross-jan_stock)
results['afsia_version_sensitivity']={
 'may_final_primary':{
  'status':'May 2026 final build (publisher PDF held and inspected; primary)',
  'five_category_total_mwp':sum(S.values()),'access_relevant_stock_mwp':distrib,
  'optimistic_residual_mwp':net,
  'optimistic_full_credit_investment_usd_bn':net*A['mini_grid_capex_usd_kw_assumed']/1e6},
 'january_build_superseded':{
  'status':'January 2026 build (superseded; source-vintage sensitivity)',
  'five_category_total_mwp':round(sum(jan.values()),2),'access_relevant_stock_mwp':round(jan_stock,2),
  'optimistic_residual_mwp':jan_net,
  'optimistic_full_credit_investment_usd_bn':jan_net*A['mini_grid_capex_usd_kw_assumed']/1e6,
  'dares_public_finance_share_pct':A['dares_public_credit_usd_m']/1000/(jan_net*A['mini_grid_capex_usd_kw_assumed']/1e6)*100},
 'preferred_gross_no_stock_credit_investment_usd_bn':gross*A['mini_grid_capex_usd_kw_assumed']/1e6,
 'provenance':inp['afsia_vintage_provenance']}

d=inp['diesel_unit'];h=d['hours_per_day']*d['days_per_year']*d['load_factor'];out=d['fleet_midpoint_gw']*h/1000;gap=out*(d['diesel_lcoe']-bas)
results['diesel_parity']={'diesel_lcoe':d['diesel_lcoe'],'petrol_lcoe':d['petrol_lcoe'],'illustrative_generator_fleet_midpoint_gw':d['fleet_midpoint_gw'],'generator_fleet_source_range_gw':[d['fleet_low_gw'],d['fleet_high_gw']],'assumed_effective_full_load_hours_per_year':h,'hypothetical_output_twh':out,'gross_production_cost_usd_bn':out*d['diesel_lcoe'],'theoretical_cost_difference_usd_bn_NOT_net_savings':gap,'displacement_fraction_scenarios':{str(f):gap*f for f in (.1,.25,.5)},'no_net_savings_claim':True}
fc=d['fuel_cost_usd_per_kwh']+d['unit_capex_usd_kw']/(d['unit_life_years']*h)+d['maintenance_usd_per_kwh']
results['diesel_parity']['unit_cost_capital_recovery_hours_per_year']=d['unit_operating_hours_per_year']
results['diesel_parity']['fleet_consistent_unit_cost_usd_per_kwh']=fc
results['diesel_parity']['fleet_consistent_gross_contrast_usd_bn_NOT_net_savings']=out*(fc-bas)
# The loss and AHP sheets were not changed structurally but are independently recomputed here.
g=inp['grid_loss_inputs'];tc=g['technical_commercial_share'];col=g['collection_shortfall_share'];E=g['energy_received_twh_per_y_assumed'];atcc=1-(1-tc)*(1-col)
rev_ngn_bn=E*atcc*g['retail_tariff_ngn_per_kwh']; rev_usd_bn=rev_ngn_bn/g['fx_ngn_usd']
results['grid_loss']={'atcc_aggregate':atcc,'tc_energy_lost_or_unbilled_twh':E*tc,'collection_unpaid_energy_equiv_twh':E*(1-tc)*col,'illustrative_revenue_shortfall_ngn_bn':rev_ngn_bn,'illustrative_revenue_shortfall_usd_bn':rev_usd_bn,'excess_above_benchmark_usd_bn':E*(atcc-g['benchmark_atcc_share'])*g['retail_tariff_ngn_per_kwh']/g['fx_ngn_usd'],'retail_tariff_price_valuation_not_welfare_usd_bn':E*tc*g['retail_tariff_ngn_per_kwh']/g['fx_ngn_usd'],'generator_cost_price_valuation_not_welfare_usd_bn':E*tc*d['diesel_lcoe'],'does_not_measure_physical_unserved_energy_or_welfare':True}
m=np.asarray(inp['ahp_author_judgments'],dtype=float); gm=np.prod(m,axis=1)**(1/len(m));weights=gm/gm.sum();evals=np.linalg.eigvals(m);lam=float(max(evals.real));CI=(lam-len(m))/(len(m)-1);CR=CI/.90
results['ahp']={'weights_finance_regulatory_institutional_technical':weights.tolist(),'lambda_max':lam,'consistency_ratio':CR,'only_consistency_not_population_representativeness':True}

(HERE/'results_summary.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n')
print('Regenerated 7 figures (figures/) and results_summary.json')
print('Europe LCOE',lv[2],'PIGI preferred six',np.mean(P),'AFSIA access stock',distrib,'generator illustrative gap',gap)
