"""Revisa una legalización de gastos de viaje contra la política de viáticos.

Uso: python validar.py <ruta del CSV de la legalización>

Los topes y plazos salen de referencia/politica_viaticos.md (versión 2.0). El informe se
arma llenando plantilla_informe.md. Veredicto de cada gasto, en este orden:
  1. Rechazado: es un gasto no reembolsable (sección 6) o supera un tope (secciones 2 y 4).
  2. Devuelto: falta un dato o no es válido, no trae la factura que exige la sección 5 o
     necesita la aprobación del director (sección 3).
  3. Aprobado: ninguna de las anteriores.
Un valor igual al tope está dentro del tope. Los gastos rechazados y devueltos no suman.
"""
import csv
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

PLANTILLA = Path(__file__).resolve().parent.parent / "plantilla_informe.md"
COLUMNAS = ["legalizacion", "empleado", "ciudad", "salida", "regreso", "id", "fecha",
            "categoria", "descripcion", "factura", "valor_cop"]

# Valores de la política (sección 2: topes, sección 3: aprobaciones, sección 5: facturas)
GRUPO_A = {"bogota", "medellin", "cartagena"}
TOPE_HOSPEDAJE_NOCHE = {"A": 320_000, "B": 240_000}
TOPE_DIA = {"alimentacion": 95_000, "transporte terrestre": 60_000}
LIMITE_SIN_FACTURA = 30_000
LIMITE_DIRECTOR = 1_500_000
CATEGORIAS = {"alimentacion", "hospedaje", "transporte terrestre", "tiquetes aereos", "otros"}

# Gastos no reembolsables (sección 6), detectados por la descripción
NO_REEMBOLSABLES = [
    (r"\bminibar\b", "Minibar"),
    (r"\bpropinas?\b", "Propina"),
    (r"\b(multas?|comparendos?)\b", "Multa de tránsito"),
    (r"\b(alcohol\w*|licor\w*|cervezas?|vinos?|aguardiente|whisky|coctel\w*|tragos?)\b",
     "Bebida alcohólica"),
    (r"\b(cine|conciertos?|tours?|entretenimiento)\b", "Entretenimiento personal"),
    (r"\bacompanantes?\b", "Gasto de acompañante"),
]


def normalizar(texto):
    """Minúsculas y sin tildes, para comparar sin distinguir mayúsculas ni acentos."""
    sin_tildes = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).casefold().strip()


def pesos(valor):
    return f"${valor:,}".replace(",", ".") + " COP"


def leer_fecha(texto):
    try:
        return date.fromisoformat(texto.strip())
    except ValueError:
        return None


def leer_valor(texto):
    texto = texto.strip()
    return int(texto) if re.fullmatch(r"\d+", texto) and int(texto) > 0 else None


def motivo_no_reembolsable(descripcion, noches):
    texto = normalizar(descripcion)
    for patron, nombre in NO_REEMBOLSABLES:
        if re.search(patron, texto):
            return f"{nombre} es un gasto no reembolsable (sección 6)."
    if re.search(r"\blavanderia\b", texto) and noches < 5:
        return "Lavandería en un viaje de menos de 5 noches no es reembolsable (sección 6)."
    return None


