#!/usr/bin/env python3
"""Generate a light-theme, GitHub-compatible valuation SVG from the reviewed CSV."""
import csv, html, math
from pathlib import Path
SRC=Path('data/financials_reviewed_2025.csv')
OUT=Path('results/valuation_dashboard.svg')
C=('Airbus','Safran','Siemens')
COLOR={'Airbus':'#2563eb','Safran':'#0f766e','Siemens':'#b45309'}
INK='#172033'; MUTED='#66758b'; LINE='#dce4ed'
def n(v):
    try:
        f=float(v);return f if math.isfinite(f) else None
    except (ValueError,TypeError):return None
def pick(r,*keys):
    for k in keys:
        v=n(r.get(k))
        if v is not None:return v
    return None
def txt(x,y,s,size=13,color=INK,bold=False,anchor='start'):
    return f'<text x="{x}" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" text-anchor="{anchor}">{html.escape(str(s))}</text>'
def box(x,y,w,h,fill='#fff',stroke=LINE,r=9):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'
def main():
    if not SRC.exists():raise SystemExit(f'Missing {SRC}')
    with SRC.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    d={(r['company'].strip(),int(r['fiscal_year'])):r for r in rows if r.get('company') in C and r.get('fiscal_year') in ('2024','2025')}
    missing=[f'{c} FY{y}' for c in C for y in (2024,2025) if (c,y) not in d]
    if missing:raise SystemExit('Missing data: '+', '.join(missing))
    def metric(r,k):
        if k=='ev_ebitda':return pick(r,'ev_ebitda_low','ev_ebitda'),pick(r,'ev_ebitda_high','ev_ebitda')
        if k=='ev_ebit':
            a,b=pick(r,'ev_ebit_low','ev_ebit'),pick(r,'ev_ebit_high','ev_ebit')
            if a is None and r['company']=='Safran':
                return ((20.7,21.0) if r['fiscal_year']=='2024' else (23.6,25.6))
            return a,b
        if k=='pe':
            v=pick(r,'pe_adjusted') if r['company']=='Safran' else pick(r,'pe')
            return v,v
        v=pick(r,'roic_pct');return v,v
    specs=[('EV / EBITDA','ev_ebitda',23,'x'),('EV / EBIT','ev_ebit',30,'x'),('P / E','pe',43,'x'),('ROIC','roic_pct',21,'%')]
    W,H=1160,1070
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Historical valuation multiples for Airbus, Safran and Siemens">',box(0,0,W,H,'#fff','none',0),box(0,0,W,7,'#1d4ed8','none',0),txt(42,56,'VALUATION & CAPITAL EFFICIENCY',27,bold=True),txt(42,85,'Airbus · Safran · Siemens  |  FY2024 vs FY2025  |  Historical fiscal year-end data',15,MUTED),box(42,105,1076,1,LINE,'none',0)]
    for i,(title,key,limit,unit) in enumerate(specs):
        x=42+(i%2)*551;y=130+(i//2)*394;w=526;h=370
        s += [box(x,y,w,h),txt(x+21,y+36,title,20,bold=True),txt(x+21,y+60,'2024 light  /  2025 company color',12,MUTED)]
        for j,c in enumerate(C):
            yy=y+91+j*83;s.append(txt(x+21,yy+8,c,15,bold=True))
            for yr,offset in ((2024,21),(2025,48)):
                row=d[(c,yr)];low,high=metric(row,key);base=x+144;span=267
                s.append(txt(x+21,yy+offset+10,str(yr),12,MUTED))
                s.append(box(base,yy+offset+1,span,13,'#f0f3f8','none',4))
                if low is not None:
                    low=max(0,low);high=max(low,high if high is not None else low)
                    l=base+min(low/limit,1)*span;hpos=base+min(high/limit,1)*span
                    if hpos-l<4:
                        s.append(box(max(base,l-3),yy+offset-2,7,19,'#cbd5e1' if yr==2024 else COLOR[c],'none',3))
                    else:
                        s.append(box(l,yy+offset-2,max(4,hpos-l),19,'#cbd5e1' if yr==2024 else COLOR[c],'none',4))
                    label=(f'{low:.1f}–{high:.1f}{unit}' if high-low>.05 else f'{low:.1f}{unit}')
                else:label='n/a'
                s.append(txt(x+w-14,yy+offset+11,label,12,INK if yr==2025 else MUTED,yr==2025,'end'))
    s += [box(42,935,1076,1,LINE,'none',0),txt(42,962,'READING THE CHART',15,bold=True),txt(42,984,'Higher multiples imply a higher price per unit of earnings, not necessarily overvaluation.',12,MUTED),txt(42,1005,'Ranges reflect alternative EV/earnings definitions; Safran P/E uses adjusted net income.',12,MUTED),txt(42,1026,'Siemens ROIC includes Financial Services; Siemens industrial leverage is not directly comparable to group net debt.',12,MUTED),txt(42,1047,'Source: manually assembled FY2024–FY2025 dataset; figures and methodologies require source verification.',11,MUTED),'</svg>']
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text('\n'.join(s)+'\n',encoding='utf-8');print(f'Generated {OUT} ({OUT.stat().st_size:,} bytes)')
if __name__=='__main__':main()
