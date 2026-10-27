"""Capa de datos: guarda y consulta empleados, ciudades y solicitudes en SQLite.

Esta capa solo almacena y busca. No aplica reglas de negocio: los topes de ciudades.csv se
guardan como datos y el estado de cada solicitud lo decide quien la guarda.
"""
import csv
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import date
from pathlib import Path

RUTA_BD = Path(__file__).parent / "altiplano.db"
CARPETA_CSV = Path(__file__).resolve().parent.parent / "kit7"

TABLAS = """
CREATE TABLE IF NOT EXISTS empleados (
    id_empleado TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    area        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ciudades (
    ciudad         TEXT PRIMARY KEY,
    grupo          TEXT NOT NULL,
    tope_hospedaje INTEGER NOT NULL CHECK (typeof(tope_hospedaje) = 'integer')
);
CREATE TABLE IF NOT EXISTS solicitudes (
    radicado       TEXT PRIMARY KEY,
    fecha_radicado TEXT NOT NULL,
    id_empleado    TEXT NOT NULL REFERENCES empleados (id_empleado),
    ciudad         TEXT NOT NULL,
    fecha_salida   TEXT NOT NULL,
    noches         INTEGER NOT NULL CHECK (typeof(noches) = 'integer'),
    motivo         TEXT NOT NULL,
    valor_noche    INTEGER NOT NULL CHECK (typeof(valor_noche) = 'integer'),
    valor_tiquete  INTEGER NOT NULL CHECK (typeof(valor_tiquete) = 'integer'),
    estado         TEXT NOT NULL
);
"""

# (archivo CSV, tabla, columnas de texto, columnas enteras)
CARGAS = [
    ("empleados.csv", "empleados", ["id_empleado", "nombre", "area"], []),
    ("ciudades.csv", "ciudades", ["ciudad", "grupo"], ["tope_hospedaje"]),
    ("solicitudes_historicas.csv", "solicitudes",
     ["radicado", "fecha_radicado", "id_empleado", "ciudad", "fecha_salida", "motivo", "estado"],
     ["noches", "valor_noche", "valor_tiquete"]),
]


def normalizar(texto):
    """Minúsculas y sin tildes, para comparar nombres sin distinguir mayúsculas ni acentos."""
    sin_tildes = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).casefold().strip()


@contextmanager
def _conexion():
    """Abre la base, confirma los cambios al salir (o los deshace si hubo un error) y la cierra."""
    con = sqlite3.connect(RUTA_BD)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.create_function("normalizar", 1, normalizar, deterministic=True)
    try:
        with con:
            yield con
    finally:
        con.close()


def crear_tablas():
    with _conexion() as con:
        con.executescript(TABLAS)


def cargar_csv():
    """Carga los tres CSV de kit7/. Las filas que ya existen (misma llave primaria) no se
    duplican. Devuelve cuántas filas nuevas entraron en cada tabla."""
    nuevas = {}
    with _conexion() as con:
        for archivo, tabla, textos, enteros in CARGAS:
            columnas = textos + enteros
            with open(CARPETA_CSV / archivo, encoding="utf-8-sig", newline="") as f:
                filas = [[*(fila[c].strip() for c in textos), *(int(fila[c]) for c in enteros)]
                         for fila in csv.DictReader(f)]
            antes = con.total_changes
            con.executemany(
                f"INSERT OR IGNORE INTO {tabla} ({', '.join(columnas)}) "
                f"VALUES ({', '.join('?' * len(columnas))})", filas)
            nuevas[tabla] = con.total_changes - antes
    return nuevas


def inicializar():
    """Crea las tablas y carga los CSV. Se puede llamar las veces que sea necesario."""
    crear_tablas()
    return cargar_csv()


def contar_filas():
    with _conexion() as con:
        return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("empleados", "ciudades", "solicitudes")}


def buscar_empleado(nombre):
    """Empleado cuyo nombre coincide con `nombre` sin distinguir mayúsculas ni tildes, o None."""
    with _conexion() as con:
        fila = con.execute("SELECT * FROM empleados WHERE normalizar(nombre) = ?",
                           (normalizar(nombre),)).fetchone()
    return dict(fila) if fila else None


def buscar_ciudad(nombre):
    """Ciudad (con su grupo y tope de hospedaje) que coincide con `nombre`, o None."""
    with _conexion() as con:
        fila = con.execute("SELECT * FROM ciudades WHERE normalizar(ciudad) = ?",
                           (normalizar(nombre),)).fetchone()
    return dict(fila) if fila else None


def _siguiente_radicado(con):
    mayor = con.execute(
        "SELECT MAX(CAST(SUBSTR(radicado, 3) AS INTEGER)) FROM solicitudes").fetchone()[0]
    return f"S-{(mayor or 100) + 1:03d}"  # sin solicitudes, el primero es S-101


def siguiente_radicado():
    """Radicado que sigue al mayor guardado (S-101, S-102...)."""
    with _conexion() as con:
        return _siguiente_radicado(con)


def guardar_solicitud(id_empleado, ciudad, fecha_salida, noches, motivo,
                      valor_noche, valor_tiquete, estado, fecha_radicado=None):
    """Guarda una solicitud con el estado que le dé quien llama y devuelve su radicado.
    La fecha de radicación es hoy si no se indica. El empleado debe existir."""
    with _conexion() as con:
        radicado = _siguiente_radicado(con)
        con.execute(
            "INSERT INTO solicitudes (radicado, fecha_radicado, id_empleado, ciudad, fecha_salida, "
            "noches, motivo, valor_noche, valor_tiquete, estado) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (radicado, fecha_radicado or date.today().isoformat(), id_empleado, ciudad,
             fecha_salida, int(noches), motivo, int(valor_noche), int(valor_tiquete), estado))
    return radicado


def listar_solicitudes(id_empleado):
    """Solicitudes del empleado, de la más antigua a la más reciente."""
    with _conexion() as con:
        filas = con.execute(
            "SELECT * FROM solicitudes WHERE id_empleado = ? "
            "ORDER BY CAST(SUBSTR(radicado, 3) AS INTEGER)", (id_empleado,)).fetchall()
    return [dict(f) for f in filas]


if __name__ == "__main__":
    nuevas = inicializar()
    print("Filas nuevas:", nuevas)
    print("Filas en la base:", contar_filas())
