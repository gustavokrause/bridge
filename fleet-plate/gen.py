#!/usr/bin/env python3
# Cyan Stratigraphy — "THE WORKING DEEP"
# A bathymetric survey plate that secretly charts the bridge/whale/ai-team/krill fleet.
import base64, math, random, os

HERE = os.path.dirname(os.path.abspath(__file__))
# Set FONT_DIR env to your canvas-design fonts dir; defaults to ./canvas-fonts next to this script.
FONT_DIR = os.environ.get("FONT_DIR", os.path.join(HERE, "canvas-fonts"))
W, H = 1240, 1754
rnd = random.Random(4100)

# ---------- palette ----------
BG_TOP="#0C2230"; BG_MID="#08182333"; BG_BOT="#03101A"
INK="#D2E7ED"; INK_DIM="#6E94A2"; INK_FAINT="#3F6573"
HAIR="#2C5061"; HAIR_HI="#46798B"
GLOW="#5CC6D8"; COP="#E0A35E"; COP_HI="#F4CE96"; COP_DIM="#9A6E3E"

def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def txt(x,y,s,size,fam="Jura",weight=300,fill=INK,anchor="start",ls=0,style="normal",op=1):
    st=f"font-family:'{fam}';font-weight:{weight};font-size:{size}px;letter-spacing:{ls}px;font-style:{style}"
    return f'<text x="{x:.2f}" y="{y:.2f}" fill="{fill}" text-anchor="{anchor}" style="{st}" opacity="{op}">{esc(s)}</text>'

def line(x1,y1,x2,y2,stroke=HAIR,w=1,op=1,dash=None,cap="butt"):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{w}" opacity="{op}" stroke-linecap="{cap}"{d}/>'

def wavy_path(y, x0, x1, amp, wl, step=6, phase=0.0):
    pts=[]
    x=x0
    while x<=x1:
        yy=y+amp*math.sin((x/wl)*2*math.pi+phase)
        pts.append((x,yy)); x+=step
    d="M "+" L ".join(f"{px:.1f} {py:.1f}" for px,py in pts)
    return d

S=[]  # svg fragments
def add(*a): S.extend(a)

# ============================================================ DEFS
defs=[]
defs.append(f'''<linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#0E2A3A"/>
  <stop offset="0.18" stop-color="#0B2230"/>
  <stop offset="0.5" stop-color="#071824"/>
  <stop offset="0.8" stop-color="#04121C"/>
  <stop offset="1" stop-color="#020B12"/>
</linearGradient>''')
defs.append('<radialGradient id="surfaceglow" cx="0.5" cy="0" r="0.9"><stop offset="0" stop-color="#1C4257" stop-opacity="0.55"/><stop offset="1" stop-color="#1C4257" stop-opacity="0"/></radialGradient>')
defs.append('<radialGradient id="vign" cx="0.5" cy="0.42" r="0.75"><stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.45"/></radialGradient>')
defs.append('<filter id="softcop" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3.2"/></filter>')
defs.append('<filter id="softcy" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="3.6"/></filter>')

# whale silhouette parts
# cetacean silhouette: rounded head (left), low dorsal fin, full belly, two-lobe fluke (right)
WHALE_BODY=("M 296 934 "
            "C 296 882 360 850 452 846 "          # head upper -> back
            "C 560 842 700 850 808 884 "          # long back
            "C 856 899 884 910 902 922 "          # to peduncle top
            "C 912 930 912 944 902 952 "          # peduncle
            "C 884 962 856 970 808 982 "          # underside back from peduncle
            "C 700 1010 560 1024 452 1020 "       # full belly
            "C 372 1017 316 1000 302 974 "        # lower head
            "C 297 962 296 948 296 934 Z")
WHALE_DORSAL="M 612 856 C 626 824 656 814 682 822 C 662 834 648 848 642 866 Z"
WHALE_FLUKE=("M 894 936 C 932 926 968 910 1004 906 "
             "C 990 922 972 932 950 938 "
             "C 972 944 990 956 1004 972 "
             "C 968 968 932 952 894 942 Z")
