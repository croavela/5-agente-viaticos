import csv
import json
import sys
import unicodedata
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google import genai

MODELO = "gemini-3.5-flash-lite"
BASE = Path(__file__).parent
GASTOS = BASE / "conocimiento" / "gastos.csv"
SOLICITUDES = BASE / "solicitudes.csv"
MAX_VUELTAS = 5
DOCUMENTOS = "\n\n".join(
    f'<documento nombre="{archivo.name}">\n{archivo.read_text(encoding="utf-8")}\n</documento>'
    for archivo in sorted((BASE / "conocimiento").iterdir())
    if archivo.is_file() and archivo.suffix == ".md"
)
INSTRUCCIONES = (BASE / "prompts" / "sistema.md").read_text(encoding="utf-8") + "\n\n" + DOCUMENTOS

load_dotenv()


def normalizar(texto):
    """Minúsculas y sin tildes, para comparar sin distinguir mayúsculas ni acentos."""
    sin_tildes = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).casefold().strip()


def sumar_gastos(area=None, estado=None):
    with open(GASTOS, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    if area:
        filas = [r for r in filas if normalizar(r["area"]) == normalizar(area)]
    if estado:
        filas = [r for r in filas if normalizar(r["estado"]) == normalizar(estado)]
    return {"filas": len(filas), "total_cop": sum(int(r["valor_cop"]) for r in filas)}


def registrar_solicitud(empleado, ciudad, fecha_salida, noches, motivo):
    existe = SOLICITUDES.exists()
    radicado = "S-001"
    if existe:
        with open(SOLICITUDES, encoding="utf-8", newline="") as f:
            radicado = f"S-{sum(1 for _ in csv.DictReader(f)) + 1:03d}"
    with open(SOLICITUDES, "a", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        if not existe:
            escritor.writerow(["radicado", "fecha_registro", "empleado", "ciudad",
                               "fecha_salida", "noches", "motivo", "estado"])
        escritor.writerow([radicado, date.today().isoformat(), empleado, ciudad,
                           fecha_salida, int(noches), motivo,
                           "Pendiente de aprobación del jefe inmediato"])
    return {"radicado": radicado}


FUNCIONES = {"sumar_gastos": sumar_gastos, "registrar_solicitud": registrar_solicitud}

HERRAMIENTAS = [
    {
        "type": "function",
        "name": "sumar_gastos",
        "description": (
            "Cuenta y suma, en pesos colombianos (COP), los gastos registrados en gastos.csv. "
            "Úsala siempre que pregunten cuánto suman, cuántos son o cuál es el total de gastos, "
            "opcionalmente de un área o con un estado. No la uses para consultar topes o reglas "
            "de la política."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "area": {"type": "string", "description": "Área a filtrar, por ejemplo Ventas. Omítelo para incluir todas."},
                "estado": {"type": "string", "description": "Estado a filtrar, por ejemplo Aprobado. Omítelo para incluir todos."},
            },
        },
    },
    {
        "type": "function",
        "name": "registrar_solicitud",
        "description": (
            "Registra una solicitud de viáticos y devuelve su radicado. Úsala solo cuando el "
            "empleado pida registrar una solicitud y ya tengas los cinco datos que él te dio. "
            "Si falta alguno, no la llames: pídelo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "empleado": {"type": "string", "description": "Nombre completo del empleado."},
                "ciudad": {"type": "string", "description": "Ciudad de destino."},
                "fecha_salida": {"type": "string", "description": "Fecha de salida en formato AAAA-MM-DD."},
                "noches": {"type": "integer", "description": "Número de noches del viaje."},
                "motivo": {"type": "string", "description": "Motivo del viaje."},
            },
            "required": ["empleado", "ciudad", "fecha_salida", "noches", "motivo"],
        },
    },
]


def ejecutar_herramienta(llamada):
    """Ejecuta la herramienta pedida por el modelo y devuelve el resultado listo para enviarle."""
    try:
        resultado = FUNCIONES[llamada.name](**llamada.arguments)
        error = False
    except Exception as e:
        resultado, error = {"error": str(e)}, True
    print(f"[herramienta] {llamada.name}({llamada.arguments}) -> {resultado}")
    paso = {"type": "function_result", "call_id": llamada.id, "name": llamada.name,
            "result": json.dumps(resultado, ensure_ascii=False)}
    if error:
        paso["is_error"] = True
    return paso


def preguntar(pregunta, interaccion_previa=None):
    """Envía la pregunta al modelo y atiende sus herramientas hasta que responda con texto.
    Con interaccion_previa continúa esa conversación."""
    client = genai.Client()  # toma GEMINI_API_KEY del entorno
    entrada, previa = pregunta, interaccion_previa
    for _ in range(MAX_VUELTAS):
        datos = {"model": MODELO, "input": entrada, "system_instruction": INSTRUCCIONES,
                 "tools": HERRAMIENTAS}
        if previa:
            datos["previous_interaction_id"] = previa
        interaccion = client.interactions.create(**datos)
        llamadas = [p for p in interaccion.steps or [] if p.type == "function_call"]
        if not llamadas:
            return interaccion
        entrada = [ejecutar_herramienta(llamada) for llamada in llamadas]
        previa = interaccion.id
    raise RuntimeError(f"El modelo siguió pidiendo herramientas tras {MAX_VUELTAS} vueltas.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('Uso: python agente.py "tu pregunta"')
    print(preguntar(" ".join(sys.argv[1:])).output_text)
