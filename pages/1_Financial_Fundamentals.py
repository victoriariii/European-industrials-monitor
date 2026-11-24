from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Financial Fundamentals', page_icon='📊', layout='wide')

st.markdown('''<style>
.block-container{max-width:1450px;padding-top:2rem;padding-bottom:3rem}
h1,h2,h3{letter-spacing:-.035em;color:#12243a}
[data-testid="stMetric"]{background:#f5f8fa;border:1px solid #e0e7ed;border-radius:14px;padding:15px 18px}
[data-testid="stMetricLabel"]{font-size:.87rem;color:#586a7a}
[data-testid="stMetricValue"]{font-size:1.65rem;font-weight:750}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden}
div[data-testid="stVerticalBlock"]>div{gap:.6rem}
</style>''', unsafe_allow_html=True)

PATH=Path('data/financials_reviewed_2025.csv')
if not PATH.exists():
    st.error('Missing data/financials_reviewed_2025.csv. Run python import_reviewed_fy2025.py first.')
    st.stop()
df=pd.read_csv(PATH)
# Explicit correction: user-provided Siemens FY2025 consolidated EBIT, pending source reconciliation.
df.loc[(df.company=='Siemens')&(df.fiscal_year==2025),'ebit']=10179
# Correct stale margin derived from the earlier €10,620m estimate.
for metric,base in [('ebit_margin_pct','ebit'),('ebitda_margin_pct','ebitda')]:
    if base in df and 'revenue' in df:
        df[metric]=pd.to_numeric(df[base],errors='coerce')/pd.to_numeric(df.revenue,errors='coerce')*100

st.title('Financial fundamentals')
st.caption('Airbus · Safran · Siemens  |  FY2024–FY2025  |  EUR millions unless otherwise stated')
left,right=st.columns([2.5,1])
with left:
    chosen=st.multiselect('Companies', sorted(df.company.unique()), default=sorted(df.company.unique()))
with right:
    years=st.multiselect('Fiscal years', [2024,2025], default=[2024,2025])
sub=df[df.company.isin(chosen)&df.fiscal_year.isin(years)].copy()
if sub.empty: st.info('Select at least one company and year.');st.stop()

COLORS={2024:'#8da9be',2025:'#087f8c'}
LABELS={'revenue':'Revenue','ebitda':'EBITDA','ebit':'EBIT','net_income':'Net income','ebit_margin_pct':'EBIT margin','ebitda_margin_pct':'EBITDA margin','roic_pct':'ROIC','total_assets':'Total assets','total_equity':'Total equity','cash':'Cash','operating_cash_flow':'Operating cash flow','capex_cash_outflow':'CAPEX','dividend_per_share_eur':'Dividend / share','pe':'P/E'}

def fmt(x,unit='€m',digits=1):
    if pd.isna(x):return '—'
    if unit=='€m':return f'€{x/1000:,.1f}bn' if abs(x)>=1000 else f'€{x:,.0f}m'
    if unit=='%':return f'{x:,.1f}%'
    if unit=='x':return f'{x:,.1f}×'
    if unit=='€':return f'€{x:,.2f}'
    return f'{x:,.{digits}f}'

def fy_value(company,year,key):
    s=sub[(sub.company==company)&(sub.fiscal_year==year)]
    if s.empty or key not in s:return float('nan')
    return pd.to_numeric(s.iloc[0][key],errors='coerce')

# A single defensible FCF series; definition explicitly disclosed below.
def fcf(r):
    if r.company=='Airbus':return r.get('fcf_before_customer_financing',float('nan'))
    if r.company=='Safran':return r.get('free_cash_flow_reported',float('nan'))
    if r.company=='Siemens':return r.get('free_cash_flow_total',float('nan'))
    return float('nan')
sub['fcf_selected']=sub.apply(fcf,axis=1)

latest_year=max(years)
latest=sub[sub.fiscal_year==latest_year]
st.markdown(f'### FY{latest_year} snapshot')
kpis=[('Revenue','revenue','€m'),('EBITDA','ebitda','€m'),('Net income','net_income','€m'),('Free cash flow','fcf_selected','€m')]
cols=st.columns(4)
for col,(label,key,unit) in zip(cols,kpis):
    value=pd.to_numeric(latest[key],errors='coerce').sum(min_count=1)
    with col:st.metric(label,fmt(value,unit))
st.caption('Snapshot totals aggregate selected companies; they are not portfolio-weighted. FCF definitions vary by company.')

