import json
import os
import unicodedata

from flask import Flask, render_template, request
from rapidfuzz import fuzz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "pcge_data.json")

app = Flask(__name__)

ELEMENTOS = [
    (1, "Activo Disponible y Exigible"),
    (2, "Activo Realizable"),
    (3, "Activo Inmovilizado"),
    (4, "Pasivo"),
    (5, "Patrimonio"),
    (6, "Gastos por Naturaleza"),
    (7, "Ingresos por Naturaleza"),
    (8, "Saldos Intermediarios de Gestion"),
    (9, "Gastos por Categoria"),
]

FUZZY_THRESHOLD = 65
LIMIT = 500

SINONIMOS = {
    "luz": "energia electrica",
    "electricidad": "energia electrica",
    "planilla": "remuneraciones",
    "sueldos": "remuneraciones",
    "salario": "remuneraciones",
    "afp": "administradoras de fondos de pensiones",
    "pension": "administradoras de fondos de pensiones",
    "jubilacion": "pensiones y jubilaciones",
    "gasolina": "combustibles",
    "petroleo": "combustibles",
    "diesel": "combustibles",
    "flete": "transporte",
    "caja chica": "fondos fijos",
    "banco": "cuentas corrientes en instituciones financieras",
    "cliente": "cuentas por cobrar comerciales",
    "clientes": "cuentas por cobrar comerciales",
    "proveedor": "cuentas por pagar comerciales",
    "proveedores": "cuentas por pagar comerciales",
    "detraccion": "fondos sujetos a restriccion",
    "detracciones": "fondos sujetos a restriccion",
    "renta": "impuesto a las ganancias",
    "iva": "impuesto general a las ventas",
    "utilidad": "resultados acumulados",
    "utilidades": "resultados acumulados",
    "celular": "telefono",
    "cts": "compensacion por tiempo de servicios",
    "gratificacion": "gratificaciones por pagar",
    "mercaderia": "mercaderias",
    "deuda": "obligaciones financieras",
    "prestamo": "obligaciones financieras",
}


def normalizar(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.lower()


with open(DATA_FILE, encoding="utf-8") as f:
    CUENTAS = json.load(f)
for c in CUENTAS:
    c["_norm"] = normalizar(c["descripcion"])
CUENTAS.sort(key=lambda c: c["codigo"])


def buscar_cuentas(q, elemento):
    base = CUENTAS
    if elemento:
        base = [c for c in base if str(c["elemento"]) == elemento]

    if not q:
        return base[:LIMIT]

    qn = normalizar(q)
    terminos = [qn]
    if qn in SINONIMOS:
        terminos.append(normalizar(SINONIMOS[qn]))

    exactos = []
    vistos = set()
    for c in base:
        if c["codigo"] in vistos:
            continue
        if any(t in c["_norm"] or t in c["codigo"] for t in terminos):
            exactos.append(c)
            vistos.add(c["codigo"])
    if exactos or len(qn) < 3:
        return exactos[:LIMIT]

    puntuados = ((fuzz.partial_ratio(qn, c["_norm"]), c) for c in base)
    difusos = sorted(
        (x for x in puntuados if x[0] >= FUZZY_THRESHOLD),
        key=lambda x: -x[0],
    )
    return [c for _, c in difusos][:LIMIT]


def to_json(c):
    return {
        "codigo": c["codigo"],
        "descripcion": c["descripcion"],
        "nivel": c["nivel"],
        "elemento": c["elemento"],
        "elemento_nombre": c["elemento_nombre"],
    }


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    elemento = request.args.get("elemento", "").strip()
    resultados = buscar_cuentas(q, elemento)

    return render_template(
        "index.html",
        resultados=resultados,
        elementos=ELEMENTOS,
        q=q,
        elemento_sel=elemento,
        total=len(resultados),
    )


@app.route("/buscar")
def buscar():
    q = request.args.get("q", "").strip()
    elemento = request.args.get("elemento", "").strip()
    resultados = buscar_cuentas(q, elemento)

    return {
        "total": len(resultados),
        "resultados": [to_json(c) for c in resultados],
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
