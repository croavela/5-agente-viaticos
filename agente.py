import sys

from dotenv import load_dotenv
from google import genai

MODELO = "gemini-3.5-flash-lite"
INSTRUCCIONES = "Responde como un cavernicola."

load_dotenv()
client = genai.Client()  # toma GEMINI_API_KEY del entorno

if len(sys.argv) < 2:
    sys.exit('Uso: python agente.py "tu pregunta"')

interaction = client.interactions.create(
    model=MODELO,
    input=" ".join(sys.argv[1:]),
    system_instruction=INSTRUCCIONES,
)
print(interaction.output_text)