WHALE_FIN="M 560 1008 C 584 1056 632 1072 668 1058 C 640 1038 602 1014 580 1004 Z"
defs.append(f'<clipPath id="whaleclip"><path d="{WHALE_BODY}"/><path d="{WHALE_FLUKE}"/><path d="{WHALE_DORSAL}"/></clipPath>')
add('<defs>'+ "".join(defs) + '</defs>')

# ============================================================ BACKGROUND
add(f'<rect width="{W}" height="{H}" fill="#03101A"/>')
add(f'<rect width="{W}" height="{H}" fill="url(#water)"/>')
add(f'<rect width="{W}" height="420" fill="url(#surfaceglow)"/>')

# faint full-column isobath grain
for i in range(0, 70):
    y=300+i*21
    if y>1500: break
    ph=(i*0.7)
    add(f'<path d="{wavy_path(y,150,1140,2.2,520,8,ph)}" fill="none" stroke="{HAIR}" stroke-width="1" opacity="0.07"/>')

# ============================================================ PLATE FRAME
add(f'<rect x="56" y="56" width="{W-112}" height="{H-112}" fill="none" stroke="{INK_DIM}" stroke-width="1.1" opacity="0.55"/>')
add(f'<rect x="64" y="64" width="{W-128}" height="{H-128}" fill="none" stroke="{INK_FAINT}" stroke-width="0.8" opacity="0.5"/>')
# corner registration ticks
for cx,cy in [(64,64),(W-64,64),(64,H-64),(W-64,H-64)]:
    sx = 1 if cx<W/2 else -1
    sy = 1 if cy<H/2 else -1
    add(line(cx,cy,cx+sx*22,cy,INK_DIM,1,0.7))
    add(line(cx,cy,cx,cy+sy*22,INK_DIM,1,0.7))

# ============================================================ HEADER
add(txt(96,100,"PLATE I",12,"Geist",400,INK_DIM,ls=3))
add(txt(176,100,"FLEET HYDROGRAPHY",12,"Geist",400,INK_DIM,ls=3))
add(txt(1144,100,"SER. ai-team · whale · krill",12,"Geist",400,INK_DIM,anchor="end",ls=2))
add(line(96,114,1144,114,HAIR,1,0.7))
# title
add(txt(W/2,202,"THE WORKING DEEP",78,"Jura",300,INK,anchor="middle",ls=18))
# small flank ticks around subtitle
add(line(W/2-300,230,W/2-160,230,HAIR_HI,1,0.6))
add(line(W/2+160,230,W/2+300,230,HAIR_HI,1,0.6))
add(f'<circle cx="{W/2-150}" cy="230" r="2.2" fill="{COP}"/>')
add(f'<circle cx="{W/2+150}" cy="230" r="2.2" fill="{COP}"/>')
add(txt(W/2,238,"a hydrography of one self-operating fleet",25,"ISerif",400,INK_DIM,anchor="middle",style="italic",ls=1))
add(txt(W/2,266,"CAPTURED AT  bridge — fleet control room",11,"Geist",400,INK_FAINT,anchor="middle",ls=4))

# ============================================================ LEFT DEPTH AXIS
AX=150
SURF_Y=320; FLOOR_Y=1500
add(line(AX,SURF_Y,AX,FLOOR_Y,HAIR_HI,1,0.6))
# minor + major ticks; map depth 0..1400m across SURF..FLOOR
n_major=8
for m in range(0,n_major):
    yy=SURF_Y+(FLOOR_Y-SURF_Y)*m/(n_major-1)
    add(line(AX-12,yy,AX,yy,HAIR_HI,1.1,0.8))
    depth=int(round(m*(1400/(n_major-1))/10)*10)
    add(txt(AX-18,yy+4,f"{depth}",11,"Geist",400,INK_DIM,anchor="end",ls=1))
# minor ticks
yy=SURF_Y
while yy<=FLOOR_Y:
    add(line(AX-6,yy,AX,yy,HAIR,1,0.5))
    yy+=((FLOOR_Y-SURF_Y)/(n_major-1))/5
add(txt(AX-18,SURF_Y-10,"m",10,"Geist",400,INK_FAINT,anchor="end",ls=1))

