# -*- coding: utf-8 -*-
"""
Flujo de caja mensual EN VIVO (clave "flujo" de economia.json).

A diferencia de FF26, acá NO hay fechas ni montos hardcodeados: todo sale de
tablero_economico/cronograma.json
  - "desembolsos": plan de pagos del cliente (ingresos)
  - "semanas" + "cap_semanas": cronograma de ejecución → curva de egreso del objetivo
Si la obra se corre, se edita cronograma.json y se vuelve a publicar.
"""
import json, sys, datetime as dt
sys.stdout.reconfigure(encoding="utf-8")
from _paths import SIE
base = SIE + "/tablero_economico/"
eco = json.load(open(base + "economia.json", encoding="utf-8"))
crono = json.load(open(base + "cronograma.json", encoding="utf-8"))
try: compras = json.load(open(base + "compras_reg.json", encoding="utf-8"))["compras"]
except Exception: compras = []
HOY = dt.date.today()

def n(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0
mk = lambda d: f"{d.year}-{d.month:02d}"

# curva de egreso del objetivo por mes: cada capítulo repartido parejo en sus semanas activas
fecha_sem = {s["semana"]: dt.date.fromisoformat(s["fecha"]) for s in crono["semanas"]}
E = {}
for cap in eco["capitulos"]:
    act = [s for s in crono["cap_semanas"].get(cap["cap"], []) if s in fecha_sem]
    for s in act:
        k = mk(fecha_sem[s]); E[k] = E.get(k, 0) + cap["objetivo"] / len(act)
totE = sum(E.values()) or 1

# cobros: plan de pagos del cliente (con IVA)
ing = {}
for d in crono["desembolsos"]:
    k = d["fecha"][:7]; ing[k] = ing.get(k, 0) + d["monto"]

# egresos REALES por fecha de pago. Prioridad: fecha_vencimiento explícita
# (cheque marcado a mano) > estimación por condición (crédito 30d / cheque dif → +30 días)
def pago_date(fecha, cond, vencimiento):
    if vencimiento:
        try: return dt.date.fromisoformat(vencimiento)
        except (ValueError, TypeError): pass
    try: d = dt.date.fromisoformat(fecha)
    except (ValueError, TypeError): d = HOY
    cl = (cond or "").lower()
    if "crédit" in cl or "credit" in cl or "cheque dif" in cl: return d + dt.timedelta(days=30)
    return d
egr_real = {}; comprometido = 0.0
for c in compras:
    comprometido += n(c.get("monto"))
    k = mk(pago_date(c.get("fecha"), c.get("cond"), c.get("fechaVencimiento")))
    egr_real[k] = egr_real.get(k, 0) + n(c.get("monto"))

# resto del objetivo (no comprado) distribuido por la curva del cronograma
resto = max(0, eco["resumen"]["objetivo_con_iva"] - comprometido)
meses = sorted(set(E) | set(ing) | set(egr_real))

flujo = []; ia = ea = 0.0; lo = None
for m in meses:
    egr = round(egr_real.get(m, 0) + resto * (E.get(m, 0) / totE))
    ia += ing.get(m, 0); ea += egr; neto = ia - ea
    row = {"mes": m, "ingreso": round(ing.get(m, 0)), "egreso": egr,
           "ing_acum": round(ia), "egr_acum": round(ea), "neto_acum": round(neto)}
    flujo.append(row)
    if lo is None or neto < lo["neto_acum"]: lo = row

eco["flujo"] = flujo
eco["flujo_supuesto"] = False
eco["esquema_cobro"] = ("plan de pagos entregado al cliente (45% anticipo · 25% fin fundaciones · 20% inicio chapas · "
                        "10% término) · egresos reales por fecha de pago (crédito 30d = +30 días) + resto del objetivo según cronograma")
eco["resumen"]["comprometido"] = round(comprometido)
eco["pico_exposicion"] = {"mes": lo["mes"], "monto": lo["neto_acum"]}
eco["necesidad_caja"] = max(0, -lo["neto_acum"])
json.dump(eco, open(base + "economia.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("Flujo en vivo (con IVA):")
for f in flujo: print(f"  {f['mes']}: ing {f['ingreso']:>13,} egr {f['egreso']:>13,} neto_acum {f['neto_acum']:>13,}")
print(f"\nComprometido: {round(comprometido):,} · resto objetivo: {round(resto):,}")
print(f"Punto más bajo de caja: {lo['neto_acum']:,} en {lo['mes']}")
