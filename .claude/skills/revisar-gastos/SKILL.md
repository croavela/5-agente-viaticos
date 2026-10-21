---
name: revisar-gastos
description: Revisa una legalización de gastos de viaje (un CSV como datos/legalizacion_L-2031.csv) contra la política de viáticos y entrega un informe con el veredicto de cada gasto y el total a reembolsar. Úsala cuando pidan revisar, validar o auditar una legalización, o saber cuánto se le reembolsa a un empleado por un viaje.
---

# Revisar una legalización de gastos

1. Si no te dicen qué archivo revisar, pregúntalo.
2. Ejecuta el script con la ruta del CSV:

   ```
   python .claude/skills/revisar-gastos/scripts/validar.py <ruta del CSV>
   ```

   El script aplica la política (`referencia/politica_viaticos.md`), decide el veredicto de cada gasto, suma el total y llena `plantilla_informe.md`. Si termina con un error, muéstralo tal cual y no inventes el informe.
3. Muestra el informe completo, tal como lo imprime el script. No cambies cifras, veredictos ni motivos.
4. Debajo del informe agrega **Notas del revisor**: una lista corta con lo que el script no puede juzgar y que aplique a esta legalización. Consulta `referencia/politica_viaticos.md` para redactarlas. Posibles notas:
   - Tiquetes: clase económica, compra por la agencia y 7 días de anticipación (sección 2).
   - Hospedaje: hotel de máximo 4 estrellas (sección 2).
   - Gastos en "Otros" (parqueaderos, peajes, papelería): que estén relacionados con el motivo del viaje (sección 2).
   - Facturas: que sean electrónicas y a nombre de Altiplano S.A.S.; el script solo ve que haya un número (sección 5).
   - Plazo de 5 días hábiles para legalizar: el archivo no trae la fecha de entrega (sección 5).
   - Aprobación previa del jefe inmediato (sección 3) y autorización escrita del director para topes superados (sección 4).
   - Descripciones ambiguas que podrían ser gastos no reembolsables y que el script no detecta por palabras clave (sección 6).
   - Fechas de gastos fuera de las fechas del viaje.