# helper: stratum seam + labels
def seam(y,left,right,heavy=False):
    add(line(170,y,1140,y,HAIR_HI,1.4 if heavy else 1,0.7 if heavy else 0.5))
    add(txt(174,y-9,left,14,"Jura",500,INK,ls=3))
    add(txt(1140,y-9,right,12,"Geist",400,INK_DIM,anchor="end",ls=1.5))

# ============================================================ A — BRIDGE (surface)
add(f'<path d="{wavy_path(SURF_Y,170,1140,3.2,150,6,0)}" fill="none" stroke="{INK_DIM}" stroke-width="1.4" opacity="0.8"/>')
add(f'<path d="{wavy_path(SURF_Y+7,170,1140,2.6,150,6,1.2)}" fill="none" stroke="{HAIR_HI}" stroke-width="1" opacity="0.5"/>')
add(txt(174,SURF_Y-12,"bridge — THE CONTROL ROOM",14,"Jura",500,INK,ls=3))
add(txt(1140,SURF_Y-12,"the operator's deck · ./bin",12,"Geist",400,INK_DIM,anchor="end",ls=1.5))
# control switches
keys=[("npm start","boot the fleet"),("npm run status","diagnose"),("npm stop","by port")]
kx=210
for label,sub in keys:
    wkey=176
    add(f'<rect x="{kx}" y="356" width="{wkey}" height="44" rx="6" fill="none" stroke="{INK_DIM}" stroke-width="1" opacity="0.7"/>')
    add(f'<circle cx="{kx+16}" cy="378" r="3.4" fill="{GLOW}"/>')
    add(f'<circle cx="{kx+16}" cy="378" r="7" fill="none" stroke="{GLOW}" stroke-width="0.8" opacity="0.5"/>')
    add(txt(kx+30,375,label,14,"Geist",400,INK,ls=0.5))
    add(txt(kx+30,391,sub,10,"Geist",400,INK_FAINT,ls=0.5))
    kx+=wkey+34
add(txt(1140,382,"logs → ./logs",12,"Geist",400,INK_DIM,anchor="end",ls=1))
add(txt(1140,398,"real Claude · both apps",10,"Geist",400,INK_FAINT,anchor="end",ls=1))

# ============================================================ B — AI-TEAM
seam(470,"ai-team — SOURCE OF TRUTH","read-only · 14 personas · :—")
personas=[("A","STRAT"),("C","ORCH"),("M","PROD"),("R","SALES"),("F","FIN"),("C","MKT"),("D","METR"),
          ("H","UX"),("M","UI"),("J","COPY"),("A","FE"),("R","BE"),("L","OPS"),("P","LEGAL")]
cols=7
x0,x1=205,1135
pitch=(x1-x0)/(cols-1)
def persona(cx,cy,init,area,glow=False):
    if glow:
        add(f'<circle cx="{cx}" cy="{cy}" r="18" fill="none" stroke="{GLOW}" stroke-width="1" opacity="0.4" filter="url(#softcy)"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="15" fill="#08202C" stroke="{INK_DIM}" stroke-width="1" opacity="0.95"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="15" fill="none" stroke="{HAIR_HI}" stroke-width="0.6" opacity="0.5"/>')
    add(txt(cx,cy+5,init,15,"Jura",500,INK if not glow else COP_HI,anchor="middle"))
    add(txt(cx,cy+32,area,9,"Geist",400,INK_DIM,anchor="middle",ls=1))
for i,(init,area) in enumerate(personas[:7]):
    persona(x0+i*pitch,524,init,area, glow=(area=="ORCH"))
for i,(init,area) in enumerate(personas[7:]):
    persona(x0+i*pitch,604,init,area)
# bracket caption
add(txt(174,548,"{",30,"Jura",300,INK_DIM))
add(txt(174,628,"personas feed the",11,"Geist",400,INK_FAINT,ls=0.5))
add(txt(174,642,"strategy brain  ↓",11,"Geist",400,COP_DIM,ls=0.5))

