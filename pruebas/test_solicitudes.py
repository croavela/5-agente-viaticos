from datetime import date

import pytest

from bd import basedatos
from logica import solicitudes
from logica.solicitudes import (APROBADA, PENDIENTE_DIRECTOR, PENDIENTE_JEFE, POR_REVISAR,
                                RECHAZADA, EmpleadoNoEncontrado, validar_solicitud)

# (ciudad, noches, valor_noche, valor_tiquete, estado esperado). Las reglas se revisan en orden:
# 1 ciudad sin tope -> Por revisar; 2 hotel > tope -> Rechazada; 3 tiquete > 1.500.000 -> Pendiente
# de director; 4 lo demás -> Aprobada. "Más de" es estricto: un valor igual al límite cumple.
CASOS = [
    # C1: tope de Medellín 320.000; el hotel es igual al tope (cumple) y el tiquete no pasa de 1.500.000.
    pytest.param("Medellín", 2, 320_000, 1_360_000, APROBADA, id="C1"),
    # C2: tope de Bucaramanga 240.000; el hotel de 262.000 lo supera. La regla 2 decide.
    pytest.param("Bucaramanga", 3, 262_000, 390_000, RECHAZADA, id="C2"),
    # C3: tope de Cartagena 320.000; hotel 300.000 dentro del tope y tiquete exactamente en 1.500.000
    # (igual al límite, no "más de").
    pytest.param("Cartagena", 1, 300_000, 1_500_000, APROBADA, id="C3"),
    # C4: tope de Bogotá 320.000; hotel 250.000 dentro del tope, pero el tiquete de 1.620.000 supera
    # 1.500.000 y necesita al director.
    pytest.param("Bogotá", 2, 250_000, 1_620_000, PENDIENTE_DIRECTOR, id="C4"),
    # C5: Miami no está en ciudades.csv. La regla 1 decide primero, aunque el tiquete también pase de 1.500.000.
    pytest.param("Miami", 3, 280_000, 2_100_000, POR_REVISAR, id="C5"),
    # C6: tope de Barranquilla 240.000; hotel igual al tope (cumple) y tiquete de 1.100.000. Aunque el
    # costo estimado (1.100.000 + 4 x 240.000 = 2.060.000) pase de 1.500.000, la regla 3 mira solo el tiquete.
    pytest.param("Barranquilla", 4, 240_000, 1_100_000, APROBADA, id="C6"),
]


@pytest.fixture
def base(tmp_path, monkeypatch):
    """Base temporal con los CSV de kit7/, para no tocar bd/altiplano.db."""
    monkeypatch.setattr(basedatos, "RUTA_BD", tmp_path / "prueba.db")
    basedatos.inicializar()


@pytest.mark.parametrize("ciudad, noches, valor_noche, valor_tiquete, esperado", CASOS)
def test_validar_solicitud(base, ciudad, noches, valor_noche, valor_tiquete, esperado):
    registro = basedatos.buscar_ciudad(ciudad)
    tope = registro["tope_hospedaje"] if registro else None
    estado, motivo = validar_solicitud(tope, noches, valor_noche, valor_tiquete)
    assert estado == esperado
    assert motivo


@pytest.mark.parametrize("ciudad, noches, valor_noche, valor_tiquete, esperado", CASOS)
def test_registrar_solicitud_guarda_el_estado(base, ciudad, noches, valor_noche, valor_tiquete, esperado):
    resultado = solicitudes.registrar_solicitud(
        "natalia guzman", ciudad, "2026-11-03", noches, "Prueba", valor_noche, valor_tiquete)
    assert resultado["estado"] == esperado
    guardada = solicitudes.consultar_solicitudes("Natalia Guzmán")[-1]
    assert guardada["radicado"] == resultado["radicado"]
    assert guardada["estado"] == esperado


def test_los_radicados_son_consecutivos(base):
    primero = solicitudes.registrar_solicitud("Natalia Guzmán", "Cali", "2026-11-03", 1, "x", 100_000, 0)
    segundo = solicitudes.registrar_solicitud("Natalia Guzmán", "Cali", "2026-11-04", 1, "x", 100_000, 0)
    assert (primero["radicado"], segundo["radicado"]) == ("S-141", "S-142")


def test_empleado_inexistente_no_guarda_nada(base):
    antes = basedatos.contar_filas()["solicitudes"]
    with pytest.raises(EmpleadoNoEncontrado, match="Nadie Conocido"):
        solicitudes.registrar_solicitud("Nadie Conocido", "Cali", "2026-11-03", 1, "x", 100_000, 0)
    assert basedatos.contar_filas()["solicitudes"] == antes


def test_consultar_solicitudes_ignora_mayusculas_y_tildes(base):
    assert [s["radicado"] for s in solicitudes.consultar_solicitudes("JULIANA PENA")] == [
        "S-105", "S-120", "S-135"]


# Regla nueva: desde el 1 de noviembre de 2026, un costo estimado (tiquete + noches x valor por noche)
# de más de 2.000.000 requiere al jefe inmediato. Si ya requiere al director, sigue con el director.
ANTES, DESDE = date(2026, 10, 31), date(2026, 11, 1)


@pytest.mark.parametrize("ciudad, noches, valor_noche, valor_tiquete, fecha, esperado", [
    # C6: costo 1.100.000 + 4 x 240.000 = 2.060.000. Antes de la vigencia se aprueba; desde ella pide al jefe.
    pytest.param("Barranquilla", 4, 240_000, 1_100_000, ANTES, APROBADA, id="C6-antes"),
    pytest.param("Barranquilla", 4, 240_000, 1_100_000, DESDE, PENDIENTE_JEFE, id="C6-desde"),
    # C1: costo 1.360.000 + 2 x 320.000 = 2.000.000, igual al límite (no "más de"): se aprueba.
    pytest.param("Medellín", 2, 320_000, 1_360_000, DESDE, APROBADA, id="C1-justo-en-el-limite"),
    # C4: costo 2.120.000, pero el tiquete ya pide al director y sigue con el director.
    pytest.param("Bogotá", 2, 250_000, 1_620_000, DESDE, PENDIENTE_DIRECTOR, id="C4-sigue-con-director"),
    # C2 y C5 se deciden antes (hotel sobre el tope; ciudad sin tope).
    pytest.param("Bucaramanga", 3, 262_000, 390_000, DESDE, RECHAZADA, id="C2-rechazada-primero"),
    pytest.param("Miami", 3, 280_000, 2_100_000, DESDE, POR_REVISAR, id="C5-por-revisar-primero"),
])
def test_regla_nueva_costo_mayor_a_dos_millones(base, ciudad, noches, valor_noche, valor_tiquete, fecha, esperado):
    registro = basedatos.buscar_ciudad(ciudad)
    tope = registro["tope_hospedaje"] if registro else None
    assert validar_solicitud(tope, noches, valor_noche, valor_tiquete, fecha)[0] == esperado


def test_registrar_solicitud_con_fecha_de_radicacion(base):
    resultado = solicitudes.registrar_solicitud(
        "Natalia Guzmán", "Barranquilla", "2026-11-10", 4, "Prueba", 240_000, 1_100_000,
        fecha_radicado="2026-11-01")
    assert resultado["estado"] == PENDIENTE_JEFE
    guardada = solicitudes.consultar_solicitudes("Natalia Guzmán")[-1]
    assert (guardada["estado"], guardada["fecha_radicado"]) == (PENDIENTE_JEFE, "2026-11-01")
