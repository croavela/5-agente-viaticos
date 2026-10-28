"""Avisos por Telegram. Es el único lugar que conoce el token y la URL de la API."""
import os

import requests
from dotenv import load_dotenv

ESPERA_MAXIMA = 10  # segundos
LIMITE_TEXTO = 4096  # máximo de caracteres que admite sendMessage


def enviar_aviso(texto):
    """Envía el texto al chat de TELEGRAM_CHAT_ID. Devuelve True si Telegram lo aceptó.
    Nunca lanza errores ni imprime el token o la URL (el token va dentro de la URL): si algo
    falla, imprime una línea corta y devuelve False."""
    try:
        load_dotenv()
        token, chat_id = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            print("[aviso] no enviado: faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en el .env")
            return False
        respuesta = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": str(texto)[:LIMITE_TEXTO]},
            timeout=ESPERA_MAXIMA)
        if respuesta.status_code != 200:
            print(f"[aviso] no enviado: Telegram respondió {respuesta.status_code}")
            return False
        return True
    except Exception as e:  # el texto de la excepción de requests puede incluir la URL con el token
        print(f"[aviso] no enviado: {type(e).__name__}")
        return False
