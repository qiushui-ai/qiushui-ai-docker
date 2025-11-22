import{c as d,j as a,y as r,B as o}from"./index-CTPVv2qI.js";/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h=d("Grid3x3",[["rect",{width:"18",height:"18",x:"3",y:"3",rx:"2",key:"afitv7"}],["path",{d:"M3 9h18",key:"1pudct"}],["path",{d:"M3 15h18",key:"5xshup"}],["path",{d:"M9 3v18",key:"fh3hqa"}],["path",{d:"M15 3v18",key:"14nvp0"}]]);/**
 * @license lucide-react v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const i=d("List",[["path",{d:"M3 12h.01",key:"nlz23k"}],["path",{d:"M3 18h.01",key:"1tta3j"}],["path",{d:"M3 6h.01",key:"1rqtza"}],["path",{d:"M8 12h13",key:"1za7za"}],["path",{d:"M8 18h13",key:"1lx6n3"}],["path",{d:"M8 6h13",key:"ik3vkj"}]]);function l({currentView:t,onViewChange:e,className:n}){return a.jsxs("div",{className:r("flex items-center border rounded-md",n),children:[a.jsx(o,{variant:t==="card"?"default":"ghost",size:"sm",onClick:()=>e("card"),className:r("h-8 px-3 rounded-none rounded-l-md",t==="card"?"bg-primary text-primary-foreground hover:bg-primary/90":"hover:bg-muted"),children:a.jsx(h,{className:"h-4 w-4"})}),a.jsx(o,{variant:t==="table"?"default":"ghost",size:"sm",onClick:()=>e("table"),className:r("h-8 px-3 rounded-none rounded-r-md",t==="table"?"bg-primary text-primary-foreground hover:bg-primary/90":"hover:bg-muted"),children:a.jsx(i,{className:"h-4 w-4"})})]})}const s="notes-view-mode";function m(t){try{localStorage.setItem(s,t)}catch(e){console.warn("Failed to save notes view mode:",e)}}function p(t="card"){try{const e=localStorage.getItem(s);if(e==="card"||e==="table")return e}catch(e){console.warn("Failed to get notes view mode:",e)}return t}export{l as V,p as g,m as s};
