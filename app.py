import html
import sys
from contextlib import redirect_stderr, redirect_stdout

import streamlit as st

from agente import preguntar


class Duplicar:
    """Escribe en la consola original y guarda el texto para mostrarlo debajo de la respuesta."""

    def __init__(self, original, registro):
        self.original, self.registro = original, registro

    def write(self, texto):
        self.registro.append(texto)
        return self.original.write(texto)

    def __getattr__(self, nombre):
        return getattr(self.original, nombre)


def mostrar_consola(texto):
    st.markdown(
        '<pre style="font-family:Consolas,\'Lucida Console\',monospace;font-size:0.8rem;'
        'color:#ffffff;background:#000000;padding:0.6rem 0.8rem;border-radius:4px;margin:0;'
        f'white-space:pre-wrap;text-align:left">{html.escape(texto)}</pre>',
        unsafe_allow_html=True,
    )

st.set_page_config(page_title="Agente de viáticos", page_icon="💬")
st.title("💬 Agente de viáticos")
st.caption("Pregunta lo que necesites sobre tus viáticos.")

# Tus mensajes a la derecha (con el avatar a ese lado); las respuestas quedan a la izquierda.
st.markdown(
    """
    <style>
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
    st.session_state.interaccion_id = None

with st.sidebar:
    if st.button("Nueva conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.session_state.interaccion_id = None
        st.rerun()

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["texto"])
        if mensaje.get("consola"):
            mostrar_consola(mensaje["consola"])

if pregunta := st.chat_input("Escribe tu pregunta..."):
    st.session_state.mensajes.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    registro = []
    with st.chat_message("assistant"):
        try:
            with (
                st.spinner("Pensando..."),
                redirect_stdout(Duplicar(sys.stdout, registro)),
                redirect_stderr(Duplicar(sys.stderr, registro)),
            ):
                interaccion = preguntar(pregunta, st.session_state.interaccion_id)
            st.session_state.interaccion_id = interaccion.id
            respuesta = interaccion.output_text
            st.markdown(respuesta)
        except Exception as error:
            respuesta = f"⚠️ No pude responder: {error}"
            st.error(respuesta)
        consola = "".join(registro).strip()
        if consola:
            mostrar_consola(consola)
    st.session_state.mensajes.append({"rol": "assistant", "texto": respuesta, "consola": consola})
