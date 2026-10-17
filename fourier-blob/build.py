import json, numpy as np, math
S=json.load(open('strokes.json'))
strokes=[np.array(v) for v in S.values()]
closed=[np.linalg.norm(s[0]-s[-1])<3 for s in strokes]
# greedy ordering starting from outline
order=[]; cur=strokes[0]; rem=list(range(1,len(strokes))); path=[(cur,False)]
pos=cur[-1]
while rem:
    best=None
    for i in rem:
        s=strokes[i]
        if closed[i]:
            j=int(np.argmin(np.linalg.norm(s-pos,axis=1))); d=np.linalg.norm(s[j]-pos)
            cand=np.vstack([s[j:-1],s[:j+1]])
        else:
            d0=np.linalg.norm(s[0]-pos); d1=np.linalg.norm(s[-1]-pos)
            d,cand=(d0,s) if d0<=d1 else (d1,s[::-1])
        if best is None or d<best[0]: best=(d,i,cand)
    d,i,cand=best; rem.remove(i)
    path.append((np.vstack([pos,cand[0]]),True)); path.append((cand,False)); pos=cand[-1]
path.append((np.vstack([pos,path[0][0][0]]),True))
# resample uniformly
step=2.0; pts=[]; pen=[]
for seg,up in path:
    for a,b in zip(seg[:-1],seg[1:]):
        L=np.linalg.norm(b-a); n=max(1,int(math.ceil(L/step)))
        for t in range(n): pts.append(a+(b-a)*t/n); pen.append(up)
P=np.array(pts); M=len(P); print('M',M)
cx,cy=240,380
X=P[:,0]-cx; Y=P[:,1]-cy
t=2*np.pi*np.arange(M)/M
K=400
co=[]
for k in range(1,K+1):
    c,s=np.cos(k*t),np.sin(k*t)
    co.append([2/M*(X@c),2/M*(X@s),2/M*(Y@c),2/M*(Y@s)])
co=np.round(np.array(co),3)
# pen-up intervals as fraction [0,1)
iv=[];i=0
while i<M:
    if pen[i]:
        j=i
        while j<M and pen[j]: j+=1
        iv.append([round(i/M,5),round(j/M,5)]); i=j
    else: i+=1
art=[[[round(x-cx,1),round(y-cy,1)] for x,y in np.array(v)[::2].tolist()+[v[-1]]] for v in S.values()]
data=dict(a0=[round(X.mean(),2),round(Y.mean(),2)],co=co.tolist(),up=iv,art=art,w=480,h=760)
# check reconstruction error
rec=np.zeros(M);
for k in range(1,K+1): rec+=co[k-1][0]*np.cos(k*t)+co[k-1][1]*np.sin(k*t)
print('err',np.abs(rec+X.mean()-X).mean(), len(iv))
s=json.dumps(data,separators=(',',':')); open('data.json','w').write(s); print(len(s))
