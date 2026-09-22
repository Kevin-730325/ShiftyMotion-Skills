// Seconds in, deterministic geometry out. Usable in DOM, Canvas or offline frame rendering.
export const clamp01=x=>Math.max(0,Math.min(1,x));
export function progress(t,start,end){if(end<=start)throw new RangeError('end must exceed start');return clamp01((t-start)/(end-start));}
export const lerp=(a,b,p)=>a+(b-a)*p;
export const outExpo=p=>{p=clamp01(p);return p===1?1:1-2**(-10*p)};
export const inOut=p=>{p=clamp01(p);return p*p*p*(6*p*p-15*p+10)};
export function outBack(p,c=.65){p=clamp01(p)-1;return 1+(c+1)*p*p*p+c*p*p;}
export function rectAt(from,to,t,start,end,ease=inOut){const q=ease(progress(t,start,end));return Object.fromEntries(['x','y','width','height'].map(k=>[k,lerp(from[k],to[k],q)]));}
export function place(node,rect,{opacity=1,rotate=0,blur=0}={}){Object.assign(node.style,{width:rect.width+'px',height:rect.height+'px',transformOrigin:'0 0',transform:`translate3d(${rect.x}px,${rect.y}px,0) rotate(${rotate}deg)`,opacity:String(clamp01(opacity)),filter:blur>.08?`blur(${blur}px)`:'none'});}
// Each chunk owns an explicit reveal time, so text and optional key cues share a timeline.
export function textAt(chunks,t){return [...chunks].sort((a,b)=>a.t-b.t).filter(e=>e.t<=t).map(e=>e.text).join('');}
export function sceneAt(scenes,t){return scenes.find(s=>t>=s.start&&t<s.end)||null;}
