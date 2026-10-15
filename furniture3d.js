import * as THREE from 'three';
import {RoundedBoxGeometry} from 'three/addons/geometries/RoundedBoxGeometry.js';
// Original procedural models. Dimensions follow the saved footprint, in metres.
export function detailedFurniture(o,scale,wallHeight){
 const g=new THREE.Group(),t=o.type.toLowerCase(),w=Math.max(.1,(o.width||70)*scale),d=Math.max(.1,(o.height||50)*scale);
 const material=(color,extra={})=>new THREE.MeshStandardMaterial({color,roughness:.78,...extra});
 const wood=material('#a78a64'),oak=material('#cbb18b'),fabric=material(o.finishColor||'#81938b'),linen=material('#eee9df'),dark=material('#34443f'),metal=material('#bcaa82',{metalness:.65,roughness:.28});
 function surfaceTexture(color,grain){const canvas=document.createElement('canvas');canvas.width=canvas.height=128;const ctx=canvas.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,128,128);for(let i=0;i<128;i++){ctx.strokeStyle=i%3?'#ffffff0c':'#2e241018';ctx.lineWidth=grain?1:.6;ctx.beginPath();ctx.moveTo(0,i);ctx.lineTo(128,i+(grain?Math.sin(i*1.3)*2:0));ctx.stroke();if(!grain){ctx.beginPath();ctx.moveTo(i,0);ctx.lineTo(i,128);ctx.stroke()}}const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;texture.wrapS=texture.wrapT=THREE.RepeatWrapping;return texture}
 wood.map=surfaceTexture('#a78a64',true);wood.color.set('#ffffff');oak.map=surfaceTexture('#cbb18b',true);oak.color.set('#ffffff');fabric.map=surfaceTexture(o.finishColor||'#81938b',false);fabric.color.set('#ffffff');
 function mesh(geometry,m,x,y,z){const n=new THREE.Mesh(geometry,m);n.position.set(x,y,z);n.castShadow=true;n.receiveShadow=true;g.add(n);return n}
 const box=(a,b,c,x,y,z,m,r=.025)=>mesh(new RoundedBoxGeometry(Math.max(a,.01),Math.max(b,.01),Math.max(c,.01),2,Math.min(r,a/4,b/4,c/4)),m,x,y,z);
 const cyl=(r,h,x,y,z,m)=>mesh(new THREE.CylinderGeometry(r,r,h,20),m,x,y,z);
 const sphere=(a,b,c,x,y,z,m)=>{const n=mesh(new THREE.SphereGeometry(1,16,10),m,x,y,z);n.scale.set(a,b,c);return n};
 const legs=(height,spanW=w*.8,spanD=d*.8)=>{for(const x of [-spanW/2,spanW/2])for(const z of [-spanD/2,spanD/2])cyl(.025,height,x,height/2,z,dark)};
 if(/bed/.test(t)){
  legs(.18);box(w,.22,d,0,.24,0,wood);box(w*.97,.24,d*.96,0,.46,0,linen,.07);box(w+.02,1.05,.09,0,.62,-d/2,wood);box(w*.92,.67,.045,0,.72,-d/2+.07,fabric,.06);
  box(w*.97,.075,d*.66,0,.615,d*.15,fabric,.035);box(w*.98,.04,d*.15,0,.665,d*.35,linen);
  const count=w<1.2?1:2;for(let i=0;i<count;i++){const x=(i-(count-1)/2)*w*.46,p=box(w*.4,.14,d*.21,x,.66,-d*.3,linen,.06);p.rotation.y=(i?-.06:.06);box(w*.28,.16,d*.12,x,.74,-d*.19,fabric,.06)}
  for(let i=1;i<=6;i++)box(w*.96,.008,.008,0,.657,-d*.1+i*d*.06,material('#ffffff24',{transparent:true,opacity:.22}));
 }else if(/sofa|loveseat|chair|conversation/.test(t)){
  const chair=/chair|single/.test(t),n=chair?1:/2-seater|loveseat/.test(t)?2:3;legs(.14);box(w,.26,d,0,.28,0,fabric,.07);box(w,.5,d*.17,0,.65,-d*.42,fabric,.07);
  for(const x of [-w*.45,w*.45])box(w*.1,.43,d,x,.5,0,fabric,.05);
  for(let i=0;i<n;i++){const x=-w*.39+(i+.5)*w*.78/n;box(w*.76/n,.15,d*.69,x,.47,d*.04,linen,.055);const pillow=box(w*.7/n,.36,d*.12,x,.67,-d*.29,linen,.055);pillow.rotation.x=-.1}
  if(!chair){for(const sign of [-1,1]){const p=box(Math.min(.32,w*.18),.31,.12,sign*w*.29,.64,-d*.12,material(sign===1?'#c3a57f':'#72837f'),.055);p.rotation.z=sign*.15}}
  if(/l-shape|sectional/.test(t))box(w*.32,.24,d*.48,w*.28,.33,d*.56,fabric,.07);
 }else if(/table|desk|dining set/.test(t)){
  const coffee=/center|coffee/.test(t),h=coffee?.43:.76;legs(h-.05);box(w,.065,d,0,h,0,oak,.045);
  if(coffee){box(w*.22,.025,d*.28,-w*.17,h+.05,0,linen);cyl(Math.min(w,d)*.08,.14,w*.22,h+.11,0,material('#d5cbb7'));plant(w*.22,h+.18,0,Math.min(w,d)*.18)}
  if(/dining/.test(t)){const count=Math.max(2,Math.min(6,Math.floor(w/.55)));for(let i=0;i<count;i++){const x=(i-(count-1)/2)*w/count;for(const sign of [-1,1]){const z=sign*(d/2+.24);box(.38,.1,.38,x,.45,z,fabric);box(.38,.42,.06,x,.68,z+sign*.16,wood);for(const dx of [-.14,.14])cyl(.02,.42,x+dx,.21,z)}}}
 }else if(/wardrobe|storage|dresser|safe|tv unit|refrigerator/.test(t)){
  const h=/tv unit|dresser/.test(t)?.65:1.95;box(w,h,d,0,h/2,0,wood);const count=Math.max(2,Math.round(w/.55));for(let i=0;i<count;i++){const x=(i-(count-1)/2)*w/count;box(w/count-.015,h*.95,.035,x,h/2,d/2+.015,/refrigerator/.test(t)?linen:oak);cyl(.012,.15,x+w/count*.3,h*.53,d/2+.045,metal)}
  if(/tv/.test(t)){box(w*.85,.65,.04,0,1.13,-d*.2,dark);box(w*.8,.59,.012,0,1.13,-d*.2+.03,material('#26393e',{roughness:.2}));box(w*.3,.025,d*.4,0,.7,-d*.2,dark)}
 }else if(/lamp|light|pendant|chandelier|flush/.test(t)){
  const ceiling=/pendant|chandelier|flush|downlight|spotlight/.test(t),h=ceiling?wallHeight-.4:/table/.test(t)?.55:1.5,r=Math.min(w,d)*.44;
  cyl(r*.65,.04,0,.04,0,metal);cyl(.018,ceiling?.4:h-.2,0,ceiling?wallHeight-.2:h/2,0,metal);
  const shade=mesh(new THREE.CylinderGeometry(r*.6,r,.3,24,1,true),material('#f0d4a4',{side:THREE.DoubleSide,emissive:'#b99057',emissiveIntensity:.14}),0,h,0);sphere(.045,.05,.045,0,h-.08,0,material('#fff4cd',{emissive:'#fff0b0',emissiveIntensity:.5}));
 }else if(/plant/.test(t)){cyl(Math.min(w,d)*.28,.28,0,.14,0,linen);plant(0,.29,0,Math.min(w,d)*.45)
 }else if(/toilet/.test(t)){box(w*.72,.7,d*.26,0,.35,-d*.35,linen,.06);sphere(w*.4,.18,d*.36,0,.35,d*.1,linen);cyl(w*.2,.28,0,.14,d*.07,linen);const ring=mesh(new THREE.TorusGeometry(w*.25,.035,8,24),dark,0,.49,d*.1);ring.rotation.x=Math.PI/2;ring.scale.y=d/w;
 }else if(/puja|mandir/.test(t)){box(w,.12,d,0,.14,0,wood);for(const x of [-w*.43,w*.43])cyl(.03,1.1,x,.75,-d*.3,metal);box(w*1.05,.12,d,0,1.35,0,wood);box(w*.9,.09,d*.9,0,.55,0,oak);sphere(.08,.12,.08,0,.72,0,metal)
 }else if(/sink|stove/.test(t)){box(w,.85,d,0,.425,0,wood);box(w+.025,.055,d+.025,0,.88,0,dark);if(/stove/.test(t)){for(const x of [-w*.25,w*.25])for(const z of [-d*.25,d*.25])cyl(Math.min(w,d)*.12,.025,x,.92,z,metal)}else{box(w*.65,.025,d*.65,0,.915,0,metal,.04);box(w*.49,.028,d*.49,0,.93,0,dark,.04);cyl(.025,.3,0,1.05,-d*.3,metal);box(.03,.03,d*.3,0,1.19,-d*.17,metal)}
 }else return null;
 function plant(x,y,z,r){const stem=material('#64836a'),leaf=material('#456d50');cyl(.012,r*.9,x,y+r*.45,z,stem);for(let i=0;i<9;i++){const angle=i*2.4,n=sphere(r*.16,r*.38,r*.09,x+Math.cos(angle)*r*.4,y+r*.5+(i%3)*r*.15,z+Math.sin(angle)*r*.4,leaf);n.rotation.z=Math.sin(angle)*.6;n.rotation.y=angle}}
 g.userData.detail='crafted';g.userData.labelHeight=1;return g;
}
