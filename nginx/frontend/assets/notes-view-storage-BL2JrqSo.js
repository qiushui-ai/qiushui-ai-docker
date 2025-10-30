import{c as m,j as o,Y as d,B as l}from"./index-QCM3tg6T.js";/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M=m("Grid3x3",[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",key:"afitv7"}],["path",{d:"M3 9h18",key:"1pudct"}],["path",{d:"M3 15h18",key:"5xshup"}],["path",{d:"M9 3v18",key:"fh3hqa"}],["path",{d:"M15 3v18",key:"14nvp0"}]]);/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const y=m("List",[["path",{d:"M3 12h.01",key:"nlz23k"}],["path",{d:"M3 18h.01",key:"1tta3j"}],["path",{d:"M3 6h.01",key:"1rqtza"}],["path",{d:"M8 12h13",key:"1za7za"}],["path",{d:"M8 18h13",key:"1lx6n3"}],["path",{d:"M8 6h13",key:"ik3vkj"}]]);function v({currentView:t,onViewChange:e,className:a}){return o.jsxs("div",{className:d("flex items-center border rounded-md",a),children:[o.jsx(l,{variant:t==="card"?"default":"ghost",size:"sm",onClick:()=>e("card"),className:d("h-8 px-3 rounded-none rounded-l-md",t==="card"?"bg-primary text-primary-foreground hover:bg-primary/90":"hover:bg-muted"),children:o.jsx(M,{className:"h-4 w-4"})}),o.jsx(l,{variant:t==="table"?"default":"ghost",size:"sm",onClick:()=>e("table"),className:d("h-8 px-3 rounded-none rounded-r-md",t==="table"?"bg-primary text-primary-foreground hover:bg-primary/90":"hover:bg-muted"),children:o.jsx(y,{className:"h-4 w-4"})})]})}function x(t){const e=new Date,a=new Date(t),i=e.getTime()-a.getTime();if(i<0)return"现在";const c=Math.floor(i/1e3),s=Math.floor(c/60),n=Math.floor(s/60),r=Math.floor(n/24),h=Math.floor(r/7),f=Math.floor(r/30),p=Math.floor(r/365);return c<60?"现在":s<60?`${s}分钟前`:n<24?`${n}小时前`:r<7?`${r}天前`:h<4?`${h}周前`:f<12?`${f}个月前`:`${p}年前`}const u="notes-view-mode";function k(t){try{localStorage.setItem(u,t)}catch(e){console.warn("Failed to save notes view mode:",e)}}function b(t="card"){try{const e=localStorage.getItem(u);if(e==="card"||e==="table")return e}catch(e){console.warn("Failed to get notes view mode:",e)}return t}export{v as V,x as f,b as g,k as s};
