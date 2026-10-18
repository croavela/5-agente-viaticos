# Reporte del lote de legalizaciones

Lote: legalizaciones_octubre.csv (28 de septiembre al 9 de octubre de 2026)

## Resumen

| Decisión | Filas | Total COP |
|---|---|---|
| Aprobadas | 15 | 2.213.900 |
| Rechazadas | 8 | 1.455.501 |
| Por revisar | 7 | 2.122.000 |
| Duplicadas | 2 | - |

## Aprobadas

| Radicado | Fecha | Empleado | Ciudad | Categoría | Valor COP |
|---|---|---|---|---|---|
| L-001 | 2026-09-28 | Daniela Osorio | Cartagena | alimentacion | 68.000 |
| L-002 | 2026-09-28 | Daniela Osorio | Cartagena | transporte_terrestre | 38.000 |
| L-003 | 2026-09-28 | Daniela Osorio | Cartagena | hospedaje | 298.000 |
| L-004 | 2026-09-29 | Felipe Arango | Bogotá | alimentacion | 95.000 |
| L-005 | 2026-09-29 | Felipe Arango | Bogotá | hospedaje | 320.000 |
| L-006 | 2026-09-30 | Felipe Arango | Bogotá | transporte_terrestre | 27.500 |
| L-008 | 2026-09-30 | Marcela Pineda | Barranquilla | hospedaje | 240.000 |
| L-011 | 2026-10-01 | Jorge Cárdenas | Cartagena | alimentacion | 72.000 |
| L-013 | 2026-10-02 | Carolina Bernal | Barranquilla | transporte_terrestre | 60.000 |
| L-014 | 2026-10-02 | Carolina Bernal | Barranquilla | alimentacion | 88.000 |
| L-017 | 2026-10-05 | Natalia Guzmán | Medellín | tiquetes_aereos | 412.000 |
| L-019 | 2026-10-06 | Natalia Guzmán | Medellín | transporte_terrestre | 22.000 |
| L-022 | 2026-10-06 | Andrés Quintero | Bucaramanga | hospedaje | 224.000 |
| L-025 | 2026-10-07 | Juliana Peña | Medellín | transporte_terrestre | 14.400 |
| L-030 | 2026-10-08 | Ricardo Nieto | Pereira | hospedaje | 235.000 |

## Rechazadas

| Radicado | Fecha | Empleado | Ciudad | Categoría | Valor COP | Motivo |
|---|---|---|---|---|---|---|
| L-007 | 2026-09-30 | Marcela Pineda | Barranquilla | alimentacion | 95.001 | Supera el tope de Barranquilla para alimentacion ($95.000 COP) |
| L-009 | 2026-10-01 | Jorge Cárdenas | Cartagena | hospedaje | 385.000 | Supera el tope de Cartagena para hospedaje ($320.000 COP) |
| L-010 | 2026-10-01 | Jorge Cárdenas | Cartagena | no_reembolsable | 64.000 | Gasto no reembolsable |
| L-012 | 2026-10-02 | Carolina Bernal | Barranquilla | hospedaje | 290.000 | Supera el tope de Barranquilla para hospedaje ($240.000 COP) |
| L-015 | 2026-10-05 | Paola Rincón | Bucaramanga | no_reembolsable | 234.000 | Gasto no reembolsable |
| L-018 | 2026-10-05 | Natalia Guzmán | Medellín | alimentacion | 180.000 | Supera el tope de Medellín para alimentacion ($95.000 COP) |
| L-029 | 2026-10-08 | Iván Salcedo | Cali | alimentacion | 132.500 | Supera el tope de Cali para alimentacion ($95.000 COP) |
| L-031 | 2026-10-08 | Juliana Peña | Medellín | transporte_terrestre | 75.000 | Supera el tope de Medellín para transporte_terrestre ($60.000 COP) |

## Por revisar

| Radicado | Fecha | Empleado | Ciudad | Categoría | Valor COP | Motivo |
|---|---|---|---|---|---|---|
| L-016 | 2026-10-05 | Paola Rincón | Bucaramanga | tiquetes_aereos | 1.640.000 | Mayor a $1.500.000 COP: requiere aprobación del director del área |
| L-020 | 2026-10-06 | Sandra Beltrán | Miami | alimentacion | 210.000 | Dato no válido: la ciudad no está en topes_por_ciudad.csv |
| L-021 | 2026-10-02 | Ricardo Nieto | Pereira | otro | 45.000 | Categoría 'otro': una persona debe revisarla |
| L-024 | 2026-10-07 | Andrés Quintero | Bucaramanga | otro | 110.000 | Categoría 'otro': una persona debe revisarla |
| L-026 | 2026-01-10 | Sandra Beltrán | Bogotá | alimentacion | 56.000 | Dato no válido: la fecha está fuera del periodo del lote (28 sep a 9 oct de 2026) |
| L-027 | 31/09/2026 (no válida) | Óscar Villamil | Pereira | alimentacion | 61.000 | Dato no válido: la fecha no existe o no se pudo leer |
| L-028 | 2026-10-07 | Iván Salcedo | Cali | hospedaje | sin valor | Dato no válido: falta el valor |

## Duplicadas

| Radicado | Empleado | Valor COP | Repite a |
|---|---|---|---|
| L-023 | Andrés Quintero | 224.000 | L-022 |
| L-006 | Felipe Arango | 27.500 | L-006 (misma fila repetida) |

## Mensajes

**Marcela Pineda:** Hola Marcela, te informamos que tu legalización con radicado L-007 fue rechazada. El motivo es que supera el tope de Barranquilla para alimentacion ($95.000 COP).

**Jorge Cárdenas:** Hola Jorge, te informamos que tus legalizaciones con radicado L-009 y L-010 fueron rechazadas. Los motivos son: Supera el tope de Cartagena para hospedaje ($320.000 COP) y Gasto no reembolsable, respectivamente.

**Carolina Bernal:** Hola Carolina, te informamos que tu legalización con radicado L-012 fue rechazada. El motivo es que supera el tope de Barranquilla para hospedaje ($240.000 COP).

**Paola Rincón:** Hola Paola, te informamos que tu legalización con radicado L-015 fue rechazada. El motivo es Gasto no reembolsable.

**Natalia Guzmán:** Hola Natalia, te informamos que tu legalización con radicado L-018 fue rechazada. El motivo es que supera el tope de Medellín para alimentacion ($95.000 COP).

**Iván Salcedo:** Hola Iván, te informamos que tu legalización con radicado L-029 fue rechazada. El motivo es que supera el tope de Cali para alimentacion ($95.000 COP).

**Juliana Peña:** Hola Juliana, te informamos que tu legalización con radicado L-031 fue rechazada. El motivo es que supera el tope de Medellín para transporte_terrestre ($60.000 COP).
