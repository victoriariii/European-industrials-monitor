#!/usr/bin/env python3
"""Create a clean, light-theme, GitHub-compatible SVG from reviewed financial CSV."""
import csv, html, math
from pathlib import Path
SOURCE=Path('data/financials_reviewed_2025.csv')
DEST=Path('results/financial_dashboard.svg')
COMPANIES=('Airbus','Safran','Siemens')
COLORS={'Airbus':'#2563eb','Safran':'#0f766e','Siemens':'#b45309'}
INK='#172033'; MUTED='#66758b'; BORDER='#dce4ed'; PALE='#f5f8fc'
def num(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError): return None
def pick(r,*keys):
    for k in keys:
        v=num(r.get(k))
        if v is not None:return v
    return None
def esc(s):return html.escape(str(s),quote=True)
def text(x,y,s,size=14,color=INK,weight=400,anchor='start'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" font-family="Arial,Helvetica,sans-serif">{esc(s)}</text>'
def rect(x,y,w,h,fill,rx=0,stroke='none'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'
def euro(v):
    if v is None:return '—'
    return f'−€{abs(v):,.0f}m' if v<0 else f'€{v:,.0f}m'
def main():
    if not SOURCE.is_file():raise SystemExit(f'Missing {SOURCE}. Generate or copy reviewed CSV first.')
    with SOURCE.open(newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    data={}
    for r in rows:
        try:key=(r['company'].strip(),int(float(r['fiscal_year'])))
        except (KeyError,ValueError):continue
        data[key]=r
    missing=[f'{c} {y}' for c in COMPANIES for y in (2024,2025) if (c,y) not in data]
    if missing:raise SystemExit('Missing rows: '+', '.join(missing))
    def val(c,y,k):
        r=data[c,y]
        if k=='ebitda':return pick(r,'ebitda_company_reported','ebitda_reported','ebitda')
        if k=='fcf':return pick(r,'free_cash_flow_total','free_cash_flow_reported','fcf_before_customer_financing','fcf_simple')
        if k=='net_income':return pick(r,'net_income','net_income_group')
        return pick(r,k)
    metrics=[('Revenue','revenue'),('EBITDA','ebitda'),('Net income','net_income'),('Free cash flow','fcf')]
    W,H=1160,960
    p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="European industrials financial comparison, fiscal 2024 and 2025">',rect(0,0,W,H,'#ffffff'),rect(0,0,W,7,'#1d4ed8'),text(42,57,'FINANCIAL FUNDAMENTALS',27,INK,700),text(42,84,'Airbus · Safran · Siemens   |   FY2024 vs FY2025   |   € millions',15,MUTED),rect(42,106,1076,1,BORDER)]
    # One concise company card per firm; latest FY25 with year-on-year change.
    for i,c in enumerate(COMPANIES):
        x=42+i*367
        p.extend([rect(x,128,342,215,'#ffffff',12,BORDER),rect(x,128,342,6,COLORS[c],3),text(x+20,167,c,21,INK,700),text(x+322,166,'FY2025',12,MUTED,600,'end')])
        for j,(label,key) in enumerate(metrics):
            y=199+j*37; v=val(c,2025,key); old=val(c,2024,key)
            p.append(text(x+20,y,label,13,MUTED))
            p.append(text(x+322,y,euro(v),15,INK,700,'end'))
            if j<3:p.append(rect(x+20,y+10,302,1,'#eef2f6'))
    p.extend([text(42,392,'YEAR-ON-YEAR COMPARISON',22,INK,700),text(42,417,'FY2024 shown in pale bars; FY2025 shown in company color. Values are in € millions.',13,MUTED)])
    # Four uncluttered panels with both year values explicitly labeled.
    for idx,(title,key) in enumerate(metrics):
        col=idx%2;row=idx//2;x=42+col*551;y=439+row*224;pw=526;ph=205
        p.extend([rect(x,y,pw,ph,'#ffffff',10,BORDER),text(x+20,y+32,title,17,INK,700)])
        values=[val(c,yr,key) for c in COMPANIES for yr in (2024,2025)]
        limit=max([abs(v) for v in values if v is not None] or [1]);bar_x=x+125;bar_span=240
        for j,c in enumerate(COMPANIES):
            yy=y+66+j*43
            p.append(text(x+20,yy+13,c,13,INK,600))
            for yr,dy in ((2024,0),(2025,15)):
                v=val(c,yr,key)
                if v is None:continue
                width=max(2,abs(v)/limit*bar_span)
                fill='#dce5f0' if yr==2024 else COLORS[c]
                p.append(rect(bar_x,yy+dy,width,11,fill,3))
                if v<0:p.append(text(bar_x+width+5,yy+dy+10,'−',12,'#b91c1c',700))
            p.append(text(x+pw-16,yy+5,euro(val(c,2024,key)),11,MUTED,400,'end'))
            p.append(text(x+pw-16,yy+20,euro(val(c,2025,key)),11,INK,700,'end'))
    p.extend([rect(42,899,1076,1,BORDER),text(42,925,'Source: reviewed company FY2024–FY2025 financial data. Company accounting definitions may differ.',12,MUTED),text(42,944,'FCF definitions differ: Airbus before customer financing; Siemens total FCF; Safran reported FCF.',11,MUTED),'</svg>'])
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text('\n'.join(p)+'\n',encoding='utf-8')
    print('Generated',DEST,'(',DEST.stat().st_size,'bytes )')
if __name__=='__main__':main()
