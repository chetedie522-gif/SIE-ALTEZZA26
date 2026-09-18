# -*- coding: utf-8 -*-
"""
PUBLICAR el sitio ALTEZZA26 de una sola pasada.

Recalcula los tableros desde los datos actuales (compras_reg / cobros_reg / economia /
pendientes), rearma la carpeta del sitio y hace `git push` SOLO si algo cambió.

Lo corre:
  - a mano:  python _sistema/publish_site.py
  - la tarea programada de Windows (cada 30 min).

Idempotente: si no cambió ningún dato, no genera commit (no ensucia el historial).
"""
import os, sys, json, subprocess, datetime
sys.stdout.reconfigure(encoding="utf-8")
from _paths import SIE, SYS

PY = sys.executable
SITE = os.environ.get("SIE_SITE_DIR", os.path.join(os.path.expanduser("~"), "SIE_ALTEZZA26_site"))

def run(script):
    print(f"→ {script}")
    subprocess.run([PY, os.path.join(SYS, script)], check=True)

def n(x):
    try: return float(x)
    except: return 0.0

def recompute_capitulos():
    """Actualiza economia.json: comprometido/desvío/‰ por capítulo desde compras_reg.
    (Antes quedaba en 0 aunque hubiera compras.)"""
    p = os.path.join(SIE, "tablero_economico", "economia.json")
    eco = json.load(open(p, encoding="utf-8"))
    try:
        compras = json.load(open(os.path.join(SIE, "tablero_economico", "compras_reg.json"), encoding="utf-8"))["compras"]
    except Exception:
        compras = []
    by_cap = {}
    for c in compras:
        by_cap[c.get("cap", "")] = by_cap.get(c.get("cap", ""), 0) + n(c.get("monto"))
    for cap in eco["capitulos"]:
        comp = round(by_cap.get(cap["cap"], 0))
        cap["comprometido"] = comp
        cap["desvio"] = max(0, comp - cap["objetivo"])   # solo sobregiro (positivo); 0 si está dentro del objetivo
        cap["consumido_pct"] = round(comp / cap["objetivo"] * 100, 1) if cap["objetivo"] else 0
    eco["resumen"]["comprometido"] = round(sum(by_cap.values()))
    eco["actualizado"] = datetime.date.today().isoformat()
    json.dump(eco, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"   economia.json · comprometido total: {eco['resumen']['comprometido']:,}")

def git(*args):
    return subprocess.run(["git", "-C", SITE, *args], capture_output=True, text=True)

print("== PUBLICAR SITIO ALTEZZA26 ==", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

# 0) traer las compras nuevas del formulario público (Supabase) al registro durable
import sync_compras_web
sync_compras_web.main()

# 1) recalcular datos derivados
recompute_capitulos()
run("compute_flujo_live.py")     # flujo de caja en vivo (reescribe economia.json, conserva capítulos)
run("compute_flujo_semanal.py")  # flujo semanal por rubro (usa capítulos recién actualizados)

# 2) regenerar los HTML de los tableros
run("gen_economico.py")
run("gen_control.py")
run("gen_form_compras.py")

# 3) rearmar la carpeta del sitio
run("build_site.py")

# 4) publicar si hay cambios
git("add", "-A")
status = git("status", "--porcelain").stdout.strip()
if not status:
    print("Sin cambios — no hay nada que publicar.")
    sys.exit(0)
git("commit", "-m", "auto: actualizar tableros " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
push = git("push")
out = (push.stdout + push.stderr).strip()
if push.returncode == 0:
    print("✓ Sitio publicado.\n" + out)
else:
    print("✗ Falló el push:\n" + out)
    sys.exit(1)