def bars(title,key,unit='€bn'):
    data=sub[['company','fiscal_year',key]].dropna().copy()
    if data.empty:return
    data['Value']=data[key]/1000 if unit=='€bn' else data[key]
    data['Fiscal year']=data['fiscal_year'].astype(str)
    fig=px.bar(data,x='company',y='Value',color='Fiscal year',barmode='group',
               color_discrete_map={'2024':'#8da9be','2025':'#087f8c'},category_orders={'Fiscal year':['2024','2025']},
               labels={'company':'','Value':unit,'fiscal_year':'Fiscal year'},text='Value')
    fig.update_traces(texttemplate='%{text:,.1f}',textposition='outside',cliponaxis=False)
    fig.update_layout(height=330,margin=dict(l=0,r=10,t=20,b=0),legend=dict(orientation='h',y=1.17,x=0),
                      plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',font=dict(size=12))
    fig.update_yaxes(showgrid=True,gridcolor='#e7edf2',zeroline=False)
    st.markdown(f'**{title}**')
    st.plotly_chart(fig,use_container_width=True)

st.markdown('### Performance comparison')
a,b=st.columns(2)
with a:bars('Revenue','revenue')
with b:bars('EBITDA','ebitda')
a,b=st.columns(2)
with a:bars('Net income attributable to shareholders','net_income')
with b:bars('Free cash flow · company-specific definitions','fcf_selected')

st.markdown('### Profitability and capital efficiency')
a,b=st.columns(2)
with a:bars('EBIT margin','ebit_margin_pct','%')
with b:bars('ROIC · third-party/standardized estimates','roic_pct','%')

# Compact company rows, fiscal years as columns: no 40-column tables.
st.markdown('### Financial scorecard')
metric_rows=[('Revenue','revenue','€m'),('Revenue growth','revenue_growth_pct','%'),
             ('EBITDA','ebitda','€m'),('EBITDA margin','ebitda_margin_pct','%'),
             ('EBIT','ebit','€m'),('EBIT margin','ebit_margin_pct','%'),
             ('Net income','net_income','€m'),('Free cash flow','fcf_selected','€m'),
             ('Total assets','total_assets','€m'),('Total equity','total_equity','€m'),
             ('ROIC','roic_pct','%'),('P/E','pe','x'),('Dividend per share','dividend_per_share_eur','€')]
# Remove metric if only one company has values, except key metrics that are expected to be available for all.
company_count=len(chosen)
metric_rows=[(label,key,unit) for label,key,unit in metric_rows if key in sub.columns and sub.groupby('company')[key].apply(lambda s:s.notna().any()).sum()>=min(2,company_count)]
score=[]
for label,key,unit in metric_rows:
    row={'Metric':label}
    for company in chosen:
        for year in sorted(years):row[f'{company} · {year}']=fmt(fy_value(company,year,key) if key!='fcf_selected' else fy_value(company,year,key),unit)
    score.append(row)
st.dataframe(pd.DataFrame(score).set_index('Metric'),use_container_width=True,height=min(650,52+len(score)*36))

with st.expander('Balance sheet and liquidity · additional details'):
    balance=[('Cash','cash','€m'),('Current assets','current_assets','€m'),('Current liabilities','current_liabilities','€m'),('Inventories','inventories','€m'),('Gross debt (selected borrowings)','gross_debt_selected','€m')]
    rows=[]
    for label,key,unit in balance:
        if key not in sub or sub.groupby('company')[key].apply(lambda s:s.notna().any()).sum()<min(2,company_count):continue
        row={'Metric':label}
        for company in chosen:
            for year in sorted(years):row[f'{company} · {year}']=fmt(fy_value(company,year,key),unit)
        rows.append(row)
    if rows:st.dataframe(pd.DataFrame(rows).set_index('Metric'),use_container_width=True)

with st.expander('Methodology and comparability notes'):
    st.markdown('''- **Siemens EBIT FY2025:** €10,179m, supplied by the user; not verified as a published consolidated IFRS EBIT line. FY2024 Siemens EBIT remains blank. The 2025 margin is recalculated accordingly.
- **Safran EBIT:** consolidated profit from operations, including non-recurring items; **Airbus EBIT:** reported EBIT. They are not strictly identical definitions.
- **Net income:** IFRS attributable net income. Safran's FY2025 figure is strongly influenced by foreign-exchange hedge fair-value changes.
- **EBITDA:** definitions vary by company; Safran uses a different reported/adjusted presentation. Treat cross-company EBITDA margins cautiously.
- **Free cash flow:** Airbus before customer financing; Safran reported FCF; Siemens total FCF (including discontinued operations). These are **not strictly comparable**.
- **ROIC:** source-dependent, particularly for Siemens' financial-services business. **P/E:** historical fiscal year-end estimates, not live valuations.
- **Fiscal years:** Siemens ends September 30; Airbus and Safran end December 31.
- **Missing values:** intentionally left blank. No artificial estimates are inserted.''')
    st.download_button('Download full underlying data',sub.to_csv(index=False).encode('utf-8'),'financials_full.csv','text/csv')
