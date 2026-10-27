from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from bd import basedatos
from logica import solicitudes


@asynccontextmanager
async def ciclo_de_vida(app):
    basedatos.inicializar()  # abre la base de bd/ (la crea y carga kit7/ si hace falta)
    yield


app = FastAPI(title="Viáticos Altiplano", lifespan=ciclo_de_vida)


class SolicitudNueva(BaseModel):
    nombre: str = Field(description="Nombre completo del empleado.")
    ciudad: str = Field(description="Ciudad de destino.")
    fecha_salida: date = Field(description="Fecha de salida (AAAA-MM-DD).")
    noches: int = Field(ge=0, description="Número de noches del viaje.")
    motivo: str = Field(description="Motivo del viaje.")
    valor_noche: int = Field(ge=0, description="Valor por noche del hotel cotizado, en COP.")
    valor_tiquete: int = Field(ge=0, description="Valor del tiquete, en COP.")

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "nombre": "Natalia Guzmán",
        "ciudad": "Medellín",
        "fecha_salida": "2026-11-17",
        "noches": 1,
        "motivo": "Auditoría de bodega",
        "valor_noche": 280000,
        "valor_tiquete": 450000,
    }]})


class SolicitudRegistrada(BaseModel):
    radicado: str
    estado: str
    motivo: str


class SolicitudGuardada(BaseModel):
    radicado: str
    fecha_radicado: str
    id_empleado: str
    ciudad: str
    fecha_salida: str
    noches: int
    motivo: str
    valor_noche: int
    valor_tiquete: int
    estado: str


@app.get("/solicitudes", response_model=list[SolicitudGuardada])
def listar_solicitudes(empleado: str):
    """Solicitudes de un empleado, de la más antigua a la más reciente."""
    try:
        return solicitudes.consultar_solicitudes(empleado)
    except solicitudes.EmpleadoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.post("/solicitudes", response_model=SolicitudRegistrada)
def crear_solicitud(solicitud: SolicitudNueva):
    """Registra una solicitud. El estado y su motivo los decide la lógica, no quien llama."""
    try:
        return solicitudes.registrar_solicitud(
            solicitud.nombre, solicitud.ciudad, solicitud.fecha_salida.isoformat(),
            solicitud.noches, solicitud.motivo, solicitud.valor_noche, solicitud.valor_tiquete)
    except solicitudes.EmpleadoNoEncontrado as error:
        raise HTTPException(status_code=404, detail=str(error))
