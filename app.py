import streamlit as st

from agente import preguntar

st.set_page_config(page_title="Agente de viáticos", page_icon="💬")
st.title("💬 Agente de viáticos")
st.caption("Pregunta lo que necesites sobre tus viáticos.")

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

if pregunta := st.chat_input("Escribe tu pregunta..."):
    st.session_state.mensajes.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Pensando..."):
                interaccion = preguntar(pregunta, st.session_state.interaccion_id)
            st.session_state.interaccion_id = interaccion.id
            respuesta = interaccion.output_text
            st.markdown(respuesta)
        except Exception as error:
            respuesta = f"⚠️ No pude responder: {error}"
            st.error(respuesta)
    st.session_state.mensajes.append({"rol": "assistant", "texto": respuesta})