# ============================================================ feed current (copper) personas -> whale head
add(f'<path d="M 360 650 C 360 720 320 760 320 820 C 320 850 322 862 332 884" fill="none" stroke="{COP}" stroke-width="1.6" opacity="0.85"/>')
add(f'<path d="M 360 650 C 360 720 320 760 320 820 C 320 850 322 862 332 884" fill="none" stroke="{COP_HI}" stroke-width="0.8" opacity="0.6" filter="url(#softcop)"/>')
add(f'<circle cx="360" cy="650" r="3" fill="{COP_HI}"/>')

# ============================================================ C — WHALE (the brain)
seam(690,"whale — THE STRATEGY BRAIN",":4100 · capture→distill→plan→triage→push")
# whale body fill + contour isobaths
add(f'<path d="{WHALE_FIN}" fill="#071C28" stroke="{HAIR_HI}" stroke-width="0.8" opacity="0.85"/>')
add(f'<path d="{WHALE_DORSAL}" fill="#0A2230" stroke="none" opacity="0.9"/>')
add(f'<path d="{WHALE_BODY}" fill="#0A2230" stroke="none" opacity="0.9"/>')
add(f'<path d="{WHALE_FLUKE}" fill="#0A2230" stroke="none" opacity="0.9"/>')
# interior isobaths clipped to whale
add(f'<g clip-path="url(#whaleclip)">')
yy=812
while yy<=1024:
    add(f'<path d="{wavy_path(yy,290,1010,1.8,320,6,(yy*0.05))}" fill="none" stroke="{HAIR_HI}" stroke-width="0.8" opacity="0.5"/>')
    yy+=8
# denser lateral-line contours along the body axis
for off in (-2,0,2):
    add(f'<path d="{wavy_path(934+off,300,902,3,440,6,0)}" fill="none" stroke="{HAIR_HI}" stroke-width="0.8" opacity="0.7"/>')
add('</g>')
# whale outline
add(f'<path d="{WHALE_DORSAL}" fill="none" stroke="{INK}" stroke-width="1.4" opacity="0.9"/>')
add(f'<path d="{WHALE_BODY}" fill="none" stroke="{INK}" stroke-width="1.7" opacity="0.95"/>')
add(f'<path d="{WHALE_FLUKE}" fill="none" stroke="{INK}" stroke-width="1.5" opacity="0.95"/>')
# eye + mouth + throat pleats
add(f'<circle cx="362" cy="938" r="4" fill="{INK}"/>')
add(f'<circle cx="362" cy="938" r="8" fill="none" stroke="{INK_DIM}" stroke-width="0.8" opacity="0.55"/>')
add(f'<path d="M 300 968 C 344 992 398 996 452 988" fill="none" stroke="{INK_DIM}" stroke-width="1.1" opacity="0.75"/>')
for px in (330,348,366,384,402):
    add(line(px,978,px,1006,HAIR_HI,0.7,0.4))
# blowhole spout hint above head
add(line(420,848,420,808,INK_DIM,1,0.4,dash="2 5"))
add(f'<circle cx="420" cy="806" r="2" fill="none" stroke="{INK_DIM}" stroke-width="0.8" opacity="0.5"/>')

# whale internal pipeline (copper spine current, left->right)
stages=[("capture",380),("distill",500),("plan",620),("triage",740),("push",858)]
spine_y=924
# current spline along spine, entering from head feed (332,884)
sp=f"M 332 884 C 348 904 360 916 {stages[0][1]} {spine_y} "
for i in range(1,len(stages)):
    px=stages[i][1]; pp=stages[i-1][1]
    sp+=f"C {pp+ (px-pp)*0.5:.0f} {spine_y-6} {px-(px-pp)*0.5:.0f} {spine_y-6} {px} {spine_y} "
sp+=f"C 884 924 892 932 906 952"
add(f'<path d="{sp}" fill="none" stroke="{COP}" stroke-width="1.8" opacity="0.9"/>')
add(f'<path d="{sp}" fill="none" stroke="{COP_HI}" stroke-width="0.9" opacity="0.55" filter="url(#softcop)"/>')
for i,(name,px) in enumerate(stages):
    add(f'<circle cx="{px}" cy="{spine_y}" r="5.5" fill="#0A2230" stroke="{COP_HI}" stroke-width="1.4"/>')
    add(f'<circle cx="{px}" cy="{spine_y}" r="2" fill="{COP_HI}"/>')
    # leader to label
    add(line(px,spine_y+8,px,1066,COP_DIM,0.8,0.7))
    add(txt(px,1082,name,12,"Geist",400,COP_HI,anchor="middle",ls=0.5))
    add(txt(px,1096,f"0{i+1}",9,"Geist",400,INK_FAINT,anchor="middle",ls=1))
