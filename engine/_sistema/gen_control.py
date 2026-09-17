# -*- coding: utf-8 -*-
import json, sys, datetime as dt
sys.stdout.reconfigure(encoding="utf-8")
from _paths import SIE, SYS
tree = json.load(open(SIE + "/tablero_economico/partidas_insumos.json", encoding="utf-8"))
byPart = {p["cod"]: p for p in tree["partidas"]}
try: compras = json.load(open(SIE + "/tablero_economico/compras_reg.json", encoding="utf-8"))["compras"]
except: compras = []
CONTRATO = 343254000   # contrato BASE; los adicionales aprobados se leen de economia.json
try:
    _eco = json.load(open(SIE + "/tablero_economico/economia.json", encoding="utf-8"))
    ADICIONALES = _eco["resumen"].get("adicionales", [])
except Exception:
    ADICIONALES = []
AD_VENTA = round(sum(a.get("venta_con_iva", 0) for a in ADICIONALES))
UMB_AM, UMB_RO = 0.08, 0.15
def n(x):
    try: return float(x)
    except: return 0.0
try: cobros = json.load(open(SIE + "/tablero_economico/cobros_reg.json", encoding="utf-8"))["cobros"]
except: cobros = []
cobrado = sum(n(c.get("monto")) for c in cobros)

# comprometido por partida + análisis por insumo
comp_part = {}
insumoAn = []
for c in compras:
    comp_part[c["partida"]] = comp_part.get(c["partida"],0)+n(c["monto"])
    p = byPart.get(c["partida"]); ins=None
    if p and c.get("insumo")!="NUEVO":
        ins = next((i for i in p["insumos"] if i["cod"]==c["insumo"]), None)
    row = {"codigo":c["codigo"],"partida":c["partida"],"insumo":c.get("insumo",""),"detalle":c.get("detalle",""),
           "cantC":n(c.get("cant")),"un":c.get("unidad",""),"montoC":n(c.get("monto")),"nuevo":c.get("insumo")=="NUEVO",
           "estado":c.get("estadoPago",""),"medio":c.get("medio","")}
    if ins:
        oc=n(ins.get("cant")); ot=n(ins.get("total"))
        row["objCant"]=oc; row["objMonto"]=ot
        row["dCant"]= (row["cantC"]/oc-1) if oc else None
        row["dMonto"]=(row["montoC"]/ot-1) if ot else None
    else:
        row["objCant"]=0; row["objMonto"]=0; row["dCant"]=None; row["dMonto"]=None
    insumoAn.append(row)

# consolidado de insumo en TODA la obra (para materiales transversales: varilla, cemento, arena...)
master={}
for p in tree["partidas"]:
    for i in p["insumos"]:
        m=master.setdefault(i["cod"],{"desc":i["desc"],"un":i.get("unidad",""),"oCant":0.0,"oMonto":0.0,"nP":0})
        m["oCant"]+=n(i.get("cant")); m["oMonto"]+=n(i.get("total")); m["nP"]+=1
compIns={}
for c in compras:
    if c.get("insumo") and c["insumo"]!="NUEVO":
        d=compIns.setdefault(c["insumo"],{"cant":0.0,"monto":0.0}); d["cant"]+=n(c.get("cant")); d["monto"]+=n(c.get("monto"))
consol=[]
for cod,d in compIns.items():
    m=master.get(cod,{"desc":"","un":"","oCant":0,"oMonto":0,"nP":0})
    consol.append({"cod":cod,"desc":m["desc"],"un":m["un"],"cCant":d["cant"],"cMonto":d["monto"],
                   "oCant":m["oCant"],"oMonto":m["oMonto"],"nP":m["nP"],
                   "dCant":(d["cant"]/m["oCant"]-1) if m["oCant"] else None,
                   "dMonto":(d["monto"]/m["oMonto"]-1) if m["oMonto"] else None})

