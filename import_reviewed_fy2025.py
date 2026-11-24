"""Import page-checked FY2025 and FY2024 report figures; preserves original files.
Run from the repository root: python import_reviewed_fy2025.py
All monetary figures in EUR millions. Blank means not verified, not zero.
"""
from pathlib import Path
import csv

# metric: (FY2025, FY2024, PDF page, exact reporting label)
DATA = {
 'Airbus': {
 'revenue':(73420,69230,4,'Revenue'), 'cost_of_sales':(-62453,-58555,4,'Cost of sales'),
 'gross_profit':(10967,10675,4,'Gross margin'), 'rd_expense':(-3153,-3250,4,'Research and development expenses'),
 'ebit':(6082,5304,4,'Profit before financial result and income taxes'),
 'ebit_adjusted':(7128,None,None,'EBIT Adjusted; FY2025 figure supplied by user; page not independently checked'),
 'fcf_before_customer_financing':(4574,None,None,'Free Cash Flow before Customer Financing; FY2025 figure supplied by user; not identical to simple FCF'),
 'net_income':(5221,4232,4,'Equity owners of the parent (Net Income)'),
 'net_income_group':(4960,4078,4,'Profit for the period'),
 'eps_basic_eur':(6.61,5.36,4,'Basic earnings per share'),
 'total_assets':(134939,129213,6,'Total assets'), 'inventories':(41676,37745,6,'Inventories'),
 'trade_receivables':(5454,5293,6,'Trade receivables'), 'cash':(14128,15003,6,'Cash and cash equivalents'),
 'total_equity':(26184,19696,7,'Total equity'), 'trade_payables':(15878,13791,7,'Trade liabilities'),
 'current_assets':(73584,69371,6,'Total current assets'), 'current_liabilities':(63429,60548,7,'Total current liabilities'),
 'short_term_debt':(5186,3924,7,'Short-term financing liabilities'),
 'long_term_debt':(9063,10355,7,'Long-term financing liabilities'),
 'operating_cash_flow':(7995,7402,8,'Cash provided by operating activities'),
 'capex_cash_outflow':(3964,3669,8,'Purchases of intangible assets, property, plant and equipment, investment property'),
 'depreciation_amortization':(3133,2853,8,'Depreciation and amortisation'),
 },
 'Safran': {
 'revenue':(31189,27716,201,'Revenue (consolidated, not adjusted)'),
 'revenue_adjusted':(31329,27317,67,'Adjusted revenue; FY2024 and FY2025'),
 'recurring_operating_income_adjusted':(5197,4119,67,'Adjusted recurring operating income'),
 'net_income_adjusted':(3174,3068,67,'Adjusted net income attributable to owners of parent'),
 'eps_basic_adjusted_eur':(7.60,7.37,67,'Adjusted basic EPS'),
 'free_cash_flow_reported':(3921,3189,None,'Safran FY2025 results press release: free cash flow'),
 'ebitda_company_adjusted':(6318,5417,None,'Safran FY2025 results press release: adjusted cash flow highlights EBITDA'),
 'net_cash_company_reported':(1738,1738,None,'Safran FY2025 results press release: net cash at period end'),
 'dividend_per_share_proposed_eur':(3.35,2.90,None,'Safran FY2025 results press release: FY2025 proposed; FY2024 prior-year dividend'),
 'gross_operating_income':(31656,28154,201,'Income from operations (not EBIT)'),
 'recurring_operating_income':(4787,4186,201,'Recurring operating income (consolidated)'),
 'ebit':(4308,4192,201,'Profit from operations'),
 'net_income':(7177,-667,201,'Profit attributable to owners of the parent'),
 'net_income_group':(7286,-575,201,'Profit (loss) for the period'),
 'eps_basic_eur':(17.17,-1.60,201,'Basic earnings (loss) per share'),
 'total_assets':(61814,55012,202,'TOTAL ASSETS'),
 'inventories':(10285,9491,202,'Inventories and work-in-progress'),
 'trade_receivables':(14196,10572,202,'Trade and other receivables'),
 'cash':(6789,6514,202,'Cash and cash equivalents'),
 'current_assets':(38022,31523,202,'Current assets'),
 'current_liabilities':(41121,37440,203,'Current liabilities'),
 'total_equity':(15461,10725,203,'Total equity'),
 'trade_payables':(13444,9802,203,'Trade and other payables'),
 'short_term_debt':(2605,988,203,'Current interest-bearing financial liabilities'),
 'long_term_debt':(2446,3788,203,'Non-current interest-bearing financial liabilities'),
 'operating_cash_flow':(5721,4733,205,'TOTAL I (cash flow from operating activities)'),
 'capex_cash_outflow':(1800,1544,205,'Capitalized R&D + purchases intangible assets + purchases PP&E, net'),
 'depreciation_amortization_impairment_provisions':(1818,1691,205,'Depreciation, amortization, impairment and provisions; NOT pure D&A'),
 },
 'Siemens': {
 'revenue':(78914,75930,43,'Revenue (continuing operations)'),
 'profit_industrial_business':(11766,11390,None,'Profit Industrial Business; user supplied; reported margin 15.4%; not consolidated Group EBIT'),
 'ebit':(10179,None,None,'Consolidated Group EBIT EUR 10,179m; user supplied; definition and report page require verification'),
 'cost_of_sales':(-48515,-46107,43,'Cost of sales'),
 'gross_profit':(30399,29823,43,'Gross profit'),
 'rd_expense':(-6559,-6276,43,'Research and development expenses'),
 'net_income':(9620,8301,43,'Net income attributable to shareholders of Siemens AG'),
 'net_income_group':(10387,8992,43,'Net income incl. discontinued operations'),
 'net_income_continuing':(8328,8907,43,'Income from continuing operations'),
 'eps_basic_eur':(12.25,10.53,43,'Basic earnings per share: net income'),
 'total_assets':(166202,147812,44,'Total assets'),
 'inventories':(10582,10923,44,'Inventories'),
 'trade_receivables':(16628,16963,44,'Trade and other receivables'),
 'cash':(14495,9156,44,'Cash and cash equivalents'),
 'current_assets':(64711,61353,44,'Total current assets'),
 'current_liabilities':(47261,43913,44,'Total current liabilities'),
 'total_equity':(68371,56231,44,'Total equity'),
 'trade_payables':(9183,8843,44,'Trade payables'),
 'short_term_debt':(11174,6598,44,'Short-term debt and current maturities of long-term debt'),
 'long_term_debt':(44841,41321,44,'Long-term debt'),
 'operating_cash_flow':(13448,11814,21,'Cash flows from operating activities, continuing operations'),
 'capex_cash_outflow':(2445,2088,21,'Additions to intangible assets and PP&E, continuing operations'),
 'free_cash_flow_reported':(11004,9726,21,'Free cash flow, continuing operations'),
 'depreciation_amortization_impairment':(3389,3158,45,'Amortization, depreciation and impairments'),
 },
}

