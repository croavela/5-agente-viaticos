import csv
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from bd import basedatos
from logica import solicitudes

MODELO = "gemini-3.5-flash-lite"
BASE = Path(__file__).parent
GASTOS = BASE / "conocimiento" / "gastos.csv"
CARPETA_SKILLS = BASE / ".claude" / "skills"
MAX_VUELTAS = 5
DOCUMENTOS = "\n\n".join(
    f'<documento nombre="{archivo.name}">\n{archivo.read_text(encoding="utf-8")}\n</documento>'
    for archivo in sorted((BASE / "conocimiento").iterdir())
    if archivo.is_file() and archivo.suffix == ".md"
)


def leer_skills():
    """Lee name y description del encabezado de cada .claude/skills/*/SKILL.md.
    Devuelve {name: {"descripcion": ..., "carpeta": ...}}; ignora las que no tengan ambos campos."""
    skills = {}
    for archivo in sorted(CARPETA_SKILLS.glob("*/SKILL.md")):
        partes = archivo.read_text(encoding="utf-8").split("---", 2)
        if len(partes) < 3:
            continue
        campos = dict(linea.split(":", 1) for linea in partes[1].splitlines() if ":" in linea)
        nombre, descripcion = campos.get("name", "").strip(), campos.get("description", "").strip()
        if nombre and descripcion:
            skills[nombre] = {"descripcion": descripcion, "carpeta": archivo.parent}
    return skills


SKILLS = leer_skills()
SECCION_SKILLS = (
    "<skills>\n"
    "Tienes estas skills disponibles:\n"
    + "\n".join(f"- {nombre}: {s['descripcion']}" for nombre, s in SKILLS.items())
    + "\n\nAntes de usar una skill, cárgala con la herramienta cargar_skill y sigue sus "
    "instrucciones; sus scripts se ejecutan con ejecutar_script. Cuando uses una skill, el "
    "formato de esa skill reemplaza al de <formato>.\n"
    "</skills>"
) if SKILLS else ""
INSTRUCCIONES = ((BASE / "prompts" / "sistema.md").read_text(encoding="utf-8") + "\n\n" + DOCUMENTOS
                 + ("\n\n" + SECCION_SKILLS if SECCION_SKILLS else ""))

load_dotenv()
basedatos.inicializar()  # abre la base de bd/ (la crea y carga kit7/ si hace falta)


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


def registrar_solicitud(nombre, ciudad, fecha_salida, noches, motivo, valor_noche, valor_tiquete):
    """Herramienta: la lógica de logica/ valida, asigna el radicado, decide el estado y guarda."""
    return solicitudes.registrar_solicitud(nombre, ciudad, fecha_salida, int(noches), motivo,
                                           int(valor_noche), int(valor_tiquete))


def consultar_mis_solicitudes(nombre):
    """Herramienta: solicitudes ya registradas del empleado."""
    return solicitudes.consultar_solicitudes(nombre)


def buscar_skill(nombre):
    if nombre not in SKILLS:
        raise ValueError(f"No existe la skill '{nombre}'. Disponibles: {', '.join(SKILLS) or 'ninguna'}.")
    return SKILLS[nombre]["carpeta"]


def cargar_skill(nombre):
    carpeta = buscar_skill(nombre)
    print(f"[skill] cargando {nombre} ...")
    return (carpeta / "SKILL.md").read_text(encoding="utf-8")


def ejecutar_script(skill, script, argumento=""):
    scripts = (buscar_skill(skill) / "scripts").resolve()
    ruta = (scripts / script).resolve()
    if scripts not in ruta.parents or ruta.suffix != ".py" or not ruta.is_file():
        raise ValueError(f"Solo puedo ejecutar scripts .py de la carpeta scripts/ de la skill '{skill}'; "
                         f"'{script}' no es uno de ellos.")
    print(f"[script] ejecutando {skill}/{ruta.name} {argumento} ...")
    comando = [sys.executable, str(ruta)] + ([argumento] if argumento else [])
    proceso = subprocess.run(comando, cwd=BASE, capture_output=True, text=True,
                             encoding="utf-8", timeout=60)
    if proceso.returncode != 0:
        raise RuntimeError((proceso.stderr or proceso.stdout).strip() or f"El script terminó con código {proceso.returncode}.")
    return proceso.stdout


FUNCIONES = {"sumar_gastos": sumar_gastos, "registrar_solicitud": registrar_solicitud,
             "consultar_mis_solicitudes": consultar_mis_solicitudes, "cargar_skill": cargar_skill, "ejecutar_script": ejecutar_script}

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
            "Registra una solicitud de viáticos y devuelve su radicado, su estado y el motivo del "
            "estado. Úsala solo cuando el empleado pida registrar una solicitud y ya tengas los "
            "siete datos que él te dio. Si falta alguno, no la llames: pídelo. El estado lo decide "
            "la herramienta, no tú."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre completo del empleado."},
                "ciudad": {"type": "string", "description": "Ciudad de destino."},
                "fecha_salida": {"type": "string", "description": "Fecha de salida en formato AAAA-MM-DD."},
                "noches": {"type": "integer", "description": "Número de noches del viaje."},
                "motivo": {"type": "string", "description": "Motivo del viaje."},
                "valor_noche": {"type": "integer", "description": "Valor por noche del hotel cotizado, en pesos colombianos."},
                "valor_tiquete": {"type": "integer", "description": "Valor del tiquete, en pesos colombianos."},
            },
            "required": ["nombre", "ciudad", "fecha_salida", "noches", "motivo", "valor_noche", "valor_tiquete"],
        },
    },
    {
        "type": "function",
        "name": "consultar_mis_solicitudes",
        "description": (
            "Devuelve las solicitudes de viáticos ya registradas de un empleado (radicado, fechas, "
            "ciudad, noches, valores y estado). Úsala cuando pregunten por sus solicitudes, por el "
            "estado de una solicitud o por su historial de viajes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre completo del empleado."},
            },
            "required": ["nombre"],
        },
    },
    {
        "type": "function",
        "name": "cargar_skill",
        "description": (
            "Devuelve el contenido de SKILL.md de una skill de la lista de <skills>. Llámala antes "
            "de usar esa skill y sigue sus instrucciones."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre de la skill, por ejemplo revisar-gastos."},
            },
            "required": ["nombre"],
        },
    },
    {
        "type": "function",
        "name": "ejecutar_script",
        "description": (
            "Ejecuta con Python un script de la carpeta scripts/ de una skill y devuelve lo que "
            "imprime. Úsala solo cuando las instrucciones de la skill (cargar_skill) lo pidan. "
            "Solo ejecuta scripts de esa carpeta."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "skill": {"type": "string", "description": "Nombre de la skill, por ejemplo revisar-gastos."},
                "script": {"type": "string", "description": "Nombre del archivo dentro de scripts/, por ejemplo validar.py."},
                "argumento": {"type": "string", "description": "Argumento del script, por ejemplo la ruta de un CSV como datos/legalizacion_L-2031.csv. Omítelo si no lleva."},
            },
            "required": ["skill", "script"],
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
    vista = str(resultado)
    print(f"[herramienta] {llamada.name}({llamada.arguments}) -> {vista if len(vista) <= 300 else vista[:300] + '...'}")
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