# devoluciones: efectivo de una persona → la empresa le debe reintegrar (TC de socios NO genera devolución)
devol={}
for c in compras:
    m=(c.get("medio") or "").strip()
    if m.lower().startswith("efvo") or m.lower().startswith("efectivo"):
        per=m.split(" ",1)[1].strip() if " " in m else "otro"
        devol[per]=devol.get(per,0)+n(c.get("monto"))
devolList=[{"persona":k,"monto":round(v)} for k,v in sorted(devol.items(),key=lambda x:-x[1])]

# próximos vencimientos de cheques (fechaVencimiento marcada a mano en el formulario)
HOY = dt.date.today()
vencList=[]
for c in compras:
    v = c.get("fechaVencimiento")
    if not v: continue
    try: vd = dt.date.fromisoformat(v)
    except (ValueError, TypeError): continue
    vencList.append({"fecha":v,"dias":(vd-HOY).days,"proveedor":c.get("proveedor",""),
                      "beneficiario":c.get("beneficiario",""),"monto":n(c.get("monto")),
                      "estado":c.get("estadoPago",""),"vencido":vd<HOY})
vencList.sort(key=lambda x:x["fecha"])

# comprometido dividido: PAGADO (plata que ya salió) vs A PAGAR (cheques emitidos / pendientes).
# Misma regla que el flujo semanal: Pagada, o Autorizada con fecha de pago ya pasada = pagado;
# Autorizada con vencimiento futuro (cheque emitido) = a pagar.
def fecha_pago(c):
    v = c.get("fechaVencimiento")
    if v:
        try: return dt.date.fromisoformat(v)
        except (ValueError, TypeError): pass
    try: d = dt.date.fromisoformat(c.get("fecha"))
    except (ValueError, TypeError): d = HOY
    cl = (c.get("cond") or "").lower()
    if "créd" in cl or "cred" in cl or "cheque dif" in cl: return d + dt.timedelta(days=30)
    return d

pagado = 0.0; porPagar = 0.0; pend_por_fecha = {}
for c in compras:
    m = n(c.get("monto")); fp = fecha_pago(c)
    est = (c.get("estadoPago") or "").strip().lower()
    if est == "pagada" or (est == "autorizada" and fp <= HOY):
        pagado += m
    else:
        porPagar += m
        pend_por_fecha[fp.isoformat()] = pend_por_fecha.get(fp.isoformat(), 0.0) + m
proxVenc = None
if pend_por_fecha:
    f0 = min(pend_por_fecha)
    proxVenc = {"fecha": f0, "monto": round(pend_por_fecha[f0])}

partidas=[{"cod":p["cod"],"cap":p["cap"],"desc":p["desc"],"obj":p["obj"],"comp":round(comp_part.get(p["cod"],0))} for p in tree["partidas"]]
objTotal=sum(p["obj"] for p in tree["partidas"])
DES=[["2026-08-14","Anticipo (pago inicial)",287950230],["2026-08-21","Pago semanal N°2",35993779],["2026-08-28","Pago semanal N°3",35993779],["2026-09-04","Pago semanal N°4",35993778],["2026-09-11","Pago semanal N°5",35993779],["2026-09-18","Pago semanal N°6",35993779],["2026-09-25","Pago semanal N°7",179968894],["2026-10-02","Pago semanal N°8",35993778],["2026-10-09","Pago semanal N°9",35993779],["2026-10-16","Pago semanal N°10",35993779],["2026-10-23","Pago semanal N°11",35993779],["2026-10-30","Pago semanal N°12",179968893],["2026-11-06","Pago semanal N°13",35993779],["2026-11-13","Pago semanal N°14",35993779],["2026-11-20","Pago semanal N°15",35993779],["2026-11-27","Pago semanal N°16",143975115],["2026-12-04","Pago semanal N°17",35993778],["2026-12-11","Pago semanal N°18",35993779],["2026-12-18","Pago semanal N°19 (saldo)",143975115]]
EMB=json.dumps({"partidas":partidas,"insumos":insumoAn,"consol":consol,"devol":devolList,"venc":vencList,"cobros":cobros,"cobrado":round(cobrado),
                "contrato":CONTRATO,"adVenta":AD_VENTA,
                "ads":[{"cod":a.get("cod"),"nombre":a.get("nombre"),"venta":a.get("venta_con_iva")} for a in ADICIONALES],
                "objTotal":objTotal,"comprometido":round(sum(comp_part.values())),
                "pagado":round(pagado),"porPagar":round(porPagar),"proxVenc":proxVenc,
                "umAm":UMB_AM,"umRo":UMB_RO}, ensure_ascii=False)