add(txt(620,1124,"capture the day → distill signal → plan → triage by risk → push to the hands",12,"ISerif",400,INK_DIM,anchor="middle",style="italic"))

# ============================================================ HTTP sweep (whale -> krill)
add(f'<path d="M 906 952 C 980 1010 1010 1070 1010 1120 C 1010 1180 760 1180 560 1230 C 430 1262 330 1300 286 1330" fill="none" stroke="{COP}" stroke-width="1.7" opacity="0.85"/>')
add(f'<path d="M 906 952 C 980 1010 1010 1070 1010 1120 C 1010 1180 760 1180 560 1230 C 430 1262 330 1300 286 1330" fill="none" stroke="{COP_HI}" stroke-width="0.8" opacity="0.5" filter="url(#softcop)"/>')
# HTTP label badge
add(f'<rect x="966" y="1120" width="92" height="26" rx="13" fill="#0A2230" stroke="{COP_DIM}" stroke-width="1"/>')
add(txt(1012,1137,"HTTP",13,"Geist",400,COP_HI,anchor="middle",ls=3))
# arrowhead into krill
add(f'<path d="M 286 1330 l 14 -7 l -2 7 l 11 6 z" fill="{COP_HI}"/>')

# ============================================================ D — KRILL (the hands)
seam(1170,"krill — THE HANDS",":3000 · plan→implement→AI-review→verify→PR")
# krill swarm
kstations=[("plan",286),("implement",470),("AI-review",662),("verify",854),("PR",1030)]
KSY=1330
def krill_glyph(cx,cy,sc,rot,fill,op):
    return (f'<g transform="translate({cx:.1f} {cy:.1f}) rotate({rot:.1f}) scale({sc:.2f})" opacity="{op:.2f}">'
            f'<path d="M -5 1 Q -1 -3 5 -1 Q 6.5 0 5 1 Q 0 3 -5 1 Z" fill="{fill}"/>'
            f'<line x1="-3" y1="1" x2="-5" y2="3" stroke="{fill}" stroke-width="0.5"/>'
            f'<line x1="-1" y1="1.4" x2="-2" y2="3.6" stroke="{fill}" stroke-width="0.5"/>'
            f'<line x1="1" y1="1.4" x2="0.6" y2="3.8" stroke="{fill}" stroke-width="0.5"/>'
            f'<line x1="5" y1="-1" x2="8" y2="-2.4" stroke="{fill}" stroke-width="0.5"/></g>')
swarm=[]
attract_x=662
placed=0
attempts=0
while placed<340 and attempts<4000:
    attempts+=1
    x=rnd.uniform(186,1134); y=rnd.uniform(1196,1466)
    # density falloff from center x and avoid station label lane
    dx=abs(x-attract_x)/480
    edge_y=min((y-1196),(1466-y))/120
    p=(1-dx*0.55)*min(1,edge_y+0.2)
    if rnd.random()>p: continue
    if abs(y-KSY)<22 and 240<x<1100: continue   # keep station lane clear-ish
    placed+=1
    sc=rnd.uniform(0.8,1.5); rot=rnd.uniform(0,360)
    roll=rnd.random()
    if roll>0.965: fill,op=COP,rnd.uniform(0.7,0.95)
    elif roll>0.86: fill,op=INK,rnd.uniform(0.5,0.8)
    else: fill,op=HAIR_HI,rnd.uniform(0.25,0.6)
    swarm.append((y,krill_glyph(x,y,sc,rot,fill,op)))
for _,g in sorted(swarm,key=lambda t:t[0]):
    add(g)

