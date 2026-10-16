from pathlib import Path
from decimal import Decimal as D
import csv,json,textwrap,html
OUT=Path(__file__).resolve().parent
ANT="https://platform.claude.com/docs/en/about-claude/pricing"
GOO="https://ai.google.dev/gemini-api/docs/pricing"
rates=[
["Claude Sonnet 4.6","3","15","current; active legacy model",ANT],
["Claude Sonnet 5.5","2","10","current",ANT],
["Gemini 4 Argon","2","10","through 2026-11-30",GOO],
["Gemini 4 Argon","4","20","scheduled from 2026-12-01",GOO],
["Gemini 3.5 Flash-Lite","0.30","2.50","current",GOO]]
with (OUT/"rates.csv").open("w",newline="") as f:
 w=csv.writer(f);w.writerow(["model","usd_per_million_uncached_input_tokens","usd_per_million_billable_output_tokens","effective_period_as_observed","source_url"]);w.writerows(rates)
scenarios=[
["tokenizer","Sonnet 4.6; reference corpus","1","0","3","15","1","3.00",ANT],
["tokenizer","Sonnet 5.5; equal token count","1","0","2","10","1","2.00",ANT],
["tokenizer","Sonnet 5.5; hypothetical same text","1.3","0","2","10","1.3","2.60",ANT],
["date","Argon; rates through Nov 30","1","0.2","2","10","1","4.00",GOO],
["date","Argon; scheduled Dec 1 rates","1","0.2","4","20","1","8.00",GOO],
["output","Flash-Lite; input charge only","1","0","0.30","2.50","1","0.30",GOO],
["output","Flash-Lite; input plus output","1","0.2","0.30","2.50","1","0.80",GOO]]
with (OUT/"scenarios.csv").open("w",newline="") as f:
 w=csv.writer(f);w.writerow(["case","scenario","aggregate_million_input_tokens","aggregate_million_billable_output_tokens","usd_per_million_input","usd_per_million_output","assumed_input_token_multiplier_vs_reference","calculated_usd","source_url"]);w.writerows(scenarios)
for r in scenarios:assert D(r[2])*D(r[4])+D(r[3])*D(r[5])==D(r[7]),r
assert (D("3")-D("2.6"))/D("3")*100 == D("13.33333333333333333333333333")
assert D(".5")/D(".8")*100==D("62.5")
INK="#14232e";MUT="#596977";TEAL="#087f8c";PALE="#eef5f5";GRAY="#ccd7dc";ORANGE="#b85b31"
class Canvas:
 def __init__(self,w,h): self.w=w;self.h=h;self.ops=[]
 def text(self,s,x,y,size=10,color=INK,bold=False): self.ops.append(("t",s,x,y,size,color,bold))
 def rect(self,x,y,w,h,color): self.ops.append(("r",x,y,w,h,color))
 def line(self,x,y,x2,y2,color=GRAY): self.ops.append(("l",x,y,x2,y2,color))
 def para(self,s,x,y,width=88,size=10,leading=14,color=INK):
  for line in textwrap.wrap(s,width): self.text(line,x,y,size,color);y+=leading
  return y
 def add(self,other,x,y):
  for o in other.ops:
   o=list(o)
   if o[0]=="t":o[2]+=x;o[3]+=y
   else:o[1]+=x;o[2]+=y
   if o[0]=="l":o[3]+=x;o[4]+=y
   self.ops.append(tuple(o))
 def svg(self):
  out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">','<rect width="100%" height="100%" fill="white"/>']
  for o in self.ops:
   if o[0]=="t":
    _,s,x,y,z,c,b=o;out.append(f'<text x="{x}" y="{y}" fill="{c}" font-family="Arial,Helvetica,sans-serif" font-size="{z}" font-weight="{700 if b else 400}">{html.escape(s)}</text>')
   elif o[0]=="r":
    _,x,y,w,h,c=o;out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"/>')
   else:
    _,x,y,x2,y2,c=o;out.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{c}"/>')
  return "\n".join(out+["</svg>"])
 def pdf(self):
  def col(h):return " ".join(f"{int(h[i:i+2],16)/255:.4f}" for i in (1,3,5))
  def esc(s):return s.replace("\\","\\\\").replace("(","\\(").replace(")","\\)")
  out=[]
  for o in self.ops:
   if o[0]=="t":
    _,s,x,y,z,c,b=o;out.append(f"BT /{'F2' if b else 'F1'} {z} Tf {col(c)} rg 1 0 0 1 {x} {self.h-y} Tm ({esc(s)}) Tj ET")
   elif o[0]=="r":
    _,x,y,w,h,c=o;out.append(f"{col(c)} rg {x} {self.h-y-h} {w} {h} re f")
   else:
    _,x,y,x2,y2,c=o;out.append(f"{col(c)} RG 0.7 w {x} {self.h-y} m {x2} {self.h-y2} l S")
  return "\n".join(out).encode("ascii")