def evaluar(gastos, grupo, noches):
    """Devuelve (veredicto, motivo) por gasto, en el orden del archivo."""
    acumulado = {}  # (fecha, categoría) -> suma de lo que ya cuenta contra el tope diario
    resultados = []
    for g in gastos:
        categoria = normalizar(g["categoria"])
        fecha, valor = leer_fecha(g["fecha"]), leer_valor(g["valor_cop"])

        motivo = motivo_no_reembolsable(g["descripcion"], noches)
        if motivo:
            resultados.append(("Rechazado", motivo))
            continue

        faltan = [nombre for nombre, ok in (("la fecha", fecha), ("el valor", valor),
                                            ("la categoría", categoria in CATEGORIAS)) if not ok]
        if faltan:
            resultados.append(("Devuelto", f"Falta o no es válido: {', '.join(faltan)}."))
            continue

        if categoria == "hospedaje" and valor > TOPE_HOSPEDAJE_NOCHE[grupo]:
            resultados.append(("Rechazado", f"Supera el tope de {pesos(TOPE_HOSPEDAJE_NOCHE[grupo])} "
                               f"por noche del Grupo {grupo}; se rechaza completo (secciones 2 y 4)."))
            continue
        if categoria in TOPE_DIA:
            total_dia = acumulado.get((fecha, categoria), 0) + valor
            if total_dia > TOPE_DIA[categoria]:
                resultados.append(("Rechazado", f"Con este gasto el total del día en {g['categoria']} "
                                   f"({pesos(total_dia)}) supera el tope de {pesos(TOPE_DIA[categoria])} "
                                   "por día; se rechaza completo (secciones 2 y 4)."))
                continue
            acumulado[(fecha, categoria)] = total_dia

        if valor > LIMITE_SIN_FACTURA and not g["factura"].strip():
            resultados.append(("Devuelto", f"Falta la factura: todo gasto mayor a "
                               f"{pesos(LIMITE_SIN_FACTURA)} la requiere (sección 5)."))
        elif valor > LIMITE_DIRECTOR:
            resultados.append(("Devuelto", f"Supera {pesos(LIMITE_DIRECTOR)} y requiere la aprobación "
                               "del director del área, que el archivo no trae (sección 3)."))
        else:
            resultados.append(("Aprobado", ""))
    return resultados


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        sys.exit("Uso: python validar.py <ruta del CSV de la legalización>")
    try:
        with open(sys.argv[1], encoding="utf-8-sig", newline="") as f:
            lector = csv.DictReader(f)
            faltantes = [c for c in COLUMNAS if c not in (lector.fieldnames or [])]
            gastos = list(lector)
    except OSError as e:
        sys.exit(f"Error: no pude abrir el archivo ({e}).")
    if faltantes:
        sys.exit(f"Error: al archivo le faltan las columnas {', '.join(faltantes)}.")
    if not gastos:
        sys.exit("Error: el archivo no tiene gastos.")

    for campo in ("legalizacion", "empleado", "ciudad", "salida", "regreso"):
        valores = {g[campo].strip() for g in gastos}
        if len(valores) > 1:
            sys.exit(f"Error: el archivo mezcla varios valores en '{campo}': {sorted(valores)}.")
    cabecera = gastos[0]
    salida, regreso = leer_fecha(cabecera["salida"]), leer_fecha(cabecera["regreso"])
    if not salida or not regreso or regreso < salida:
        sys.exit("Error: las fechas de salida y regreso del viaje no son válidas.")
    grupo = "A" if normalizar(cabecera["ciudad"]) in GRUPO_A else "B"

    resultados = evaluar(gastos, grupo, (regreso - salida).days)
    filas, total = [], 0
    for g, (veredicto, motivo) in zip(gastos, resultados):
        valor = leer_valor(g["valor_cop"])
        if veredicto == "Aprobado":
            total += valor
        celdas = [g["id"], g["fecha"], g["categoria"], pesos(valor) if valor else "sin valor",
                  veredicto, motivo]
        filas.append("| " + " | ".join(c.strip().replace("|", "/") for c in celdas) + " |")

    cuenta = [v for v, _ in resultados]
    datos = {
        "legalizacion": cabecera["legalizacion"].strip(), "empleado": cabecera["empleado"].strip(),
        "ciudad": cabecera["ciudad"].strip(), "grupo": grupo, "salida": cabecera["salida"].strip(),
        "regreso": cabecera["regreso"].strip(), "filas": "\n".join(filas),
        "presentados": len(gastos), "aprobados": cuenta.count("Aprobado"),
        "rechazados": cuenta.count("Rechazado"), "devueltos": cuenta.count("Devuelto"),
        "total": pesos(total),
    }
    informe = PLANTILLA.read_text(encoding="utf-8")
    for clave, valor in datos.items():
        informe = informe.replace("{{" + clave + "}}", str(valor))
    print(informe, end="")


if __name__ == "__main__":
    main()