# krill pipeline conveyor
add(line(286,KSY,1030,KSY,HAIR_HI,1,0.45,dash="1 6"))
for i,(name,px) in enumerate(kstations):
    glow = (name=="PR")
    col = COP_HI if glow else INK
    add(f'<rect x="{px-6}" y="{KSY-6}" width="12" height="12" fill="#06161F" stroke="{col}" stroke-width="1.2" transform="rotate(45 {px} {KSY})"/>')
    if i<len(kstations)-1:
        nx=kstations[i+1][1]
        add(f'<path d="M {px+12} {KSY} L {nx-14} {KSY}" stroke="{INK_DIM}" stroke-width="1" opacity="0.6"/>')
        add(f'<path d="M {nx-14} {KSY} l -8 -3.5 l 2 3.5 l -2 3.5 z" fill="{INK_DIM}" opacity="0.8"/>')
    ly = KSY-22 if i%2==0 else KSY+30
    add(txt(px,ly,name,12,"Geist",400,col,anchor="middle",ls=0.5))
    num = KSY-36 if i%2==0 else KSY+44
    add(txt(px,num,f"S{i+1}",9,"Geist",400,INK_FAINT,anchor="middle",ls=1))
add(txt(662,1452,"each task runs in its own worktree → lands as a pull-request",12,"ISerif",400,INK_DIM,anchor="middle",style="italic"))

# ============================================================ PR results rise through the right gutter
gx=1150
add(f'<path d="M 1030 {KSY} C 1092 {KSY} {gx} {KSY-26} {gx} {KSY-72} L {gx} 348" fill="none" stroke="{COP}" stroke-width="1.2" opacity="0.5"/>')
# arrowhead surfacing into the bridge
add(f'<path d="M {gx} 342 l -5 12 l 5 -4 l 5 4 z" fill="{COP_HI}" opacity="0.95"/>')
for i in range(9):
    t=i/8
    by=KSY-78-t*(KSY-78-362)
    r=4.4-t*2.7
    op=0.82-t*0.48
    bxx=gx+math.sin(t*5)*3
    add(f'<circle cx="{bxx:.1f}" cy="{by:.1f}" r="{max(1.3,r):.1f}" fill="none" stroke="{COP}" stroke-width="1" opacity="{op:.2f}"/>')
    if i in (2,5):
        add(f'<circle cx="{bxx:.1f}" cy="{by:.1f}" r="{max(1.3,r):.1f}" fill="none" stroke="{COP_HI}" stroke-width="0.8" opacity="{op:.2f}" filter="url(#softcop)"/>')
add(f'<text transform="translate(1170 940) rotate(-90)" text-anchor="middle" fill="{COP_DIM}" style="font-family:Geist;font-weight:400;font-size:10px;letter-spacing:3.5px">PULL-REQUESTS SURFACE AT THE BRIDGE</text>')

# ============================================================ FLOOR + FOOTER
# seabed
add(f'<path d="{wavy_path(FLOOR_Y,170,1140,4,260,6,0.4)}" fill="none" stroke="{INK_DIM}" stroke-width="1.3" opacity="0.7"/>')
hx=176
while hx<1140:
    hh=rnd.uniform(6,16)
    add(line(hx,FLOOR_Y+2,hx+rnd.uniform(-3,3),FLOOR_Y+2+hh,HAIR_HI,0.9,0.45))
    hx+=rnd.uniform(7,13)
add(txt(AX-18,FLOOR_Y+4,"1400",11,"Geist",400,INK_DIM,anchor="end",ls=1))
add(txt(174,FLOOR_Y-10,"FLOOR — self-modification gated to human review",11,"Geist",400,INK_FAINT,ls=1.5))