def save_pdf(pages,path):
 objs=[b"<< /Type /Catalog /Pages 2 0 R >>",None,b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"];ids=[]
 for p in pages:
  pageid=len(objs)+1;streamid=pageid+1;ids.append(pageid);data=p.pdf()
  objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {p.w} {p.h}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {streamid} 0 R >>".encode())
  objs.append(f"<< /Length {len(data)} >>\nstream\n".encode()+data+b"\nendstream")
 objs[1]=f"<< /Type /Pages /Count {len(pages)} /Kids [{' '.join(str(i)+' 0 R' for i in ids)}] >>".encode()
 out=bytearray(b"%PDF-1.4\n");offsets=[0]
 for i,obj in enumerate(objs,1):offsets.append(len(out));out.extend(f"{i} 0 obj\n".encode()+obj+b"\nendobj\n")
 start=len(out);out.extend(f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode())
 for offset in offsets[1:]:out.extend(f"{offset:010d} 00000 n \n".encode())
 out.extend(f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode());path.write_bytes(out)
chart=Canvas(503,421)
def bar(y,label,value,maxv,color,labelvalue=None):
 chart.text(label,0,y+10,9);chart.rect(230,y,225*float(value)/maxv,13,color);chart.text(labelvalue or "$"+format(float(value),".2f"),462,y+10,9,INK,bold=True)
chart.text("01  TOKENIZER",0,14,10,TEAL,True);chart.text("Same input text can become more billable tokens.",0,35,11,INK,True)
bar(52,"Sonnet 4.6 reference",3,3,GRAY);bar(75,"Sonnet 5.5, same token count",2,3,TEAL);bar(98,"Sonnet 5.5, assumed +30% tokens",2.6,3,ORANGE)
chart.text("Hypothetical: 1M old input tokens; 33.3% lower unit price, 13.3% lower cost.",0,134,9,MUT);chart.line(0,150,503,150)
chart.text("02  EFFECTIVE DATE",0,175,10,TEAL,True);chart.text("Gemini 4 Argon: the effective date changes the cost.",0,196,11,INK,True)
bar(213,"Argon, through Nov 30",4,8,TEAL);bar(238,"Argon, scheduled from Dec 1",8,8,ORANGE)
chart.text("1M input + 0.2M billable output tokens, aggregated across requests.",0,274,9,MUT);chart.line(0,290,503,290)
chart.text("03  OUTPUT MIX",0,315,10,TEAL,True);chart.text("Gemini 3.5 Flash-Lite: output can dominate.",0,336,11,INK,True)
bar(353,"Flash-Lite, input charge only",.3,.8,GRAY)
chart.text("Flash-Lite, input + output",0,388,9);chart.rect(230,378,225*.3/.8,13,TEAL);chart.rect(230+225*.3/.8,378,225*.5/.8,13,ORANGE);chart.text("$0.80",462,388,9,ORANGE,True)
chart.text("Same aggregate mix as case 02; output contributes $0.50, or 62.5%.",0,415,9,MUT)
standalone=Canvas(551,513)
standalone.text("API price comparisons: three accounting traps",24,25,14,INK,True)
standalone.text("USD | 16 Oct 2026 | Compare bars within each panel; scales differ.",24,44,9,MUT)
standalone.add(chart,24,58)
standalone.text("Sources: Anthropic and Google pricing docs. Method and CSVs accompany the chart.",24,503,8,MUT)
(OUT/"cost-comparison.svg").write_text(standalone.svg())
p1=Canvas(595,842);p1.text("RESEARCH NOTE   /   16 OCTOBER 2026",46,49,9,TEAL,True)
p1.text("A cheaper token is not",46,89,25,INK,True);p1.text("always a cheaper task.",46,119,25,INK,True)
p1.para("Three reproducible examples show why API price comparisons need a tokenizer, an effective date and an output budget. These are accounting scenarios, not model-quality rankings.",46,151,86,10.5,15,MUT)
p1.add(chart,46,211);p1.text("Bar scales differ between cases; compare lengths only within each case.",46,649,8,MUT);p1.line(46,669,549,669);p1.text("EDITORIAL TAKEAWAY",46,685,10,TEAL,True)
p1.para("Ask what stays constant. Equal token counts do not guarantee equal text; current rates need not survive a budget period; and input-only prices omit output. Report the exact accounting basis alongside any savings claim.",46,708,88,10.5,15)
p1.text("Independent AI-produced work sample. No paid API calls or benchmark runs.",46,802,8,MUT);p1.text("1 / 2",525,802,8,MUT)
p2=Canvas(595,842);p2.text("METHOD & SOURCE CHECKS",46,49,9,TEAL,True);p2.text("Reproduce the comparison.",46,86,23,INK,True)
p2.text("Standard paid API rates, USD per million tokens; observed 16 October 2026.",46,114,9.5,MUT);p2.rect(46,132,503,24,PALE)
for s,x in [("Model",54),("Input",277),("Output",335),("Effective period",402)]:p2.text(s,x,148,9,INK,True)
table=[("Sonnet 4.6 [1]","3.00","15.00","Current; legacy"),("Sonnet 5.5 [1]","2.00","10.00","Current"),("Gemini 4 Argon [2]","2.00","10.00","To 30 Nov 2026"),("Gemini 4 Argon [2]","4.00","20.00","From 1 Dec; scheduled"),("Gemini 3.5 Flash-Lite [2]","0.30","2.50","Current")]
for i,row in enumerate(table):
 y=176+i*23
 for s,x in zip(row,[54,277,335,402]):p2.text(s,x,y,9)
 p2.line(46,y+9,549,y+9)
p2.text("WHAT WAS CALCULATED",46,315,10,TEAL,True)
y=p2.para("Cost = input millions x input rate + billable output millions x output rate. Quantities are aggregate across requests, never a single oversized request.",46,337,92,10,14)
y=p2.para("Case 01 uses an assumed 1.30 input-token multiplier, based on Anthropic's approximate newer-tokenizer comparison. $2 x 1.30 = $2.60 versus $3.00: 13.3% lower. This is a sensitivity example, not a measured corpus result.",46,y+9,92,10,14)
y=p2.para("Case 02 holds billable volumes fixed: $2 + (0.2 x $10) = $4; scheduled $4 + (0.2 x $20) = $8. Case 03: $0.30 + (0.2 x $2.50) = $0.80. Output share: $0.50 / $0.80 = 62.5%.",46,y+9,92,10,14)
p2.text("VERIFICATION & LIMITS",46,y+24,10,TEAL,True)
y=p2.para("Rates were checked against provider pricing tables; model pages confirmed the selected current models and Sonnet 4.6's legacy status. A second AI agent checked the source interpretation and arithmetic. The accompanying CSVs and Python script reproduce every plotted value.",46,y+46,92,10,14)
y=p2.para("No live bills, tokenization, latency or quality were measured. Google output counts include thinking tokens. Caching, batch/flex/priority rates, regional premiums, tool charges, taxes and negotiated discounts are excluded. Future prices are the published schedule observed today, not a guarantee.",46,y+9,92,10,14)
p2.text("PRIMARY SOURCES",46,y+24,10,TEAL,True);p2.text("[1] Anthropic model pricing and tokenizer note",46,y+44,9,INK,True);p2.text(ANT,46,y+58,8,MUT)
p2.text("[2] Google Gemini Developer API pricing",46,y+77,9,INK,True);p2.text(GOO,46,y+91,8,MUT)
p2.text("Verification session: 15:36-15:42 UTC, 16 October 2026. Provenance in JSON.",46,775,8,MUT)
p2.text("Prepared by Sanyam Singh's AI assistant. Original analysis; not commissioned.",46,802,8,MUT);p2.text("2 / 2",525,802,8,MUT)
save_pdf([p1,p2],OUT/"api-cost-analysis.pdf")
print(json.dumps({"scenarios_verified":len(scenarios),"pages":2,"pdf_bytes":(OUT/"api-cost-analysis.pdf").stat().st_size,"source_bottom_y":y+91}))
