# -*- coding: utf-8 -*-
"""
Genera el FORMULARIO PÚBLICO de carga de compras (reemplaza la app-Artifact).
Escribe directo a Supabase por fetch() desde el navegador — sin backend propio,
sin login. Vive en el sitio como cualquier otro tablero: `/compras/`.

Una factura puede tener varias líneas (insumos, incluso de distinta partida) —
se arman en un borrador local y se registran todas juntas en un solo POST
(array) a Supabase cuando se aprieta "Registrar factura".

Sale desde el mismo partidas_app.json que usaba la app vieja (desplegable
partida -> insumo). Fuente: build_site.py lo copia a site/compras/index.html.
"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
from _paths import SYS
from _supabase import SUPABASE_URL, SUPABASE_ANON_KEY

data = json.load(open(SYS + "/partidas_app.json", encoding="utf-8"))
DATA = json.dumps(data, ensure_ascii=False)

HTML = r'''<title>Cargar compras · ALTEZZA26</title>
<style>
:root{--bg:#12161c;--card:#1b212a;--card2:#212a35;--line:#2c3540;--txt:#e8ecf1;--mut:#8c98a8;--ok:#2fa76a;--warn:#d9a020;--bad:#e0555f;--acc:#5b8fd6}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:14px;max-width:720px;margin:0 auto}
h1{font-size:19px}.sub{color:var(--mut);font-size:12.5px;margin:2px 0 14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--mut);margin-bottom:12px}
h3{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--acc);margin:14px 0 8px;border-top:1px solid var(--line);padding-top:12px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
label{display:block;font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.4px;margin-bottom:3px}
input,select{width:100%;background:var(--card2);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:9px 10px;font-size:14px}
.full{grid-column:1/-1}
button.main{background:var(--acc);color:#fff;border:none;border-radius:8px;padding:11px 18px;font-size:14px;font-weight:700;cursor:pointer;margin-top:12px;width:100%}
button.main:disabled{opacity:.5;cursor:default}
button.add{background:var(--card2);color:var(--txt);border:1px solid var(--acc);border-radius:8px;padding:9px 14px;font-size:13px;font-weight:600;cursor:pointer;margin-top:10px;width:100%}
.draft{margin-top:12px}
.dline{display:flex;justify-content:space-between;gap:10px;align-items:center;background:var(--card2);border-radius:8px;padding:8px 11px;margin-bottom:6px;font-size:13px}
.dline .x{background:transparent;border:none;color:var(--mut);cursor:pointer;font-size:14px}
.subt{display:flex;justify-content:space-between;font-weight:800;padding:8px 11px;font-size:14px}
details.conv{background:var(--card2);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-top:6px}
details.conv summary{cursor:pointer;font-size:12.5px;color:var(--acc);font-weight:600}
details.conv input[readonly]{background:var(--card);font-weight:700}
td.ed{cursor:text;outline:none}
td.ed:focus{background:rgba(91,143,214,.12)}
td.est{cursor:pointer;font-weight:700;font-size:11px;white-space:nowrap}
td.est[data-v="Pendiente a autorizar"]{color:var(--bad)}
td.est[data-v="Autorizada"]{color:var(--warn)}
td.est[data-v="Pagada"]{color:var(--ok)}
button.mini{background:transparent;border:none;cursor:pointer;font-size:14px;padding:2px 4px}
button.mini.save{opacity:.25}
tr.dirty button.mini.save{opacity:1;filter:drop-shadow(0 0 4px rgba(91,143,214,.9))}
.hint{color:var(--mut);font-size:11px;margin-top:2px}
.msg{border-radius:8px;padding:10px 12px;font-size:13px;margin-top:12px;display:none}
.msg.ok{background:rgba(47,167,106,.14);border:1px solid rgba(47,167,106,.4);color:#8fe0b6;display:block}
.msg.bad{background:rgba(224,85,95,.14);border:1px solid rgba(224,85,95,.4);color:#f0a8ad;display:block}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;color:var(--mut);font-weight:600;padding:6px 8px;border-bottom:1px solid var(--line);font-size:10px}
td{padding:6px 8px;border-bottom:1px solid var(--card2)}
.empty{color:var(--mut);font-style:italic;font-size:13px}
a.back{color:var(--acc);text-decoration:none;font-size:13px}
</style>

<a class="back" href="../">← volver al hub</a>
<h1>🛒 Cargar compra — Obra ALTEZZA26</h1>
<div class="sub">Techos y carpintería metálica — Pádel Santa Teresa</div>

<div class="card">
  <h2>➕ Cargar factura</h2>
  <div class="g3">
    <div><label>Proveedor</label><input id="proveedor" placeholder="ej. Hierro Matt"></div>
    <div><label>N° de factura</label><input id="factura" placeholder="ej. 001-0012345"></div>
    <div><label>Fecha</label><input id="fecha" type="date"></div>
    <div><label>Condición de pago</label><select id="cond"><option>Contado</option><option>Crédito 30 días (cheque)</option><option>Cheque diferido</option><option>Adelanto (antes de entrega)</option></select><div class="hint">el PLAZO acordado — si es a 30 días, elegí acá y abajo en "Medio de pago" marcá Cheque</div></div>
    <div><label>¿Quién carga?</label><select id="quien"><option>Nancy</option><option>Meli</option><option>Nacho</option><option>Elias</option><option>Otro</option></select></div>
    <div id="wrap_venc" style="display:none"><label>Vencimiento del cheque</label><input id="venc" type="date"><div class="hint">se sugiere fecha+30, ajustá si el cheque real vence otro día</div></div>
  </div>

  <h3>¿Cómo se paga? — el INSTRUMENTO (la condición de arriba ya dice el plazo)</h3>
  <div class="g3">
    <div><label>Medio de pago</label><select id="medio"><option value="">— elegir —</option><option>Transferencia</option><option>Cheque</option><option>TC Nacho</option><option>TC Elias</option><option>Efvo Nacho</option><option>Efvo Elias</option><option>Efvo Otro</option></select></div>
    <div><label>Estado de pago</label><select id="estado_pago"><option>Pendiente a autorizar</option><option>Autorizada</option><option>Pagada</option></select></div>
    <div><label>Beneficiario</label><input id="beneficiario" placeholder="a quién se le paga"></div>
    <div class="full"><label>Concepto (para conciliar con el extracto del banco)</label><input id="concepto" placeholder="ej. Pago factura 001-0012345 Hierro Matt"></div>
  </div>
  <div class="hint" id="devolHint" style="display:none">⚠ Efectivo puesto por una persona → queda pendiente de devolución (se ve en el tablero Control). La TC de Nacho/Elias es de la empresa, no genera devolución.</div>

  <h3>Líneas de la factura (un insumo por línea — pueden ser de distinta partida)</h3>
  <div class="grid">
    <div class="full"><label>Partida (capítulo)</label><select id="partida"></select></div>
    <div class="full"><label>Insumo dentro de la partida</label><select id="insumo" disabled><option value="">— elegí primero la partida —</option></select><div class="hint" id="hint"></div></div>
    <div class="full"><label id="lbldesc">Detalle (opcional)</label><input id="detalle" placeholder="marca / observación; o descripción del insumo nuevo"></div>
    <div><label>Cantidad</label><input id="cant" inputmode="decimal" placeholder="ej. 40"></div>
    <div><label>Unidad</label><input id="unidad" placeholder="auto del insumo"></div>
    <details class="full conv" id="cv"><summary>🔧 ¿Comprás varillas por unidad (12 m)? Convertí a kg</summary>
      <div class="g3" style="margin-top:8px">
        <div><label>Diámetro</label><select id="cv_dia"><option value="">—</option><option value="6">6 mm</option><option value="8">8 mm</option><option value="10">10 mm</option><option value="12">12 mm</option><option value="14">14 mm</option><option value="16">16 mm</option><option value="18">18 mm</option><option value="20">20 mm</option><option value="25">25 mm</option><option value="32">32 mm</option></select></div>
        <div><label>N° de varillas (12 m)</label><input id="cv_n" inputmode="numeric" placeholder="ej. 50"></div>
        <div><label>Equivale a</label><input id="cv_out" readonly value="0 kg"></div>
      </div>
      <button class="add" id="cv_use" type="button">Usar como cantidad (kg)</button>
    </details>
    <div class="full"><label>Tipo</label><select id="tipo"><option>Material</option><option>Subcontrato</option><option>Alquiler de equipo</option><option>Mano de obra</option><option>Otro</option></select></div>
    <div class="full"><label>TOTAL de esta línea (Gs, con IVA)</label><input id="monto" inputmode="numeric" placeholder="ej. 3.200.000"><div class="hint">el total que suma esta línea (cantidad × precio unitario), no el precio unitario.</div></div>
  </div>
  <button class="add" id="l_add">➕ Agregar línea a la factura</button>

  <div class="draft" id="draft"></div>
  <div class="subt" id="subt" style="display:none"><span>Subtotal factura</span><span id="subt_v">0</span></div>
  <button class="main" id="ok" disabled>Registrar factura</button>
  <div class="msg" id="msg"></div>
</div>

<div class="card">
  <h2>📋 Compras ya cargadas — para no repetir</h2>
  <input id="buscar" placeholder="🔎 buscar por proveedor, N° factura o detalle..." style="margin-bottom:10px">
  <div id="recientesWrap"><div class="empty">Cargando historial…</div></div>
</div>

<script>
const SUPABASE_URL = "__SB_URL__";
const SUPABASE_ANON_KEY = "__SB_KEY__";
const D = __DATA__;
const byId = Object.fromEntries(D.partidas.map(p=>[p.id,p]));
const f2 = n => new Intl.NumberFormat('es-PY').format(Math.round(n));
const fc = n => { const x=Number(n); return isFinite(x)?(Math.round(x*100)/100).toString():(n||''); };
const hoy = () => new Date().toISOString().slice(0,10);
document.getElementById('fecha').value = hoy();
let lines = [];  // líneas locales de la factura en armado

const selP=document.getElementById('partida'), selI=document.getElementById('insumo');
selP.innerHTML='<option value="">— elegí la partida —</option>';
for(const [c,nom] of Object.entries(D.caps)){
  const og=document.createElement('optgroup'); og.label=nom;
  D.partidas.filter(p=>p.cap===c).forEach(p=>{const o=document.createElement('option');o.value=p.id;o.textContent=`${p.cod} · ${p.desc}`;og.appendChild(o);});
  selP.appendChild(og);
}
selP.addEventListener('change',()=>{
  const p=byId[selP.value]; selI.innerHTML='';
  if(!p){selI.disabled=true;selI.innerHTML='<option value="">— elegí primero la partida —</option>';return;}
  selI.disabled=false;
  selI.appendChild(new Option('— elegí el insumo —',''));
  p.ins.forEach(i=>{const o=new Option(`${i.cod} · ${i.desc}`+(i.cant?` · obj ${fc(i.cant)} ${i.un||''}`:''),i.cod);selI.appendChild(o);});
  selI.appendChild(new Option('➕ nuevo insumo (no previsto)','NUEVO'));
  hintUpd();
});
selI.addEventListener('change',hintUpd);
function hintUpd(){
  const p=byId[selP.value],v=selI.value,lbl=document.getElementById('lbldesc'),h=document.getElementById('hint'),un=document.getElementById('unidad');
  if(v==='NUEVO'){lbl.textContent='Descripción del insumo NUEVO (obligatorio)';h.textContent='Se imputa a la partida como no previsto → aparecerá como desvío.';un.value='';un.readOnly=false;}
  else{lbl.textContent='Detalle (opcional)';const i=p&&p.ins.find(x=>x.cod===v);
    h.textContent=i&&i.cant?`Objetivo planificado: ${fc(i.cant)} ${i.un||''}`:'';
    if(i){un.value=i.un||'';
      const mm=(i.desc||'').match(/(\d{1,2})\s*mm/i);
      if(/varilla/i.test(i.desc||'') && mm && PV[+mm[1]]){document.getElementById('cv_dia').value=mm[1]; document.getElementById('cv').open=true; cvCalc();}
    } else {un.value='';}}
}
const lm=document.getElementById('monto');
lm.addEventListener('input',()=>{const d=lm.value.replace(/[^0-9]/g,'');lm.value=d?f2(parseInt(d,10)):'';});

// conversor de varillas: kg por varilla de 12 m según diámetro
const PV={6:2.66,8:4.74,10:7.40,12:10.66,14:14.52,16:18.96,18:24.00,20:29.64,25:46.20,32:75.72};
function cvCalc(){const d=+document.getElementById('cv_dia').value,nv=parseFloat((document.getElementById('cv_n').value||'').replace(',','.'))||0;
  const kg=d&&PV[d]?nv*PV[d]:0; document.getElementById('cv_out').value=fc(kg)+' kg'; return kg;}
document.getElementById('cv_dia').addEventListener('change',cvCalc);
document.getElementById('cv_n').addEventListener('input',cvCalc);
document.getElementById('cv_use').addEventListener('click',()=>{const kg=cvCalc();
  if(!kg){alert('Elegí el diámetro y el N° de varillas.');return;}
  document.getElementById('cant').value=Math.round(kg*100)/100; document.getElementById('unidad').value='kg';
  document.getElementById('cv').open=false;});

// vencimiento del cheque: solo visible con condición a crédito/cheque diferido, sugiere fecha+30
const selCond=document.getElementById('cond'), wrapVenc=document.getElementById('wrap_venc'), venc=document.getElementById('venc');
function condChange(){
  const cl=selCond.value.toLowerCase();
  const esCredito = cl.includes('crédito') || cl.includes('credito') || cl.includes('cheque dif');
  wrapVenc.style.display = esCredito ? 'block' : 'none';
  if(esCredito && !venc.value){
    const f=new Date(document.getElementById('fecha').value || hoy());
    f.setDate(f.getDate()+30);
    venc.value=f.toISOString().slice(0,10);
  }
}
selCond.addEventListener('change',condChange); condChange();

// alarma de devolución: efectivo de una persona (no la TC de la empresa)
const selMedio=document.getElementById('medio'), devolHint=document.getElementById('devolHint');
selMedio.addEventListener('change',()=>{devolHint.style.display = selMedio.value.startsWith('Efvo') ? 'block' : 'none';});

document.getElementById('l_add').addEventListener('click',()=>{
  const p=byId[selP.value], ins=selI.value, detalle=document.getElementById('detalle').value.trim();
  const monto=parseFloat((lm.value||'').replace(/[^0-9]/g,''));
  if(!p){alert('Elegí la partida de la línea.');return;}
  if(!ins){alert('Elegí el insumo (o "nuevo insumo").');return;}
  if(ins==='NUEVO'&&!detalle){alert('Poné la descripción del insumo nuevo.');return;}
  if(!monto){alert('Poné el monto de la línea.');return;}
  lines.push({partida:p.cod,insumo:ins,insDisp:ins==='NUEVO'?'NUEVO':ins,detalle,
              cant:document.getElementById('cant').value.trim(),unidad:document.getElementById('unidad').value.trim(),
              monto,tipo:document.getElementById('tipo').value});
  ['detalle','cant','unidad'].forEach(id=>document.getElementById(id).value=''); lm.value='';
  selP.value=''; selI.value=''; selI.disabled=true;
  selI.innerHTML='<option value="">— elegí primero la partida —</option>';
  document.getElementById('hint').textContent=''; renderDraft();
});

function renderDraft(){
  const d=document.getElementById('draft');
  d.innerHTML = lines.map((l,i)=>`<div class="dline"><span>${l.partida} · ${l.insDisp}${l.cant?' · '+l.cant+' '+(l.unidad||''):''}${l.detalle?' · '+l.detalle:''} <span style="color:var(--mut)">(${l.tipo})</span></span>`+
    `<span><b>${f2(l.monto)}</b> Gs <button class="x" data-i="${i}">✕</button></span></div>`).join('');
  const tot=lines.reduce((a,l)=>a+l.monto,0);
  const s=document.getElementById('subt'); s.style.display=lines.length?'flex':'none';
  document.getElementById('subt_v').textContent=f2(tot)+' Gs';
  document.getElementById('ok').disabled=!lines.length;
}
document.getElementById('draft').addEventListener('click',e=>{if(e.target.classList.contains('x')){lines.splice(+e.target.dataset.i,1);renderDraft();}});

let recientes=[];
const ESC=s=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
function renderRecientes(){
  const w=document.getElementById('recientesWrap');
  const q=(document.getElementById('buscar').value||'').trim().toLowerCase();
  const filt = q ? recientes.filter(r=>(r.proveedor||'').toLowerCase().includes(q)||(r.factura||'').toLowerCase().includes(q)||(r.detalle||'').toLowerCase().includes(q)) : recientes;
  if(!filt.length){w.innerHTML=`<div class="empty">${q?'Sin resultados para "'+q+'".':'Todavía no hay compras cargadas.'}</div>`;return;}
  let h='<div style="overflow-x:auto"><table><thead><tr><th>Fecha</th><th>Proveedor</th><th>N° factura</th><th>Partida</th><th>Detalle</th><th>Cant</th><th>Monto</th><th>Pago</th><th></th></tr></thead><tbody>';
  filt.forEach(r=>{
    const est=r.estado_pago||'Pendiente a autorizar';
    h+=`<tr data-id="${r.id}">`+
      `<td class="ed" data-f="fecha" contenteditable>${ESC(r.fecha)}</td>`+
      `<td class="ed" data-f="proveedor" contenteditable>${ESC(r.proveedor)}</td>`+
      `<td class="ed" data-f="factura" contenteditable>${ESC(r.factura)||''}</td>`+
      `<td>${ESC(r.partida)}</td>`+
      `<td class="ed" data-f="detalle" contenteditable>${ESC(r.detalle||r.insumo)}</td>`+
      `<td class="ed" data-f="cant" contenteditable>${ESC(r.cant)}${r.unidad?' '+ESC(r.unidad):''}</td>`+
      `<td class="ed" data-f="monto" contenteditable>${f2(r.monto)}</td>`+
      `<td class="est" data-v="${ESC(est)}" title="tocá para cambiar el estado">${ESC(est)}</td>`+
      `<td style="white-space:nowrap"><button class="mini save" title="guardar cambios">💾</button><button class="mini del" title="borrar esta línea">🗑</button></td>`+
      `</tr>`;
  });
  h+='</tbody></table></div><div class="hint" style="margin-top:6px">✏️ Tocá una celda para corregirla — el 💾 del final de la fila se enciende: apretalo para guardar. Tocá la columna Pago para marcar Pendiente → Autorizada → Pagada (también se guarda con 💾). 🗑 borra la línea (¡no tiene deshacer!).</div>';
  w.innerHTML=h;
}
document.getElementById('buscar').addEventListener('input',renderRecientes);

const wrapReg=document.getElementById('recientesWrap');
wrapReg.addEventListener('input',e=>{const tr=e.target.closest('tr[data-id]'); if(tr) tr.classList.add('dirty');});
wrapReg.addEventListener('click',async e=>{
  const tr=e.target.closest('tr[data-id]'); if(!tr) return;
  const id=tr.dataset.id;
  // return=representation: si el permiso (RLS) bloquea la edición, Supabase devuelve 200 con []
  // — con eso detectamos el "guardado fantasma" y avisamos en vez de mostrar ✅ falso.
  const HDRS={'apikey':SUPABASE_ANON_KEY,'Authorization':'Bearer '+SUPABASE_ANON_KEY,'Content-Type':'application/json','Prefer':'return=representation'};
  const MSG_PERM='⚠ NO SE GUARDÓ: Supabase rechazó el cambio (falta el permiso de edición/borrado — hay que correr el SQL de políticas). Avisale a Nacho.';
  if(e.target.classList.contains('est')){
    const o=['Pendiente a autorizar','Autorizada','Pagada'];
    const c=e.target; const nx=o[(o.indexOf(c.dataset.v)+1)%o.length];
    c.dataset.v=nx; c.textContent=nx; tr.classList.add('dirty'); return;
  }
  if(e.target.classList.contains('del')){
    if(!confirm('¿Borrar esta línea definitivamente?')) return;
    const r=await fetch(`${SUPABASE_URL}/rest/v1/compras_altezza26?id=eq.${id}`,{method:'DELETE',headers:HDRS});
    const filas=r.ok?await r.json().catch(()=>[]):[];
    if(r.ok&&filas.length){recientes=recientes.filter(x=>String(x.id)!==String(id)); renderRecientes();}
    else if(r.ok) alert(MSG_PERM);
    else alert('No se pudo borrar (HTTP '+r.status+'). Avisale a Nacho/Claude.');
    return;
  }
  if(e.target.classList.contains('save')){
    const get=f=>{const c=tr.querySelector(`[data-f="${f}"]`);return c?c.textContent.trim():null;};
    const body={
      fecha:get('fecha')||null, proveedor:get('proveedor'), factura:get('factura'),
      detalle:get('detalle'), estado_pago:tr.querySelector('.est').dataset.v,
      monto:parseFloat((get('monto')||'').replace(/[^0-9]/g,''))||0,
    };
    const cantRaw=(get('cant')||'').trim(); const mCant=cantRaw.match(/^([\d.,]+)\s*(.*)$/);
    if(mCant){body.cant=mCant[1].replace(',','.'); if(mCant[2]) body.unidad=mCant[2];}
    const r=await fetch(`${SUPABASE_URL}/rest/v1/compras_altezza26?id=eq.${id}`,{method:'PATCH',headers:HDRS,body:JSON.stringify(body)});
    const filas=r.ok?await r.json().catch(()=>[]):[];
    if(r.ok&&filas.length){tr.classList.remove('dirty'); e.target.textContent='✅'; setTimeout(()=>{e.target.textContent='💾';},1200);
      const it=recientes.find(x=>String(x.id)===String(id)); if(it) Object.assign(it,body);}
    else if(r.ok) alert(MSG_PERM);
    else alert('No se pudo guardar (HTTP '+r.status+'). Avisale a Nacho/Claude.');
  }
});

async function cargarHistorial(){
  try{
    const r = await fetch(SUPABASE_URL + '/rest/v1/compras_altezza26?select=id,codigo,fecha,proveedor,factura,partida,detalle,insumo,cant,unidad,monto,estado_pago,medio&order=creado_en.desc&limit=500', {
      headers:{'apikey':SUPABASE_ANON_KEY,'Authorization':'Bearer '+SUPABASE_ANON_KEY}
    });
    if(!r.ok) throw new Error('HTTP '+r.status);
    recientes = await r.json();
    renderRecientes();
  }catch(e){
    document.getElementById('recientesWrap').innerHTML='<div class="empty">No se pudo cargar el historial. Revisá tu conexión.</div>';
  }
}
cargarHistorial();

document.getElementById('ok').addEventListener('click', async ()=>{
  const btn=document.getElementById('ok'), msg=document.getElementById('msg');
  const proveedor=document.getElementById('proveedor').value.trim();
  if(!proveedor){alert('Poné el proveedor.');return;}
  if(!lines.length){alert('Agregá al menos una línea a la factura.');return;}

  const fecha=document.getElementById('fecha').value||hoy();
  const cond=document.getElementById('cond').value, quien=document.getElementById('quien').value;
  const factura=document.getElementById('factura').value.trim();
  const medio=selMedio.value, estado_pago=document.getElementById('estado_pago').value;
  const beneficiario=document.getElementById('beneficiario').value.trim();
  const concepto=document.getElementById('concepto').value.trim();
  const fecha_vencimiento = wrapVenc.style.display!=='none' ? (venc.value||null) : null;
  const rows = lines.map(l=>({fecha, proveedor, partida:l.partida, insumo:l.insumo, detalle:l.detalle,
    cant:l.cant, unidad:l.unidad, monto:l.monto, tipo:l.tipo, cond, quien, factura,
    medio, estado_pago, beneficiario, concepto, fecha_vencimiento}));

  btn.disabled=true; btn.textContent='Guardando...'; msg.className='msg';
  try{
    const r = await fetch(SUPABASE_URL + '/rest/v1/compras_altezza26', {
      method:'POST',
      headers:{'apikey':SUPABASE_ANON_KEY,'Authorization':'Bearer '+SUPABASE_ANON_KEY,
               'Content-Type':'application/json','Prefer':'return=minimal'},
      body: JSON.stringify(rows)
    });
    if(!r.ok) throw new Error('HTTP '+r.status);
    msg.className='msg ok'; msg.textContent=`✓ Factura registrada (${rows.length} línea${rows.length>1?'s':''}). El sitio se va a actualizar en un rato (automático).`;
    cargarHistorial();
    lines=[]; renderDraft();
    ['factura','beneficiario','concepto'].forEach(id=>document.getElementById(id).value='');
    document.getElementById('fecha').value=hoy();
    venc.value=''; selMedio.value=''; devolHint.style.display='none';
    document.getElementById('estado_pago').value='Pendiente a autorizar';
    document.getElementById('proveedor').focus();
  }catch(e){
    msg.className='msg bad'; msg.textContent='✗ No se pudo guardar. Revisá tu conexión e intentá de nuevo. ('+e.message+')';
  }finally{
    btn.disabled=!lines.length; btn.textContent='Registrar factura';
  }
});
</script>'''

out = HTML.replace("__DATA__", DATA).replace("__SB_URL__", SUPABASE_URL).replace("__SB_KEY__", SUPABASE_ANON_KEY)
outp = SYS + "/compras_altezza26.html"
open(outp, "w", encoding="utf-8").write(out)
print("OK · compras_altezza26.html ·", len(out), "bytes ·", len(data["partidas"]), "partidas")

# Variante "solo carga" (/cargar/): mismo formulario SIN el link de vuelta al hub.
# Para compartir con quien solo carga compras, sin invitarlo a navegar el resto.
out2 = out.replace('<a class="back" href="../">← volver al hub</a>', '')
open(SYS + "/cargar_altezza26.html", "w", encoding="utf-8").write(out2)
print("OK · cargar_altezza26.html (variante sin hub)")