# legend
ly=1560
add(line(176,ly-18,1140,ly-18,HAIR,1,0.5))
add(txt(176,ly+2,"LEGEND",12,"Jura",500,INK_DIM,ls=4))
# items
lx=176; lyy=ly+30
add(f'<line x1="{lx}" y1="{lyy-4}" x2="{lx+34}" y2="{lyy-4}" stroke="{COP}" stroke-width="1.8"/>')
add(txt(lx+44,lyy,"live signal — the work-current",11,"Geist",400,INK_DIM,ls=0.5))
lx=176; lyy=ly+52
add(f'<circle cx="{lx+17}" cy="{lyy-4}" r="4" fill="{GLOW}"/>')
add(txt(lx+44,lyy,"active node / lit control",11,"Geist",400,INK_DIM,ls=0.5))
lx=520; lyy=ly+30
add(f'<path d="{wavy_path(lyy-4,lx,lx+34,2,40,5)}" fill="none" stroke="{HAIR_HI}" stroke-width="0.9"/>')
add(txt(lx+44,lyy,"isobath / depth contour",11,"Geist",400,INK_DIM,ls=0.5))
lx=520; lyy=ly+52
add(f'<circle cx="{lx+17}" cy="{lyy-4}" r="6" fill="none" stroke="{INK_DIM}" stroke-width="1"/>')
add(txt(lx+44,lyy,"persona — one of fourteen",11,"Geist",400,INK_DIM,ls=0.5))
# topology statement (right)
tx=1140
add(txt(tx,ly+30,"ONE-WAY CURRENT",12,"Jura",500,INK_DIM,anchor="end",ls=3))
add(txt(tx,ly+52,"ai-team  →  whale  →  krill",14,"Geist",400,INK,anchor="end",ls=1))
add(txt(tx,ly+70,"the brain reads the team, drives the hands; results rise",10,"Geist",400,INK_FAINT,anchor="end",ls=0.5))

# bottom catalog line
add(line(96,H-92,1144,H-92,HAIR,1,0.6))
add(txt(96,H-72,"CYAN STRATIGRAPHY",11,"Geist",400,INK_FAINT,ls=3))
add(txt(W/2,H-72,"N°  4100 / 3000",11,"Geist",400,INK_DIM,anchor="middle",ls=3))
add(txt(1144,H-72,"DEPTH IN METRES · SOUNDINGS TRUE",11,"Geist",400,INK_FAINT,anchor="end",ls=2))

# vignette on top
add(f'<rect width="{W}" height="{H}" fill="url(#vign)"/>')

svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'+"".join(S)+'</svg>'

# ---------- fonts ----------
def b64(p):
    with open(p,'rb') as f: return base64.b64encode(f.read()).decode()
faces=f"""
@font-face{{font-family:'Jura';font-weight:300;src:url(data:font/ttf;base64,{b64(FONT_DIR+'/Jura-Light.ttf')}) format('truetype');}}
@font-face{{font-family:'Jura';font-weight:500;src:url(data:font/ttf;base64,{b64(FONT_DIR+'/Jura-Medium.ttf')}) format('truetype');}}
@font-face{{font-family:'Geist';font-weight:400;src:url(data:font/ttf;base64,{b64(FONT_DIR+'/GeistMono-Regular.ttf')}) format('truetype');}}
@font-face{{font-family:'ISerif';font-style:italic;src:url(data:font/ttf;base64,{b64(FONT_DIR+'/InstrumentSerif-Italic.ttf')}) format('truetype');}}
"""
html=f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;background:#03101A}}
@page{{size:{W}px {H}px;margin:0}}
svg{{display:block}}
</style></head><body>{svg}</body></html>"""
with open(os.path.join(HERE, "plate.html"),"w") as f: f.write(html)
print("wrote plate.html", len(html), "bytes")

# crop pages for close inspection: (name, rx, ry, rw, rh, scale)
crops=[("crop_header",60,70,1120,210,1.0),
       ("crop_team",60,300,1120,360,1.1),
       ("crop_whale",230,680,920,470,1.2),
       ("crop_krill",150,1150,1090,360,1.1),
       ("crop_footer",60,1480,1120,230,1.1)]
for name,rx,ry,rw,rh,k in crops:
    cw,ch=int(rw*k),int(rh*k)
    page=f"""<!doctype html><html><head><meta charset="utf-8"><style>
{faces}
*{{margin:0;padding:0}}html,body{{width:{cw}px;height:{ch}px;overflow:hidden;background:#071824}}
#vp{{width:{cw}px;height:{ch}px;overflow:hidden;position:relative}}
#vp svg{{position:absolute;left:{-rx*k}px;top:{-ry*k}px;width:{W*k}px;height:{H*k}px}}
</style></head><body><div id="vp">{svg}</div></body></html>"""
    with open(os.path.join(HERE, f"{name}.html"),"w") as f: f.write(page)
print("wrote crops")
