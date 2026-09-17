# -*- coding: utf-8 -*-
"""
Sincroniza las compras del FORMULARIO PÚBLICO (Supabase) hacia el registro
`compras_reg.json`.

MODO RECONSTRUCCIÓN TOTAL (desde 2026-08-26): Supabase es la fuente de verdad.
En cada corrida se leen TODAS las filas y el registro se reescribe completo.
Así las EDICIONES y BORRADOS hechos desde el formulario web se reflejan solos
en los tableros (antes solo entraban filas nuevas y quedaban selladas).

El código ALTEZZA26.CP.#### se asigna una sola vez por fila (columna `codigo` en
Supabase, se escribe con service_role) y nunca se renumera — si se borra una
fila, su número queda como hueco, no se reutiliza.
"""
import sys, os, json, datetime, requests
sys.stdout.reconfigure(encoding="utf-8")
from _paths import SIE
from _supabase import REST_URL, headers

# service_role: variable de entorno primero (GitHub Actions), si no existe cae al
# archivo local (PC de Nacho) — así el mismo script corre en los dos contextos.
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not SERVICE_ROLE_KEY:
    from _supabase_secret import SERVICE_ROLE_KEY

def admin_headers(prefer=None):
    h = {"apikey": SERVICE_ROLE_KEY, "Authorization": "Bearer " + SERVICE_ROLE_KEY,
         "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    return h

REG = os.path.join(SIE, "tablero_economico", "compras_reg.json")
TREE = os.path.join(SIE, "tablero_economico", "partidas_insumos.json")

def cap_de(partida, byPart):
    p = byPart.get(partida)
    return p["cap"] if p else ""

def main():
    tree = json.load(open(TREE, encoding="utf-8"))
    byPart = {p["cod"]: p for p in tree["partidas"]}

    r = requests.get(REST_URL + "/compras_altezza26", params={"order": "id.asc"},
                     headers=headers(), timeout=30)
    if r.status_code == 404:
        print("  ⚠ la tabla compras_altezza26 aún NO existe en Supabase — registro vacío (correr el SQL).")
        rows = []
    else:
        r.raise_for_status()
        rows = r.json()

    # asignar código a las filas que no lo tienen (una sola vez, correlativo)
    mx = 0
    for row in rows:
        cod = row.get("codigo") or ""
        if cod.startswith("ALTEZZA26.CP."):
            try: mx = max(mx, int(cod.split(".")[-1]))
            except ValueError: pass
    nuevas = 0
    for row in rows:
        if row.get("codigo"):
            continue
        mx += 1
        row["codigo"] = f"ALTEZZA26.CP.{mx:04d}"
        pr = requests.patch(REST_URL + "/compras_altezza26", params={"id": f"eq.{row['id']}"},
                            headers=admin_headers(prefer="return=representation"),
                            json={"codigo": row["codigo"]}, timeout=20)
        pr.raise_for_status()
        if not pr.json():
            print(f"   ⚠ no se pudo guardar el código de id={row['id']} (revisar service_role key)")
        nuevas += 1
        print(f"  + {row['codigo']}  {row.get('proveedor','')} · {(row.get('detalle') or '')[:40]} · {row.get('monto')} Gs")

    hoy = datetime.date.today().isoformat()
    compras = []
    for row in rows:
        compras.append({
            "codigo": row.get("codigo") or "",
            "fecha": row.get("fecha") or hoy,
            "proveedor": row.get("proveedor", "") or "",
            "cap": cap_de(row.get("partida", ""), byPart),
            "partida": row.get("partida", "") or "",
            "insumo": row.get("insumo", "") or "",
            "detalle": row.get("detalle", "") or "",
            "cant": str(row.get("cant") or ""),
            "unidad": row.get("unidad", "") or "",
            "monto": str(row.get("monto") or ""),
            "tipo": row.get("tipo", "") or "",
            "cond": row.get("cond", "") or "",
            "estadoPago": row.get("estado_pago") or "Pendiente a autorizar",
            "beneficiario": row.get("beneficiario", "") or "",
            "medio": row.get("medio", "") or "",
            "refPago": row.get("concepto", "") or "",
            "fechaVencimiento": row.get("fecha_vencimiento") or "",
            "factura": row.get("factura", "") or "",
            "quien": row.get("quien", "") or "",
            "fcarga": (row.get("creado_en") or hoy)[:10],
        })

    reg = {"obra": "ALTEZZA26", "actualizado": hoy, "compras": compras}
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"OK · registro reconstruido: {len(compras)} compras ({nuevas} nuevas con código asignado).")
    return nuevas

if __name__ == "__main__":
    main()
