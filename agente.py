import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai

MODELO = "gemini-3.5-flash-lite"
INSTRUCCIONES = (Path(__file__).parent / "prompts" / "sistema.md").read_text(encoding="utf-8")

load_dotenv()


def preguntar(pregunta, interaccion_previa=None):
    """Envía la pregunta al modelo. Con interaccion_previa continúa esa conversación."""
    client = genai.Client()  # toma GEMINI_API_KEY del entorno
    datos = {"model": MODELO, "input": pregunta, "system_instruction": INSTRUCCIONES}
    if interaccion_previa:
        datos["previous_interaction_id"] = interaccion_previa
    return client.interactions.create(**datos)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('Uso: python agente.py "tu pregunta"')
    print(preguntar(" ".join(sys.argv[1:])).output_text)
