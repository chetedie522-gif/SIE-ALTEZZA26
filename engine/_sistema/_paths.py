# -*- coding: utf-8 -*-
"""
Rutas PORTABLES del SIE ALTEZZA26.

Todo se resuelve desde la ubicación de ESTE archivo, que vive en
`SIE_ALTEZZA26/_sistema/`. Por eso el motor corre en cualquier PC o usuario
(Nacho, la Lenovo de la ofi, la de casa) sin editar una sola ruta:
la carpeta SIE se deduce sola.

Uso en cada script:
    from _paths import SIE, SYS            # los que necesiten
    from _paths import LOGO, PLAN          # logo / planificado

Convención:
    SYS  = carpeta _sistema/  → acá se escriben las fuentes .html de los artifacts
    SIE  = carpeta SIE_ALTEZZA26/  → carpeta oficial de la obra (datos, xlsx, dashboards)
    ROOT = carpeta OneDrive de Cúpula → raíz que comparten el SIE y las obras
"""
from pathlib import Path

_SYS = Path(__file__).resolve().parent          # .../SIE_ALTEZZA26/_sistema
_SIE = _SYS.parent                               # .../SIE_ALTEZZA26
_ROOT = _SIE.parent                              # .../OneDrive - Cúpula S.R.L

# Como str, para que sigan funcionando las concatenaciones tipo  SIE + r"\tablero_economico\..."
SYS = str(_SYS)
SIE = str(_SIE)
ROOT = str(_ROOT)

# Logo de Cúpula embebido en los tableros (vive en la carpeta SIE)
LOGO = str(_SIE / "Logos Originales Cupula_Mesa de trabajo 1 copia 3.png")

# PLANIFICADO_V1: es externo al SIE pero cuelga de la MISMA raíz de OneDrive,
# con el mismo relativo en cualquier PC → portable.
PLAN = str(_ROOT / "02 - Obras Cúpula 2026" / "002 - 2026" / "MAURI - PADEL SANTA TERESA"
           / "01 - OBRAS" / "ALTEZZA26 - PLANIFICADO.xlsx")

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for k in ("SYS", "SIE", "ROOT", "LOGO", "PLAN"):
        print(f"{k:5} = {globals()[k]}")