# Additional FY2024/FY2025 metrics supplied by user (not independently verified).
# All monetary figures EUR millions; ratios percent or multiples as named.
EXTRA = {
 'Airbus': {
  'ebitda': (9215,8157,'Calculated EBIT + D&A; not company-reported EBITDA'),
  'net_debt': (-12200,-11753,'Company net cash definition; negative denotes net cash'),
  'roic_pct': (12.2,11.6,'Third-party standardized ROIC estimate; definition not verified'),
  'pe': (30.0,28.9,'FY-end price / IFRS EPS; historical snapshot'),
  'ev_ebitda_low': (15.7,13.6,'Indicative historical EV/EBITDA range lower bound'),
  'ev_ebitda_high': (19.9,17.8,'Indicative historical EV/EBITDA range upper bound'),
  'ev_ebit_low': (23.8,20.8,'Indicative historical EV/EBIT range lower bound'),
  'ev_ebit_high': (27.6,25.5,'Indicative historical EV/EBIT range upper bound'),
  'dividend_per_share_eur': (3.20,3.00,'FY2025 approved dividend; FY2024 includes EUR 1 special'),
 },
 'Safran': {
  'ebitda': (6202,5606,'Third-party EBITDA supplied earlier; NOT Safran company adjusted EBITDA (6318/5417)'),
  'ebitda_standardized_low': (5871,5160,'Third-party standardized EBITDA; 2024 single estimate'),
  'ebitda_standardized_high': (5905,5160,'Third-party standardized EBITDA; 2024 single estimate'),
  'net_debt': (-1738,-1738,'Safran company-reported net cash per FY2025 press release; debt less cash alone does not reproduce KPI'),
  'roic_pct': (17.9,16.9,'Third-party standardized ROIC; methodology unverified'),
  'pe_adjusted': (39.1,28.8,'FY-end market cap / adjusted net income'),
  'pe': (17.3,None,'FY2025 FY-end market cap / consolidated IFRS net income; FY2024 negative EPS, N/A'),
  'ev_ebitda_low': (19.7,15.5,'User-supplied historical EV/EBITDA range'),
  'ev_ebitda_high': (20.5,16.8,'User-supplied historical EV/EBITDA range'),
  'ev_ebit_adjusted': (23.6,21.0,'EV / adjusted recurring operating income; not comparable to IFRS EBIT'),
  'ev_ebit_recurring_consolidated': (25.6,20.7,'EV / consolidated recurring operating income; not IFRS EBIT'),
  'raw_materials_consumables_expense': (-17615,-15975,'Expense by nature; user supplied'),
  'personnel_costs': (-8678,-7792,'Expense by nature; user supplied'),
  'dividend_per_share_eur': (3.35,2.90,'FY2025 proposed; FY2024 dividend EUR 2.90, Safran FY2025 press release'),
 },
 'Siemens': {
  'ebitda': (13380,13577,'User-supplied EBITDA; reporting perimeter requires checking'),
  'industrial_net_debt': (12160,9421,'Industrial net debt excluding Siemens Financial Services'),
  'industrial_net_debt_ebitda': (0.9,0.7,'Company industrial leverage KPI'),
  'roce_pct': (17.8,19.1,'Company ROCE KPI; NOT ROIC'),
  'roic_pct': (6.90,8.26,'Third-party standardized consolidated ROIC incl SFS'),
  'pe': (18.47,17.02,'Historical FY-end P/E; user supplied'),
  'ev_ebitda': (19.62,16.06,'Historical FY-end EV/EBITDA; user supplied'),
  'ev_ebit': (24.77,19.83,'Historical FY-end EV/EBIT; user supplied'),
  'free_cash_flow_total': (10812,9494,'Total FCF incl discontinued operations; FY2024 reported 9494 despite rounded components summing to 9493'),
  'free_cash_flow_discontinued': (-192,-233,'FCF discontinued operations; FY2024 rounding: 9726-233=9493, reported total 9494'),
  'dividend_per_share_eur': (5.35,5.20,'Dividend approved/paid for respective fiscal year'),
 },
}
for company, metrics in EXTRA.items():
 for metric,(v25,v24,label) in metrics.items():
  if metric in DATA[company]:
   # Replace only when explicit correction is requested; preserve other report fields.
   continue
  DATA[company][metric]=(v25,v24,None,label)
