import{a5 as s,ak as p,a0 as x,r as g,j as e,al as m,y as n,ai as v,am as f,an as u,ao as y,w as j}from"./index-C_oIiI4O.js";import{M as k}from"./main-DSKQ9ujU.js";import{S as N,a as M,b as S,c as w,d as b}from"./select-BauWeIlu.js";import"./index-C0WwR0Wa.js";import"./chevron-down-DRo-ILD-.js";/**
 * @license @tabler/icons-react v3.26.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var I=s("outline","browser-check","IconBrowserCheck",[["path",{d:"M4 4m0 1a1 1 0 0 1 1 -1h14a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-14a1 1 0 0 1 -1 -1z",key:"svg-0"}],["path",{d:"M4 8h16",key:"svg-1"}],["path",{d:"M8 4v4",key:"svg-2"}],["path",{d:"M9.5 14.5l1.5 1.5l3 -3",key:"svg-3"}]]);/**
 * @license @tabler/icons-react v3.26.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var z=s("outline","notification","IconNotification",[["path",{d:"M10 6h-3a2 2 0 0 0 -2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2 -2v-3",key:"svg-0"}],["path",{d:"M17 7m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0",key:"svg-1"}]]);/**
 * @license @tabler/icons-react v3.26.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var C=s("outline","palette","IconPalette",[["path",{d:"M12 21a9 9 0 0 1 0 -18c4.97 0 9 3.582 9 8c0 1.06 -.474 2.078 -1.318 2.828c-.844 .75 -1.989 1.172 -3.182 1.172h-2.5a2 2 0 0 0 -1 3.75a1.3 1.3 0 0 1 -1 2.25",key:"svg-0"}],["path",{d:"M8.5 10.5m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",key:"svg-1"}],["path",{d:"M12.5 7.5m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",key:"svg-2"}],["path",{d:"M16.5 10.5m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0",key:"svg-3"}]]);/**
 * @license @tabler/icons-react v3.26.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var R=s("outline","settings","IconSettings",[["path",{d:"M10.325 4.317c.426 -1.756 2.924 -1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543 -.94 3.31 .826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756 .426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543 -.826 3.31 -2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756 -2.924 1.756 -3.35 0a1.724 1.724 0 0 0 -2.573 -1.066c-1.543 .94 -3.31 -.826 -2.37 -2.37a1.724 1.724 0 0 0 -1.065 -2.572c-1.756 -.426 -1.756 -2.924 0 -3.35a1.724 1.724 0 0 0 1.066 -2.573c-.94 -1.543 .826 -3.31 2.37 -2.37c1 .608 2.296 .07 2.572 -1.065z",key:"svg-0"}],["path",{d:"M9 12a3 3 0 1 0 6 0a3 3 0 0 0 -6 0",key:"svg-1"}]]);/**
 * @license @tabler/icons-react v3.26.0 - MIT
 *
 * This source code is licensed under the MIT license.
 * See the LICENSE file in the root directory of this source tree.
 */var V=s("outline","user","IconUser",[["path",{d:"M8 7a4 4 0 1 0 8 0a4 4 0 0 0 -8 0",key:"svg-0"}],["path",{d:"M6 21v-2a4 4 0 0 1 4 -4h4a4 4 0 0 1 4 4v2",key:"svg-1"}]]);function A({className:i,items:t,...l}){const{pathname:c}=p(),r=x(),[o,h]=g.useState(c??"/settings"),d=a=>{h(a),r({to:a})};return e.jsxs(e.Fragment,{children:[e.jsx("div",{className:"p-1 md:hidden",children:e.jsxs(N,{value:o,onValueChange:d,children:[e.jsx(M,{className:"h-12 sm:w-48",children:e.jsx(S,{placeholder:"Theme"})}),e.jsx(w,{children:t.map(a=>e.jsx(b,{value:a.href,children:e.jsxs("div",{className:"flex gap-x-4 px-2 py-1",children:[e.jsx("span",{className:"scale-125",children:a.icon}),e.jsx("span",{className:"text-md",children:a.title})]})},a.href))})]})}),e.jsx(m,{orientation:"horizontal",type:"always",className:"hidden w-full bg-background px-1 py-2 md:block min-w-40",children:e.jsx("nav",{className:n("flex py-1 space-x-2 lg:flex-col lg:space-x-0 lg:space-y-1",i),...l,children:t.map(a=>e.jsxs(v,{to:a.href,className:n(f({variant:"ghost"}),c===a.href?"bg-muted hover:bg-muted":"hover:bg-transparent hover:underline","justify-start"),children:[e.jsx("span",{className:"mr-2",children:a.icon}),a.title]},a.href))})})]})}function F(){return e.jsx(e.Fragment,{children:e.jsxs(k,{fixed:!0,children:[e.jsx("div",{className:"space-y-0.5",children:e.jsx("h1",{className:"text-2xl font-bold tracking-tight md:text-3xl",children:"Settings"})}),e.jsx(u,{className:"my-4 lg:my-6"}),e.jsxs("div",{className:"flex flex-1 flex-col space-y-2 md:space-y-2 overflow-hidden lg:flex-row lg:space-x-12 lg:space-y-0",children:[e.jsx("aside",{className:"top-0 lg:sticky lg:w-1/5",children:e.jsx(A,{items:L})}),e.jsx("div",{className:"flex w-full p-1 pr-4 overflow-y-hidden",children:e.jsx(y,{})})]})]})})}const L=[{title:"Profile",icon:e.jsx(V,{size:18}),href:"/settings"},{title:"Account",icon:e.jsx(R,{size:18}),href:"/settings/account"},{title:"Appearance",icon:e.jsx(C,{size:18}),href:"/settings/appearance"},{title:"Notifications",icon:e.jsx(z,{size:18}),href:"/settings/notifications"},{title:"Display",icon:e.jsx(I,{size:18}),href:"/settings/display"}],D=j("/_authenticated/settings")({component:F});export{D as Route};
