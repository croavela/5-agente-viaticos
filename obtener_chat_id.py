import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_TOKEN")
if not token:
    sys.exit("Falta TELEGRAM_TOKEN en el archivo .env")

try:
    # El token va en la URL, así que no se imprime la URL ni el texto de la excepción.
    respuesta = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30)
except requests.RequestException as e:
    sys.exit(f"No se pudo conectar con Telegram ({type(e).__name__}).")

datos = respuesta.json() if respuesta.headers.get("content-type", "").startswith("application/json") else {}
if not datos.get("ok"):
    sys.exit(f"Telegram respondió con error {respuesta.status_code}: {datos.get('description', 'sin detalle')}")

personas = {}
for actualizacion in datos["result"]:
    mensaje = actualizacion.get("message") or actualizacion.get("edited_message") or {}
    chat = mensaje.get("chat")
    if chat:
        nombre = " ".join(filter(None, [chat.get("first_name"), chat.get("last_name")])) or chat.get("title") or chat.get("username") or "(sin nombre)"
        personas[chat["id"]] = nombre

if not personas:
    print("La lista de mensajes está vacía: nadie le ha escrito al bot todavía. Escríbele algo al bot en Telegram y vuelve a ejecutar.")
for chat_id, nombre in personas.items():
    print(f"{nombre}: chat_id = {chat_id}")