# Existing Safran 2025 proposed dividend remains in original evidence; the new
# standardized dividend_per_share_eur field is for cross-company display.

ROOT=Path.cwd()
out=ROOT/'data';out.mkdir(exist_ok=True)
rows=[]
for company, metrics in DATA.items():
 for metric,(v25,v24,page,label) in metrics.items():
  for year,value in [(2025,v25),(2024,v24)]:
   if value is None:continue
   rows.append({'company':company,'fiscal_year':year,'metric':metric,'value':value,
    'unit':('EUR/share' if metric in ('eps_basic_eur','eps_basic_adjusted_eur','dividend_per_share_proposed_eur','dividend_per_share_eur') else ('percent' if metric.endswith('_pct') else ('multiple' if metric.startswith(('pe','ev_')) or metric=='industrial_net_debt_ebitda' else 'EUR million'))),
    'source_file':f'{company}__FY2025.pdf','pdf_page':page,'source_label':label,
    'verification':'user_supplied_unverified' if page is None else 'page_checked','fiscal_year_end':'09-30' if company=='Siemens' else '12-31'})
with (out/'financial_evidence_2025.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Long-form is source of truth; wide-form is convenient for dashboard ingestion.
wide={}
for r in rows:
 k=(r['company'],r['fiscal_year']);wide.setdefault(k,{'company':k[0],'fiscal_year':k[1]})[r['metric']]=r['value']
for d in wide.values():
 if d.get('revenue') and (d['company'],d['fiscal_year']-1) in wide:
  prior=wide[(d['company'],d['fiscal_year']-1)].get('revenue')
  if prior:d['revenue_growth_pct']=(d['revenue']/prior-1)*100
 if d.get('revenue') and d.get('ebit') is not None:d['ebit_margin_pct']=d['ebit']/d['revenue']*100
 if d.get('revenue') and d.get('ebitda') is not None:d['ebitda_margin_pct']=d['ebitda']/d['revenue']*100
 if d.get('net_debt') is not None and d.get('ebitda'):
  d['net_debt_ebitda']=d['net_debt']/d['ebitda']
 if d.get('revenue_adjusted') and d.get('recurring_operating_income_adjusted') is not None:
  d['recurring_operating_margin_adjusted_pct']=100*d['recurring_operating_income_adjusted']/d['revenue_adjusted']
 if d.get('revenue_adjusted') and (d['company'],d['fiscal_year']-1) in wide:
  prior_adj=wide[(d['company'],d['fiscal_year']-1)].get('revenue_adjusted')
  if prior_adj:d['revenue_growth_adjusted_pct']=(d['revenue_adjusted']/prior_adj-1)*100
 if d.get('revenue') and d.get('ebit_adjusted') is not None:
  d['ebit_adjusted_margin_pct']=100*d['ebit_adjusted']/d['revenue']
 if d.get('revenue') and d.get('profit_industrial_business') is not None:
  d['profit_industrial_business_margin_pct']=100*d['profit_industrial_business']/d['revenue']
 if d.get('operating_cash_flow') is not None and d.get('capex_cash_outflow') is not None:
  d['fcf_simple']=d['operating_cash_flow']-d['capex_cash_outflow']
 if d.get('short_term_debt') is not None and d.get('long_term_debt') is not None:
  d['gross_debt_selected']=d['short_term_debt']+d['long_term_debt']
# Retain company-specific accounting disclosures in the evidence file, but exclude
# non-comparable one-company metrics from the main comparison table.
COMPARISON_EXCLUDE = {
 'revenue_adjusted', 'ebit_adjusted', 'recurring_operating_income',
 'recurring_operating_income_adjusted', 'profit_industrial_business',
 'ebit_user_estimate', 'net_income_adjusted', 'eps_basic_adjusted_eur',
 'recurring_operating_margin_adjusted_pct', 'revenue_growth_adjusted_pct',
 'ebit_adjusted_margin_pct', 'profit_industrial_business_margin_pct',
}
for d in wide.values():
 for metric in COMPARISON_EXCLUDE:
  d.pop(metric, None)
keys=['company','fiscal_year']+sorted(set().union(*(set(v) for v in wide.values()))-{'company','fiscal_year'})
with (out/'financials_reviewed_2025.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(wide.values())
print(f'Wrote {len(rows)} sourced observations and {len(wide)} company-year rows.')
print('data/financial_evidence_2025.csv')
print('data/financials_reviewed_2025.csv')
print('Existing data/financials.csv was NOT overwritten.')
print('Company-specific adjusted measures remain in evidence CSV, not comparison CSV.')
print('NOTE: user_supplied_unverified rows need source-page verification before investment use.')
