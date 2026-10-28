from types import SimpleNamespace

import pytest

from logica import solicitudes


@pytest.fixture(autouse=True)
def avisos(monkeypatch):
    """En todas las pruebas la lógica usa un aviso falso: guarda los textos en una lista y nunca llama
    a Telegram. Se reemplaza la referencia de logica/, no el módulo externos/, que queda intacto."""
    enviados = []
    falso = SimpleNamespace(enviar_aviso=lambda texto: enviados.append(texto) or True)
    monkeypatch.setattr(solicitudes, "notificaciones", falso)
    return enviados
