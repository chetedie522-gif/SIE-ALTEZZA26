# -*- coding: utf-8 -*-
"""
Config del backend de compras (Supabase).

La `anon key` es PÚBLICA por diseño (Supabase la protege con Row Level Security,
no con secreto) — por eso se puede embeber en el HTML del formulario público sin
riesgo. La seguridad real está en las políticas RLS de la tabla `compras`
(insert/select para `anon`, sin update/delete).
"""
SUPABASE_URL = "https://sojylqmwrqkyskhvsatn.supabase.co"
SUPABASE_ANON_KEY = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNvanls"
                      "cW13cnFreXNraHZzYXRuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcxNjU1NDMsImV4cCI6MjEw"
                      "Mjc0MTU0M30.Q1BlbHmGqAyiD68HV_xtUF3_xSl7N6ty-1DUECwJZrk")
REST_URL = SUPABASE_URL + "/rest/v1"

def headers(prefer=None):
    h = {"apikey": SUPABASE_ANON_KEY, "Authorization": "Bearer " + SUPABASE_ANON_KEY,
         "Content-Type": "application/json"}
    if prefer: h["Prefer"] = prefer
    return h
