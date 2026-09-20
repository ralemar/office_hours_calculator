# PLAN: Herramienta lectora de calendarios ICS

## Objetivo

Leer un fichero `.ics` y, dadas dos fechas (`desde`, `hasta`), devolver los
eventos comprendidos en ese rango con estos datos:

- Nombre del evento
- Fecha
- Hora de inicio
- Hora final
- Duracion (en horas)

El resultado lo consumira un script manual de pruebas y, en el futuro, una
webapp sencilla. Por eso **no hay CLI**: la logica se expone como una funcion
reutilizable.

## Decisiones cerradas

- **Libreria ICS:** `icalendar`, unica dependencia. No hay eventos recurrentes
  (`RRULE`) ni eventos de dia completo, asi que no hacen falta librerias extra.
- **Sin CLI:** se elimino el entrypoint `[project.scripts]` de `pyproject.toml`.
- **Codigo minimo:** sin dataclasses ni capas innecesarias; el evento es un
  `dict` plano.
- **Zonas horarias:** el `.ics` real guarda las horas en UTC (`Z`), aunque el
  calendario sea de Madrid. Se convierten a **`Europe/Madrid`** con
  `ZoneInfo("Europe/Madrid")` antes de filtrar y mostrar. En Windows, `tzdata`
  entra como dependencia de `icalendar`, asi que no se anade nada extra.
- **Sin tests automaticos en esta fase:** la comprobacion se hace con un script
  manual sobre un `.ics` real.

## Renombrado del proyecto

- Nombre de distribucion: **`calendar-reader`**.
- Paquete: **`calendar_reader`** (carpeta `src/calendar_reader/`).
- `pyproject.toml`: `name = "calendar-reader"`, sin `[project.scripts]`,
  descripcion actualizada.
- Lockfile regenerado con `uv lock`.

## Estructura final

```
pyproject.toml
uv.lock
README.md
PLAN.md
src/
└── calendar_reader/
    └── __init__.py              # funcion leer_eventos()
tests/
└── fixtures/
    └── calendario_test.ics      # calendario real de prueba
scripts/
└── probar_calendario.py         # script manual de volcado
```

- `tests/` es la carpeta que busca `pytest`; aqui solo viven datos en
  `tests/fixtures/`. Los futuros test iran como `tests/test_*.py`.
- `scripts/` alberga utilidades de desarrollo que se ejecutan a mano.

## API publica

`src/calendar_reader/__init__.py`

```python
def leer_eventos(ruta, desde, hasta) -> list[dict]:
    ...
```

- `ruta`: `str | Path` al fichero `.ics`.
- `desde`, `hasta`: `datetime.date`.
- Devuelve una lista de `dict`, ordenada por fecha y hora de inicio.

### Esquema de cada evento

| clave | tipo | descripcion |
|---|---|---|
| `nombre` | `str` | `SUMMARY` del evento |
| `fecha` | `datetime.date` | fecha de inicio (en Madrid) |
| `inicio` | `datetime.time` | hora de inicio (en Madrid) |
| `fin` | `datetime.datetime` | fecha y hora finales (en Madrid) |
| `duracion_horas` | `float` | `(fin - inicio)` en horas |

`fin` se devuelve como `datetime` completo para no perder los eventos que
terminan despues de medianoche (p. ej. `Evento test 3`). `inicio` se mantiene
como `time` porque su fecha ya esta en `fecha`.

## Logica de la funcion

1. Abrir el fichero y parsearlo con `icalendar.Calendar.from_ical(...)`.
2. Recorrer los componentes `VEVENT`.
3. Para cada evento extraer `SUMMARY`, `DTSTART` y `DTEND`.
4. Convertir `DTSTART`/`DTEND` a `Europe/Madrid` con `.astimezone(MADRID)`.
5. Filtrar: incluir solo si `desde <= inicio.date() <= hasta`
   (rango inclusivo, de 00:00 del dia inicial a 23:59 del dia final).
   El filtrado se basa en la fecha de inicio, no en el solape.
6. Calcular `duracion_horas = (fin - inicio).total_seconds() / 3600`.
7. Ordenar por `(fecha, inicio)`.
8. Devolver la lista de `dict`.

## Casos limite: como se tratan

- **Falta `DTEND` (y no hay `DURATION`):** se asume `fin = inicio`, es decir,
  duracion `0.0`. Se emite un `warnings.warn(...)` avisando del evento. No se
  interrumpe la ejecucion.
- **`DURATION` en lugar de `DTEND`:** `icalendar` ya lo expone; si aparece, se
  resuelve con `inicio + duration` para obtener `fin`.
- **Falta `SUMMARY`:** se usa cadena vacia `""` como nombre.
- **Eventos sin hora (dia completo):** fuera de alcance por decision explicita;
  no se contemplan.
- **Recurrencias (`RRULE`):** fuera de alcance; solo se lee la primera
  ocurrencia que aparezca en el `VEVENT`.
- **Zonas horarias:** se convierten a `Europe/Madrid` (ver "Decisiones
  cerradas").

## Pasos de implementacion

Ejecutados:

1. **Renombrar** paquete y proyecto; quitar `[project.scripts]`; `uv lock`.
2. **Anadir dependencia:** `uv add icalendar`.
3. **Implementar `leer_eventos`** en `src/calendar_reader/__init__.py`.
4. **Dato de prueba:** mover el `.ics` a `tests/fixtures/calendario_test.ics`.
5. **Script manual:** crear `scripts/probar_calendario.py`, que llama a
   `leer_eventos` con el `.ics` de fixtures y lo imprime.
6. **Documentacion:** `README.md` con la firma, ejemplo de uso y limitaciones.

Pendiente:

7. **Ejecutar el script** contra el `.ics` real para validar la salida.
   `uv run python scripts/probar_calendario.py`

## Fuera de alcance

- CLI y entrypoint de consola.
- Expansion de recurrencias (`RRULE`).
- Eventos de dia completo.
- Tests automaticos (se anadiran con `pytest` cuando haga falta).
- Exportacion a Excel/JSON y la futura webapp.

## Riesgos conocidos

- Si apareciera un evento flotante (sin zona), `.astimezone(MADRID)` lo
  interpreta como hora del sistema; no se espera en este calendario.
- El codigo se valida solo con el script manual, no con tests automaticos.
