"""Reglas de kit7/reglas_solicitudes.md. Usa la capa de datos de bd/ para buscar y guardar."""
from datetime import date

from bd import basedatos

LIMITE_TIQUETE_DIRECTOR = 1_500_000  # política, sección 3: "más de" este valor pide al director
LIMITE_COSTO_JEFE = 2_000_000  # nueva política: "más de" este costo estimado pide al jefe inmediato
FECHA_VIGENCIA_JEFE = date(2026, 11, 1)  # la regla nueva aplica a solicitudes radicadas desde este día

APROBADA = "Aprobada"
RECHAZADA = "Rechazada"
POR_REVISAR = "Por revisar"
PENDIENTE_DIRECTOR = "Pendiente de director"
PENDIENTE_JEFE = "Pendiente de jefe inmediato"


class EmpleadoNoEncontrado(ValueError):
    """El nombre no corresponde a ningún empleado de empleados.csv."""


def _pesos(valor):
    return f"${valor:,}".replace(",", ".") + " COP"


def _a_fecha(fecha):
    return date.fromisoformat(fecha) if isinstance(fecha, str) else fecha


def validar_solicitud(tope_hospedaje, noches, valor_noche, valor_tiquete, fecha_radicado=None):
    """Devuelve (estado, motivo). Se revisan las reglas en orden y la primera que se cumple decide.
    tope_hospedaje es None si la ciudad no está en ciudades.csv. fecha_radicado (date o AAAA-MM-DD)
    es el día en que se radica la solicitud; si no se indica, es hoy. No usa archivos ni base de datos."""
    if tope_hospedaje is None:
        return POR_REVISAR, "La ciudad no está en ciudades.csv; una persona debe revisarla (regla 1)."
    if valor_noche > tope_hospedaje:
        return RECHAZADA, (f"El valor por noche ({_pesos(valor_noche)}) supera el tope de hospedaje "
                           f"de la ciudad ({_pesos(tope_hospedaje)}) (regla 2).")
    if valor_tiquete > LIMITE_TIQUETE_DIRECTOR:
        return PENDIENTE_DIRECTOR, (f"El tiquete ({_pesos(valor_tiquete)}) supera "
                                    f"{_pesos(LIMITE_TIQUETE_DIRECTOR)}; requiere la aprobación "
                                    "del director (regla 3).")
    costo = valor_tiquete + noches * valor_noche
    if costo > LIMITE_COSTO_JEFE and _a_fecha(fecha_radicado or date.today()) >= FECHA_VIGENCIA_JEFE:
        return PENDIENTE_JEFE, (f"El costo estimado ({_pesos(costo)}) supera {_pesos(LIMITE_COSTO_JEFE)}; "
                                "requiere la aprobación del jefe inmediato (regla nueva, vigente "
                                "desde el 1 de noviembre de 2026).")
    return APROBADA, f"Cumple las reglas (regla 4). Costo estimado: {_pesos(costo)}."


def _buscar_empleado(nombre):
    empleado = basedatos.buscar_empleado(nombre)
    if empleado is None:
        raise EmpleadoNoEncontrado(
            f"No existe el empleado '{nombre}' en empleados.csv; no se registró ninguna solicitud.")
    return empleado


def registrar_solicitud(nombre_empleado, ciudad, fecha_salida, noches, motivo,
                        valor_noche, valor_tiquete, fecha_radicado=None):
    """Valida la solicitud, le asigna el siguiente radicado y la guarda. La fecha de radicación
    (date o AAAA-MM-DD) es hoy si no se indica; también decide si aplica la regla del jefe inmediato.
    Devuelve {"radicado", "estado", "motivo"}. Si el empleado no existe, lanza EmpleadoNoEncontrado."""
    empleado = _buscar_empleado(nombre_empleado)
    ciudad_registrada = basedatos.buscar_ciudad(ciudad)
    tope = ciudad_registrada["tope_hospedaje"] if ciudad_registrada else None
    fecha_radicado = _a_fecha(fecha_radicado or date.today())
    estado, motivo_estado = validar_solicitud(tope, noches, valor_noche, valor_tiquete, fecha_radicado)
    radicado = basedatos.guardar_solicitud(  # asigna el siguiente radicado al guardar
        empleado["id_empleado"],
        ciudad_registrada["ciudad"] if ciudad_registrada else ciudad.strip(),
        fecha_salida, noches, motivo, valor_noche, valor_tiquete, estado,
        fecha_radicado.isoformat())
    return {"radicado": radicado, "estado": estado, "motivo": motivo_estado}


def consultar_solicitudes(nombre):
    """Solicitudes del empleado, de la más antigua a la más reciente."""
    return basedatos.listar_solicitudes(_buscar_empleado(nombre)["id_empleado"])