HTML=r'''<title>Control ALTEZZA26</title>
<style>
:root{--bg:#12161c;--card:#1b212a;--card2:#212a35;--line:#2c3540;--txt:#e8ecf1;--mut:#8c98a8;--ok:#2fa76a;--warn:#d9a020;--bad:#e0555f;--acc:#5b8fd6}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:14px;max-width:1050px;margin:0 auto}
.conf{background:rgba(224,85,95,.12);border:1px solid rgba(224,85,95,.35);color:#f0a8ad;border-radius:8px;padding:8px 12px;font-size:12px;font-weight:600;margin-bottom:12px;text-align:center}
h1{font-size:19px}.sub{color:var(--mut);font-size:12.5px;margin:2px 0 12px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:16px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:11px 13px}
.kpi .l{color:var(--mut);font-size:10px;text-transform:uppercase;letter-spacing:.5px}.kpi .v{font-size:18px;font-weight:800;margin-top:4px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--mut);margin-bottom:12px}
.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
label{display:block;font-size:11px;color:var(--mut);text-transform:uppercase;margin-bottom:3px}
input,select{width:100%;background:var(--card2);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:9px 10px;font-size:14px}
button.main{background:var(--acc);color:#fff;border:none;border-radius:8px;padding:10px 16px;font-size:14px;font-weight:700;cursor:pointer;margin-top:10px}
table{width:100%;border-collapse:collapse;font-size:12px;white-space:nowrap}
th{text-align:right;color:var(--mut);font-weight:600;padding:6px 8px;border-bottom:1px solid var(--line);font-size:10px}
th:nth-child(-n+3){text-align:left}
td{padding:6px 8px;border-bottom:1px solid var(--card2);text-align:right;font-variant-numeric:tabular-nums}
td:nth-child(-n+3){text-align:left}
.pill{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700}
.ok{background:rgba(47,167,106,.16);color:var(--ok)}.warn{background:rgba(217,160,32,.16);color:var(--warn)}.bad{background:rgba(224,85,95,.16);color:var(--bad)}.new{background:rgba(91,143,214,.16);color:var(--acc)}
.del{background:transparent;color:var(--mut);border:none;cursor:pointer;font-size:13px;padding:0 4px}
.wrap{overflow-x:auto}.empty{color:var(--mut);font-style:italic;font-size:13px;margin-top:6px}.note{color:var(--mut);font-size:11.5px;margin-top:8px}
a.back{color:var(--acc);text-decoration:none;font-size:13px;display:inline-block;margin-bottom:8px}
</style>

<a class="back" href="../">← volver al hub</a>
<div class="conf">🔒 CONFIDENCIAL · Solo dirección (Nacho / Elias) — cobros, costos y objetivos. No compartir.</div>
<h1>📊 Control ALTEZZA26 · Cobros y material</h1>
<div class="sub">Techos y carpintería metálica — Pádel Santa Teresa</div>
<div class="kpis" id="kpis"></div>

<div class="card">
  <h2>🎯 Consumo de material CONSOLIDADO en toda la obra (alarma real)</h2>
  <div class="wrap"><table id="tconsol"></table></div>
  <div class="note">Suma lo comprado de cada insumo contra su objetivo en TODAS las partidas. Es la alarma correcta para materiales transversales (varilla, cemento, arena) que sirven a varias partidas.</div>
</div>

<div class="card">
  <h2>📄 Detalle por línea de compra (imputación a la partida)</h2>
  <div class="wrap"><table id="tins"></table></div>
  <div class="note" id="insnote"></div>
</div>

<div class="card">
  <h2>💵 Depósitos del cliente (cobros)</h2>
  <div class="wrap"><table id="tcob"></table></div>
  <div class="note">Registro durable en OneDrive. Para sumar un depósito, avisale a Claude (fecha + concepto + monto) → queda guardado y NO se borra al actualizar el tablero.</div>
</div>

<div class="card">
  <h2>💸 Devoluciones a rendir (efectivo puesto por una persona)</h2>
  <div class="wrap"><table id="tdev"></table></div>
  <div class="note">Compras pagadas en efectivo por Nacho/Elias/otro → la empresa debe reintegrarles. La tarjeta de crédito de los socios NO genera devolución.</div>
</div>

<div class="card">
  <h2>🗓️ Próximos vencimientos de cheques</h2>
  <div class="wrap"><table id="tvenc"></table></div>
  <div class="note">Fecha marcada a mano al cargar la compra (condición crédito/cheque diferido). Ya está reflejado en el flujo de caja del tablero Económico.</div>
</div>

<div class="card">
  <h2>💰 Comprometido por partida (vs objetivo)</h2>
  <div class="wrap"><table id="tpart"></table></div>
</div>

<script>
const D=__EMB__;
const f2=n=>new Intl.NumberFormat('es-PY').format(Math.round(n));
const g=n=>Number(n).toLocaleString('es-PY',{maximumFractionDigits:1});
const hoy=()=>new Date().toISOString().slice(0,10);

// consolidado por insumo (toda la obra)
(function(){
  let h='<thead><tr><th>Insumo</th><th>Descripción</th><th></th><th>Comprado (obra)</th><th>Objetivo (obra)</th><th>Desvío cant.</th><th>Desvío $</th></tr></thead><tbody>';
  if(!D.consol.length){h+='<tr><td colspan="7" class="empty">Sin insumos previstos con compras.</td></tr>';}
  D.consol.forEach(i=>{
    const dc=i.dCant,dm=i.dMonto;
    const cc=dc==null?'ok':dc>D.umRo?'bad':dc>D.umAm?'warn':'ok';
    const cm=dm==null?'ok':dm>D.umRo?'bad':dm>D.umAm?'warn':'ok';
    const pc=`<span class="pill ${cc}">${dc==null?'—':(dc>=0?'+':'')+(dc*100).toFixed(0)+'%'}</span>`;
    const pm=`<span class="pill ${cm}">${dm==null?'—':(dm>=0?'+':'')+(dm*100).toFixed(0)+'%'}</span>`;
    h+=`<tr><td>${i.cod}</td><td>${i.desc.slice(0,34)} <span style="color:var(--mut)">(${i.nP} part.)</span></td><td></td>`+
       `<td>${g(i.cCant)} ${i.un} · ${f2(i.cMonto)}</td><td>${g(i.oCant)} ${i.un} · ${f2(i.oMonto)}</td><td>${pc}</td><td>${pm}</td></tr>`;
  });
  h+='</tbody>';document.getElementById('tconsol').innerHTML=h;
})();

// insumos
(function(){
  let h='<thead><tr><th>Partida</th><th>Insumo / detalle</th><th></th><th>Comprado</th><th>Objetivo</th><th>Desvío cant.</th><th>Desvío $</th><th>Pago</th></tr></thead><tbody>';
  if(!D.insumos.length){h+='<tr><td colspan="8" class="empty">Sin compras sincronizadas todavía.</td></tr>';}
  D.insumos.forEach(i=>{
    let cant,cost;
    if(i.nuevo){cant='<span class="pill new">🆕 no previsto</span>';cost='<span class="pill new">🆕</span>';}
    else{
      const dc=i.dCant, dm=i.dMonto;
      const cc=dc==null?'ok':dc>D.umRo?'bad':dc>D.umAm?'warn':'ok';
      const cm=dm==null?'ok':dm>D.umRo?'bad':dm>D.umAm?'warn':'ok';
      cant=`<span class="pill ${cc}">${dc==null?'—':(dc>=0?'+':'')+(dc*100).toFixed(0)+'%'}</span>`;
      cost=`<span class="pill ${cm}">${dm==null?'—':(dm>=0?'+':'')+(dm*100).toFixed(0)+'%'}</span>`;
    }
    const eCol = i.estado==='Pagada'?'ok':i.estado==='Autorizada'?'warn':'bad';
    const pago = i.estado ? `<span class="pill ${eCol}">${i.estado}</span>${i.medio?'<div style="color:var(--mut);font-size:10px;margin-top:2px">'+i.medio+'</div>':''}` : '—';
    h+=`<tr><td>${i.partida}</td><td>${(i.insumo==='NUEVO'?'':i.insumo+' · ')}${i.detalle}</td><td></td>`+
       `<td>${g(i.cantC)} ${i.un} · ${f2(i.montoC)}</td>`+
       `<td>${i.nuevo?'—':g(i.objCant)+' '+i.un+' · '+f2(i.objMonto)}</td><td>${cant}</td><td>${cost}</td><td>${pago}</td></tr>`;
  });
  h+='</tbody>';document.getElementById('tins').innerHTML=h;
  document.getElementById('insnote').textContent='🔴 rojo = se pasó +'+(D.umRo*100)+'% · 🟡 amarillo = +'+(D.umAm*100)+'% · 🆕 = insumo no previsto. Ojo: si una compra de varilla sirve a varias partidas, conviene repartirla o comparar contra el objetivo total del insumo en la obra.';
})();

// devoluciones a rendir
(function(){
  let h='<thead><tr><th>Persona</th><th></th><th>A devolver (Gs)</th></tr></thead><tbody>';
  if(!D.devol.length){h+='<tr><td colspan="3" class="empty">Sin devoluciones pendientes (nada pagado en efectivo por una persona).</td></tr>';}
  let t=0; D.devol.forEach(d=>{t+=d.monto;h+=`<tr><td>${d.persona}</td><td></td><td>${f2(d.monto)}</td></tr>`;});
  if(D.devol.length)h+=`<tr style="font-weight:800"><td>TOTAL a rendir</td><td></td><td>${f2(t)}</td></tr>`;
  h+='</tbody>';document.getElementById('tdev').innerHTML=h;
})();

// próximos vencimientos de cheques
(function(){
  let h='<thead><tr><th>Vencimiento</th><th>Proveedor / beneficiario</th><th></th><th>Estado</th><th>Monto</th></tr></thead><tbody>';
  if(!D.venc.length){h+='<tr><td colspan="5" class="empty">Sin cheques con vencimiento marcado.</td></tr>';}
  D.venc.forEach(v=>{
    const dias = v.vencido ? `<span class="pill bad">vencido</span>` : (v.dias<=7 ? `<span class="pill warn">en ${v.dias} día${v.dias==1?'':'s'}</span>` : `<span class="pill ok">en ${v.dias} días</span>`);
    h+=`<tr><td>${v.fecha}</td><td>${v.proveedor}${v.beneficiario?' · '+v.beneficiario:''}</td><td>${dias}</td><td>${v.estado}</td><td>${f2(v.monto)}</td></tr>`;
  });
  h+='</tbody>';document.getElementById('tvenc').innerHTML=h;
})();

// partidas con movimiento
(function(){
  const mov=D.partidas.filter(p=>p.comp>0);
  let h='<thead><tr><th>Cap</th><th>Partida</th><th></th><th>Objetivo</th><th>Comprometido</th><th>% cons.</th></tr></thead><tbody>';
  (mov.length?mov:[]).forEach(p=>{const pc=p.obj?p.comp/p.obj*100:0;const col=pc>100?'var(--bad)':pc>90?'var(--warn)':'var(--ok)';
    h+=`<tr><td>${p.cap}</td><td>${p.cod} · ${p.desc.slice(0,30)}</td><td></td><td>${f2(p.obj)}</td><td>${f2(p.comp)}</td><td style="color:${col}">${pc.toFixed(1)}%</td></tr>`;});
  if(!mov.length)h+='<tr><td colspan="6" class="empty">Sin comprometido todavía.</td></tr>';
  h+='</tbody>';document.getElementById('tpart').innerHTML=h;
})();

// cobros (durable, embebido — sin estado compartido → no se borra al republicar)
(function(){
  let h='<thead><tr><th>Fecha</th><th>Concepto</th><th>Monto Gs</th></tr></thead><tbody>';
  if(!D.cobros.length){h+='<tr><td colspan="3" class="empty">Sin depósitos registrados aún.</td></tr>';}
  D.cobros.forEach(c=>{h+=`<tr><td>${c.fecha}</td><td>${c.concepto}</td><td>${f2(c.monto)}</td></tr>`;});
  if(D.cobros.length)h+=`<tr style="font-weight:800"><td>TOTAL cobrado</td><td></td><td>${f2(D.cobrado)}</td></tr>`;
  h+='</tbody>';document.getElementById('tcob').innerHTML=h;
})();
function kpi(l,v,extra){return `<div class="kpi"><div class="l">${l}</div><div class="v">${v}</div>${extra?'<div style="font-size:11px;margin-top:3px">'+extra+'</div>':''}</div>`;}
let venAviso='';
if(D.proxVenc){
  const dv=Math.round((new Date(D.proxVenc.fecha)-new Date())/86400000);
  const [y,m,dd]=D.proxVenc.fecha.split('-');
  venAviso = dv<0 ? `<span style="color:var(--bad);font-weight:700">⚠ ${f2(D.proxVenc.monto)} VENCIDO (${dd}/${m})</span>`
           : `<span style="color:${dv<=7?'var(--warn)':'var(--mut)'}">próx. venc: ${dd}/${m} · ${f2(D.proxVenc.monto)} Gs${dv<=7?' ⚠':''}</span>`;
}
const contratoTotal=D.contrato+(D.adVenta||0);
document.getElementById('kpis').innerHTML=
  kpi('Contrato base',f2(D.contrato)+' Gs')+
  (D.adVenta?kpi('➕ Adicional '+(D.ads||[]).map(a=>a.cod).join('+'),f2(D.adVenta)+' Gs','trabajo aparte · aprobado'):'')+
  (D.adVenta?kpi('Contrato TOTAL',f2(contratoTotal)+' Gs'):'')+
  kpi('Cobrado',f2(D.cobrado)+' Gs · '+(contratoTotal?(D.cobrado/contratoTotal*100).toFixed(0):0)+'%')+kpi('Por cobrar',f2(contratoTotal-D.cobrado)+' Gs')+
  kpi('Objetivo material',f2(D.objTotal)+' Gs')+kpi('Comprometido',f2(D.comprometido)+' Gs · '+(D.objTotal?(D.comprometido/D.objTotal*100).toFixed(1):0)+'%')+
  kpi('✅ Pagado (gasto ejecutado)',f2(D.pagado)+' Gs')+
  kpi('🕐 A pagar (cheques emitidos / pendientes)',f2(D.porPagar)+' Gs',venAviso)+
  kpi('Compras sincronizadas',D.insumos.length);
</script>'''
out=HTML.replace("__EMB__",EMB)
open(SYS + "/control_altezza26.html","w",encoding="utf-8").write(out)
print("OK control ·",len(out),"bytes · insumos sync:",len(insumoAn),"· comprometido:",f"{round(sum(comp_part.values())):,}")
