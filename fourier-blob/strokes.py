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
S['outline']=outline
S['eye']=ellipse(210,81,18,15.5)
S['pupil']=ellipse(214,82,8.5,9,30)
S['backeye']=cr([[160,78],[156,86],[158,96]])
S['mouth']=cr([[154,116],[170,117],[188,114]])
S['belly']=cr([[96,300],[110,262],[140,234],[180,218],[225,214],[255,222]])
S['arm_top']=cr([[255,222],[262,245],[262,272],[258,282]])
S['arm']=cr([[166,334],[200,322],[240,300],[262,285],[290,287],[320,305],[340,330]])
S['arm_low']=cr([[180,358],[230,350],[280,335],[320,322]])
_=cr([[148,326],[160,318],[172,322],[175,334],[166,346],[175,352],[172,368],[150,372],[128,366],[124,352],[132,340],[140,330],[148,326]])
d=cv2.imread('dark.png',0); d[400:]=0
d=cv2.morphologyEx(d,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
hs,_=cv2.findContours(d,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
for i,hc in enumerate(sorted(hs,key=cv2.contourArea)[-2:]):
    hc=hc[:,0,:].astype(float); m=len(hc)
    hc=np.array([hc[[(a+j)%m for j in range(-3,4)]].mean(0) for a in range(m)])[::2].tolist(); hc.append(hc[0])
    S['hand%d'%i]=hc
S['finger_r1']=cr([[128,346],[145,347],[158,344]])
S['finger_r2']=cr([[130,360],[148,361],[162,358]])
_=cr([[100,316],[92,325],[88,345],[94,362],[100,372]])
S['finger_l1']=cr([[90,336],[100,338]])
S['finger_l2']=cr([[92,352],[100,354]])
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
