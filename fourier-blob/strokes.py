import cv2, numpy as np, json, math
body=cv2.imread('body.png',0)
cs,_=cv2.findContours(body,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
c=max(cs,key=cv2.contourArea)[:,0,:].astype(float)
# smooth contour
k=7; n=len(c)
c=np.array([c[[(i+j)%n for j in range(-k,k+1)]].mean(0) for i in range(0,n)])
outline=c[::3].tolist(); outline.append(outline[0])

def cr(pts,seg=12,closed=False):
    P=[np.array(p,float) for p in pts]
    if closed: P=[P[-1]]+P+[P[0],P[1]]
    else: P=[P[0]]+P+[P[-1]]
    out=[]
    for i in range(1,len(P)-2):
        p0,p1,p2,p3=P[i-1:i+3]
        for t in np.linspace(0,1,seg,endpoint=False):
            out.append((0.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t**3)).tolist())
    out.append(P[-2].tolist()); return out
def ellipse(cx,cy,rx,ry,n=40):
    return [[cx+rx*math.cos(a),cy+ry*math.sin(a)] for a in np.linspace(0,2*math.pi,n)]
S={}
S={}
S['outline']=outline
S['eye']=ellipse(210,81,18,15.5)
S['pupil']=ellipse(214,82,8.5,9,30)
S['backeye']=cr([[160,78],[156,86],[158,96]])
S['mouth']=cr([[154,116],[170,117],[188,114]])
# arm: upper-arm back edge -> elbow -> forearm bottom -> front-hand fingers -> thumb -> forearm top
S['arm']=cr([[348,232],[350,252],[348,272],[342,294],[332,312],[318,330],[300,342],[284,348],[252,358],[220,364],[188,370],[170,376],[158,381],
  [150,385],[143,387],[138,385],[135,381],[137,377],[143,375],[149,374],
  [140,374],[130,373],[125,369],[124,364],[127,360],[135,359],[146,358],
  [138,357],[129,356],[124,352],[124,347],[128,343],[138,342],[149,341],[155,338],
  [152,333],[147,328],[145,323],[148,319],[155,317],[163,319],[170,323],
  [178,326],[190,320],[207,310],[225,298],[242,290],[258,286],[276,281]],6)
S['crease']=cr([[265,230],[264,250],[263,270],[262,284]])
S['belly_top']=cr([[122,263],[138,246],[162,231],[190,224],[216,231],[236,249],[247,270],[252,285]])
S['belly_patch_low']=cr([[112,398],[135,412],[165,420],[200,421],[235,416],[265,405],[290,392],[306,375],[313,355],[314,334]])
# far-side hand: fingers wrap round the belly edge
S['hand_back']=cr([[85,318],[95,316],[103,316],[107,319],[104,327],[100,333],[97,336],
  [102,339],[106,343],[106,347],[103,352],[97,355],
  [102,357],[105,361],[103,366],[96,369],
  [101,371],[103,375],[99,379],[93,381]],6)
S['fl1']=cr([[97,336],[88,334]]); S['fl2']=cr([[97,355],[87,352]]); S['fl3']=cr([[96,369],[88,366]])
S['belly_low']=cr([[150,480],[200,500],[250,505],[300,495],[335,470]])
S['toe_l1']=cr([[124,630],[132,640],[128,650]])
S['toe_l2']=cr([[140,640],[146,650]])
S['toe_r1']=cr([[270,668],[274,676],[270,684]])
S['toe_r2']=cr([[290,672],[292,682]])
json.dump(S,open('strokes.json','w'))
img=np.full((760,480,3),255,np.uint8)
for k,v in S.items():
    cv2.polylines(img,[np.int32(v)],False,(0,0,0),2,cv2.LINE_AA)
orig=cv2.imread('../../images/2.png'); ov=orig.copy()
for v in S.values(): cv2.polylines(ov,[np.int32(v)],False,(255,0,0),2,cv2.LINE_AA)
cv2.imwrite('preview.png',np.hstack([img,ov]))
cv2.imwrite('zoomcheck.png',cv2.resize(np.hstack([img[190:440,60:380],ov[190:440,60:380]]),None,fx=2,fy=2))
