# -*- coding: utf-8 -*-
"""
Flujo de caja semanal: columnas = semanas (agrupadas por mes), filas = producción
pendiente por rubro (repartida entre las semanas reales del cronograma en que ese
rubro tiene tareas) + gastos comprometidos/cheques a vencer (fecha real de pago).

Fuente del cronograma: tablero_economico/cronograma.json (cargado del cronograma
entregado al cliente, 010926_CRONOGRAMADETRABAJOS_V2 — editar ahí si la obra se corre).
Escribe el resultado dentro de economia.json (clave "flujo_semanal").
"""
import json, os, datetime as dt
from _paths import SIE

base = os.path.join(SIE, "tablero_economico")
eco = json.load(open(os.path.join(base, "economia.json"), encoding="utf-8"))
crono = json.load(open(os.path.join(base, "cronograma.json"), encoding="utf-8"))
try:
    compras = json.load(open(os.path.join(base, "compras_reg.json"), encoding="utf-8"))["compras"]
except FileNotFoundError:
    compras = []

def n(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0

semanas = crono["semanas"]  # [{"semana":0,"fecha":"2026-08-10","mes":"AGOSTO 2026"}, ...]
fechas = [dt.date.fromisoformat(s["fecha"]) for s in semanas]

def semana_de(fecha_iso):
    """Última semana cuyo inicio es <= fecha (clampeado al rango del cronograma:
    el anticipo del viernes previo al inicio cae en la semana 1)."""
    try: d = dt.date.fromisoformat(fecha_iso)
    except (ValueError, TypeError): return len(semanas) - 1
    idx = 0
    for i, f in enumerate(fechas):
        if f <= d: idx = i
        else: break
    return idx

def pago_date(fecha, cond, vencimiento):
    if vencimiento:
        try: return vencimiento
        except (ValueError, TypeError): pass
    try: d = dt.date.fromisoformat(fecha)
    except (ValueError, TypeError): return fecha
    cl = (cond or "").lower()
    if "crédit" in cl or "credit" in cl or "cheque dif" in cl:
        return (d + dt.timedelta(days=30)).isoformat()
    return fecha

# --- producción pendiente por rubro, repartida en sus semanas activas ---
filas = []
for cap in eco["capitulos"]:
    semanas_activas = crono["cap_semanas"].get(cap["cap"], [])
    pendiente = max(0, cap["objetivo"] - cap["comprometido"])
    valores = [0.0] * len(semanas)
    if semanas_activas:
        porSemana = pendiente / len(semanas_activas)
        idx_por_semana = {s["semana"]: i for i, s in enumerate(semanas)}
        for sn in semanas_activas:
            i = idx_por_semana.get(sn)
            if i is not None: valores[i] += porSemana
    filas.append({"cap": cap["cap"], "nombre": cap["nombre"], "valores": [round(v) for v in valores]})

# --- pagos por semana real ---
# gastos_total: TODAS las compras (pagadas incluidas) → alimenta egresos/disponibilidad,
#   porque esa plata salió (o va a salir) de caja en esa semana.
# gastos (fila-alarma "a disponer"): solo lo que TODAVÍA va a salir de caja.
#   Regla (pedida por Nacho): "Autorizada" equivale a "Pagada" cuando la fecha de pago
#   ya pasó (contado ejecutado). PERO un cheque autorizado con vencimiento FUTURO sigue
#   siendo plata a disponer — el banco la debita al vencimiento, no al autorizar.
HOY_D = dt.date.today()
def es_pendiente(c, fecha_pago_iso):
    est = (c.get("estadoPago") or "").strip().lower()
    if est == "pagada":
        return False
    try: fp = dt.date.fromisoformat(fecha_pago_iso)
    except (ValueError, TypeError): fp = HOY_D
    if est == "autorizada" and fp <= HOY_D:
        return False   # autorizada y ya ejecutada = pagada
    return True

gastos_total = [0.0] * len(semanas)
gastos = [0.0] * len(semanas)
for c in compras:
    pd = pago_date(c.get("fecha"), c.get("cond"), c.get("fechaVencimiento"))
    i = semana_de(pd)
    gastos_total[i] += n(c.get("monto"))
    if es_pendiente(c, pd):
        gastos[i] += n(c.get("monto"))
gastos = [round(v) for v in gastos]
gastos_total = [round(v) for v in gastos_total]

# --- egresos totales por semana = producción pendiente (todos los rubros) + todas las compras ---
egresos = [round(sum(f["valores"][i] for f in filas) + gastos_total[i]) for i in range(len(semanas))]

# --- ingresos (cobros del cliente): plan de pagos de cronograma.json ("desembolsos") ---
DES = [[d["fecha"], d["monto"]] for d in crono["desembolsos"]]
ingresos = [0.0] * len(semanas)
for f, mo in DES:
    ingresos[semana_de(f)] += mo
ingresos = [round(v) for v in ingresos]

# --- disponibilidad en caja: acumulado ingresos - acumulado egresos ---
disponibilidad = []
ia = ea = 0
for i in range(len(semanas)):
    ia += ingresos[i]; ea += egresos[i]
    disponibilidad.append(ia - ea)

eco["flujo_semanal"] = {"semanas": semanas, "filas": filas, "gastos": gastos, "gastos_total": gastos_total,
                         "ingresos": ingresos, "egresos": egresos, "disponibilidad": disponibilidad}
json.dump(eco, open(os.path.join(base, "economia.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("OK flujo_semanal ·", len(semanas), "semanas ·", len(filas), "rubros")
print("Gastos comprometidos por semana:", gastos)
print("Ingresos por semana:", ingresos)
print("Disponibilidad en caja (fin de cada semana):", disponibilidad)
