# -*- coding: utf-8 -*-
"""
Arma la carpeta `site/` (raíz del repo de GitHub Pages) juntando los tableros
que se PUBLICAN. Determinista: se regenera con un comando y se pushea.

Estructura resultante (todo estático, sin runtime de Claude):
  site/
    index.html            portada con logo + accesos
    dashboard/            avance físico (público, sin plata)  [index.html + datos.json]
    economico/            control económico y flujo           [index.html + economia.json]
    control/              control de cobros y material         [index.html]
    pendientes/           tareas y alertas                     [index.html + pendientes.json]
    .nojekyll             (que Pages sirva las carpetas tal cual)

Los tableros leen su JSON con ruta relativa → en Pages quedan EN VIVO al refrescar.
Para actualizar el sitio: regenerar cada tablero (gen_*), correr este script y `git push`.
"""
import os, shutil, base64, sys
sys.stdout.reconfigure(encoding="utf-8")
from _paths import SIE, SYS, LOGO

# El sitio/repo vive LOCAL, fuera de OneDrive (evita locks de sync y conflictos en .git).
# La fuente de datos sigue en OneDrive (SIE); GitHub es la copia publicada.
# Se puede override con la variable de entorno SIE_SITE_DIR.
SITE = os.environ.get("SIE_SITE_DIR", os.path.join(os.path.expanduser("~"), "SIE_ALTEZZA26_site"))

def fresh(dst):
    """Deja el subdir limpio (idempotente, sin arrastrar archivos viejos)."""
    if os.path.isdir(dst): shutil.rmtree(dst)
    os.makedirs(dst, exist_ok=True)

def copy_only(src, dst, names):
    """Copia SOLO los archivos de la whitelist (nunca vuelca la carpeta entera).
    Clave para no exponer JSON confidenciales (APU por insumo, registros crudos)."""
    fresh(dst)
    for name in names:
        s = os.path.join(src, name)
        if os.path.isfile(s): shutil.copy2(s, os.path.join(dst, name))
        else: print("   ⚠ falta (no se copia):", name)

os.makedirs(SITE, exist_ok=True)

# --- copiar los tableros de VISTA · SOLO index.html + el JSON que cada uno fetchea ---
# económico: SOLO economia.json (NO partidas_insumos/compras_reg/partidas/cobros_reg → tienen plata cruda)
copy_only(os.path.join(SIE, "tablero_economico"),  os.path.join(SITE, "economico"),  ["index.html", "economia.json"])
# control: fuente única es el .html del _sistema (datos embebidos, sin JSON suelto)
fresh(os.path.join(SITE, "control"))
shutil.copy2(os.path.join(SYS, "control_altezza26.html"), os.path.join(SITE, "control", "index.html"))

# compras: formulario público (escribe directo a Supabase) — reemplaza el link externo
fresh(os.path.join(SITE, "compras"))
shutil.copy2(os.path.join(SYS, "compras_altezza26.html"), os.path.join(SITE, "compras", "index.html"))

# cargar: variante del formulario SIN link al hub (para compartir solo-carga)
fresh(os.path.join(SITE, "cargar"))
shutil.copy2(os.path.join(SYS, "cargar_altezza26.html"), os.path.join(SITE, "cargar", "index.html"))

# --- portada ---
try:
    logo_uri = "data:image/png;base64," + base64.b64encode(open(LOGO, "rb").read()).decode()
    logo_html = f'<img class="logo" src="{logo_uri}" alt="Cúpula">'
except Exception:
    logo_html = '<div class="logo-txt">CÚPULA</div>'

CSS = """
:root{--bg:#12161c;--card:#1b212a;--card2:#212a35;--line:#2c3540;--txt:#e8ecf1;--mut:#8c98a8;--acc:#5b8fd6;--bad:#e0555f}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--txt);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:26px 16px;max-width:720px;margin:0 auto;text-align:center}
img.logo{height:74px;margin-bottom:10px}.logo-txt{font-weight:800;font-size:26px;letter-spacing:2px;margin-bottom:10px}
h1{font-size:22px;letter-spacing:-.3px}.sub{color:var(--mut);font-size:13px;margin:4px 0 22px}
.grid{display:grid;gap:12px}
a.btn{display:flex;align-items:center;gap:14px;text-align:left;text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;color:var(--txt);transition:.12s}
a.btn:hover{border-color:var(--acc);transform:translateY(-2px)}
a.btn .ico{font-size:28px;flex:0 0 auto}a.btn .t{font-size:17px;font-weight:700}
a.btn .d{font-size:12.5px;color:var(--mut);margin-top:1px}a.btn .conf{font-size:11px;color:var(--bad);font-weight:700}
.foot{color:var(--mut);font-size:11.5px;margin-top:22px;border-top:1px solid var(--line);padding-top:14px}
"""

def btn(href, ico, t, d, conf=False):
    c = '<div class="conf">🔒 contiene costos/márgenes</div>' if conf else ''
    return (f'<a class="btn" href="{href}"><span class="ico">{ico}</span>'
            f'<span><span class="t">{t}</span>{c}<div class="d">{d}</div></span></a>')

botones = (
    btn("compras/",    "🛒", "Cargar compras",        "Registrar las facturas de la obra") +
    btn("economico/",  "💰", "Económico y flujo",     "Objetivo vs comprometido, margen, caja", True) +
    btn("control/",    "📊", "Control de material",   "Comprometido por insumo, cobros, alarmas", True)
)

portada = (
    '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    '<title>SIE ALTEZZA26 · Cúpula</title><style>' + CSS + '</style></head><body>'
    + logo_html +
    '<h1>Obra ALTEZZA26 · Pádel Santa Teresa</h1>'
    '<div class="sub">Mauri · Arq. Zaida Vera · Asunción · Sistema de control de obra — Cúpula Estructuras</div>'
    '<div class="grid">' + botones + '</div>'
    '<div class="foot">Actualizado al publicar. Los tableros con 🔒 muestran costos y márgenes.</div>'
    '</body></html>'
)
open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(portada)

# .nojekyll → Pages sirve las carpetas tal cual
open(os.path.join(SITE, ".nojekyll"), "w", encoding="utf-8").write("")

# inventario
print("site/ armado en:", SITE)
for root, dirs, files in os.walk(SITE):
    if ".git" in root: continue
    rel = os.path.relpath(root, SITE)
    for f in sorted(files):
        print("  ", os.path.join("" if rel == "." else rel, f))
